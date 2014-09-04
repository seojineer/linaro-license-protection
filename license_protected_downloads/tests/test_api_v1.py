import os
import urlparse
import json
import random
import shutil
import StringIO
import tempfile

import mock

from django.conf import settings
from django.test import Client, TestCase

from license_protected_downloads.models import APIKeyStore
from license_protected_downloads.tests.test_views import ViewTests

THIS_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
TESTSERVER_ROOT = os.path.join(THIS_DIRECTORY, "testserver_root")


class APITests(TestCase):
    def setUp(self):
        self.client = Client()

        path = os.path.join(os.path.dirname(__file__), 'testserver_root')
        m = mock.patch('django.conf.settings.SERVED_PATHS',
                       new_callable=lambda: [path])
        self.addCleanup(m.stop)
        m.start()

        path = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, path)
        m = mock.patch('django.conf.settings.UPLOAD_PATH',
                       new_callable=lambda: path)
        self.addCleanup(m.stop)
        m.start()

        self.pub_key = APIKeyStore.objects.create(
            key='pubkey', public=True).key
        self.priv_key = APIKeyStore.objects.create(
            key='prikey', public=False).key

        self.tmpdir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmpdir)

    def test_api_get_license_list(self):
        target_file = "build-info/snowball-blob.txt"
        digest = ViewTests.set_up_license(target_file)

        license_url = "/api/license/" + target_file

        # Download JSON containing license information
        response = self.client.get(license_url)
        data = json.loads(response.content)["licenses"]

        # Extract digests
        digests = [d["digest"] for d in data]

        # Make sure digests match what is in the database
        self.assertIn(digest, digests)
        self.assertEqual(len(digests), 1)

    def test_api_get_license_list_multi_license(self):
        target_file = "build-info/multi-license.txt"
        digest_1 = ViewTests.set_up_license(target_file)
        digest_2 = ViewTests.set_up_license(target_file, 1)

        license_url = "/api/license/" + target_file

        # Download JSON containing license information
        response = self.client.get(license_url)
        data = json.loads(response.content)["licenses"]

        # Extract digests
        digests = [d["digest"] for d in data]

        # Make sure digests match what is in the database
        self.assertIn(digest_1, digests)
        self.assertIn(digest_2, digests)
        self.assertEqual(len(digests), 2)

    def test_api_get_license_list_404(self):
        target_file = "build-info/snowball-b"
        license_url = "/api/license/" + target_file

        # Download JSON containing license information
        response = self.client.get(license_url)
        self.assertEqual(response.status_code, 404)

    def test_api_download_file(self):
        target_file = "build-info/snowball-blob.txt"
        digest = ViewTests.set_up_license(target_file)

        url = urlparse.urljoin("http://testserver/", target_file)
        response = self.client.get(url, follow=True,
                                   HTTP_LICENSE_ACCEPTED=digest)
        self.assertEqual(response.status_code, 200)
        file_path = os.path.join(TESTSERVER_ROOT, target_file)
        self.assertEqual(response['X-Sendfile'], file_path)

    def test_api_download_file_multi_license(self):
        target_file = "build-info/multi-license.txt"
        digest_1 = ViewTests.set_up_license(target_file)
        digest_2 = ViewTests.set_up_license(target_file, 1)

        url = urlparse.urljoin("http://testserver/", target_file)
        response = self.client.get(
            url, follow=True,
            HTTP_LICENSE_ACCEPTED=" ".join([digest_1, digest_2]))
        self.assertEqual(response.status_code, 200)
        file_path = os.path.join(TESTSERVER_ROOT, target_file)
        self.assertEqual(response['X-Sendfile'], file_path)

    def test_api_download_file_404(self):
        target_file = "build-info/snowball-blob.txt"
        digest = ViewTests.set_up_license(target_file)

        url = urlparse.urljoin("http://testserver/", target_file[:-2])
        response = self.client.get(url, follow=True,
                                   HTTP_LICENSE_ACCEPTED=digest)
        self.assertEqual(response.status_code, 404)

    def test_api_get_listing(self):
        url = "/api/ls/build-info"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)["files"]

        # For each file listed, check some key attributes
        for file_info in data:
            file_path = os.path.join(TESTSERVER_ROOT,
                                     file_info["url"].lstrip("/"))
            if file_info["type"] == "folder":
                self.assertTrue(os.path.isdir(file_path))
            else:
                self.assertTrue(os.path.isfile(file_path))

            mtime = os.path.getmtime(file_path)

            self.assertEqual(mtime, file_info["mtime"])

    def test_api_get_listing_single_file(self):
        url = "/api/ls/build-info/snowball-blob.txt"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)["files"]

        # Should be a listing for a single file
        self.assertEqual(len(data), 1)

        # For each file listed, check some key attributes
        for file_info in data:
            file_path = os.path.join(TESTSERVER_ROOT,
                                     file_info["url"].lstrip("/"))
            if file_info["type"] == "folder":
                self.assertTrue(os.path.isdir(file_path))
            else:
                self.assertTrue(os.path.isfile(file_path))

            mtime = os.path.getmtime(file_path)

            self.assertEqual(mtime, file_info["mtime"])

    def test_api_get_listing_404(self):
        url = "/api/ls/buld-info"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def _send_file(self, url, apikey, content, resp_code=200):
        f = StringIO.StringIO(content)
        f.name = 'name'   # to fool django's client.post
        response = self.client.post(url, data={"key": apikey, "file": f})
        self.assertEqual(response.status_code, resp_code)

    def test_get_key_post_and_get_file(self):
        key = self.priv_key
        last_used = APIKeyStore.objects.get(key=key).last_used

        file_content = "test_get_key_post_and_get_file"
        self._send_file('http://testserver/file_name', key, file_content)

        # Check the upload worked by reading the file back from its
        # uploaded location
        uploaded_file_path = os.path.join(
            settings.UPLOAD_PATH, key, "file_name")
        with open(uploaded_file_path) as f:
            self.assertEqual(f.read(), file_content)

        # Test we can fetch the newly uploaded file if we present the key
        response = self.client.get("http://testserver/file_name",
                                   data={"key": key})
        self.assertEqual(response.status_code, 200)
        with open(response.get('X-Sendfile', None)) as f:
            self.assertEqual(file_content, f.read())

        response = self.client.get("http://testserver/file_name")
        self.assertEqual(response.status_code, 404)

        self.assertNotEqual(
            APIKeyStore.objects.get(key=key).last_used, last_used)

    def test_get_public_key_post_and_get_file(self):
        key = self.pub_key

        # Now write a file so we can upload it
        file_content = "test_get_key_post_and_get_file"
        buildinfo_content = "\n".join([
            "Format-Version: 0.1",
            "Files-Pattern: *",
            "Build-Name: test",
            "License-Type: open"])

        self._send_file('http://testserver/pub/file_name', key, file_content)
        self._send_file(
            'http://testserver/pub/BUILD-INFO.txt', key, buildinfo_content)

        # Check the upload worked by reading the file back from its
        # uploaded location
        uploaded_file_path = os.path.join(
            settings.SERVED_PATHS[0], 'pub/file_name')

        with open(uploaded_file_path) as f:
            self.assertEqual(f.read(), file_content)

        # Test we can fetch the newly uploaded file
        response = self.client.get("http://testserver/pub/file_name")
        self.assertEqual(response.status_code, 200)

    def test_post_empty_file(self):
        '''Ensure we accept zero byte files'''
        key = self.priv_key

        file_content = ""
        self._send_file('http://testserver/file_name', key, file_content)

        # Check the upload worked by reading the file back from its
        # uploaded location
        uploaded_file_path = os.path.join(
            settings.UPLOAD_PATH, key, "file_name")
        with open(uploaded_file_path) as f:
            self.assertEqual(f.read(), file_content)

        response = self.client.get("http://testserver/file_name")
        self.assertNotEqual(response.status_code, 200)

    def test_post_no_file(self):
        response = self.client.post(
            "http://testserver/file_name", data={"key": self.priv_key})
        self.assertEqual(response.status_code, 500)

    def test_post_file_no_key(self):
        file_content = "test_post_file_no_key"
        self._send_file("http://testserver/file_name", None, file_content, 500)
        self.assertFalse(os.path.isfile(
            os.path.join(settings.UPLOAD_PATH, "file_name")))

    def test_post_file_random_key(self):
        key = "%030x" % random.randrange(256 ** 15)
        file_content = "test_post_file_random_key"
        self._send_file("http://testserver/file_name", key, file_content, 500)
