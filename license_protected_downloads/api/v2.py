import datetime
import json

from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from license_protected_downloads.models import (
    APIKeyStore,
    APILog,
    APIToken,
)


def token_as_dict(token):
    expires = token.expires
    if expires:
        expires = expires.isoformat()
    return {'id': token.token, 'expires': expires}


class RestException(Exception):
    def __init__(self, msg, status):
        super(RestException, self).__init__(msg)
        self.http_response = HttpResponse(msg, status=status)


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
        except RestException as e:
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
            raise RestException('Missing authentication key', 401)
        try:
            self.api_key = APIKeyStore.objects.get(
                key=self.request.META['HTTP_AUTHTOKEN'])
        except APIKeyStore.DoesNotExist:
            APILog.mark(self.request, 'INVALID_KEY')
            raise RestException('Invalid Key', 401)

    def GET(self):
        APILog.mark(self.request, 'TOKEN_GET', self.api_key)
        if self.token:
            data = token_as_dict(APIToken.objects.get(token=self.token))
        else:
            data = []
            for token in APIToken.objects.filter(key=self.api_key):
                data.append(token_as_dict(token))
        return HttpResponse(json.dumps(data), content_type='application/json')

    def _parse_expires(self):
        expires = None
        if 'expires' in self.request.POST:
            expires = self.request.POST['expires']
            if expires.isdigit():
                # accept a time in seconds for expiration
                expires = datetime.datetime.now() + datetime.timedelta(
                    seconds=int(expires))
            else:
                # accept ISO8601 formatted datetime
                expires = datetime.datetime.strptime(
                    expires, '%Y-%m-%dT%H:%M:%S.%f')
        return expires

    def POST(self):
        token = APIToken.objects.create(
            key=self.api_key, expires=self._parse_expires())
        response = HttpResponse(status=201)
        response['Location'] = self.request.path + token.token
        return response


@csrf_exempt
def token(request, token):
    return TokenResource(request, token).handle()
