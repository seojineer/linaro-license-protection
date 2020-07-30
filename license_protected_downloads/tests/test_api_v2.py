import datetime
import json
import os
import shutil
import tempfile
import StringIO

import unittest

import mock

from django.conf import settings

import django.conf
from django.test import Client, TestCase

from license_protected_downloads.models import (
    APIKeyStore,
    APIToken,
)

_orig_s3_prefix = getattr(settings, 'S3_PREFIX_PATH', None)
_access_key = getattr(settings, 'AWS_ACCESS_KEY_ID', None)
_s3_enabled = _orig_s3_prefix is not None and _access_key is not None

class APIv2Tests(TestCase):
    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)
        self.api_key = APIKeyStore.objects.create(key='foo', public=True)

        path = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, path)
        m = mock.patch('django.conf.settings.SERVED_PATHS',
                       new_callable=lambda: [path])
        self.addCleanup(m.stop)
        m.start()

        m = mock.patch(
            'license_protected_downloads.artifact.S3Artifact.get_bucket')
        self.addCleanup(m.stop)
        mo = m.start()
        mo.return_value = None

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

    def test_token_create_not_valid_til(self):
        ts = datetime.datetime.now() + datetime.timedelta(minutes=1)
        data = {'not_valid_til': ts.isoformat()}
        resp = self.client.post(
            '/api/v2/token/', data=data, HTTP_AUTHTOKEN=self.api_key.key)
        self.assertEqual(201, resp.status_code)

        # get it to verify
        resp = self.client.get(
            resp['Location'], HTTP_AUTHTOKEN=self.api_key.key)
        self.assertEqual(200, resp.status_code)
        self.assertEqual(
            ts.isoformat(), json.loads(resp.content)['not_valid_til'])

    def test_token_create_ip(self):
        data = {'ip': 'foo'}
        resp = self.client.post(
            '/api/v2/token/', data=data, HTTP_AUTHTOKEN=self.api_key.key)
        self.assertEqual(201, resp.status_code)

        # get it to verify
        resp = self.client.get(
            resp['Location'], HTTP_AUTHTOKEN=self.api_key.key)
        self.assertEqual(200, resp.status_code)
        self.assertEqual(data['ip'], json.loads(resp.content)['ip'])

    def test_token_create_int_expire(self):
        data = {'expires': 60}
        resp = self.client.post(
            '/api/v2/token/', data=data, HTTP_AUTHTOKEN=self.api_key.key)
        self.assertEqual(201, resp.status_code)

        # get it to verify
        resp = self.client.get(
            resp['Location'], HTTP_AUTHTOKEN=self.api_key.key)
        self.assertEqual(200, resp.status_code)

    def test_publish_no_token(self):
        resp = self.client.post('/api/v2/publish/a')
        self.assertEqual(401, resp.status_code)

    def test_publish_bad_token(self):
        resp = self.client.post('/api/v2/publish/a', HTTP_AUTHTOKEN='bad')
        self.assertEqual(401, resp.status_code)

    def test_publish_expired_token(self):
        expires = datetime.datetime.now() - datetime.timedelta(minutes=1)
        token = APIToken.objects.create(key=self.api_key, expires=expires)
        resp = self.client.post(
            '/api/v2/publish/a', HTTP_AUTHTOKEN=token.token)
        self.assertEqual(401, resp.status_code)

    def test_publish_not_valid_til_token(self):
        ts = datetime.datetime.now() + datetime.timedelta(minutes=1)
        token = APIToken.objects.create(key=self.api_key, not_valid_til=ts)
        resp = self.client.post(
            '/api/v2/publish/a', HTTP_AUTHTOKEN=token.token)
        self.assertEqual(401, resp.status_code)

    def test_publish_ip_token(self):
        token = APIToken.objects.create(key=self.api_key, ip='127.0.0.1').token
        self._send_file('/api/v2/publish/foo', token, 'content')

    def test_publish_bad_ip_token(self):
        token = APIToken.objects.create(key=self.api_key, ip='foo').token
        resp = self.client.post('/api/v2/publish/a', HTTP_AUTHTOKEN=token)
        self.assertEqual(401, resp.status_code)

    def _send_file(self, url, token, content, resp_code=201):
        f = StringIO.StringIO(content)
        f.name = 'name'   # to fool django's client.post
        response = self.client.post(
            url, HTTP_AUTHTOKEN=token, data={"file": f})
        self.assertEqual(response.status_code, resp_code)

    def test_publish_simple(self):
        content = 'foo bar'
        token = APIToken.objects.create(key=self.api_key).token
        self._send_file('/api/v2/publish/a', token, content)

        # we'll be missing a build-info so:
        self.assertEqual(403, self.client.get('/a').status_code)

        # add a build-info and see if the file works
        info = 'Format-Version: 0.5\n\nFiles-Pattern: *\nLicense-Type: open\n'
        self._send_file('/api/v2/publish/BUILD-INFO.txt', token, info)

        resp = self.client.get('/a')
        self.assertEqual(200, resp.status_code)
        self.assertEqual(content, open(resp['X-Sendfile']).read())

    def test_publish_with_dirs(self):
        content = 'foo bar'
        token = APIToken.objects.create(key=self.api_key).token
        self._send_file('/api/v2/publish/a/b', token, content)

        # we'll be missing a build-info so:
        self.assertEqual(403, self.client.get('/a/b').status_code)

        # add a build-info and see if the file works
        info = 'Format-Version: 0.5\n\nFiles-Pattern: *\nLicense-Type: open\n'
        self._send_file('/api/v2/publish/a/BUILD-INFO.txt', token, info)

        resp = self.client.get('/a/b')
        self.assertEqual(200, resp.status_code)
        self.assertEqual(content, open(resp['X-Sendfile']).read())

    def test_publish_no_overwrite(self):
        content = 'foo bar'
        token = APIToken.objects.create(key=self.api_key).token
        self._send_file('/api/v2/publish/a', token, content)
        self._send_file('/api/v2/publish/a', token, 'bad content', 403)

        # add a build-info and see if the file works
        info = 'Format-Version: 0.5\n\nFiles-Pattern: *\nLicense-Type: open\n'
        self._send_file('/api/v2/publish/BUILD-INFO.txt', token, info)

        resp = self.client.get('/a')
        self.assertEqual(200, resp.status_code)
        self.assertEqual(content, open(resp['X-Sendfile']).read())

    def test_link_latest_simple(self):
        token = APIToken.objects.create(key=self.api_key).token
        self._send_file('/api/v2/publish/buildX/a', token, 'content')

        resp = self.client.post(
            '/api/v2/link_latest/buildX', HTTP_AUTHTOKEN=token)
        self.assertEqual(201, resp.status_code)

    @unittest.skip('FIXME: KeyError on x-sendfile')
    def test_link_latest_trailing_slash(self):
        token = APIToken.objects.create(key=self.api_key).token
        self._send_file('/api/v2/publish/build/X/a', token, 'content')

        info = 'Format-Version: 0.5\n\nFiles-Pattern: *\nLicense-Type: open\n'
        self._send_file('/api/v2/publish/build/X/BUILD-INFO.txt', token, info)

        resp = self.client.post(
            '/api/v2/link_latest/build/X/', HTTP_AUTHTOKEN=token)
        self.assertEqual(201, resp.status_code)
        resp = self.client.get('/build/latest/a')
        self.assertIn(resp.status_code, [200,302])
        self.assertEqual('content', open(resp['X-Sendfile']).read())

    def test_link_latest_bad(self):
        token = APIToken.objects.create(key=self.api_key).token
        resp = self.client.post(
            '/api/v2/link_latest/buildY', HTTP_AUTHTOKEN=token)
        self.assertEqual(404, resp.status_code)

    def test_link_latest_exists(self):
        path = django.conf.settings.SERVED_PATHS[0]
        build = os.path.join(path, 'buildX')
        latest = os.path.join(path, 'latest')

        os.mkdir(build)
        os.symlink(build, latest)
        token = APIToken.objects.create(key=self.api_key).token
        resp = self.client.post(
            '/api/v2/link_latest/buildX', HTTP_AUTHTOKEN=token)
        self.assertEqual(201, resp.status_code)

        # make sure we can't link if a real directory exists by that name
        os.unlink(latest)
        os.mkdir(latest)
        resp = self.client.post(
            '/api/v2/link_latest/buildX', HTTP_AUTHTOKEN=token)
        self.assertEqual(404, resp.status_code)

    def test_link_latest_alt(self):
        token = APIToken.objects.create(key=self.api_key).token
        self._send_file('/api/v2/publish/buildX/a', token, 'content')

        # ensure bad link name is caught
        resp = self.client.post(
            '/api/v2/link_latest/buildX', data={'linkname': 'foo'},
            HTTP_AUTHTOKEN=token)
        self.assertEqual(401, resp.status_code)

        resp = self.client.post(
            '/api/v2/link_latest/buildX',
            data={'linkname': 'lastSuccessful'},
            HTTP_AUTHTOKEN=token)
        self.assertEqual(201, resp.status_code)
