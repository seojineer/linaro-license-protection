__author__ = 'dooferlad'

import os
import shutil
import tempfile
import unittest

from license_protected_downloads.buildinfo import (
    BuildInfoBase,
    BuildInfo,
    IncorrectDataFormatException,
)
from license_protected_downloads.tests.helpers import temporary_directory

THIS_DIRECTORY = os.path.dirname(os.path.abspath(__file__))


class BuildInfoBaseTests(unittest.TestCase):
    def setUp(self):
        p = os.path.join(THIS_DIRECTORY, "BUILD-INFO.txt")
        with open(os.path.join(THIS_DIRECTORY, "BUILD-INFO.txt")) as f:
            self.build_info = BuildInfoBase(p, os.path.dirname(p), f.read())

    def test_get_emptyField(self):
        value = "notempty"
        for pair in self.build_info.file_info_array:
            if "auth-groups" in pair:
                value = pair["auth-groups"]
        self.assertFalse(value)

    def test_get(self):
        value = None
        for pair in self.build_info.file_info_array:
            if "build-name" in pair:
                value = pair["build-name"]

        self.assertEqual(value, "landing-protected")

    def test_parseLine_fails(self):
        line = "no separator"
        with self.assertRaises(IncorrectDataFormatException):
            self.build_info.parseLine(line)

    def test_parseLine_passes(self):
        line = "Build-Name:value"
        self.assertDictEqual({"build-name": "value"},
                             self.build_info.parseLine(line))

    def test_parseLine_trims(self):
        line = "Build-Name: value"
        self.assertDictEqual({"build-name": "value"},
                             self.build_info.parseLine(line))

    def test_parseLine_invalid_field(self):
        line = "field: value"
        with self.assertRaises(IncorrectDataFormatException):
            self.build_info.parseLine(line)

    def test_parseData_no_format_version_fails(self):
        with self.assertRaises(IncorrectDataFormatException):
            self.build_info.parseData(["Build-Name: blah"])

    def test_parseData_blocks(self):
        self.build_info.build_info_array = [{}]
        data = ["Format-Version: 2.0",
                "Files-Pattern: *.txt",
                "Build-Name: weehee",
                "Files-Pattern: *.tgz",
                "Build-Name: woohoo"]
        self.build_info.parseData(data)

        expected = [{
            'format-version': '2.0',
            '*.txt': [{'build-name': 'weehee'}],
            '*.tgz': [{'build-name': 'woohoo'}]
        }]
        self.assertEquals(expected, self.build_info.build_info_array)

    def test_parseData_block_multiple_patterns(self):
        self.build_info.build_info_array = [{}]
        data = ["Format-Version: 2.0",
                "Files-Pattern: *.txt,*.tgz",
                "Build-Name: weehee"]
        self.build_info.parseData(data)

        expected = [{
            'format-version': '2.0',
            '*.txt': [{'build-name': 'weehee'}],
            '*.tgz': [{'build-name': 'weehee'}]
        }]
        self.assertEquals(expected, self.build_info.build_info_array)

    def test_parseContinuation_no_continuation(self):
        self.build_info.line_no = 0
        self.assertEquals("", self.build_info.parseContinuation(["no-space"]))

    def test_parseContinuation_indexed(self):
        self.build_info.line_no = 0
        self.assertEquals(
            "", self.build_info.parseContinuation(
                ["no-space", " space"]))

    def test_parseContinuation(self):
        self.build_info.line_no = 1
        val = self.build_info.parseContinuation(
            ["no-space", " line1", " line2"])
        self.assertEquals("\nline1\nline2", val)

    def test_parseBlock_license(self):
        self.build_info.line_no = 0
        self.build_info.build_info_array = [{}]
        data = ["Format-Version: 2.0", "License-Text: line1", " line2"]
        values = self.build_info.parseBlock(data)

        self.assertEqual(
            values,
            [{"format-version": "2.0", "license-text": "line1\nline2"}])

    def test_parseData_extra_fields(self):
        self.build_info.build_info_array = [{}]
        data = ["Format-Version: 2.0",
                "Files-Pattern: *.txt",
                "Build-Name: woohoo"]
        self.build_info.parseData(data)

        self.assertEqual(
            self.build_info.build_info_array,
            [{"format-version": "2.0", '*.txt': [{'build-name': 'woohoo'}]}])

    def test_parseData_format_version(self):
        self.build_info.build_info_array = [{}]
        data = ["Format-Version: 2.0"]
        self.build_info.parseData(data)

        self.assertEqual(
            self.build_info.build_info_array, [{"format-version": "2.0"}])

    def test_parseData_array_expected(self):
        self.build_info.build_info_array = [{}]
        data = "Format-Version: 2.0"

        with self.assertRaises(IncorrectDataFormatException):
            self.build_info.parseData(data)

    def test_parseData_fails(self):
        self.build_info.build_info_array = [{}]
        data = ["text"]

        with self.assertRaises(IncorrectDataFormatException):
            self.build_info.parseData(data)

    def test_isValidField_false(self):
        with self.assertRaises(IncorrectDataFormatException):
            self.build_info.assertValidField("field")

    def test_isValidField_true(self):
        for field in self.build_info.fields_defined:
            self.build_info.assertValidField(field)

    def test_remove_false_positives_real(self):
        self.build_info.build_info_array = [{}]
        data = ["Format-Version: 2.0",
                "Files-Pattern: *.txt",
                "License-Type: protected",
                "Files-Pattern: *.txt",
                "License-Type: open"]
        self.build_info.parseData(data)
        self.build_info.file_info_array = self.build_info.getInfoForFile()
        self.build_info.remove_false_positives()

        self.assertEquals(
            self.build_info.file_info_array, [{'license-type': 'protected'}])

    def test_remove_false_positives_none(self):
        self.build_info.build_info_array = [{}]
        data = ["Format-Version: 2.0",
                "Files-Pattern: *.txt",
                "License-Type: protected",
                "Files-Pattern: *.txt",
                "License-Type: protected"]
        self.build_info.parseData(data)
        self.build_info.file_info_array = self.build_info.getInfoForFile()
        self.build_info.remove_false_positives()

        self.assertEquals(
            self.build_info.file_info_array,
            [{'license-type': 'protected'}, {'license-type': 'protected'}])

    def test_getInfoForFile(self):
        self.build_info.full_file_name = os.path.join(
            self.build_info.search_path, 'foo.pyc')
        self.build_info.fname = 'foo.pyc'
        self.build_info.build_info_array = [{}]
        data = ["Format-Version: 2.0",
                "Files-Pattern: *.py*",
                "License-Type: protected"]
        self.build_info.parseData(data)
        file_info = self.build_info.getInfoForFile()

        self.assertEquals(file_info, [{'license-type': 'protected'}])

    def test_remove_false_positives_no_blocks_in_array(self):
        self.build_info.file_info_array = [{}]
        self.build_info.remove_false_positives()
        self.assertEquals(self.build_info.file_info_array, [{}])

    def test_getInfoForFile_no_block_for_file(self):
        self.build_info.full_file_name = os.path.join(
            self.build_info.search_path, 'foo.pyc')
        self.build_info.fname = 'foo.pyc'
        self.build_info.build_info_array = [{}]
        data = ["Format-Version: 2.0",
                "Files-Pattern: *.txt",
                "License-Type: protected"]
        self.build_info.parseData(data)
        file_info = self.build_info.getInfoForFile()

        self.assertEquals(file_info, [{}])


