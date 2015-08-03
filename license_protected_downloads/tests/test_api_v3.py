import datetime
import json

from django.test import Client, TestCase

from license_protected_downloads.models import (
    APIKeyStore,
    APIToken,
)


class APIv3TokenTests(TestCase):
    '''A subset of token tests since this *should* just be v2 token code'''
    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)
        self.api_key = APIKeyStore.objects.create(key='foo', public=True)

    def test_token_no_auth(self):
        resp = self.client.get('/api/v3/token/')
        self.assertEqual(401, resp.status_code)

    def test_token_list(self):
        keys = 3
        for x in range(keys):
            APIToken.objects.create(key=self.api_key)

        resp = self.client.get(
            '/api/v3/token/', HTTP_AUTHTOKEN=self.api_key.key)
        self.assertEqual(200, resp.status_code)
        tokens = json.loads(resp.content)
        self.assertEqual(keys, len(tokens))

    def test_token_create(self):
        expires = datetime.datetime.now() + datetime.timedelta(minutes=1)
        data = {'expires': expires.isoformat()}
        resp = self.client.post(
            '/api/v3/token/', data=data, HTTP_AUTHTOKEN=self.api_key.key)
        self.assertEqual(201, resp.status_code)
