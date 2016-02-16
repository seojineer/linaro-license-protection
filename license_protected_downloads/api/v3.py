import os

from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from license_protected_downloads.artifact.s3 import S3Artifact
from license_protected_downloads.api.v1 import (
    HttpResponseError,
)
from license_protected_downloads.api import v2
from license_protected_downloads.models import (
    APILog,
)


# no changes required for tokens in v3
token = v2.token


class PublishResource(v2.PublishResource):
    def __init__(self, request, path):
        super(PublishResource, self).__init__(request, path)

    def POST(self):
        b = S3Artifact.get_bucket()
        if not b:
            raise HttpResponseError('S3 is not enabled', 403)

        k = b.new_key(settings.S3_PREFIX_PATH + self.path)
        if k.exists():
            APILog.mark(self.request, 'FILE_OVERWRITE_DENIED')
            raise HttpResponseError('File already exists', 403)

        headers = {}
        mtype = self.request.POST.get('Content-Type', None)
        if mtype:
            headers['Content-Type'] = mtype

        resp = HttpResponse(status=201)
        resp['Location'] = k.generate_url(60, method='PUT', headers=headers)
        APILog.mark(self.request, 'FILE_UPLOAD', self.api_key)
        return resp


@csrf_exempt
def publish(request, path):
    return PublishResource(request, path).handle()


class LatestLinkResource(PublishResource):
    def POST(self):
        b = S3Artifact.get_bucket()
        if not b:
            raise HttpResponseError('S3 is not enabled', 403)

        if not self.path:
            APILog.mark(self.request, 'INVALID_ARGUMENTS', self.api_key)
            raise HttpResponseError('Invalid Arguments', 401)

        path = self.path
        if path[-1] == '/':
            path = path[:-1]  # make os.path.dirname give parent
        path = settings.S3_PREFIX_PATH + path

        items = list(b.list(path))
        if len(items) == 0:
            APILog.mark(self.request, 'INVALID_ARGUMENTS', self.api_key)
            raise HttpResponseError('Target does not exist: ' + self.path, 404)

        link_name = self.request.POST.get('linkname', 'latest')
        if link_name not in ('latest', 'lastSuccessful'):
            APILog.mark(self.request, 'INVALID_ARGUMENTS', self.api_key)
            raise HttpResponseError('Invalid link name', 401)

        dst = os.path.join(os.path.dirname(path), link_name)
        keys = b.list(dst)
        b.delete_keys(keys)
        for k in items:
            newkeyname = k.name.replace(path, dst)
            b.copy_key(newkeyname, k.bucket.name, k.name)
        # keep track of where the link content came from
        b.new_key(dst + '/.s3_linked_from').set_contents_from_string(path)

        APILog.mark(self.request, 'LINK_LATEST', self.api_key)

        resp = HttpResponse(status=201)
        resp['Location'] = dst
        return resp


@csrf_exempt
def link_latest(request, path):
    return LatestLinkResource(request, path).handle()
