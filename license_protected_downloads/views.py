import datetime
import importlib
import logging
import json
import os
import re
import sys

from django.conf import settings
from django.http import (
    Http404,
    HttpResponse,
    HttpResponseForbidden,
    HttpResponseRedirect,
)
from django.shortcuts import render, redirect
from django.utils.encoding import iri_to_uri
from django.views.decorators.csrf import csrf_exempt

from buildinfo import IncorrectDataFormatException
from render_text_files import RenderTextFiles
from models import License, Download
import config
from group_auth_common import GroupAuthError
import xml.dom.minidom as dom

from license_protected_downloads.common import (
    cached_call,
    dir_list,
    find_artifact,
    s3_replace_latest,
)
from license_protected_downloads.api.v1 import file_server_post

# Load group auth "plugin" dynamically
group_auth_modules = [
    importlib.import_module(m) for m in settings.GROUP_AUTH_MODULES]

log = logging.getLogger("llp.views")


def get_client_ip(request):
    # use forwarded_for if it was set
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def license_accepted(request, digest):
    license_header = "HTTP_LICENSE_ACCEPTED"
    if license_header in request.META:
        if digest in request.META[license_header].split():
            return True

    return 'license_accepted_' + digest in request.COOKIES


def accept_license(request):
    if "accept" in request.POST:
        lic = License.objects.filter(digest=request.GET['lic']).get()
        file_url = request.GET['url']
        listing_url = os.path.dirname(file_url)
        response = HttpResponseRedirect(listing_url +
                                        "?dl=/" + file_url)
        d = lic.digest
        cookie_name = "license_accepted_" + d.encode("ascii")
        # Set a cookie with 1 day of expiry.
        response.set_cookie(cookie_name,
                            max_age=60 * 60 * 24,
                            path="/" + os.path.dirname(file_url))
    else:
        response = render(request, 'licenses/nolicense.html')

    return response


def show_license(request):
    if 'lic' not in request.GET or 'url' not in request.GET:
        raise Http404

    lic = License.objects.filter(digest=request.GET['lic']).get()

    return render(request, 'licenses/' + lic.theme + '.html',
                  {'license': lic, 'url': request.GET['url']})


def redirect_to_root(request):
    return redirect('/')


def is_whitelisted(url):
    """ Check if requested file is under whitelisted path.
    """
    found = False
    for path in config.WHITELIST:
        if re.search(r'^%s' % path, url):
            found = True

    return found


def group_auth_failed_response(request, auth_groups):
    """Construct a nice response detailing list of auth groups that
    will allow access to the requested file."""
    if len(auth_groups) > 1:
        groups_string = "one of the "
        groups_string += ", ".join(auth_groups[0:-1])
        groups_string += " or " + auth_groups[-1] + " groups"
    else:
        groups_string = "the " + auth_groups[0] + " group"

    response = render(request, 'openid_forbidden_template.html',
                      {'login': settings.LOGIN_URL + "?next=" + request.path,
                       'authenticated': request.user.is_authenticated(),
                       'groups_string': groups_string,
                       })

    response.status_code = 403
    return response


@csrf_exempt
def file_server(request, path):
    """Serve up a file / directory listing or license page as required"""
    path = iri_to_uri(path)
    if "/latest" in path:
        new_path = s3_replace_latest(path, None)

        if new_path != path:
            return redirect('/'+new_path)

    if request.method == "POST":
        return file_server_post(request, path)
    elif request.method in ('GET', 'HEAD'):
        return file_server_get(request, path)


def _check_build_info(request, build_info):
    auth_groups = build_info.get('auth-groups')
    if auth_groups:
        auth_groups = [x.strip() for x in auth_groups.split(',')]
        log.info('Checking membership in auth groups: %s', auth_groups)
        response = False
        try:
            for m in group_auth_modules:
                response = m.process_group_auth(request, auth_groups)
                if response:
                    break
        except GroupAuthError:
            log.exception("GroupAuthError")
            response = render(request, 'group_auth_failure.html')
            response.status_code = 500
            return response

        if response is False:
            return group_auth_failed_response(request, auth_groups)
        elif response is not True:
            return response


