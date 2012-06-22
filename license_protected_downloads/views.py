# Create your views here.

from django.http import HttpResponse
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

def dir_list(path):
    files = os.listdir(path)
    listing = []
    for file in files:
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

def _insert_license_into_db(digest, text):
    if not License.objects.filter(digest=digest):
        l = License(digest=digest, text=text)
        l.save()

def is_protected(path):
    buildinfo_path = os.path.join(os.path.dirname(path), "BUILD-INFO.txt")
    digests = []
    if os.path.isfile(buildinfo_path):
        build_info = BuildInfo()
        build_info.parse_buildinfo(buildinfo_path)

        for info in build_info.data:
            if "files-pattern" not in info or "license-type" not in info:
                continue

            file_name = os.path.basename(path)
            if re.search(info["files-pattern"], file_name):
                if info["license-type"] != "open":
                    digest = hashlib.md5(info["license-text"]).hexdigest()
                    digests.append(digest)
                    _insert_license_into_db(digest, info["license-text"])

    return digests

def license_accepted(request, digest):
    return 'license_accepted_' + digest in request.COOKIES

def show_license(request):
    lic = License.objects.filter(digest=request.GET['lic']).get()

    response = HttpResponse("Some licenses..." +
                            request.GET['lic'] + " " +
                            request.GET['url'] + lic.text)
    return response

def file_server(request, path):
    result = test_path(path)
    if not result:
        raise Http404

    type = result[0]
    path = result[1]

    if type == "dir":
        return render_to_response('dir_template.html',
                                  {'dirlist': dir_list(path)})

    file_name = os.path.basename(path)

    response = None

    # Return a file...
    digests = is_protected(path)
    for digest in digests:
        if not license_accepted(request, digest):
            #response = HttpResponse("Accepting some licenses...")
            #response.set_cookie("license_accepted_" + digest)
            response = redirect('/license?lic=' + digest + "&url=" + path)

    if not response:
        response = HttpResponse(mimetype='application/force-download')
        response['Content-Disposition'] = 'attachment; filename=%s' % smart_str(file_name)
        response['X-Sendfile'] = smart_str(path)
    return response


