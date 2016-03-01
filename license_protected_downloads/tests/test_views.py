__author__ = 'dooferlad'

import hashlib
import json
import os
import unittest
import urlparse
import csv
import tempfile

import mock

from django.conf import settings
from django.test import Client, TestCase
from django.http import HttpResponse
from license_protected_downloads.buildinfo import BuildInfo
from license_protected_downloads.artifact import LocalArtifact
from license_protected_downloads.artifact.base import _insert_license_into_db
from license_protected_downloads.config import INTERNAL_HOSTS
from license_protected_downloads.models import Download
from license_protected_downloads.tests.helpers import temporary_directory
from license_protected_downloads import views
from django.core.management import call_command

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

        self.urlbase = 'http://testserver/'

        m = mock.patch(
            'license_protected_downloads.artifact.S3Artifact.get_bucket')
        self.addCleanup(m.stop)
        self.s3_mock = m.start()
        self.s3_mock.return_value = None

    def tearDown(self):
        settings.SERVED_PATHS = self.old_served_paths
        settings.MASTER_API_KEY = self.old_master_api_key
        os.rmdir(settings.UPLOAD_PATH)
        settings.UPLOAD_PATH = self.old_upload_path

    @staticmethod
    def _get_artifact(path):
        return LocalArtifact(None, '', path, False, TESTSERVER_ROOT)

    def _test_get_file(self, path, follow_redirect):
        url = urlparse.urljoin(self.urlbase, path)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        file_path = os.path.join(TESTSERVER_ROOT, path)
        self.assertEqual(resp['X-Sendfile'], file_path)


class BuildInfoProtectedTests(BaseServeViewTest):
    '''Perform tests of files protected by build-info'''
    def _test_redirected_build_info(self, path, expected_response):
        build_info = self._get_artifact(path).get_build_info()

        # Try to fetch file from server - we should be redirected
        url = urlparse.urljoin(self.urlbase, path)
        response = self.client.get(url, follow=True)
        digest = hashlib.md5(build_info.get('license-text')).hexdigest()
        redir_path = '/license?lic=%s&url=%s' % (digest, path)
        self.assertRedirects(response, redir_path)

        # Make sure that we get the license text in the license page
        self.assertContains(response, build_info.get("license-text"))
        self.assertContains(response, expected_response)

    def test_redirect_to_license_samsung(self):
        self._test_redirected_build_info(
            'build-info/origen-blob.txt', 'exynos.png')

    def test_redirect_to_license_ste(self):
        self._test_redirected_build_info(
            'build-info/snowball-blob.txt', 'igloo.png')

    def test_redirect_to_license_linaro(self):
        self._test_redirected_build_info(
            'build-info/linaro-blob.txt', 'linaro.png')

    def test_unprotected_BUILD_INFO(self):
        target_file = 'build-info/panda-open.txt'
        self._test_get_file(target_file, True)

    def test_broken_build_info_directory(self):
        url = 'http://testserver/build-info/broken-build-info'
        response = self.client.get(url, follow=True)
        # If a build-info file is invalid, we don't allow access
        self.assertEqual(response.status_code, 403)

    def test_broken_build_info_file(self):
        url = 'http://testserver/build-info/broken-build-info/test.txt'
        response = self.client.get(url, follow=True)
        # If a build-info file is invalid, we don't allow access
        self.assertEqual(response.status_code, 403)

    def test_partial_build_info_file_open(self):
        target = 'partial-license-settings/' \
                 'partially-complete-build-info/should_be_open.txt'
        self._test_get_file(target, True)

    def test_partial_build_info_file_protected(self):
        target = 'partial-license-settings/' \
                 'partially-complete-build-info/should_be_protected.txt'
        self._test_redirected_build_info(target, 'exynos.png')

    def test_partial_build_info_file_unspecified(self):
        target = 'partial-license-settings/' \
                 'partially-complete-build-info/should_be_inaccessible.txt'
        url = urlparse.urljoin("http://testserver/", target)
        response = self.client.get(url, follow=True)
        # If a build-info file has no information about this file
        self.assertEqual(response.status_code, 403)

    def test_directory_protected(self):
        '''Ensure we can protect an entire directory. This is done by having a
        trailing "," in the files-pattern of the build-info file. Given the
        fragile nature of build-info we need to validate it can work
        with/without a trailing slast'''
        url = 'http://testserver/protected_listing'
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            '<title>OpenID transaction in progress</title>', response.content)

        url = 'http://testserver/protected_listing/'
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            '<title>OpenID transaction in progress</title>', response.content)


