__author__ = 'dooferlad'

import hashlib
import os
import tempfile
import unittest
import urllib2
import urlparse

import mock

from django.conf import settings
from django.test import Client, TestCase
from django.http import HttpResponse

from license_protected_downloads.buildinfo import BuildInfo
from license_protected_downloads.common import _insert_license_into_db
from license_protected_downloads.config import INTERNAL_HOSTS
from license_protected_downloads.tests.helpers import temporary_directory
from license_protected_downloads.tests.helpers import TestHttpServer
from license_protected_downloads.views import _process_include_tags
from license_protected_downloads.views import is_same_parent_dir
from license_protected_downloads import views

THIS_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
TESTSERVER_ROOT = os.path.join(THIS_DIRECTORY, "testserver_root")


class BaseServeViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.old_served_paths = settings.SERVED_PATHS
        settings.SERVED_PATHS = [os.path.join(THIS_DIRECTORY,
                                              "testserver_root")]
        self.old_upload_path = settings.UPLOAD_PATH
        settings.UPLOAD_PATH = os.path.join(THIS_DIRECTORY,
                                            "test_upload_root")
        if not os.path.isdir(settings.UPLOAD_PATH):
            os.makedirs(settings.UPLOAD_PATH)
        self.old_master_api_key = settings.MASTER_API_KEY
        settings.MASTER_API_KEY = "1234abcd"

    def tearDown(self):
        settings.SERVED_PATHS = self.old_served_paths
        settings.MASTER_API_KEY = self.old_master_api_key
        os.rmdir(settings.UPLOAD_PATH)
        settings.UPLOAD_PATH = self.old_upload_path


