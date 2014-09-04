import datetime
import json

from django.test import Client, TestCase

from license_protected_downloads.models import (
    APIKeyStore,
    APIToken,
)


class APIv2Tests(TestCase):
    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)
        self.api_key = APIKeyStore.objects.create(key='foo')

    def test_token_no_auth(self):
        resp = self.client.get('/api/v2/token/')
        self.assertEqual(401, resp.status_code)

    def test_token_bad_auth(self):
        resp = self.client.get('/api/v2/token/', HTTP_AUTHTOKEN='bad')
        self.assertEqual(401, resp.status_code)

    def test_token_list(self):
        keys = 3
        for x in range(keys):
            APIToken.objects.create(key=self.api_key)

        resp = self.client.get(
            '/api/v2/token/', HTTP_AUTHTOKEN=self.api_key.key)
        self.assertEqual(200, resp.status_code)
        tokens = json.loads(resp.content)
        self.assertEqual(keys, len(tokens))

    def test_token_detail(self):
        token = APIToken.objects.create(key=self.api_key)
        resp = self.client.get(
            '/api/v2/token/%s' % token.token, HTTP_AUTHTOKEN=self.api_key.key)
        self.assertEqual(200, resp.status_code)
        self.assertEqual(None, json.loads(resp.content)['expires'])

    def test_token_create_iso_expire(self):
        expires = datetime.datetime.now() + datetime.timedelta(minutes=1)
        data = {'expires': expires.isoformat()}
        resp = self.client.post(
            '/api/v2/token/', data=data, HTTP_AUTHTOKEN=self.api_key.key)
        self.assertEqual(201, resp.status_code)

        # get it to verify
        resp = self.client.get(
            resp['Location'], HTTP_AUTHTOKEN=self.api_key.key)
        self.assertEqual(200, resp.status_code)
        self.assertEqual(
            expires.isoformat(), json.loads(resp.content)['expires'])

    def test_token_create_int_expire(self):
        data = {'expires': 60}
        resp = self.client.post(
            '/api/v2/token/', data=data, HTTP_AUTHTOKEN=self.api_key.key)
        self.assertEqual(201, resp.status_code)

        # get it to verify
        resp = self.client.get(
            resp['Location'], HTTP_AUTHTOKEN=self.api_key.key)
        self.assertEqual(200, resp.status_code)