def _handle_dir_list(request, artifact):
    download = None
    if 'dl' in request.GET:
        download = request.GET['dl']
    elif request.path[-1] != '/':
        return redirect(request.path + '/')

    # Generate a link to the parent directory (if one exists)
    url = artifact.url()
    if url != '/':
        if url[-1] == '/':
            # we must remove trailing slash to find parent
            url = url[:-1]
        up_dir = os.path.split(url)[0]
        if up_dir[-1] != '/':
            # now we need the trailing slash
            up_dir += '/'
    else:
        up_dir = None

    # must come before call to find_and_render to optimize s3
    dirlist = dir_list(artifact)
    rendered_files = RenderTextFiles.find_and_render(artifact)
    ann = artifact.get_annotated_manifest()
    if ann:
        rendered_files["Git Descriptions"] = render_descriptions(ann)

    lics = [x['license_digest_list'] for x in dirlist
            if x['license_digest_list']]

    args = {
        'dirlist': dirlist,
        'up_dir': up_dir,
        'dl': download,
        'header_content': artifact.get_header_html(),
        'request': request,
        'rendered_files': rendered_files,
        'hide_lics': len(lics) == 0,
    }
    return render(request, 'dir_template.html', args)


def _check_file_permission(request, artifact, internal):
    url = artifact.url()
    if internal or is_whitelisted(url) or \
            'key' in request.GET:  # If user has a key, default to open
        digests = 'OPEN'
    else:
        digests = artifact.get_license_digests()

    response = None
    if not digests:
        # File has no license text but is protected
        response = HttpResponseForbidden(
            'You do not have permission to access this file.')
    elif digests != 'OPEN':
        for digest in digests:
            if not license_accepted(request, digest):
                # Make sure that user accepted each license one by one
                assert url[0] == '/'
                url = url[1:]  # remove leading /
                response = redirect('/license?lic=' + digest + '&url=' + url)
                break
    return response


def file_server_get(request, path):
    artifact = cached_call(path, find_artifact, request, path)
    internal = get_client_ip(request) in config.INTERNAL_HOSTS

    if not internal:
        try:
            bi = artifact.get_build_info()
        except IncorrectDataFormatException:
            return HttpResponseForbidden('Error parsing BUILD-INFO.txt')
        if bi:
            resp = _check_build_info(request, bi)
            if resp:
                return resp

    if artifact.isdir():
        return cached_call(path, _handle_dir_list, request, artifact)

    # prevent download of files like BUILD-INFO.txt
    if artifact.hidden():
        raise Http404

    resp = _check_file_permission(request, artifact, internal)
    if resp:
        return resp

    if request.method == 'GET':
        Download.mark(request, artifact)
    force_http = not request.is_secure()
    return artifact.get_file_download_response(request.method, force_http)


def get_textile_files(request):
    artifact = find_artifact(request, request.GET.get("path"))
    dir_list(artifact)  # required for s3
    rendered_files = RenderTextFiles.find_and_render(artifact)
    ann = artifact.get_annotated_manifest()
    if ann:
        rendered_files["Git Descriptions"] = render_descriptions(ann)

    return HttpResponse(json.dumps(rendered_files))


def render_descriptions(buf):
    """
       Extracts project name and its description from annotated source manifest
       and returns html string to include in tab.
    """
    text = ''
    line = '<p><strong>Project:</strong> "%s"<br>' \
           '<strong>Description:</strong> "%s"</p>'
    xmldoc = dom.parseString(buf)
    nodes = xmldoc.documentElement.childNodes

    for index, node in enumerate(nodes):
        if node.nodeType == node.COMMENT_NODE:
            comment = nodes[index]
            commentedNode = nodes[index + 2]
            text += line % (commentedNode.getAttribute('name'),
                            comment.data.strip())

    return text


