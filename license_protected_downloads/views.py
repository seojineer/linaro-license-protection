import logging
import glob
import hashlib
import json
import mimetypes
import os
import re
import urllib2
from mimetypes import guess_type
from datetime import datetime

from django.conf import settings
from django.http import (
    Http404,
    HttpResponse,
    HttpResponseForbidden,
    HttpResponseRedirect,
)
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from django.utils.encoding import smart_str, iri_to_uri

import bzr_version
from buildinfo import BuildInfo, IncorrectDataFormatException
from render_text_files import RenderTextFiles
from models import License
# Load group auth "plugin" dynamically
import importlib
group_auth = importlib.import_module(settings.GROUP_AUTH_MODULE)
from BeautifulSoup import BeautifulSoup
import config
from group_auth_common import GroupAuthError


LINARO_INCLUDE_FILE_RE = re.compile(
    r'<linaro:include file="(?P<file_name>.*)"[ ]*/>')
LINARO_INCLUDE_FILE_RE1 = re.compile(
    r'<linaro:include file="(?P<file_name>.*)">(.*)</linaro:include>')

log = logging.getLogger("llp.views")


def _hidden_file(file_name):
    hidden_files = ["BUILD-INFO.txt", "EULA.txt", r"^\.", "HEADER.html"]
    for pattern in hidden_files:
        if re.search(pattern, file_name):
            return True
    return False


def _hidden_dir(file_name):
    hidden_files = [".*openid.*", ".*restricted.*", ".*private.*", r"^\."]
    for pattern in hidden_files:
        if re.search(pattern, file_name):
            return True
    return False


def _sizeof_fmt(num):
    ''' Returns in human readable format for num.
    '''
    if num < 1024 and num > -1024:
        return str(num)
    num /= 1024.0
    for x in ['K', 'M', 'G']:
        if num < 1024.0 and num > -1024.0:
            return "%3.1f%s" % (num, x)
        num /= 1024.0
    return "%3.1f%s" % (num, 'T')


def dir_list(url, path, human_readable=True):
    files = os.listdir(path)
    files.sort()
    listing = []

    for file_name in files:
        if _hidden_file(file_name):
            continue

        name = file_name
        file_name = os.path.join(path, file_name)

        if os.path.exists(file_name):
            mtime = os.path.getmtime(file_name)
        else:
            # If the file we are looking at doesn't exist (broken symlink for
            # example), it doesn't have a mtime.
            mtime = 0

        if os.path.isdir(file_name):
            target_type = "folder"
        else:
            target_type = guess_type(name)[0]

        if os.path.exists(file_name):
            size = os.path.getsize(file_name)
        else:
            # If the file we are looking at doesn't exist (broken symlink for
            # example), it doesn't have a size
            size = 0

        if not re.search(r'^/', url) and url != '':
            url = '/' + url

        # Since the code below assume no trailing slash, make sure that
        # there isn't one.
        url = re.sub(r'/$', '', url)

        if human_readable:
            if mtime:
                mtime = datetime.fromtimestamp(mtime).strftime(
                                                        '%d-%b-%Y %H:%M')
            if target_type:
                if target_type.split('/')[0] == "text":
                    target_type = "text"
            else:
                target_type = "other"

            size = _sizeof_fmt(size)

        pathname = os.path.join(path, name)
        license_digest_list = is_protected(pathname)
        license_list = License.objects.all_with_hashes(license_digest_list)
        listing.append({'name': name,
                        'size': size,
                        'type': target_type,
                        'mtime': mtime,
                        'license_digest_list': license_digest_list,
                        'license_list': license_list,
                        'url': url + '/' + name})
    return listing


def test_path(path):

    for basepath in settings.SERVED_PATHS:
        fullpath = os.path.join(basepath, path)
        if os.path.isfile(fullpath):
            return ("file", fullpath)
        if os.path.isdir(fullpath):
            return ("dir", fullpath)

    return None


def _insert_license_into_db(digest, text, theme):
    if not License.objects.filter(digest=digest):
        l = License(digest=digest, text=text, theme=theme)
        l.save()


def _check_special_eula(path):
    if glob.glob(path + ".EULA.txt.*"):
        return True


