__author__ = 'dooferlad'

import os
import unittest
from license_protected_downloads.buildinfo import BuildInfo
from license_protected_downloads.buildinfo import IncorrectDataFormatException

THIS_DIRECTORY = os.path.dirname(os.path.abspath(__file__))


class BuildInfoTests(unittest.TestCase):
    def setUp(self):
        self.buildinfo_file_path = os.path.join(THIS_DIRECTORY,
                                                "BUILD-INFO.txt")
    
    def test_readFile_nonFile(self):
        with self.assertRaises(IOError):
            build_info = BuildInfo("license_protected_downloads")

    def test_readFile_nonexistentFile(self):
        with self.assertRaises(IOError):
            build_info = BuildInfo("nonexistent.file")

    def test_readFile_File(self):
        build_info = BuildInfo(self.buildinfo_file_path)

        self.assertIn("Files-Pattern: *.txt", build_info.lines)

    def test_getFormatVersion(self):
        build_info = BuildInfo(self.buildinfo_file_path)

        self.assertEqual("0.1", build_info.getFormatVersion())

    def test_get_emptyField(self):
        build_info = BuildInfo(self.buildinfo_file_path)
        for pair in build_info.file_info_array:
            if "openid-launchpad-teams" in pair:
                value = pair["openid-launchpad-teams"]

        self.assertFalse(value)

    def test_get(self):
        build_info = BuildInfo(self.buildinfo_file_path)
        for pair in build_info.file_info_array:
            if "build-name" in pair:
                value = pair["build-name"]

        self.assertEqual(value, "landing-protected")

    def test_parseLine_fails(self):
        line = "no separator"
        build_info = BuildInfo(self.buildinfo_file_path)

        with self.assertRaises(IncorrectDataFormatException):
            build_info.parseLine(line)

    def test_parseLine_passes(self):
        line = "Build-Name:value"
        build_info = BuildInfo(self.buildinfo_file_path)

        self.assertDictEqual({"build-name":"value"}, build_info.parseLine(line))

    def test_parseLine_trims(self):
        line = "Build-Name: value"
        build_info = BuildInfo(self.buildinfo_file_path)

        self.assertDictEqual({"build-name":"value"}, build_info.parseLine(line))

    def test_parseLine_invalid_field(self):
        line = "field: value"
        build_info = BuildInfo(self.buildinfo_file_path)

        with self.assertRaises(IncorrectDataFormatException):
            build_info.parseLine(line)

    def test_parseData_no_format_version_fails(self):
        build_info = BuildInfo(self.buildinfo_file_path)

        with self.assertRaises(IncorrectDataFormatException):
            build_info.parseData(["Build-Name: blah"])

    def test_parseData_blocks(self):
        build_info = BuildInfo(self.buildinfo_file_path)
        build_info.build_info_array = [{}]
        data = ["Format-Version: 2.0", "Files-Pattern: *.txt", "Build-Name: weehee",
                "Files-Pattern: *.tgz", "Build-Name: woohoo"]
        build_info.parseData(data)

        self.assertEquals(build_info.build_info_array,
                [{"format-version": "2.0",
                 '*.txt': [{'build-name': 'weehee'}],
                 '*.tgz': [{'build-name': 'woohoo'}]}])

    def test_parseData_block_multiple_patterns(self):
        build_info = BuildInfo(self.buildinfo_file_path)
        build_info.build_info_array = [{}]
        data = ["Format-Version: 2.0", "Files-Pattern: *.txt,*.tgz",
                "Build-Name: weehee"]
        build_info.parseData(data)

        self.assertEquals(build_info.build_info_array,
                [{"format-version": "2.0",
                 '*.txt': [{'build-name': 'weehee'}],
                 '*.tgz': [{'build-name': 'weehee'}]}])

    def test_parseContinuation_no_continuation(self):
        build_info = BuildInfo(self.buildinfo_file_path)
        build_info.line_no = 0

        self.assertEquals("", build_info.parseContinuation(["no-space"]))

    def test_parseContinuation_indexed(self):
        build_info = BuildInfo(self.buildinfo_file_path)
        build_info.line_no = 0

        self.assertEquals("", build_info.parseContinuation(["no-space", " space"]))

    def test_parseContinuation(self):
        build_info = BuildInfo(self.buildinfo_file_path)
        build_info.line_no = 1
        val = build_info.parseContinuation(["no-space", " line1", " line2"])

        self.assertEquals("\nline1\nline2", val)

    def test_parseBlock_license(self):
        build_info = BuildInfo(self.buildinfo_file_path)
        build_info.line_no = 0
        build_info.build_info_array = [{}]
        data = ["Format-Version: 2.0", "License-Text: line1", " line2"]
        values = build_info.parseBlock(data)

        self.assertEqual(values, [{"format-version": "2.0",
            "license-text": "line1\nline2"}])

    def test_parseData_extra_fields(self):
        build_info = BuildInfo(self.buildinfo_file_path)
        build_info.build_info_array = [{}]
        data = ["Format-Version: 2.0", "Files-Pattern: *.txt", "Build-Name: woohoo"]
        build_info.parseData(data)

        self.assertEqual(build_info.build_info_array,
                [{"format-version": "2.0",
                  '*.txt': [{'build-name': 'woohoo'}]}])

    def test_parseData_format_version(self):
        build_info = BuildInfo(self.buildinfo_file_path)
        build_info.build_info_array = [{}]
        data = ["Format-Version: 2.0"]
        build_info.parseData(data)

        self.assertEqual(build_info.build_info_array,
                [{"format-version": "2.0"}])

    def test_parseData_array_expected(self):
        build_info = BuildInfo(self.buildinfo_file_path)
        build_info.build_info_array = [{}]
        data = "Format-Version: 2.0"

        with self.assertRaises(IncorrectDataFormatException):
            build_info.parseData(data)

    def test_parseData_fails(self):
        build_info = BuildInfo(self.buildinfo_file_path)
        build_info.build_info_array = [{}]
        data = ["text"]

        with self.assertRaises(IncorrectDataFormatException):
            build_info.parseData(data)

    def test_isValidField_false(self):
        build_info = BuildInfo(self.buildinfo_file_path)

        self.assertFalse(build_info.isValidField("field"))

    def test_isValidField_true(self):
        build_info = BuildInfo(self.buildinfo_file_path)

        for field in build_info.fields_defined:
            self.assertTrue(build_info.isValidField(field))


if __name__ == '__main__':
    unittest.main()