def error_view(request, template_name='500.html'):
    # the django error handler doesn't use the request context. We need this
    # because it sets the 'base_page' variable required for our template
    # to work across different "publishing themes"

    # produce an error message like:
    #  RuntimeError at <path>/license_protected_downloads/views.py:228
    ex, _, tb = sys.exc_info()
    while tb.tb_next:
        tb = tb.tb_next
    ex = '%s at %s:%d' % (
        ex.__name__, tb.tb_frame.f_code.co_filename, tb.tb_lineno)
    return render(request, template_name, {'exception': ex}, status=500)


def group_authenticated(group):
    def wrap(f):
        def wrapped_f(*args, **kwargs):
            resp = _check_build_info(args[0], {'auth-groups': group})
            if resp:
                return resp
            return f(*args, **kwargs)
        return wrapped_f
    return wrap


@group_authenticated('linaro')
def reports(request):
    # Start with the oldest month we have a download from and build up a list.
    months = []
    cur = Download.objects.order_by('timestamp')[0].timestamp
    now = datetime.datetime.now()

    while (100 * cur.year) + cur.month < (100 * now.year) + now.month:
        months.append(cur.strftime('%Y.%m'))
        cur = Download.next_month(cur)
    months.append(now.strftime('%Y.%m'))
    months.reverse()

    args = {
        'months': months,
    }
    return render(request, 'report_cycles.html', args)


@group_authenticated('linaro')
def reports_month_downloads(request, year_month):
    downloads = Download.report(year_month, 'name')
    if request.GET.get('by', 'build') == 'build':
        label = 'Build'
        downloads = [x for x in downloads if 'components' not in x['name']]
    else:
        label = 'Component'
        downloads = [x for x in downloads if 'components' in x['name']]

    args = {
        'label': label,
        'year_month': year_month,
        'downloads': downloads,
    }
    return render(request, 'report_downloads.html', args)


def reports_month_file_downloads(request, year_month, name):
    downloads = Download.report(year_month, 'region_isp', name=name)
    args = {
        'name': name,
        'year_month': year_month,
        'downloads': downloads,
    }
    return render(request, 'report_file.html', args)


@group_authenticated('linaro')
def _geo_report(request, year_month, column, label):
    downloads = {}
    # We have to go in 2 passes, the first pass gets the total
    # the 2nd pass gets total of components (and we can then calculate builds).
    for x in Download.report(year_month, column):
        e = downloads.setdefault(
            x[column],
            {'geo': x[column], 'components': 0, 'builds': 0})
        e['total'] = x['count']
        e['builds'] = x['count']  # in case no components are hit below

    for x in Download.report(year_month, column, name__contains='components'):
        e = downloads[x[column]]
        e['components'] = x['count']
        e['builds'] = e['total'] - x['count']

    args = {
        'column': column,
        'label': label,
        'year_month': year_month,
        'downloads': sorted(
            downloads.values(), key=lambda x: x['total'], reverse=True),
    }
    return render(request, 'report_geo.html', args)


def reports_month_country(request, year_month):
    return _geo_report(request, year_month, 'country', 'Country')


def reports_month_region(request, year_month):
    return _geo_report(request, year_month, 'region_isp', 'Region/ISP')


@group_authenticated('linaro')
def _geo_details(request, year_month, column, value):
    extra_filters = {column: value}
    downloads = Download.report(year_month, 'name', **extra_filters)
    args = {
        'label': value,
        'year_month': year_month,
        'downloads': downloads,
    }
    return render(request, 'report_downloads.html', args)


def reports_month_country_details(request, year_month, country):
    return _geo_details(request, year_month, 'country', country)


def reports_month_region_details(request, year_month, region):
    return _geo_details(request, year_month, 'region_isp', region)
