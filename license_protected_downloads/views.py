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
from models import License
import config
from group_auth_common import GroupAuthError
import xml.dom.minidom as dom

from license_protected_downloads.common import (
    dir_list,
    find_artifact,
)
from license_protected_downloads.api.v1 import file_server_post

# Load group auth "plugin" dynamically
group_auth_modules = [
    importlib.import_module(m) for m in settings.GROUP_AUTH_MODULES]

log = logging.getLogger("llp.views")


def get_client_ip(request):
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
        groups_string = "one of the " + auth_groups.pop(0) + " "
        if len(auth_groups) > 1:
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

    # Intercept post requests and send them to file_server_post.
    if request.method == "POST":
        return file_server_post(request, path)

    # GET requests are handled by file_server_get
    elif request.method == "GET":
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
    if request.path[-1] != '/':
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

    download = None
    if 'dl' in request.GET:
        download = request.GET['dl']
    rendered_files = RenderTextFiles.find_and_render(artifact)
    ann = artifact.get_annotated_manifest()
    if ann:
        rendered_files["Git Descriptions"] = render_descriptions(ann)

    dirlist = dir_list(artifact)
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
    artifact = find_artifact(request, path)
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
        return _handle_dir_list(request, artifact)

    # prevent download of files like BUILD-INFO.txt
    if artifact.hidden():
        raise Http404

    resp = _check_file_permission(request, artifact, internal)
    if resp:
        return resp
    return artifact.get_file_download_response()


def get_textile_files(request):
    artifact = find_artifact(request, request.GET.get("path"))
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
