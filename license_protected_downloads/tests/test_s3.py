import os
import shutil
import tempfile
import unittest
import urlparse

from django.conf import settings
from django.http import Http404
from django.test import TestCase

import mock

from license_protected_downloads.artifact import Artifact, S3Artifact
from license_protected_downloads import common
from license_protected_downloads.tests.test_views import (
    BuildInfoProtectedTests,
    EulaProtectedTests,
    HeaderTests,
    TESTSERVER_ROOT,
    WildCardTests,
)

_orig_s3_prefix = getattr(settings, 'S3_PREFIX_PATH', None)
_s3_enabled = _orig_s3_prefix is not None


def _upload_sampleroot(bucket):
    # make sure nothing was left from an old run
    keys = bucket.list(settings.S3_PREFIX_PATH)
    bucket.delete_keys(keys)

    for root, dirs, files in os.walk(TESTSERVER_ROOT):
        prefix = root[len(TESTSERVER_ROOT) + 1:]
        for f in files:
            if prefix:
                path = prefix + '/' + f
            else:
                path = f
            key = settings.S3_PREFIX_PATH + path
            key = bucket.get_key(key, validate=False)
            f = os.path.join(TESTSERVER_ROOT, path)
            if os.path.exists(f):
                key.set_contents_from_filename(f)


if _s3_enabled:
    def setUpModule():
        settings.S3_PREFIX_PATH = settings.S3_PREFIX_PATH[:-1] + '-test/'
        bucket = S3ViewTest.get_bucket()
        if 'FAST_TEST' not in os.environ:
            _upload_sampleroot(bucket)

    def tearDownModule():
        settings.S3_PREFIX_PATH = _orig_s3_prefix


@unittest.skipIf(_s3_enabled is False, 's3 not configured')
class S3ViewTest(BuildInfoProtectedTests, EulaProtectedTests, WildCardTests,
                 HeaderTests):
    '''Extend all the view tests to excerise with an S3 bucket backing'''
    bucket = None

    @staticmethod
    def get_bucket():
        if not S3ViewTest.bucket:
            S3ViewTest.bucket = S3Artifact.get_bucket()
        return S3ViewTest.bucket

    def setUp(self):
        super(S3ViewTest, self).setUp()

        self.request = mock.Mock()
        self.request.GET = {}
        self.s3_mock.return_value = S3ViewTest.get_bucket()

        # force lookups to hit S3 rather than local files
        m = mock.patch('django.conf.settings.SERVED_PATHS',
                       new_callable=lambda: [])
        self.addCleanup(m.stop)
        m.start()

    def _test_get_file(self, path, follow_redirect):
        # all s3 gets will be redirects, we can't follow them in the django
        # test client, so just assert we get a 302 and the path seems sane
        url = urlparse.urljoin(self.urlbase, path)
        resp = self.client.get(url)
        self.assertEqual(302, resp.status_code)
        self.assertIn('Signature=', resp['Location'])

    @staticmethod
    def _get_artifact(path):
        request = mock.Mock()
        request.GET = {}
        return common._find_s3_artifact(request, path)


@unittest.skipIf(_s3_enabled is False, 's3 not configured')
class TestS3(TestCase):
    '''Tests specific to S3 not covered in test_views'''
    def setUp(self):
        self.request = mock.Mock()
        self.request.GET = {}
        self.request.bucket = S3ViewTest.get_bucket()

        # force lookups to hit S3 rather than local files
        self.served_paths = mock.patch(
            'django.conf.settings.SERVED_PATHS', new_callable=lambda: [])
        self.addCleanup(self.served_paths.stop)
        self.served_paths.start()

    def test_find_artifact_404(self):
        '''Ensure we 404 on a bad key'''
        with self.assertRaises(Http404):
            common.find_artifact(self.request, 'does not exist')

    def test_find_artifact_partial(self):
        '''Don't return partial s3 matches

        if s3 has a key like 'foo/bar' it will return a match if you request
        'foo/ba'. Validate we reject that
        '''
        # we have two files starting with "o" under build-info
        common.find_artifact(self.request, 'build-info/openid.txt')
        with self.assertRaises(Http404):
            common.find_artifact(self.request, 'build-info/o')

    def test_find_artifact_directory(self):
        '''S3 gives different listings for subdir/ and subdir

        The trailing slash implies a directory listing. Assert we always
        remove the trailing slash.
        '''
        a = common.find_artifact(self.request, '~linaro-android')
        self.assertTrue(isinstance(a, common.S3Artifact))
        self.assertTrue(a.isdir())
        a = common.find_artifact(self.request, '~linaro-android/')
        self.assertTrue(isinstance(a, common.S3Artifact))
        self.assertTrue(a.isdir())

    def test_find_artifact_file(self):
        a = common.find_artifact(self.request, 'images/origen-blob.txt')
        self.assertTrue(isinstance(a, common.S3Artifact))
        self.assertFalse(a.isdir())

    def test_build_info_cached(self):
        '''TODO: ensure we cache build-info buffer after 1st request'''

    def test_eulas_cached(self):
        '''TODO: ensure we cache eulas for directory after 1st request'''


@unittest.skipIf(_s3_enabled is False, 's3 not configured')
class TestMixedBuilds(TestCase):
    '''Ensure a can handle a build that may have local and s3 builds

    eg: build_foo/
             1/ # this is a local file
             2/ # this is in S3
    '''

    def setUp(self):
        self.request = mock.Mock()
        self.request.GET = {}

        self.tempdir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tempdir)

        m = mock.patch('django.conf.settings.SERVED_PATHS',
                       new_callable=lambda: [self.tempdir])
        self.addCleanup(m.stop)
        m.start()

        # we'll now have a layout like:
        #  ~linaro-android/staging-snowball/1 (local)
        #  ~linaro-android/staging-snowball/173 (s3)
        path = os.path.join(self.tempdir, '~linaro-android/staging-snowball/1')
        os.makedirs(path)

    def test_find_artifact_both(self):
        # first make sure if both s3 and local are found we return the local
        # instance
        a = common.find_artifact(
            self.request, '~linaro-android/staging-snowball')
        self.assertTrue(isinstance(a, Artifact))
        self.assertTrue(a.isdir())

        # test the listing
        builds = [x['name'] for x in common.dir_list(a)]
        self.assertEqual(['1', '173'], builds)

    def test_prefer_local(self):
        '''if we happen to have local and s3 build, list local'''
        path = os.path.join(
            self.tempdir, '~linaro-android/staging-snowball/173')
        os.makedirs(path)

        a = common.find_artifact(
            self.request, '~linaro-android/staging-snowball')
        # test the listing
        listing = common.dir_list(a)
        builds = [x['name'] for x in listing]
        self.assertEqual(['1', '173'], builds)

        # s3 folder listings have no "mtime", so we can validate with that:
        self.assertNotEqual('-', listing[1]['mtime'])
