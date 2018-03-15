__author__ = 'dooferlad'

import datetime
import hashlib
import unittest

import mock

from django.conf import settings
from django.test import TestCase

from license_protected_downloads.models import (
    APIKeyStore,
    APIToken,
    Download,
    License,
)


class LicenseTestCase(TestCase):
    def setUp(self):
        lic1_text = 'Samsung License'
        lic2_text = 'Stericsson License'
        lic3_text = 'Linaro License'
        digest1 = hashlib.md5(lic1_text).hexdigest()
        digest2 = hashlib.md5(lic2_text).hexdigest()
        digest3 = hashlib.md5(lic3_text).hexdigest()
        self.lic1 = License.objects.create(
            digest=digest1, text=lic1_text, theme='samsung')
        self.lic2 = License.objects.create(
            digest=digest2, text=lic2_text, theme='stericsson')
        self.lic3 = License.objects.create(
            digest=digest3, text=lic3_text, theme='linaro')

    def test_add_license_to_database(self):
        self.assertEquals(self.lic1.theme, 'samsung')
        self.assertEquals(self.lic2.theme, 'stericsson')
        self.assertEquals(self.lic3.theme, 'linaro')

        lic1 = License.objects.get(pk=1)
        self.assertEquals(lic1.theme, 'samsung')
        self.assertEquals(lic1.text, 'Samsung License')
        lic2 = License.objects.get(pk=2)
        self.assertEquals(lic2.theme, 'stericsson')
        self.assertEquals(lic2.text, 'Stericsson License')
        lic3 = License.objects.get(pk=3)
        self.assertEquals(lic3.theme, 'linaro')
        self.assertEquals(lic3.text, 'Linaro License')


class APITokenTests(TestCase):
    def setUp(self):
        self.key = APIKeyStore.objects.create(key='foo', public=True)
        self.request = None

    def test_no_expire(self):
        token = APIToken.objects.create(key=self.key)
        self.assertTrue(token.valid_request(self.request))

        expires = datetime.datetime.now() + datetime.timedelta(minutes=1)
        token = APIToken.objects.create(key=self.key, expires=expires)
        self.assertTrue(token.valid_request(self.request))

    def test_expired(self):
        expires = datetime.datetime.now() - datetime.timedelta(seconds=1)
        token = APIToken.objects.create(key=self.key, expires=expires)
        self.assertFalse(token.valid_request(self.request))
        self.assertTrue(len(token.token) > 0)


class DownloadTests(TestCase):
    def test_cant_fail(self):
        '''Ensure Download.mark can't raise an exception.
        This would cause a user's download to fail.'''
        val = settings.TRACK_DOWNLOAD_STATS
        try:
            settings.TRACK_DOWNLOAD_STATS = True
            with mock.patch('logging.exception') as l:
                Download.mark(None, None)
                self.assertEqual(1, l.call_count)
        finally:
            settings.TRACK_DOWNLOAD_STATS = val

    def test_next_month(self):
        stamps = [
            # a leap year
            (datetime.datetime.strptime('2016.01 30', '%Y.%m %d'),
             (2016, 2, 29)),
            (datetime.datetime.strptime('2015.12', '%Y.%m'),
             (2016, 1, 01)),
            (datetime.datetime.strptime('2015.12 31', '%Y.%m %d'),
             (2016, 1, 31)),
            (datetime.datetime.strptime('2017.01 30', '%Y.%m %d'),
             (2017, 2, 28)),
        ]
        for ts, expected in stamps:
            ts = Download.next_month(ts)
            self.assertEqual(expected, (ts.year, ts.month, ts.day))


if __name__ == '__main__':
    unittest.main()
