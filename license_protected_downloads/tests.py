import unittest
import hashlib
from django.test import Client, TestCase
from linaro_license_protection_2.models import License


class LicenseTestCase(unittest.TestCase):
    def setUp(self):
        lic1_text = 'Samsung License'
        lic2_text = 'Stericsson License'
        digest1 = hashlib.md5(lic1_text).hexdigest()
        digest2 = hashlib.md5(lic2_text).hexdigest()
        self.lic1 = License.objects.create(digest=digest1, text=lic1_text,
                theme='samsung')
        self.lic2 = License.objects.create(digest=digest2, text=lic2_text,
                theme='stericsson')

    def test_add_license_to_database(self):
        self.assertEquals(self.lic1.theme, 'samsung')
        self.assertEquals(self.lic2.theme, 'stericsson')

        lic1 = License.objects.get(pk=1)
        self.assertEquals(lic1.theme, 'samsung')
        self.assertEquals(lic1.text, 'Samsung License')
        lic2 = License.objects.get(pk=2)
        self.assertEquals(lic2.theme, 'stericsson')
        self.assertEquals(lic2.text, 'Stericsson License')


class ViewTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_license_directly(self):
        response = self.client.get('/licenses/license.html')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Index of /')

    def test_licensefile_directly_samsung(self):
        response = self.client.get('/licenses/samsung.html')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Index of /')