def _get_theme(path):
    eula = glob.glob(path + ".EULA.txt.*")
    vendor = os.path.splitext(eula[0])[1]
    return vendor[1:]


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
        body = _process_include_tags(body)
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


def is_protected(path):
    build_info = None
    max_index = 1
    base_path = path
    if not os.path.isdir(base_path):
        base_path = os.path.dirname(base_path)

    buildinfo_path = os.path.join(base_path, "BUILD-INFO.txt")
    open_eula_path = os.path.join(base_path, "OPEN-EULA.txt")
    eula_path = os.path.join(base_path, "EULA.txt")

    if os.path.isfile(buildinfo_path):
        try:
            build_info = BuildInfo(path)
        except IncorrectDataFormatException:
            # If we can't parse the BuildInfo, return [], which indicates no
            # license in dir_list and will trigger a 403 error in file_server.
            return []

        license_type = build_info.get("license-type")
        license_text = build_info.get("license-text")
        theme = build_info.get("theme")
        auth_groups = build_info.get("auth-groups")
        max_index = build_info.max_index
    elif os.path.isfile(open_eula_path):
        return "OPEN"
    elif os.path.isfile(eula_path):
        if re.search("snowball", path):
            theme = "stericsson"
        elif re.search("origen", path):
            theme = "samsung"
        else:
            theme = "linaro"
        license_type = "protected"
        license_file = os.path.join(settings.PROJECT_ROOT,
                                    'templates/licenses/' + theme + '.txt')
        auth_groups = False
        with open(license_file, "r") as infile:
            license_text = infile.read()
    elif _check_special_eula(path):
        theme = _get_theme(path)
        license_type = "protected"
        license_file = os.path.join(settings.PROJECT_ROOT,
                                    'templates/licenses/' + theme + '.txt')
        auth_groups = False
        with open(license_file, "r") as infile:
            license_text = infile.read()
    elif _check_special_eula(base_path + "/*"):
        return "OPEN"
    else:
        return []

    digests = []

    if license_type:
        if license_type == "open":
            return "OPEN"

        # File matches a license, isn't open.
        if auth_groups:
            return "OPEN"
        elif license_text:
            for i in range(max_index):
                if build_info is not None:
                    license_text = build_info.get("license-text", i)
                    theme = build_info.get("theme", i)
                digest = hashlib.md5(license_text).hexdigest()
                digests.append(digest)
                _insert_license_into_db(digest, license_text, theme)
        else:
            # No license text - file as inaccessible.
            return []
    else:
        # No license found - file is inaccessible.
        return []

    return digests


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
        response = render_to_response('licenses/nolicense.html')

    return response


def show_license(request):
    if 'lic' not in request.GET or 'url' not in request.GET:
        raise Http404

    lic = License.objects.filter(digest=request.GET['lic']).get()

    return render_to_response('licenses/' + lic.theme + '.html',
                              {'license': lic,
                               'url': request.GET['url'],
                               'revno': bzr_version.get_my_bzr_revno(),
                               },
                              context_instance=RequestContext(request))


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
    #response['Content-Length'] = os.path.getsize(path)
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

    response = render_to_response(
        'openid_forbidden_template.html',
        {'login': settings.LOGIN_URL + "?next=" + request.path,
         'authenticated': request.user.is_authenticated(),
         'groups_string': groups_string,
         'revno': bzr_version.get_my_bzr_revno(),
         })

    response.status_code = 403
    return response


