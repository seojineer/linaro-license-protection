import json
import os

from django.views.decorators.csrf import csrf_exempt
from django.http import (
    HttpResponse,
    HttpResponseServerError
)
from django.conf import settings
from django.utils.encoding import iri_to_uri

from license_protected_downloads.models import (
    APIKeyStore,
    APILog,
    License
)
from license_protected_downloads.common import (
    dir_list,
    find_artifact,
    safe_path_join,
)


class HttpResponseError(Exception):
    def __init__(self, msg, status):
        super(HttpResponseError, self).__init__(msg)
        self.http_response = HttpResponse(msg, status=status)


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


def do_upload(request, infd, path, api_key):
    path = upload_target_path(
        path, api_key.key, public=api_key.public)

    if os.path.exists(path):
        APILog.mark(request, 'FILE_OVERWRITE_DENIED')
        raise HttpResponseError('File already exists', 403)

    # Create directory if required
    dirname = os.path.dirname(path)
    if not os.path.isdir(dirname):
        os.makedirs(dirname)

    with open(path, "wb") as destination:
        for chunk in infd.chunks():
            destination.write(chunk)


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

    try:
        do_upload(request, request.FILES['file'], path, api_key)
        APILog.mark(request, 'FILE_UPLOAD', api_key)
    except HttpResponseError as e:
        APILog.mark(request, 'FILE_UPLOAD_FAIL', api_key)
        return e.http_response
    return HttpResponse("OK")


def list_files_api(request, path):
    path = iri_to_uri(path)
    artifact = find_artifact(request, path)

    if artifact.isdir():
        listing = dir_list(artifact, human_readable=False)
    else:
        listing = [artifact.get_listing()]

    clean_listing = []
    for entry in listing:
        clean_listing.append({
            "name": entry["name"],
            "size": entry["size"],
            "type": entry["type"],
            "mtime": entry["mtime"],
            "url": entry["url"],
        })

    data = json.dumps({"files": clean_listing})
    return HttpResponse(data, content_type='application/json')


def get_license_api(request, path):
    path = iri_to_uri(path)
    artifact = find_artifact(request, path)

    if artifact.isdir():
        data = json.dumps({"licenses":
                           ["ERROR: License only shown for a single file."]})
    else:
        license_digest_list = artifact.get_license_digests()
        license_list = License.objects.all_with_hashes(license_digest_list)
        if len(license_list) == 0:
            license_list = ["Open"]
        else:
            license_list = [{"text": l.text, "digest": l.digest}
                            for l in license_list]
        data = json.dumps({"licenses": license_list})

    return HttpResponse(data, content_type='application/json')