class EulaProtectedTests(BaseServeViewTest):
    '''Perform tests of files protected by EULA in their directory'''
    def test_never_available_dirs(self):
        target_file = '~linaro-android/staging-imx53/test.txt'
        url = urlparse.urljoin(self.urlbase, target_file)
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 403)

    def test_OPEN_EULA_txt(self):
        target_file = '~linaro-android/staging-vexpress-a9/test.txt'
        self._test_get_file(target_file, True)

    def _test_redirected_eula(self, path, license, theme_txt):
        with open(license) as f:
            license = f.read()

        url = urlparse.urljoin(self.urlbase, path)
        response = self.client.get(url, follow=True)
        digest = hashlib.md5(license).hexdigest()

        redir_path = '/license?lic=%s&url=%s' % (digest, path)
        self.assertRedirects(response, redir_path)
        self.assertContains(response, license)
        self.assertContains(response, theme_txt)

    def test_protected_by_EULA_txt(self):
        target_file = '~linaro-android/staging-origen/test.txt'
        eula_path = os.path.join(
            settings.PROJECT_ROOT, 'templates/licenses/samsung.txt')
        self._test_redirected_eula(target_file, eula_path, 'exynos.png')

    def test_per_file_license_samsung(self):
        # Get BuildInfo for target file
        target_file = 'images/origen-blob.txt'
        eula_path = os.path.join(
            settings.PROJECT_ROOT, 'templates/licenses/samsung.txt')
        self._test_redirected_eula(target_file, eula_path, 'exynos.png')

    def test_per_file_non_protected_dirs(self):
        self._test_get_file('images/MANIFEST', False)

    @mock.patch('license_protected_downloads.views.config')
    def test_protected_internal_file(self, config):
        '''ensure a protected file can be downloaded by an internal host'''
        config.INTERNAL_HOSTS = ('127.0.0.1',)
        target_file = '~linaro-android/staging-origen/test.txt'
        self._test_get_file(target_file, False)


class WildCardTests(BaseServeViewTest):
    def test_wildcard_found(self):
        url = 'http://testserver/~linaro-android/staging-panda/te*.txt'
        resp = self.client.get(url, follow=True)
        self.assertEquals(200, resp.status_code)

        # test the single character match "?" which is urlencoded as %3f
        url = 'http://testserver/~linaro-android/staging-panda/te%3ft.txt'
        resp = self.client.get(url, follow=True)
        self.assertEquals(200, resp.status_code)

    def test_wildcard_multiple(self):
        url = 'http://testserver/~linaro-android/staging-panda/*.txt'
        resp = self.client.get(url, follow=True)
        self.assertEquals(404, resp.status_code)

    def test_wildcard_protected(self):
        url = 'https://testserver/~linaro-android/staging-origen/te*.txt'
        resp = self.client.get(url)
        self.assertEquals(302, resp.status_code)
        self.assertIn('license?lic=', resp['Location'])