def file_server(request, path):
    """Serve up a file / directory listing or license page as required"""
    path = iri_to_uri(path)
    url = path
    result = test_path(path)
    if not result:
        raise Http404

    target_type = result[0]
    path = result[1]

    if get_client_ip(request) in config.INTERNAL_HOSTS:
        # For internal trusted hosts, short-circuit any further checks
        return send_file(path)

    if BuildInfo.build_info_exists(path):
        try:
            build_info = BuildInfo(path)
        except IncorrectDataFormatException:
            # If we can't parse the BuildInfo. Return a HttpResponseForbidden.
            return HttpResponseForbidden(
                "Error parsing BUILD-INFO.txt")

        auth_groups = build_info.get("auth-groups")
        if auth_groups:
            auth_groups = auth_groups.split(",")
            auth_groups = [g.strip() for g in auth_groups]
            log.info("Checking membership in auth groups: %s", auth_groups)
            try:
                response = group_auth.process_group_auth(request, auth_groups)
            except GroupAuthError:
                log.exception("GroupAuthError")
                response = render_to_response('group_auth_failure.html')
                response.status_code = 500
                return response

            if response == False:
                return group_auth_failed_response(request, auth_groups)
            elif response == True:
                pass
            else:
                return response

    if target_type == "dir":
        # Generate a link to the parent directory (if one exists)
        if url != '/' and url != '':
            up_dir = "/" + os.path.split(url)[0]
        else:
            up_dir = None

        old_cwd = os.getcwd()
        os.chdir(path)
        header_content = _get_header_html_content(path)
        os.chdir(old_cwd)
        download = None
        if 'dl' in request.GET:
            download = request.GET['dl']

        return render_to_response('dir_template.html',
                                  {'dirlist': dir_list(url, path),
                                   'up_dir': up_dir,
                                   'dl': download,
                                   'revno': bzr_version.get_my_bzr_revno(),
                                   'header_content': header_content,
                                   'request': request,
                                   'rendered_files':
                                   RenderTextFiles.find_and_render(path)
                                   })

    # If the file listing doesn't contain the file requested for download,
    # return a 404. This prevents the download of BUILD-INFO.txt and other
    # hidden files.
    if not file_listed(path, url):
        raise Http404

    if get_client_ip(request) in config.INTERNAL_HOSTS or\
       is_whitelisted(os.path.join('/', url)):
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

    result = test_path(request.GET.get("path"))
    if not result:
        raise Http404

    path = result[1]

    return HttpResponse(json.dumps(RenderTextFiles.find_and_render(path)))


def get_remote_static(request):
    """Fetches remote static files based on the dict map in settings.py."""
    name = request.GET.get("name")
    if name not in settings.SUPPORTED_REMOTE_STATIC_FILES:
        raise Http404("File name not supported.")

    try:
        data = urllib2.urlopen(settings.SUPPORTED_REMOTE_STATIC_FILES[name])
    except urllib2.HTTPError:
        # TODO: send an email to infrastructure-errors list,
        # then implement raising of Http404 instead of HTTPError
        raise

    return HttpResponse(data)


def list_files_api(request, path):
    path = iri_to_uri(path)
    url = path
    result = test_path(path)
    if not result:
        raise Http404

    target_type = result[0]
    path = result[1]

    if target_type:
        if target_type == "file":
            file_url = url
            if file_url[0] != "/":
                file_url = "/" + file_url
            path = os.path.dirname(path)
            url = os.path.dirname(url)

        listing = dir_list(url, path, human_readable=False)

        clean_listing = []
        for entry in listing:
            if target_type == "file" and file_url != entry["url"]:
                # If we are getting a listing for a single file, skip the rest
                continue

            if len(entry["license_list"]) == 0:
                entry["license_list"] = ["Open"]

            clean_listing.append({
                "name": entry["name"],
                "size": entry["size"],
                "type": entry["type"],
                "mtime": entry["mtime"],
                "url": entry["url"],
            })

        data = json.dumps({"files": clean_listing})
    else:
        data = json.dumps({"files": ["File not found."]})

    return HttpResponse(data, mimetype='application/json')


def get_license_api(request, path):
    path = iri_to_uri(path)
    result = test_path(path)
    if not result:
        raise Http404

    target_type = result[0]
    path = result[1]

    if target_type == "dir":
        data = json.dumps({"licenses":
                           ["ERROR: License only shown for a single file."]})
    else:
        license_digest_list = is_protected(path)
        license_list = License.objects.all_with_hashes(license_digest_list)
        if len(license_list) == 0:
            license_list = ["Open"]
        else:
            license_list = [{"text": l.text, "digest": l.digest}
                            for l in license_list]
        data = json.dumps({"licenses": license_list})

    return HttpResponse(data, mimetype='application/json')
