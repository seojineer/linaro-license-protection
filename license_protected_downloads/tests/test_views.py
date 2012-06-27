from license_protected_downloads.views import _insert_license_into_db

__author__ = 'dooferlad'

import os
import unittest
import hashlib
from django.test import Client, TestCase
from license_protected_downloads.buildinfo import BuildInfo

THIS_DIRECTORY = os.path.dirname(os.path.abspath(__file__))


class ViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        buildinfo_file_path = os.path.join(THIS_DIRECTORY,
                                                "BUILD-INFO.txt")
        self.build_info = BuildInfo(buildinfo_file_path)

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
        response = self.client.get('/licenses/ste.html', follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '/build-info')

    def test_redirect_to_license_samsung(self):
        text = self.build_info.get("license-text")
        digest = hashlib.md5(text).hexdigest()
        theme = "samsung"

        _insert_license_into_db(digest, text, theme)

        url = "/"
        response = self.client.get('/license?lic=%s&url=%s' % (digest, url))
        self.assertEqual(response.status_code, 200)

        # Make sure that we get the license text in the license page
        self.assertContains(response, text)

        # Test that we use the "samsung" theme. This contains exynos.png
        self.assertContains(response, "exynos.png")

    def test_redirect_to_license_ste(self):
        text = self.build_info.get("license-text")
        digest = hashlib.md5(text).hexdigest()
        theme = "stericsson"

        _insert_license_into_db(digest, text, theme)

        url = "/"
        response = self.client.get('/license?lic=%s&url=%s' % (digest, url))
        self.assertEqual(response.status_code, 200)

        # Make sure that we get the license text in the license page
        self.assertContains(response, text)

        # Test that we use the "stericsson" theme. This contains igloo.png
        self.assertContains(response, "igloo.png")

    def test_redirect_to_license_linaro(self):
        text = self.build_info.get("license-text")
        digest = hashlib.md5(text).hexdigest()
        theme = "linaro"

        _insert_license_into_db(digest, text, theme)

        url = "/"
        response = self.client.get('/license?lic=%s&url=%s' % (digest, url))
        self.assertEqual(response.status_code, 200)

        # Make sure that we get the license text in the license page
        self.assertContains(response, text)

        # Test that we use the "linaro" theme. This contains linaro.png
        self.assertContains(response, "linaro.png")


if __name__ == '__main__':
    unittest.main()
