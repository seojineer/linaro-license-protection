import unittest
import urllib2
import datetime
import json

from django.conf import settings
from django.test import Client, TestCase

from license_protected_downloads.artifact.s3 import S3Artifact
from license_protected_downloads.models import (
    APIKeyStore,
    APIToken,
)

import requests


_orig_s3_prefix = getattr(settings, 'S3_PREFIX_PATH', None)
_s3_enabled = _orig_s3_prefix is not None


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


@unittest.skipIf(_s3_enabled is False, 's3 not configured')
class APIv3PublishTests(TestCase):
    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)
        self.api_key = APIKeyStore.objects.create(key='foo', public=True)

        settings.S3_PREFIX_PATH = settings.S3_PREFIX_PATH[:-1] + '-test-pub/'
        self.bucket = S3Artifact.get_bucket()

        # make sure nothing was left from an old run
        keys = self.bucket.list(settings.S3_PREFIX_PATH)
        self.bucket.delete_keys(keys)

    def tearDown(self):
        settings.S3_PREFIX_PATH = _orig_s3_prefix

    def _post_file(self, url, token, content, resp_code=201):
        response = self.client.post(url, HTTP_AUTHTOKEN=token)
        self.assertEqual(response.status_code, resp_code)
        if resp_code == 201:
            url = response['Location']
            r = requests.put(url, data=content)
            self.assertEqual(200, r.status_code)

    def test_publish_simple(self):
        content = 'foo bar'
        token = APIToken.objects.create(key=self.api_key).token
        self._post_file('/api/v3/publish/a/b', token, content)

        # we'll be missing a build-info so:
        self.assertEqual(403, self.client.get('/a/b').status_code)

        # add a build-info and see if the file works
        info = 'Format-Version: 0.5\n\nFiles-Pattern: *\nLicense-Type: open\n'
        self._post_file('/api/v3/publish/a/BUILD-INFO.txt', token, info)

        resp = self.client.get('/a/b')
        self.assertEqual(302, resp.status_code)
        resp = urllib2.urlopen(resp['Location'])
        self.assertEqual(content, resp.read())

    def test_publish_no_overwrite(self):
        content = 'foo bar'
        token = APIToken.objects.create(key=self.api_key).token
        k = self.bucket.get_key(settings.S3_PREFIX_PATH + 'a', validate=False)
        k.set_contents_from_string(content)
        self._post_file('/api/v3/publish/a', token, 'wont overwrite', 403)

    def test_link_latest_simple(self):
        content = 'build123'
        token = APIToken.objects.create(key=self.api_key).token

        self._post_file('/api/v3/publish/builds/123/a', token, content)
        info = 'Format-Version: 0.5\n\nFiles-Pattern: *\nLicense-Type: open\n'
        self._post_file(
            '/api/v3/publish/builds/123/BUILD-INFO.txt', token, info)

        resp = self.client.post(
            '/api/v3/link_latest/builds/123', HTTP_AUTHTOKEN=token)
        self.assertEqual(201, resp.status_code)

        resp = self.client.get('/builds/latest/a')
        self.assertEqual(302, resp.status_code)
        resp = urllib2.urlopen(resp['Location'])
        self.assertEqual(content, resp.read())

        k = self.bucket.get_key(
            settings.S3_PREFIX_PATH + 'builds/latest/.s3_linked_from')
        self.assertEqual(
            settings.S3_PREFIX_PATH + 'builds/123', k.get_contents_as_string())

    def test_link_latest_trailing_slash(self):
        content = 'build123'
        token = APIToken.objects.create(key=self.api_key).token

        self._post_file('/api/v3/publish/builds/123/a', token, content)
        info = 'Format-Version: 0.5\n\nFiles-Pattern: *\nLicense-Type: open\n'
        self._post_file(
            '/api/v3/publish/builds/123/BUILD-INFO.txt', token, info)

        resp = self.client.post(
            '/api/v3/link_latest/builds/123/', HTTP_AUTHTOKEN=token)
        self.assertEqual(201, resp.status_code)

        resp = self.client.get('/builds/latest/a')
        self.assertEqual(302, resp.status_code)
        resp = urllib2.urlopen(resp['Location'])
        self.assertEqual(content, resp.read())

    def test_link_latest_bad(self):
        token = APIToken.objects.create(key=self.api_key).token

        resp = self.client.post(
            '/api/v3/link_latest/builds/123', HTTP_AUTHTOKEN=token)
        self.assertEqual(404, resp.status_code)

    def test_link_latest_alt(self):
        token = APIToken.objects.create(key=self.api_key).token
        self._post_file('/api/v3/publish/buildX/a', token, 'content')

        # ensure bad link name is caught
        resp = self.client.post(
            '/api/v3/link_latest/buildX', data={'linkname': 'foo'},
            HTTP_AUTHTOKEN=token)
        self.assertEqual(401, resp.status_code)

        resp = self.client.post(
            '/api/v3/link_latest/buildX',
            data={'linkname': 'lastSuccessful'},
            HTTP_AUTHTOKEN=token)
        self.assertEqual(201, resp.status_code)
