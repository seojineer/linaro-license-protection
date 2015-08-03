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
