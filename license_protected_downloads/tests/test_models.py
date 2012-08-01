__author__ = 'dooferlad'

import unittest
import hashlib
from django.test import TestCase
from license_protected_downloads.models import License
from django.conf import settings


class LicenseTestCase(TestCase):
    def setUp(self):
        lic1_text = 'Samsung License'
        lic2_text = 'Stericsson License'
        lic3_text = 'Linaro License'
        digest1 = hashlib.md5(lic1_text).hexdigest()
        digest2 = hashlib.md5(lic2_text).hexdigest()
        digest3 = hashlib.md5(lic2_text).hexdigest()
        self.lic1 = License.objects.create(digest=digest1, text=lic1_text,
                theme='samsung', sites_id=settings.SITE_ID)
        self.lic2 = License.objects.create(digest=digest2, text=lic2_text,
            theme='stericsson', sites_id=settings.SITE_ID)
        self.lic3 = License.objects.create(digest=digest3, text=lic3_text,
            theme='linaro', sites_id=settings.SITE_ID)

    def test_add_license_to_database(self):
        self.assertEquals(self.lic1.theme, 'samsung')
        self.assertEquals(self.lic2.theme, 'stericsson')
        self.assertEquals(self.lic3.theme, 'linaro')

        lic1 = License.objects.get(pk=1)
        self.assertEquals(lic1.theme, 'samsung')
        self.assertEquals(lic1.text, 'Samsung License')
        self.assertEquals(lic1.sites_id, settings.SITE_ID)
        lic2 = License.objects.get(pk=2)
        self.assertEquals(lic2.theme, 'stericsson')
        self.assertEquals(lic2.text, 'Stericsson License')
        self.assertEquals(lic2.sites_id, settings.SITE_ID)
        lic3 = License.objects.get(pk=3)
        self.assertEquals(lic3.theme, 'linaro')
        self.assertEquals(lic3.text, 'Linaro License')
        self.assertEquals(lic3.sites_id, settings.SITE_ID)


if __name__ == '__main__':
    unittest.main()
