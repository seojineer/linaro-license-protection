# Create your views here.

from django.http import HttpResponse
from django.conf import settings
import os.path
from django.http import Http404
from django.utils.encoding import smart_str
from buildinfo import BuildInfo
import re

def dir_list(request, path):
    return HttpResponse("dir_list: " + path)

def test_path(path):

    for basepath in settings.SERVED_PATHS:
        fullpath = os.path.join(basepath, path)
        if os.path.isfile(fullpath):
            return ("file", fullpath)
        if os.path.isdir(fullpath):
            return ("dir", fullpath)

    return None

def is_protected(path):
    buildinfo_path = os.path.join(os.path.dirname(path), "BUILD-INFO.txt")
    if os.path.isfile(buildinfo_path):
        build_info = BuildInfo()
        build_info.parse_buildinfo(buildinfo_path)

        for info in build_info.data:
            if "files-pattern" not in info or "license-type" not in info:
                continue

            file_name = os.path.basename(path)
            if re.search(info["files-pattern"], file_name):
                if info["license-type"] == "open":
                    return False
                else:
                    return True

    return False

def license_accepted(request):
    return 'license_accepted' in request.COOKIES

def file_server(request, path):
    result = test_path(path)
    if not result:
        raise Http404

    type = result[0]
    path = result[1]

    if type == "dir":
        return HttpResponse("file_server: " + path + " " + type)

    file_name = os.path.basename(path)

    # Return a file...
    if is_protected(path) and not license_accepted(request):
        response = HttpResponse("Yea")
        response.set_cookie("license_accepted")
    else:
        response = HttpResponse(mimetype='application/force-download')
        response['Content-Disposition'] = 'attachment; filename=%s' % smart_str(file_name)
        response['X-Sendfile'] = smart_str(path)
    return response

