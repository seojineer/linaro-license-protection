__author__ = 'dooferlad'

import unittest
import hashlib
from django.test import Client, TestCase
from license_protected_downloads.models import License
from license_protected_downloads.buildinfo import BuildInfo
from license_protected_downloads.buildinfo import IncorrectDataFormatException


class LicenseTestCase(TestCase):
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


class BuildInfoTests(unittest.TestCase):
    def test_readFile_nonFile(self):
        with self.assertRaises(IOError):
            build_info = BuildInfo("license_protected_downloads")

    def test_readFile_nonexistentFile(self):
        with self.assertRaises(IOError):
            build_info = BuildInfo("nonexistent.file")

    def test_readFile_File(self):
        build_info = BuildInfo("license_protected_downloads/BUILD-INFO.txt")

        self.assertIn("Files-Pattern: *.txt", build_info.lines)

    def test_getFormatVersion(self):
        build_info = BuildInfo("license_protected_downloads/BUILD-INFO.txt")

        self.assertEqual("0.1", build_info.getFormatVersion())

    def test_get_emptyField(self):
        build_info = BuildInfo("license_protected_downloads/BUILD-INFO.txt")
        for pair in build_info.file_info_array:
            if "openid-launchpad-teams" in pair:
                value = pair["openid-launchpad-teams"]

        self.assertFalse(value)

    def test_get(self):
        build_info = BuildInfo("license_protected_downloads/BUILD-INFO.txt")
        for pair in build_info.file_info_array:
            if "build-name" in pair:
                value = pair["build-name"]

        self.assertEqual(value, "landing-protected")

    def test_parseLine_fails(self):
        line = "no separator"
        build_info = BuildInfo("license_protected_downloads/BUILD-INFO.txt")

        with self.assertRaises(IncorrectDataFormatException):
            build_info.parseLine(line)

    def test_parseLine_passes(self):
        line = "Build-Name:value"
        build_info = BuildInfo("license_protected_downloads/BUILD-INFO.txt")

        self.assertDictEqual({"build-name":"value"}, build_info.parseLine(line))

    def test_parseLine_trims(self):
        line = "Build-Name: value"
        build_info = BuildInfo("license_protected_downloads/BUILD-INFO.txt")

        self.assertDictEqual({"build-name":"value"}, build_info.parseLine(line))

    def test_parseLine_invalid_field(self):
        line = "field: value"
        build_info = BuildInfo("license_protected_downloads/BUILD-INFO.txt")

        with self.assertRaises(IncorrectDataFormatException):
            build_info.parseLine(line)

    def test_parseData_no_format_version_fails(self):
        build_info = BuildInfo("license_protected_downloads/BUILD-INFO.txt")

        with self.assertRaises(IncorrectDataFormatException):
            build_info.parseData(["Build-Name: blah"])

    def test_parseData_blocks(self):
        build_info = BuildInfo("license_protected_downloads/BUILD-INFO.txt")
        build_info.build_info_array = [{}]
        data = ["Format-Version: 2.0", "Files-Pattern: *.txt", "Build-Name: weehee",
                "Files-Pattern: *.tgz", "Build-Name: woohoo"]
        build_info.parseData(data)

        self.assertEquals(build_info.build_info_array,
                [{"format-version": "2.0",
                 '*.txt': [{'build-name': 'weehee'}],
                 '*.tgz': [{'build-name': 'woohoo'}]}])

    def test_parseData_block_multiple_patterns(self):
        build_info = BuildInfo("license_protected_downloads/BUILD-INFO.txt")
        build_info.build_info_array = [{}]
        data = ["Format-Version: 2.0", "Files-Pattern: *.txt,*.tgz",
                "Build-Name: weehee"]
        build_info.parseData(data)

        self.assertEquals(build_info.build_info_array,
                [{"format-version": "2.0",
                 '*.txt': [{'build-name': 'weehee'}],
                 '*.tgz': [{'build-name': 'weehee'}]}])

    def test_parseContinuation_no_continuation(self):
        build_info = BuildInfo("license_protected_downloads/BUILD-INFO.txt")
        build_info.line_no = 0

        self.assertEquals("", build_info.parseContinuation(["no-space"]))

    def test_parseContinuation_indexed(self):
        build_info = BuildInfo("license_protected_downloads/BUILD-INFO.txt")
        build_info.line_no = 0

        self.assertEquals("", build_info.parseContinuation(["no-space", " space"]))

    def test_parseContinuation(self):
        build_info = BuildInfo("license_protected_downloads/BUILD-INFO.txt")
        build_info.line_no = 1
        val = build_info.parseContinuation(["no-space", " line1", " line2"])

        self.assertEquals("\nline1\nline2", val)

    def test_parseBlock_license(self):
        build_info = BuildInfo("license_protected_downloads/BUILD-INFO.txt")
        build_info.line_no = 0
        build_info.build_info_array = [{}]
        data = ["Format-Version: 2.0", "License-Text: line1", " line2"]
        values = build_info.parseBlock(data)

        self.assertEqual(values, [{"format-version": "2.0",
            "license-text": "line1\nline2"}])

    def test_parseData_extra_fields(self):
        build_info = BuildInfo("license_protected_downloads/BUILD-INFO.txt")
        build_info.build_info_array = [{}]
        data = ["Format-Version: 2.0", "Files-Pattern: *.txt", "Build-Name: woohoo"]
        build_info.parseData(data)

        self.assertEqual(build_info.build_info_array,
                [{"format-version": "2.0",
                  '*.txt': [{'build-name': 'woohoo'}]}])

    def test_parseData_format_version(self):
        build_info = BuildInfo("license_protected_downloads/BUILD-INFO.txt")
        build_info.build_info_array = [{}]
        data = ["Format-Version: 2.0"]
        build_info.parseData(data)

        self.assertEqual(build_info.build_info_array,
                [{"format-version": "2.0"}])

    def test_parseData_array_expected(self):
        build_info = BuildInfo("license_protected_downloads/BUILD-INFO.txt")
        build_info.build_info_array = [{}]
        data = "Format-Version: 2.0"

        with self.assertRaises(IncorrectDataFormatException):
            build_info.parseData(data)

    def test_parseData_fails(self):
        build_info = BuildInfo("license_protected_downloads/BUILD-INFO.txt")
        build_info.build_info_array = [{}]
        data = ["text"]

        with self.assertRaises(IncorrectDataFormatException):
            build_info.parseData(data)

    def test_isValidField_false(self):
        build_info = BuildInfo("license_protected_downloads/BUILD-INFO.txt")

        self.assertFalse(build_info.isValidField("field"))

    def test_isValidField_true(self):
        build_info = BuildInfo("license_protected_downloads/BUILD-INFO.txt")

        for field in build_info.fields_defined:
            self.assertTrue(build_info.isValidField(field))


if __name__ == '__main__':
    unittest.main()