class ViewTests(BaseServeViewTest):
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

    @staticmethod
    def set_up_license(target_file, index=0):
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

    @mock.patch('license_protected_downloads.views.config')
    def test_protected_internal_file(self, config):
        '''ensure a protected file can be downloaded by an internal host'''
        config.INTERNAL_HOSTS = ('127.0.0.1',)
        target_file = "~linaro-android/staging-origen/test.txt"
        url = urlparse.urljoin("http://testserver/", target_file)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('X-Sendfile', response)

    @mock.patch('license_protected_downloads.views.config')
    def test_protected_internal_listing(self, config):
        '''ensure directory listings are browseable for internal hosts'''
        config.INTERNAL_HOSTS = ('127.0.0.1',)
        response = self.client.get('http://testserver/')
        self.assertIn('linaro-license-protection.git/commit', response.content)

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
        self.assertContains(
            response,
            r"<th></th><th>Name</th><th>Last modified</th>"
            "<th>Size</th><th>License</th>")

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
        self.assertEqual(
            response['Location'], listing_url + "?dl=/" + target_file)

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
        self.assertEqual(
            response['Location'], listing_url + "?dl=/" + target_file)

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

        self.assertContains(
            response, r"Welcome to the Linaro releases server")

    def test_exception_internal_host_for_lic(self):
        internal_host = INTERNAL_HOSTS[0]
        target_file = 'build-info/origen-blob.txt'
        url = urlparse.urljoin("http://testserver/", target_file)
        response = self.client.get(
            url, follow=True, REMOTE_ADDR=internal_host)

        # If we have access to the file, we will get an X-Sendfile response
        self.assertEqual(response.status_code, 200)
        file_path = os.path.join(TESTSERVER_ROOT, target_file)
        self.assertEqual(response['X-Sendfile'], file_path)

    def test_exception_internal_host_for_openid(self):
        internal_host = INTERNAL_HOSTS[0]
        target_file = 'build-info/openid.txt'
        url = urlparse.urljoin("http://testserver/", target_file)
        response = self.client.get(
            url, follow=True, REMOTE_ADDR=internal_host)

        # If we have access to the file, we will get an X-Sendfile response
        self.assertEqual(response.status_code, 200)
        file_path = os.path.join(TESTSERVER_ROOT, target_file)
        self.assertEqual(response['X-Sendfile'], file_path)

    def test_exception_internal_host_for_lic_and_openid(self):
        internal_host = INTERNAL_HOSTS[0]
        target_file = 'build-info/origen-blob-openid.txt'
        url = urlparse.urljoin("http://testserver/", target_file)
        response = self.client.get(
            url, follow=True, REMOTE_ADDR=internal_host)

        # If we have access to the file, we will get an X-Sendfile response
        self.assertEqual(response.status_code, 200)
        file_path = os.path.join(TESTSERVER_ROOT, target_file)
        self.assertEqual(response['X-Sendfile'], file_path)

    def test_no_exception_ip(self):
        internal_host = '10.1.2.3'
        target_file = 'build-info/origen-blob.txt'
        file_path = os.path.join(TESTSERVER_ROOT, target_file)
        build_info = BuildInfo(file_path)

        # Try to fetch file from server - we should be redirected
        url = urlparse.urljoin("http://testserver/", target_file)
        response = self.client.get(
            url, follow=True, REMOTE_ADDR=internal_host)
        digest = hashlib.md5(build_info.get("license-text")).hexdigest()
        self.assertRedirects(response, '/license?lic=%s&url=%s' %
                                       (digest, target_file))

        # Make sure that we get the license text in the license page
        self.assertContains(response, build_info.get("license-text"))

        # Test that we use the "samsung" theme. This contains exynos.png
        self.assertContains(response, "exynos.png")

    def test_broken_build_info_directory(self):
        target_file = "build-info/broken-build-info"
        url = urlparse.urljoin("http://testserver/", target_file)
        response = self.client.get(url, follow=True)

        # If a build-info file is invalid, we don't allow access
        self.assertEqual(response.status_code, 403)

    def test_broken_build_info_file(self):
        target_file = "build-info/broken-build-info/test.txt"
        url = urlparse.urljoin("http://testserver/", target_file)
        response = self.client.get(url, follow=True)

        # If a build-info file is invalid, we don't allow access
        self.assertEqual(response.status_code, 403)

    def test_unable_to_download_hidden_files(self):
        target_file = '~linaro-android/staging-vexpress-a9/OPEN-EULA.txt'
        url = urlparse.urljoin("http://testserver/", target_file)
        response = self.client.get(url, follow=True)

        # This file exists, but isn't listed so we shouldn't be able to
        # download it.
        self.assertEqual(response.status_code, 404)

    def test_partial_build_info_file_open(self):
        target_file = ("partial-license-settings/"
                       "partially-complete-build-info/"
                       "should_be_open.txt")
        url = urlparse.urljoin("http://testserver/", target_file)
        response = self.client.get(url, follow=True)

        # If a build-info file specifies this file is open
        self.assertEqual(response.status_code, 200)

    def test_partial_build_info_file_protected(self):
        target_file = ("partial-license-settings/"
                       "partially-complete-build-info/"
                       "should_be_protected.txt")
        file_path = os.path.join(TESTSERVER_ROOT, target_file)
        build_info = BuildInfo(file_path)

        # Try to fetch file from server - we should be redirected
        url = urlparse.urljoin("http://testserver/", target_file)
        response = self.client.get(url, follow=True)
        digest = hashlib.md5(build_info.get("license-text")).hexdigest()
        self.assertRedirects(response, '/license?lic=%s&url=%s' %
                                       (digest, target_file))

    def test_partial_build_info_file_unspecified(self):
        target_file = ("partial-license-settings/"
                       "partially-complete-build-info/"
                       "should_be_inaccessible.txt")
        url = urlparse.urljoin("http://testserver/", target_file)
        response = self.client.get(url, follow=True)

        # If a build-info file has no information about this file
        self.assertEqual(response.status_code, 403)

    def test_listings_do_not_contain_double_slash_in_link(self):
        target_file = 'images/'
        url = urlparse.urljoin("http://testserver/", target_file)
        response = self.client.get(url, follow=True)

        # this link should not contain a double slash:
        self.assertNotContains(response, "//origen-blob.txt")

    def test_directory_with_broken_symlink(self):
        target_file = 'broken-symlinks'
        url = urlparse.urljoin("http://testserver/", target_file)
        response = self.client.get(url, follow=True)

        # this test should not cause an exception. Anything else is a pass.
        self.assertEqual(response.status_code, 200)

    def test_whitelisted_dirs(self):
        target_file = "precise/restricted/whitelisted.txt"
        url = urlparse.urljoin("http://testserver/", target_file)
        response = self.client.get(url, follow=True)

        # If we have access to the file, we will get an X-Sendfile response
        self.assertEqual(response.status_code, 200)
        file_path = os.path.join(TESTSERVER_ROOT, target_file)
        self.assertEqual(response['X-Sendfile'], file_path)

    def make_temporary_file(self, data, root=None):
        """Creates a temporary file and fills it with data.

        Returns the file name of the new temporary file.
        """
        tmp_file_handle, tmp_filename = tempfile.mkstemp(dir=root)
        tmp_file = os.fdopen(tmp_file_handle, "w")
        tmp_file.write(data)
        tmp_file.close()
        self.addCleanup(os.unlink, tmp_filename)
        return os.path.basename(tmp_filename)

    def test_replace_self_closing_tag(self):
        target_file = "readme"
        old_cwd = os.getcwd()
        file_path = os.path.join(TESTSERVER_ROOT, target_file)
        os.chdir(file_path)
        ret = _process_include_tags(
            'Test <linaro:include file="README" /> html')
        self.assertEqual(ret, r"Test Included from README html")
        os.chdir(old_cwd)

    def test_replace_self_closing_tag1(self):
        target_file = "readme"
        old_cwd = os.getcwd()
        file_path = os.path.join(TESTSERVER_ROOT, target_file)
        os.chdir(file_path)
        ret = _process_include_tags(
            'Test <linaro:include file="README"/> html')
        self.assertEqual(ret, r"Test Included from README html")
        os.chdir(old_cwd)

    def test_replace_with_closing_tag(self):
        target_file = "readme"
        old_cwd = os.getcwd()
        file_path = os.path.join(TESTSERVER_ROOT, target_file)
        os.chdir(file_path)
        ret = _process_include_tags(
            'Test <linaro:include file="README">README is missing'
            '</linaro:include> html')
        self.assertEqual(ret, r"Test Included from README html")
        os.chdir(old_cwd)

    def test_replace_non_existent_file(self):
        target_file = "readme"
        old_cwd = os.getcwd()
        file_path = os.path.join(TESTSERVER_ROOT, target_file)
        os.chdir(file_path)
        ret = _process_include_tags(
            'Test <linaro:include file="NON_EXISTENT_FILE" /> html')
        self.assertEqual(ret, r"Test  html")
        os.chdir(old_cwd)

    def test_replace_empty_file_property(self):
        target_file = "readme"
        old_cwd = os.getcwd()
        file_path = os.path.join(TESTSERVER_ROOT, target_file)
        os.chdir(file_path)
        ret = _process_include_tags(
            'Test <linaro:include file="" /> html')
        self.assertEqual(ret, r"Test  html")
        os.chdir(old_cwd)

    def test_replace_parent_dir(self):
        target_file = "readme"
        old_cwd = os.getcwd()
        file_path = os.path.join(TESTSERVER_ROOT, target_file)
        os.chdir(file_path)
        ret = _process_include_tags(
            'Test <linaro:include file="../README" /> html')
        self.assertEqual(ret, r"Test  html")
        os.chdir(old_cwd)

    def test_replace_subdir(self):
        target_file = "readme"
        old_cwd = os.getcwd()
        file_path = os.path.join(TESTSERVER_ROOT, target_file)
        os.chdir(file_path)
        ret = _process_include_tags(
            'Test <linaro:include file="subdir/README" /> html')
        self.assertEqual(ret, r"Test  html")
        os.chdir(old_cwd)

    def test_replace_subdir_parent_dir(self):
        target_file = "readme"
        old_cwd = os.getcwd()
        file_path = os.path.join(TESTSERVER_ROOT, target_file)
        os.chdir(file_path)
        ret = _process_include_tags(
            'Test <linaro:include file="subdir/../README" /> html')
        self.assertEqual(ret, r"Test Included from README html")
        os.chdir(old_cwd)

    def test_replace_full_path(self):
        target_file = "readme"
        old_cwd = os.getcwd()
        file_path = os.path.join(TESTSERVER_ROOT, target_file)
        os.chdir(file_path)
        tmp = self.make_temporary_file("Included from /tmp", root="/tmp")
        ret = _process_include_tags(
            'Test <linaro:include file="/tmp/%s" /> html' % tmp)
        self.assertEqual(ret, r"Test  html")
        os.chdir(old_cwd)

    def test_replace_self_dir(self):
        target_file = "readme"
        old_cwd = os.getcwd()
        file_path = os.path.join(TESTSERVER_ROOT, target_file)
        os.chdir(file_path)
        ret = _process_include_tags(
            'Test <linaro:include file="./README" /> html')
        self.assertEqual(ret, r"Test Included from README html")
        os.chdir(old_cwd)

    def test_replace_self_parent_dir(self):
        target_file = "readme"
        old_cwd = os.getcwd()
        file_path = os.path.join(TESTSERVER_ROOT, target_file)
        os.chdir(file_path)
        ret = _process_include_tags(
            'Test <linaro:include file="./../README" /> html')
        self.assertEqual(ret, r"Test  html")
        os.chdir(old_cwd)

    def test_replace_symlink(self):
        target_file = "readme"
        old_cwd = os.getcwd()
        file_path = os.path.join(TESTSERVER_ROOT, target_file)
        os.chdir(file_path)
        ret = _process_include_tags(
            'Test <linaro:include file="READMELINK" /> html')
        self.assertEqual(ret, r"Test  html")
        os.chdir(old_cwd)

    def test_process_include_tags(self):
        target_file = "readme"
        url = urlparse.urljoin("http://testserver/", target_file)
        response = self.client.get(url, follow=True)

        self.assertContains(response, r"Included from README")

    def test_is_same_parent_dir_true(self):
        fname = os.path.join(TESTSERVER_ROOT, "subdir/../file")
        self.assertTrue(is_same_parent_dir(TESTSERVER_ROOT, fname))

    def test_is_same_parent_dir_false(self):
        fname = os.path.join(TESTSERVER_ROOT, "../file")
        self.assertFalse(is_same_parent_dir(TESTSERVER_ROOT, fname))

    def test_get_remote_static_unsupported_file(self):
        response = self.client.get('/get-remote-static?name=unsupported.css')
        self.assertEqual(response.status_code, 404)

    def test_get_remote_static_nonexisting_file(self):
        pages = {"/": "index"}

        with TestHttpServer(pages) as http_server:
            css_url = '%s/init.css' % http_server.base_url
            settings.SUPPORTED_REMOTE_STATIC_FILES = {
                'init.css': css_url}

            self.assertRaises(urllib2.HTTPError, self.client.get,
                              '/get-remote-static?name=init.css')

    def test_get_remote_static(self):
        pages = {"/": "index", "/init.css": "test CSS"}

        with TestHttpServer(pages) as http_server:
            css_url = '%s/init.css' % http_server.base_url
            settings.SUPPORTED_REMOTE_STATIC_FILES = {
                'init.css': css_url}

            response = self.client.get('/get-remote-static?name=init.css')
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, 'test CSS')

    def test_path_to_root(self):
        response = self.client.get("http://testserver//", follow=True)

        # Shouldn't be able to escape served paths...
        self.assertEqual(response.status_code, 404)

    def test_path_to_dir_above(self):
        response = self.client.get("http://testserver/../", follow=True)

        # Shouldn't be able to escape served paths...
        self.assertEqual(response.status_code, 404)

    def test_path_to_dir_above2(self):
        response = self.client.get("http://testserver/..", follow=True)

        # Shouldn't be able to escape served paths...
        self.assertEqual(response.status_code, 404)


