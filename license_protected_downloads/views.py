import importlib
import logging
import json
import mimetypes
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
from django.utils.encoding import smart_str, iri_to_uri
from django.views.decorators.csrf import csrf_exempt

from buildinfo import BuildInfo, IncorrectDataFormatException
from render_text_files import RenderTextFiles
from models import License
from BeautifulSoup import BeautifulSoup
import config
from group_auth_common import GroupAuthError
import xml.dom.minidom as dom

from license_protected_downloads.common import (
    dir_list,
    is_protected,
    test_path
)
from license_protected_downloads.api.v1 import file_server_post

# Load group auth "plugin" dynamically
group_auth_modules = [
    importlib.import_module(m) for m in settings.GROUP_AUTH_MODULES]

LINARO_INCLUDE_FILE_RE = re.compile(
    r'<linaro:include file="(?P<file_name>.*)"[ ]*/>')
LINARO_INCLUDE_FILE_RE1 = re.compile(
    r'<linaro:include file="(?P<file_name>.*)">(.*)</linaro:include>')

log = logging.getLogger("llp.views")


def _get_header_html_content(path):
    """
        Read HEADER.html in current directory if exists and return
        contents of <div id="content"> block to include in rendered
        html.
    """
    header_html = os.path.join(path, "HEADER.html")
    header_content = u""
    if os.path.isfile(header_html):
        with open(header_html, "r") as infile:
            body = infile.read()
        orig = os.getcwd()
        try:
            os.chdir(path)
            body = _process_include_tags(body)
        finally:
            os.chdir(orig)
        soup = BeautifulSoup(body)
        for chunk in soup.findAll(id="content"):
            header_content += chunk.prettify().decode("utf-8")
        header_content = '\n'.join(header_content.split('\n')[1:-1])

    return header_content


def is_same_parent_dir(parent, filename):
    """
        Checks if filename's parent dir is parent.
    """
    full_filename = os.path.join(parent, filename)
    normalized_path = os.path.normpath(os.path.realpath(full_filename))
    if parent == os.path.dirname(normalized_path):
        return True

    return False


def read_file_with_include_data(matchobj):
    """
        Function to get data for re.sub() in _process_include_tags() from file
        which name is in named match group 'file_name'.
        Returns content of file in current directory otherwise empty string.
    """
    content = ''
    current_dir = os.getcwd()
    fname = matchobj.group('file_name')
    if is_same_parent_dir(current_dir, fname):
        if os.path.isfile(fname) and not os.path.islink(fname):
            with open(fname, "r") as infile:
                content = infile.read()

    return content


def _process_include_tags(content):
    """
        Replaces <linaro:include file="README" /> or
        <linaro:include file="README">text to show</linaro:include> tags
        with content of README file or empty string if file not found or
        not allowed.
    """
    content = re.sub(LINARO_INCLUDE_FILE_RE,
                     read_file_with_include_data,
                     content)
    content = re.sub(LINARO_INCLUDE_FILE_RE1,
                     read_file_with_include_data,
                     content)
    return content


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


def file_listed(path, url):
    """Boolean response to "does this files show up in a directory listing."""
    file_name = os.path.basename(path)
    dir_name = os.path.dirname(path)

    found = False
    file_list = dir_list(url, dir_name)
    for file in file_list:
        if file["name"] == file_name:
            found = True

    return found


def is_whitelisted(url):
    """ Check if requested file is under whitelisted path.
    """
    found = False
    for path in config.WHITELIST:
        if re.search(r'^%s' % path, url):
            found = True

    return found


def send_file(path):
    "Return HttpResponse which will send path to user's browser."
    file_name = os.path.basename(path)
    mimetypes.init()
    mime = mimetypes.guess_type(path)[0]
    if mime is None:
        mime = "application/force-download"
    response = HttpResponse(mimetype=mime)
    response['Content-Disposition'] = ('attachment; filename=%s' %
                                       smart_str(file_name))
    response['X-Sendfile'] = smart_str(path)
    # response['Content-Length'] = os.path.getsize(path)
    # TODO: Is it possible to add a redirect to response so we can take
    # the user back to the original directory this file is in?
    return response


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


def _check_build_info(request, path):
    try:
        build_info = BuildInfo(path)
    except IncorrectDataFormatException:
        # If we can't parse the BuildInfo. Return a HttpResponseForbidden.
        return HttpResponseForbidden('Error parsing BUILD-INFO.txt')

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


def _handle_dir_list(request, url, path):
    # Generate a link to the parent directory (if one exists)
    if url != '/' and url != '':
        up_dir = "/" + os.path.split(url)[0]
    else:
        up_dir = None

    header_content = _get_header_html_content(path)
    download = None
    if 'dl' in request.GET:
        download = request.GET['dl']
    rendered_files = RenderTextFiles.find_and_render(path)
    if os.path.exists(os.path.join(path, settings.ANNOTATED_XML)):
        if rendered_files is None:
            rendered_files = {}
        rendered_files["Git Descriptions"] = render_descriptions(path)

    dirlist = dir_list(url, path)
    lics = [x['license_digest_list'] for x in dirlist
            if x['license_digest_list']]

    args = {
        'dirlist': dirlist,
        'up_dir': up_dir,
        'dl': download,
        'header_content': header_content,
        'request': request,
        'rendered_files': rendered_files,
        'hide_lics': len(lics) == 0,
    }
    return render(request, 'dir_template.html', args)


def file_server_get(request, path):

    url = path
    result = test_path(path, request)
    internal = get_client_ip(request) in config.INTERNAL_HOSTS

    target_type = result[0]
    path = result[1]

    if not internal and BuildInfo.build_info_exists(path):
        resp = _check_build_info(request, path)
        if resp:
            return resp

    if target_type == "dir":
        return _handle_dir_list(request, url, path)

    # If the file listing doesn't contain the file requested for download,
    # return a 404. This prevents the download of BUILD-INFO.txt and other
    # hidden files.
    if not file_listed(path, url):
        raise Http404

    if (internal or
        is_whitelisted(os.path.join('/', url)) or
        "key" in request.GET):  # If user has a key, default to open
        digests = 'OPEN'
    else:
        digests = is_protected(path)

    response = None
    if not digests:
        # File has no license text but is protected
        response = HttpResponseForbidden(
            "You do not have permission to access this file.")
    elif digests == "OPEN":
        response = None
    else:
        for digest in digests:
            if not license_accepted(request, digest):
                # Make sure that user accepted each license one by one
                response = redirect(
                    '/license?lic=' + digest + "&url=" + url)
                break

    # If we didn't have any other response, it's ok to send file now
    if not response:
        response = send_file(path)

    return response


def get_textile_files(request):
    path = test_path(request.GET.get("path"), request)[1]
    rendered_files = RenderTextFiles.find_and_render(path)
    if os.path.exists(os.path.join(path, settings.ANNOTATED_XML)):
        if rendered_files is None:
            rendered_files = {}
        rendered_files["Git Descriptions"] = render_descriptions(path)

    return HttpResponse(json.dumps(rendered_files))


def render_descriptions(path):
    """
       Extracts project name and its description from annotated source manifest
       and returns html string to include in tab.
    """
    text = ''
    line = '<p><strong>Project:</strong> "%s"<br>' \
           '<strong>Description:</strong> "%s"</p>'
    filename = os.path.join(path, settings.ANNOTATED_XML)
    xmldoc = dom.parse(filename)
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
