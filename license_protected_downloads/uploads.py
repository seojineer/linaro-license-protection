from django.views.decorators.csrf import csrf_exempt
from django.http import (
    HttpResponse,
    HttpResponseForbidden,
    HttpResponseServerError
)
from django import forms
import random
import settings
import os
from models import APIKeyStore
from common import *


class UploadFileForm(forms.Form):
    file = forms.FileField()


def upload_target_path(path, key):
    """Quick path handling function.

    Checks that the generated path doesn't end up outside the target directory,
    so you can't set path to start with "/" and upload to anywhere.
    """
    base_path = os.path.join(settings.UPLOAD_PATH, key)
    return safe_path_join(base_path)


@csrf_exempt
def file_server_post(request, path):
    """ Handle post requests.

    All post requests must be accompanied by a valid key. If not, the upload
    will be ignored.

    Files are stored in a private directory that can not be accessed via the
    web interface unless you have the same key.
    """
    if not ("key" in request.GET and
        APIKeyStore.objects.filter(key=request.GET["key"])):
        return HttpResponseServerError("Invalid key")

    form = UploadFileForm(request.POST, request.FILES)
    if not form.is_valid() or not path:
        return HttpResponseServerError("Invalid call")

    path = upload_target_path(path, request.GET["key"])

    # Create directory if required
    dirname = os.path.dirname(path)
    if not os.path.isdir(dirname):
        os.mkdir(dirname)

    with open(path, "wb") as destination:
        for chunk in request.FILES["file"].chunks():
            destination.write(chunk)

    return HttpResponse("OK")


def api_request_key(request):
    if("key" in request.GET and
       request.GET["key"] == settings.MASTER_API_KEY):

        # Generate a new, random key.
        key = "%030x" % random.randrange(256**15)
        while APIKeyStore.objects.filter(key=key):
            key = "%030x" % random.randrange(256**15)

        api_key = APIKeyStore(key=key)
        api_key.save()
        return HttpResponse(key)

    return HttpResponseForbidden()