class HowtoViewTests(BaseServeViewTest):
    def test_no_howtos(self):
        with temporary_directory() as serve_root:
            settings.SERVED_PATHS = [serve_root.root]
            serve_root.make_file(
                "build/9/build.tar.bz2", with_buildinfo=True)
            response = self.client.get('/build/9/')
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, 'build.tar.bz2')

    def test_howtos_without_license(self):
        with temporary_directory() as serve_root:
            settings.SERVED_PATHS = [serve_root.root]
            serve_root.make_file(
                "build/9/build.tar.bz2", with_buildinfo=True)
            serve_root.make_file(
                "build/9/howto/HOWTO_test.txt", data=".h1 HowTo Test")
            response = self.client.get('/build/9/')
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, 'build.tar.bz2')

    def test_howtos_with_license_in_buildinfo(self):
        with temporary_directory() as serve_root:
            settings.SERVED_PATHS = [serve_root.root]
            serve_root.make_file(
                "build/9/build.tar.bz2", with_buildinfo=True)
            serve_root.make_file(
                "build/9/howto/HOWTO_test.txt", data=".h1 HowTo Test",
                with_buildinfo=True)
            response = self.client.get('/build/9/')
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, 'howto')

    def test_howtos_with_license_in_openeula(self):
        with temporary_directory() as serve_root:
            settings.SERVED_PATHS = [serve_root.root]
            serve_root.make_file(
                "build/9/build.tar.bz2", with_buildinfo=True)
            serve_root.make_file(
                "build/9/howto/HOWTO_test.txt", data=".h1 HowTo Test",
                with_buildinfo=False)
            serve_root.make_file(
                "build/9/howto/OPEN-EULA.txt", with_buildinfo=False)
            response = self.client.get('/build/9/')
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, 'howto')

    def test_howtos_howto_dir(self):
        with temporary_directory() as serve_root:
            settings.SERVED_PATHS = [serve_root.root]
            serve_root.make_file(
                "build/9/build.tar.bz2", with_buildinfo=True)
            serve_root.make_file(
                "build/9/howto/HOWTO_releasenotes.txt", data=".h1 HowTo Test")
            response = self.client.get('/build/9/howto/')
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, 'HowTo Test')

    def test_howtos_product_dir(self):
        with temporary_directory() as serve_root:
            settings.SERVED_PATHS = [serve_root.root]
            serve_root.make_file(
                "build/9/build.tar.bz2", with_buildinfo=True)
            serve_root.make_file(
                "build/9/target/product/panda/howto/HOWTO_releasenotes.txt",
                data=".h1 HowTo Test")
            response = self.client.get('/build/9/target/product/panda/howto/')
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, 'HowTo Test')


class FileViewTests(BaseServeViewTest):
    def test_static_file(self):
        with temporary_directory() as serve_root:
            settings.SERVED_PATHS = [serve_root.root]
            serve_root.make_file("MD5SUM")
            serve_root.make_file(
                "BUILD-INFO.txt",
                data=("Format-Version: 2.0\n\n"
                      "Files-Pattern: MD5SUM\n"
                      "License-Type: open\n"))
            response = self.client.get('/MD5SUM')
            self.assertEqual(response.status_code, 200)


class ViewHelpersTests(BaseServeViewTest):
    def test_auth_group_error(self):
        groups = ["linaro", "batman", "catwoman", "joker"]
        request = mock.Mock()
        request.path = "mock_path"
        response = views.group_auth_failed_response(request, groups)
        self.assertIsNotNone(response)
        self.assertTrue(isinstance(response, HttpResponse))
        self.assertContains(
            response,
            "You need to be the member of one of the linaro batman, catwoman "
            "or joker groups",
            status_code=403)


if __name__ == '__main__':
    unittest.main()
