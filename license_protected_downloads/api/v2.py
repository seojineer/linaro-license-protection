import datetime
import json
import os

from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from license_protected_downloads.api.v1 import (
    HttpResponseError,
    do_upload,
    upload_target_path,
)
from license_protected_downloads.models import (
    APIKeyStore,
    APILog,
    APIToken,
)


def token_as_dict(token):
    expires = token.expires
    if expires:
        expires = expires.isoformat()
    not_valid_til = token.not_valid_til
    if not_valid_til:
        not_valid_til = not_valid_til.isoformat()
    return {
        'id': token.token,
        'not_valid_til': not_valid_til,
        'expires': expires,
        'ip': token.ip
    }


class RestResource(object):
    def __init__(self, request):
        self.request = request

    def authenticate(self):
        pass

    def handle(self):
        method = getattr(self, self.request.method, None)
        if not method:
            APILog.mark(self.request, 'TOKEN_INVALID_REQUEST')
            return HttpResponse('Invalid request method', status=400)
        try:
            self.authenticate()
            return method()
        except HttpResponseError as e:
            return e.http_response
        except ObjectDoesNotExist:
            return HttpResponse(status=404)


class TokenResource(RestResource):
    def __init__(self, request, token):
        super(TokenResource, self).__init__(request)
        self.token = token

    def authenticate(self):
        if 'HTTP_AUTHTOKEN' not in self.request.META:
            APILog.mark(self.request, 'INVALID_KEY_MISSING')
            raise HttpResponseError('Missing authentication key', 401)
        try:
            self.api_key = APIKeyStore.objects.get(
                key=self.request.META['HTTP_AUTHTOKEN'])
        except APIKeyStore.DoesNotExist:
            APILog.mark(self.request, 'INVALID_KEY')
            raise HttpResponseError('Invalid Key', 401)

    def GET(self):
        APILog.mark(self.request, 'TOKEN_GET', self.api_key)
        if self.token:
            data = token_as_dict(APIToken.objects.get(token=self.token))
        else:
            data = []
            for token in APIToken.objects.filter(key=self.api_key):
                data.append(token_as_dict(token))
        return HttpResponse(json.dumps(data), content_type='application/json')

    def _parse_time(self, field):
        ts = None
        if field in self.request.POST:
            ts = self.request.POST[field]
            if ts.isdigit():
                # accept a time in seconds for expiration
                ts = datetime.datetime.now() + datetime.timedelta(
                    seconds=int(ts))
            else:
                # accept ISO8601 formatted datetime
                ts = datetime.datetime.strptime(ts, '%Y-%m-%dT%H:%M:%S.%f')
        return ts

    def POST(self):
        ip = self.request.POST.get('ip', None)
        token = APIToken.objects.create(
            key=self.api_key, ip=ip,
            expires=self._parse_time('expires'),
            not_valid_til=self._parse_time('not_valid_til'))
        response = HttpResponse(status=201)
        response['Location'] = self.request.path + token.token
        return response


@csrf_exempt
def token(request, token):
    return TokenResource(request, token).handle()


class PublishResource(RestResource):
    def __init__(self, request, path):
        super(PublishResource, self).__init__(request)
        self.path = path

    def authenticate(self):
        if 'HTTP_AUTHTOKEN' not in self.request.META:
            APILog.mark(self.request, 'INVALID_KEY_MISSING')
            raise HttpResponseError('Missing api token', 401)
        try:
            token = APIToken.objects.get(
                token=self.request.META['HTTP_AUTHTOKEN'])
            if not token.valid_request(self.request):
                raise HttpResponseError('Token no longer valid', 401)
            self.api_key = token.key
        except APIToken.DoesNotExist:
            APILog.mark(self.request, 'INVALID_KEY')
            raise HttpResponseError('Invalid api token', 401)

    def POST(self):
        if 'file' not in self.request.FILES or not self.path:
            APILog.mark(self.request, 'INVALID_ARGUMENTS', self.api_key)
            raise HttpResponseError('Invalid Arguments', 401)

        APILog.mark(self.request, 'FILE_UPLOAD', self.api_key)
        do_upload(self.request, self.request.FILES['file'],
                  self.path, self.api_key)
        resp = HttpResponse(status=201)
        resp['Location'] = self.path
        return resp


@csrf_exempt
def publish(request, path):
    return PublishResource(request, path).handle()


class LatestLinkResource(PublishResource):
    def POST(self):
        if not self.path:
            APILog.mark(self.request, 'INVALID_ARGUMENTS', self.api_key)
            raise HttpResponseError('Invalid Arguments', 401)

        src = upload_target_path(
            self.path, self.api_key.key, self.api_key.public)
        if not os.path.isdir(src):
            APILog.mark(self.request, 'INVALID_ARGUMENTS', self.api_key)
            raise HttpResponseError('Target does not exist: ' + self.path, 404)

        link_name = self.request.POST.get('linkname', 'latest')
        if link_name not in ('latest', 'lastSuccessful'):
            APILog.mark(self.request, 'INVALID_ARGUMENTS', self.api_key)
            raise HttpResponseError('Invalid link name', 401)

        dst = os.path.join(os.path.dirname(src), link_name)
        if os.path.exists(dst):
            if os.path.islink(dst):
                os.unlink(dst)
            else:
                APILog.mark(self.request, 'INVALID_ARGUMENTS', self.api_key)
                raise HttpResponseError('Invalid destination', 404)

        os.symlink(src, dst)

        resp = HttpResponse(status=201)
        resp['Location'] = dst
        return resp


@csrf_exempt
def link_latest(request, path):
    return LatestLinkResource(request, path).handle()