class BuildInfoFileTests(unittest.TestCase):
    def setUp(self):
        self.buildinfo_file_path = os.path.join(
            THIS_DIRECTORY, "BUILD-INFO.txt")

    def test_no_buildinfo(self):
        file_path = THIS_DIRECTORY + \
            '/testserver_root/build-info/no-build-info/file'
        with self.assertRaises(IOError):
            BuildInfo(file_path)

    def test_apply_to_dir(self):
        dir_path = THIS_DIRECTORY + \
            '/testserver_root/build-info/subdir'
        build_info = BuildInfo(dir_path)
        expected = [
            {'build-name': 'landing-protected', 'license-type': 'protected',
             'auth-groups': 'linaro'}
        ]
        self.assertEquals(expected, build_info.getInfoForFile())

    def test_apply_to_dir_auth_groups_field(self):
        dir_path = THIS_DIRECTORY + \
            '/testserver_root/build-info/subdir2'
        build_info = BuildInfo(dir_path)
        expected = [
            {'build-name': 'landing-protected', 'license-type': 'protected',
             'auth-groups': 'linaro'}
        ]
        self.assertEquals(expected, build_info.getInfoForFile())

    def test_apply_to_nonexistent_file(self):
        with self.assertRaises(IOError):
            BuildInfo("nonexistent.file")

    def test_get_search_path(self):
        dir_path = THIS_DIRECTORY + '/testserver_root/build-info/subdir'
        search_path = BuildInfo.get_search_path(dir_path)
        self.assertEquals(dir_path, search_path)

        file_path = dir_path + '/testfile.txt'
        search_path = BuildInfo.get_search_path(file_path)
        self.assertEquals(dir_path, search_path)

    def test_write_from_array(self):
        build_info = BuildInfo(self.buildinfo_file_path)
        file_path = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, file_path)
        file_path = os.path.join(file_path, 'BUILD-INFO.txt')
        BuildInfo.write_from_array(build_info.build_info_array, file_path)
        build_info_test = BuildInfo(file_path)
        self.assertEquals(build_info_test.build_info_array,
                          build_info.build_info_array)


class FileNameMatchingTests(unittest.TestCase):
    def test_buildinfo_simple_filename(self):
        with temporary_directory() as serve_root:
            sample_file = serve_root.make_file("MD5SUM", data="blah")
            serve_root.make_file(
                "BUILD-INFO.txt",
                data=(
                    "Format-Version: 2.0\n\n"
                    "Files-Pattern: MD5SUM\n"
                    "License-Type: open\n"
                ))
            build_info = BuildInfo(sample_file)
            file_info = build_info.getInfoForFile()
            self.assertEqual('open', file_info[0]['license-type'])


if __name__ == '__main__':
    unittest.main()
