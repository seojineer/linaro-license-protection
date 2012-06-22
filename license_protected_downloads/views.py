# Create your views here.

from django.http import (
    HttpResponse, HttpResponseRedirect, HttpResponseForbidden
)
from django.conf import settings
from django.shortcuts import render_to_response, redirect
import os.path
import os
from django.http import Http404
from django.utils.encoding import smart_str
from buildinfo import BuildInfo
import time
import re
import hashlib
from mimetypes import guess_type
from models import License
from django.template import RequestContext

def _hidden_file(file_name):
    hidden_files = ["BUILD-INFO.txt", "EULA.txt", "OPEN-EULA.txt"]
    for pattern in hidden_files:
        if re.search(pattern, file_name):
            return True
    return False

def _hidden_dir(file_name):
    hidden_files = [".*openid.*", ".*restricted.*", ".*private.*"]
    for pattern in hidden_files:
        if re.search(pattern, file_name):
            return True
    return False

def dir_list(path):
    files = os.listdir(path)
    listing = []

    for file in files:
        if _hidden_file(file):
            continue

        name = file
        file = os.path.join(path, file)
        mtime = time.ctime(os.path.getmtime(file))

        type = "other"
        if os.path.isdir(file):
            type = "folder"
        else:
            type_tuple = guess_type(name)
            if type_tuple and type_tuple[0]:
                if type_tuple[0].split('/')[0] == "text":
                    type = "text"

        size = os.path.getsize(file)
        listing.append({'name': name,
                        'size': size,
                        'type': type,
                        'mtime': mtime})
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

def is_protected(path):
    buildinfo_path = os.path.join(os.path.dirname(path), "BUILD-INFO.txt")
    if os.path.isfile(buildinfo_path):
        build_info = BuildInfo()
        build_info.parse_buildinfo(buildinfo_path)
    else:
        return []

    digests = []
    for info in build_info.data:
        if "files-pattern" not in info or "license-type" not in info:
            continue

        file_name = os.path.basename(path)
        if re.search(info["files-pattern"], file_name):
            if info["license-type"] != "open":
                if "license-text" in info:
                    digest = hashlib.md5(info["license-text"]).hexdigest()
                    digests.append(digest)
                    _insert_license_into_db(digest, info["license-text"],
                                            info["theme"])
                else:
                    return None

    return digests

def license_accepted(request, digest):
    return 'license_accepted_' + digest in request.COOKIES

def accept_license(request):
    if "accept" in request.POST:
        lic = License.objects.filter(digest=request.GET['lic']).get()
        response = HttpResponseRedirect(request.GET['url'])
        d = lic.digest
        cookie_name = "license_accepted_" + d.encode("ascii")
        response.set_cookie(cookie_name,
                            max_age=60*60*24, # 1 day expiry
                            path="/" + os.path.dirname(request.GET['url']))
    else:
        response = render_to_response('licenses/nolicense.html')

    return response

def show_license(request):
    lic = License.objects.filter(digest=request.GET['lic']).get()

    return render_to_response('licenses/' + lic.theme + '.html',
                              {'license': lic,
                               'url': request.GET['url']},
                              context_instance=RequestContext(request))


def file_server(request, path):
    url = path
    result = test_path(path)
    if not result:
        raise Http404

    type = result[0]
    path = result[1]

    if type == "dir":
        return render_to_response('dir_template.html',
                                  {'dirlist': dir_list(path),
                                   'basepath': url})

    file_name = os.path.basename(path)

    response = None
    digests = is_protected(path)
    if not digests:
        # File has no license text but is protected
        response = HttpResponseForbidden(
            "You do not have permission to access this file.")

    # Return a file...
    else:
        for digest in digests:
            if not license_accepted(request, digest):
                response = redirect('/license?lic=' + digest + "&url=" + url)

        if not response:
            response = HttpResponse(mimetype='text/plain')
            response['Content-Disposition'] = ('attachment; filename=%s' %
                                               smart_str(file_name))
            response['X-Sendfile'] = smart_str(path)
            # TODO: Is it possible to add a redirect to response so we can take
            # the user back to the original directory this file is in?
    return response


