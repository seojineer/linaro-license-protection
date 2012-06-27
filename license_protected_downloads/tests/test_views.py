import urlparse
from license_protected_downloads.views import _insert_license_into_db

__author__ = 'dooferlad'

import os
import unittest
import hashlib
from django.test import Client, TestCase
from license_protected_downloads.buildinfo import BuildInfo
from django.conf import settings

THIS_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
TESTSERVER_ROOT = os.path.join(THIS_DIRECTORY, "testserver_root")

class ViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.old_served_paths = settings.SERVED_PATHS
        settings.SERVED_PATHS = [os.path.join(THIS_DIRECTORY,
                                             "testserver_root")]

    def tearDown(self):
        settings.SERVED_PATHS = self.old_served_paths

    def test_license_directly(self):
        response = self.client.get('/licenses/license.html', follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '/build-info')

    def test_licensefile_directly_samsung(self):
        response = self.client.get('/licenses/samsung.html', follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '/build-info')

    def test_licensefile_directly_ste(self):
        response = self.client.get('/licenses/ste.html', follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '/build-info')

    def test_licensefile_directly_linaro(self):
        response = self.client.get('/licenses/linaro.html', follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '/build-info')

    def test_redirect_to_license_samsung(self):
        # Get BuildInfo for target file
        target_file = "build-info/origen-blob.txt"
        file_path = os.path.join(TESTSERVER_ROOT, target_file)
        build_info = BuildInfo(file_path)

        # Try to fetch file from server - we should be redirected
        url = urlparse.urljoin("http://testserver/", target_file)
        response = self.client.get(url, follow=True)
        digest = hashlib.md5(build_info.get("license-text")).hexdigest()
        self.assertRedirects(response, '/license?lic=%s&url=%s' %
                                       (digest, target_file))

        # Make sure that we get the license text in the license page
        self.assertContains(response, build_info.get("license-text"))

        # Test that we use the "samsung" theme. This contains exynos.png
        self.assertContains(response, "exynos.png")

    def test_redirect_to_license_ste(self):
        # Get BuildInfo for target file
        target_file = "build-info/snowball-blob.txt"
        file_path = os.path.join(TESTSERVER_ROOT, target_file)
        build_info = BuildInfo(file_path)

        # Try to fetch file from server - we should be redirected
        url = urlparse.urljoin("http://testserver/", target_file)
        response = self.client.get(url, follow=True)
        digest = hashlib.md5(build_info.get("license-text")).hexdigest()
        self.assertRedirects(response, '/license?lic=%s&url=%s' %
                                       (digest, target_file))

        # Make sure that we get the license text in the license page
        self.assertContains(response, build_info.get("license-text"))

        # Test that we use the "stericsson" theme. This contains igloo.png
        self.assertContains(response, "igloo.png")

    def test_redirect_to_license_linaro(self):
        # Get BuildInfo for target file
        target_file = "build-info/linaro-blob.txt"
        file_path = os.path.join(TESTSERVER_ROOT, target_file)
        build_info = BuildInfo(file_path)

        # Try to fetch file from server - we should be redirected
        url = urlparse.urljoin("http://testserver/", target_file)
        response = self.client.get(url, follow=True)
        digest = hashlib.md5(build_info.get("license-text")).hexdigest()
        self.assertRedirects(response, '/license?lic=%s&url=%s' %
                                       (digest, target_file))

        # Make sure that we get the license text in the license page
        self.assertContains(response, build_info.get("license-text"))

        # Test that we use the "linaro" theme. This contains linaro.png
        self.assertContains(response, "linaro.png")


if __name__ == '__main__':
    unittest.main()