class HeaderTests(BaseServeViewTest):
    def test_header_html(self):
        url = 'http://testserver/~linaro-android'
        resp = self.client.get(url, follow=True)
        self.assertContains(resp, 'Welcome to the Linaro releases server')

    def test_process_include_tags(self):
        url = 'http://testserver/readme'
        response = self.client.get(url, follow=True)
        self.assertContains(response, 'Included from README')

    def test_render_descriptions(self):
        url = 'http://testserver/~linaro-android/staging-panda/'
        resp = self.client.get(url, follow=True)
        self.assertEquals(200, resp.status_code)
        self.assertIn('<a href="#tabs-2">Git Descriptions</a>', resp.content)

    def test_get_textile_files(self):
        resp = self.client.get(
            '/get-textile-files?path=~linaro-android/staging-panda/')
        self.assertIn('EULA', json.loads(resp.content))


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

    @staticmethod
    def set_up_license(target_file, index=0):
        # Get BuildInfo for target file
        build_info = ViewTests._get_artifact(target_file).get_build_info()

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
        response = client.get(response['Location'])

        # If we have access to the file, we get a page with "refresh" directive
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            '<meta http-equiv="REFRESH" content="0;url=', response.content)

        # now download the file
        response = client.get(url)
        file_path = os.path.join(TESTSERVER_ROOT, target_file)
        self.assertEqual(response['X-Sendfile'], file_path)

    @mock.patch('license_protected_downloads.views.config')
    def test_protected_internal_listing(self, config):
        '''ensure directory listings are browseable for internal hosts'''
        config.INTERNAL_HOSTS = ('127.0.0.1',)
        response = self.client.get('http://testserver/')
        self.assertIn('linaro-license-protection.git/commit', response.content)

    def test_dir_containing_only_dirs(self):
        target_file = "~linaro-android"
        url = urlparse.urljoin("http://testserver/", target_file)
        response = self.client.get(url, follow=True)

        # If we have access to the file, we will get an X-Sendfile response
        self.assertContains(
            response,
            r'<th></th><th>Name</th><th>Last modified</th>'
            '<th>Size</th><th style="display: None">License</th>')

    def test_dir_redirect(self):
        '''URLs to directs without trailing / should result in a redirect'''
        url = 'http://testserver/~linaro-android'
        response = self.client.get(url)
        self.assertEqual(302, response.status_code)
        self.assertEqual(url + '/', response['Location'])

    def test_parent_dir(self):
        '''Ensure the listing has the correct parent directory link'''
        url = 'http://testserver/~linaro-android/'
        response = self.client.get(url)
        self.assertEqual(200, response.status_code)
        self.assertIn('"/">Parent Directory', response.content)

        url = 'http://testserver/~linaro-android/staging-panda/'
        response = self.client.get(url, follow_redirect=True)
        self.assertIn('"/~linaro-android/">Parent Directory', response.content)

    def test_not_found_file(self):
        target_file = "12qwaszx"
        url = urlparse.urljoin("http://testserver/", target_file)
        response = self.client.get(url, follow=True)
        self.assertContains(response, "not found", status_code=404)

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

    def test_unable_to_download_hidden_files(self):
        target_file = '~linaro-android/staging-vexpress-a9/OPEN-EULA.txt'
        url = urlparse.urljoin("http://testserver/", target_file)
        response = self.client.get(url, follow=True)

        # This file exists, but isn't listed so we shouldn't be able to
        # download it.
        self.assertEqual(response.status_code, 404)

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

    @mock.patch('django.conf.settings.REPORT_CSV',
                tempfile.mkdtemp() + '/download_report.csv')
    @mock.patch('django.conf.settings.TRACK_DOWNLOAD_STATS', True)
    def test_download_stats(self):
        self._test_get_file('build-info/panda-open.txt', True)
        for row in csv.reader(open(settings.REPORT_CSV)):
            self.assertEqual('/build-info/panda-open.txt', row[1])
            self.assertEqual('127.0.0.1', row[0])
            self.assertEqual('False', row[2])
        # Process CSV into DB and check data
        call_command('report_process')
        downloads = list(Download.objects.all())
        self.assertEqual(1, len(downloads))
        self.assertEqual('/build-info/panda-open.txt', downloads[0].name)
        self.assertEqual('127.0.0.1', downloads[0].ip)
        self.assertFalse(downloads[0].link)


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
            "You need to be the member of one of the linaro, batman, catwoman "
            "or joker groups",
            status_code=403)


if __name__ == '__main__':
    unittest.main()
