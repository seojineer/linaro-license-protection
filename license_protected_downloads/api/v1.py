import os
import random
import shutil

from django.views.decorators.csrf import csrf_exempt
from django.http import (
    HttpResponse,
    HttpResponseForbidden,
    HttpResponseServerError
)
from django.conf import settings

from license_protected_downloads.models import APIKeyStore, APILog
from license_protected_downloads.common import safe_path_join


def upload_target_path(path, key, public):
    """Quick path handling function.

    Checks that the generated path doesn't end up outside the target directory,
    so you can't set path to start with "/" and upload to anywhere.
    """
    if public:
        base_path = os.path.join(settings.SERVED_PATHS[0])
    else:
        base_path = os.path.join(settings.UPLOAD_PATH, key)
    return safe_path_join(base_path, path)


@csrf_exempt
def file_server_post(request, path):
    """ Handle post requests.

    All post requests must be accompanied by a valid key. If not, the upload
    will be ignored.

    Files are stored in a private directory that can not be accessed via the
    web interface unless you have the same key.
    """
    if not ("key" in request.POST and
            APIKeyStore.objects.filter(key=request.POST["key"])):
        APILog.mark(request, 'INVALID_KEY')
        return HttpResponseServerError("Invalid key")

    api_key = APIKeyStore.objects.get(key=request.POST["key"])

    if 'file' not in request.FILES or not path:
        APILog.mark(request, 'INVALID_ARGUMENTS', api_key)
        return HttpResponseServerError("Invalid call")

    APILog.mark(request, 'FILE_UPLOAD', api_key)

    path = upload_target_path(
        path, request.POST["key"], public=api_key.public)

    # Create directory if required
    dirname = os.path.dirname(path)
    if not os.path.isdir(dirname):
        os.makedirs(dirname)

    with open(path, "wb") as destination:
        for chunk in request.FILES["file"].chunks():
            destination.write(chunk)

    return HttpResponse("OK")


def api_request_key(request):
    APILog.mark(request, 'REQUEST_KEY')
    if("key" in request.GET and
       request.GET["key"] == settings.MASTER_API_KEY and
       settings.MASTER_API_KEY):

        # Generate a new, random key.
        key = "%030x" % random.randrange(256 ** 15)
        while APIKeyStore.objects.filter(key=key):
            key = "%030x" % random.randrange(256 ** 15)

        # Look for a hint of sanity in the value given to public, but don't
        # care about it too much.
        yes = ["", "y", "yes", "true", "1"]
        if "public" in request.GET:
            public = request.GET["public"].lower() in yes
        else:
            public = False

        api_key = APIKeyStore(key=key, public=public)
        api_key.save()
        return HttpResponse(key)

    return HttpResponseForbidden()


def api_delete_key(request):
    APILog.mark(request, 'DELETE_KEY')
    if "key" not in request.GET:
        return HttpResponseServerError("Invalid key")

    key = request.GET["key"]
    api_key = APIKeyStore.objects.filter(key=key)

    if not api_key:
        return HttpResponseServerError("Invalid key")

    # Delete key from database and all files associated with it
    api_key.delete()
    shutil.rmtree(os.path.join(settings.UPLOAD_PATH, key))

    return HttpResponse("OK")


def api_push_to_server(request):
    # TODO: Upload files from this machine to another linaro-licence-protection
    # node.
    """
    Something like:

    if request.GET["target"] in settings.REMOTE_SERVERS:
        remote_server = settings.REMOTE_SERVERS[request.GET["target"]]

        remote_server should contain:
        {
            "key": "...",
            "url": "...",
        }

        now just POST files from this machine to the specified URL/KEY.

        Possibly add some magic to POST endpoint (file_server_post) to allow
        (some users??) uploads to a public path:

        POST snapshots.linaro.org/path/to/file?key="key"&public=true

    """
    pass
