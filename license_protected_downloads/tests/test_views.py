__author__ = 'dooferlad'

from django.conf import settings
from django.test import Client, TestCase
import hashlib
import os
import unittest
import urlparse

from license_protected_downloads.buildinfo import BuildInfo
from license_protected_downloads.views import _insert_license_into_db

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

    def set_up_license(self, target_file, index=0):
        # Get BuildInfo for target file
        file_path = os.path.join(TESTSERVER_ROOT, target_file)
        build_info = BuildInfo(file_path)

        # Insert license information into database
        text = build_info.get("license-text", index)
        digest = hashlib.md5(text).hexdigest()
        theme = build_info.get("theme", index)
        _insert_license_into_db(digest, text, theme)
        return digest

    def test_redirect_to_file_on_accept_license(self):
        target_file = "build-info/linaro-blob.txt"
        digest = self.set_up_license(target_file)

        # Accept the license for our file...
        accept_url = '/accept-license?lic=%s&url=%s' % (digest, target_file)
        response = self.client.post(accept_url, {"accept": "accept"})

        # We should have a license accept cookie.
        accept_cookie_name = "license_accepted_" + digest
        self.assertTrue(accept_cookie_name in response.cookies)

        # We should get redirected back to the original file location.
        self.assertEqual(response.status_code, 302)
        url = urlparse.urljoin("http://testserver/", target_file)
        listing_url = os.path.dirname(url)
        self.assertEqual(response['Location'],
                         listing_url + "?dl=/" + target_file)

    def test_redirect_to_decline_page_on_decline_license(self):
        target_file = "build-info/linaro-blob.txt"
        digest = self.set_up_license(target_file)

        # Reject the license for our file...
        accept_url = '/accept-license?lic=%s&url=%s' % (digest, target_file)
        response = self.client.post(accept_url, {"reject": "reject"})

        # We should get a message saying we don't have access to the file.
        self.assertContains(response, "Without accepting the license, you can"
                                      " not download the requested files.")

    def test_download_file_accepted_license(self):
        target_file = "build-info/linaro-blob.txt"
        url = urlparse.urljoin("http://testserver/", target_file)
        digest = self.set_up_license(target_file)

        # Accept the license for our file...
        accept_url = '/accept-license?lic=%s&url=%s' % (digest, target_file)
        response = self.client.post(accept_url, {"accept": "accept"})

        # We should get redirected back to the original file location.
        self.assertEqual(response.status_code, 302)
        listing_url = os.path.dirname(url)
        self.assertEqual(response['Location'],
                         listing_url + "?dl=/" + target_file)

        # We should have a license accept cookie.
        accept_cookie_name = "license_accepted_" + digest
        self.assertTrue(accept_cookie_name in response.cookies)

        # XXX Workaround for seemingly out of sync cookie handling XXX
        # The cookies in client.cookies are instances of
        # http://docs.python.org/library/cookie.html once they have been
        # returned by a client get/post. Unfortunately for the next query
        # client.cookies needs to be a dictionary keyed by cookie name and
        # containing a value of whatever is stored in the cookie (or so it
        # seems). For this reason we start up a new client, erasing all
        # cookies from the current session, and re-introduce them.
        client = Client()
        client.cookies[accept_cookie_name] = accept_cookie_name
        response = client.get(url)

        # If we have access to the file, we will get an X-Sendfile response
        self.assertEqual(response.status_code, 200)
        file_path = os.path.join(TESTSERVER_ROOT, target_file)
        self.assertEqual(response['X-Sendfile'], file_path)

    def test_OPEN_EULA_txt(self):
        target_file = '~linaro-android/staging-vexpress-a9/test.txt'
        url = urlparse.urljoin("http://testserver/", target_file)
        response = self.client.get(url, follow=True)

        # If we have access to the file, we will get an X-Sendfile response
        self.assertEqual(response.status_code, 200)
        file_path = os.path.join(TESTSERVER_ROOT, target_file)
        self.assertEqual(response['X-Sendfile'], file_path)

    def test_never_available_dirs(self):
        target_file = '~linaro-android/staging-imx53/test.txt'
        url = urlparse.urljoin("http://testserver/", target_file)
        response = self.client.get(url, follow=True)

        # If we don't have access we will get a Forbidden response (403)
        self.assertEqual(response.status_code, 403)

    def test_protected_by_EULA_txt(self):
        # Get BuildInfo for target file
        target_file = "~linaro-android/staging-origen/test.txt"

        # Try to fetch file from server - we should be redirected
        url = urlparse.urljoin("http://testserver/", target_file)
        response = self.client.get(url, follow=True)

        eula_path = os.path.join(settings.PROJECT_ROOT,
                                 "templates/licenses/samsung.txt")
        with open(eula_path) as license_file:
            license_text = license_file.read()

        digest = hashlib.md5(license_text).hexdigest()
        self.assertRedirects(response, "/license?lic=%s&url=%s" %
                                       (digest, target_file))

        # Make sure that we get the license text in the license page
        self.assertContains(response, license_text)

        # Test that we use the "samsung" theme. This contains exynos.png
        self.assertContains(response, "exynos.png")

    # test_internal_host_* are integration, not unit tests and will be
    # located in another file...

    def test_per_file_license_samsung(self):
        # Get BuildInfo for target file
        target_file = "images/origen-blob.txt"

        # Try to fetch file from server - we should be redirected
        url = urlparse.urljoin("http://testserver/", target_file)
        response = self.client.get(url, follow=True)

        eula_path = os.path.join(settings.PROJECT_ROOT,
                                 "templates/licenses/samsung.txt")
        with open(eula_path) as license_file:
            license_text = license_file.read()

        digest = hashlib.md5(license_text).hexdigest()
        self.assertRedirects(response, "/license?lic=%s&url=%s" %
                                       (digest, target_file))

        # Make sure that we get the license text in the license page
        self.assertContains(response, license_text)

        # Test that we use the "samsung" theme. This contains exynos.png
        self.assertContains(response, "exynos.png")

    def test_per_file_non_protected_dirs(self):
        target_file = "images/MANIFEST"
        url = urlparse.urljoin("http://testserver/", target_file)
        response = self.client.get(url, follow=True)

        # If we have access to the file, we will get an X-Sendfile response
        self.assertEqual(response.status_code, 200)
        file_path = os.path.join(TESTSERVER_ROOT, target_file)
        self.assertEqual(response['X-Sendfile'], file_path)

    def test_dir_containing_only_dirs(self):
        target_file = "~linaro-android"
        url = urlparse.urljoin("http://testserver/", target_file)
        response = self.client.get(url, follow=True)

        # If we have access to the file, we will get an X-Sendfile response
        self.assertContains(response,
            r"<th></th><th>Name</th><th>License</th><th>Last modified</th>"
            "<th>Size</th>")

    def test_not_found_file(self):
        target_file = "12qwaszx"
        url = urlparse.urljoin("http://testserver/", target_file)
        response = self.client.get(url, follow=True)
        self.assertContains(response, "not found", status_code=404)

    def test_unprotected_BUILD_INFO(self):
        target_file = 'build-info/panda-open.txt'
        url = urlparse.urljoin("http://testserver/", target_file)
        response = self.client.get(url, follow=True)

        # If we have access to the file, we will get an X-Sendfile response
        self.assertEqual(response.status_code, 200)
        file_path = os.path.join(TESTSERVER_ROOT, target_file)
        self.assertEqual(response['X-Sendfile'], file_path)

    def test_redirect_to_file_on_accept_multi_license(self):
        target_file = "build-info/multi-license.txt"
        digest = self.set_up_license(target_file)

        # Accept the first license for our file...
        accept_url = '/accept-license?lic=%s&url=%s' % (digest, target_file)
        response = self.client.post(accept_url, {"accept": "accept"})

        # We should have a license accept cookie.
        accept_cookie_name = "license_accepted_" + digest
        self.assertTrue(accept_cookie_name in response.cookies)

        # We should get redirected back to the original file location.
        self.assertEqual(response.status_code, 302)
        url = urlparse.urljoin("http://testserver/", target_file)
        listing_url = os.path.dirname(url)
        self.assertEqual(response['Location'],
            listing_url + "?dl=/" + target_file)

        client = Client()
        client.cookies[accept_cookie_name] = accept_cookie_name

        digest = self.set_up_license(target_file, 1)

        # Accept the second license for our file...
        accept_url = '/accept-license?lic=%s&url=%s' % (digest, target_file)
        response = client.post(accept_url, {"accept": "accept"})

        # We should have a license accept cookie.
        accept_cookie_name1 = "license_accepted_" + digest
        self.assertTrue(accept_cookie_name1 in response.cookies)

        # We should get redirected back to the original file location.
        self.assertEqual(response.status_code, 302)
        url = urlparse.urljoin("http://testserver/", target_file)
        listing_url = os.path.dirname(url)
        self.assertEqual(response['Location'],
            listing_url + "?dl=/" + target_file)

        client = Client()
        client.cookies[accept_cookie_name] = accept_cookie_name
        client.cookies[accept_cookie_name1] = accept_cookie_name1
        response = client.get(url)

        # If we have access to the file, we will get an X-Sendfile response
        self.assertEqual(response.status_code, 200)
        file_path = os.path.join(TESTSERVER_ROOT, target_file)
        self.assertEqual(response['X-Sendfile'], file_path)

    def test_header_html(self):
        target_file = "~linaro-android"
        url = urlparse.urljoin("http://testserver/", target_file)
        response = self.client.get(url, follow=True)

        self.assertContains(response,
            r"Welcome to the Linaro releases server")

if __name__ == '__main__':
    unittest.main()
