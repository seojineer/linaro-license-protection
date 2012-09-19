import glob
import hashlib
import mimetypes
import os
import re
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
from django.utils.encoding import smart_str

import bzr_version
from buildinfo import BuildInfo, IncorrectDataFormatException
from models import License
from openid_auth import OpenIDAuth
from BeautifulSoup import BeautifulSoup
import config


LINARO_INCLUDE_FILE_RE = re.compile(r'<linaro:include file="(?P<file_name>.*)"[ ]*/>')
LINARO_INCLUDE_FILE_RE1 = re.compile(r'<linaro:include file="(?P<file_name>.*)">(.*)</linaro:include>')


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


def dir_list(url, path):
    files = os.listdir(path)
    files.sort()
    listing = []

    for file in files:
        if _hidden_file(file):
            continue

        name = file
        file = os.path.join(path, file)

        if os.path.exists(file):
            mtime = datetime.fromtimestamp(os.path.getmtime(file)).strftime('%d-%b-%Y %H:%M')
        else:
            # If the file we are looking at doesn't exist (broken symlink for
            # example), it doesn't have a mtime.
            mtime = 0

        type = "other"
        if os.path.isdir(file):
            type = "folder"
        else:
            type_tuple = guess_type(name)
            if type_tuple and type_tuple[0]:
                if type_tuple[0].split('/')[0] == "text":
                    type = "text"

        if os.path.exists(file):
            size = os.path.getsize(file)
        else:
            # If the file we are looking at doesn't exist (broken symlink for
            # example), it doesn't have a size
            size = 0

        if not re.search(r'^/', url) and url != '':
            url = '/' + url

        # Since the code below assume no trailing slash, make sure that
        # there isn't one.
        url = re.sub(r'/$', '', url)

        pathname = os.path.join(path, name)
        license_digest_list = is_protected(pathname)
        license_list = License.objects.all_with_hashes(license_digest_list)
        listing.append({'name': name,
                        'size': _sizeof_fmt(size),
                        'type': type,
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


def read_file_with_include_data(matchobj):
    """
        Function to get data for re.sub() in _process_include_tags() from file
        which name is in named match group 'file_name'.
        Returns content of file in current directory otherwise empty string.
    """
    content = ''
    fname = matchobj.group('file_name')
    current_dir = os.getcwd()
    full_filename = os.path.join(current_dir, fname)
    normalized_path = os.path.normpath(os.path.realpath(full_filename))
    if current_dir == os.path.dirname(normalized_path):
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
    buildinfo_path = os.path.join(os.path.dirname(path), "BUILD-INFO.txt")
    open_eula_path = os.path.join(os.path.dirname(path), "OPEN-EULA.txt")
    eula_path = os.path.join(os.path.dirname(path), "EULA.txt")

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
        openid_teams = build_info.get("openid-launchpad-teams")
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
        openid_teams = False
        with open(license_file, "r") as infile:
            license_text = infile.read()
    elif _check_special_eula(path):
        theme = _get_theme(path)
        license_type = "protected"
        license_file = os.path.join(settings.PROJECT_ROOT,
                                    'templates/licenses/' + theme + '.txt')
        openid_teams = False
        with open(license_file, "r") as infile:
            license_text = infile.read()
    elif _check_special_eula(os.path.dirname(path) + "/*"):
        return "OPEN"
    else:
        return []

    digests = []

    if license_type:
        if license_type == "open":
            return "OPEN"

        # File matches a license, isn't open.
        if openid_teams:
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


def file_server(request, path):
    """Serve up a file / directory listing or license page as required"""
    url = path
    result = test_path(path)
    if not result:
        raise Http404

    type = result[0]
    path = result[1]

    if BuildInfo.build_info_exists(path):
        try:
            build_info = BuildInfo(path)
        except IncorrectDataFormatException:
            # If we can't parse the BuildInfo. Return a HttpResponseForbidden.
            return HttpResponseForbidden(
                "Error parsing BUILD-INFO.txt")

        launchpad_teams = build_info.get("openid-launchpad-teams")
        if launchpad_teams:
            launchpad_teams = launchpad_teams.split(",")
            launchpad_teams = [team.strip() for team in launchpad_teams]
            openid_response = OpenIDAuth.process_openid_auth(
                request, launchpad_teams)
            if openid_response:
                return openid_response

    if type == "dir":
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
                                   'header_content': header_content})

    file_name = os.path.basename(path)

    # If the file listing doesn't contain the file requested for download,
    # return a 404. This prevents the download of BUILD-INFO.txt and other
    # hidden files.
    if not file_listed(path, url):
        raise Http404

    response = None
    if get_client_ip(request) in config.INTERNAL_HOSTS or\
       is_whitelisted(os.path.join('/', url)):
        digests = 'OPEN'
    else:
        digests = is_protected(path)
    if not digests:
        # File has no license text but is protected
        response = HttpResponseForbidden(
            "You do not have permission to access this file.")

    # Return a file...
    else:
        if digests == "OPEN":
            response = None
        else:
            for digest in digests:
                if not license_accepted(request, digest):
                    response = redirect(
                        '/license?lic=' + digest + "&url=" + url)

        if not response:
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
