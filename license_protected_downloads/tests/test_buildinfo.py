__author__ = 'dooferlad'

import os
import shutil
import tempfile
import unittest

from license_protected_downloads.buildinfo import (
    BuildInfo,
    IncorrectDataFormatException,
)
from license_protected_downloads.tests.helpers import temporary_directory

THIS_DIRECTORY = os.path.dirname(os.path.abspath(__file__))


class BuildInfoTests(unittest.TestCase):
    def setUp(self):
        self.buildinfo_file_path = os.path.join(THIS_DIRECTORY,
                                                "BUILD-INFO.txt")

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

    def test_apply_to_file(self):
        build_info = BuildInfo(self.buildinfo_file_path)

        self.assertIn("Files-Pattern: *.txt", build_info.lines)

    def test_getFormatVersion(self):
        build_info = BuildInfo(self.buildinfo_file_path)

        self.assertEqual("0.5", build_info.getFormatVersion())

    def test_get_emptyField(self):
        value = "notempty"
        build_info = BuildInfo(self.buildinfo_file_path)
        for pair in build_info.file_info_array:
            if "auth-groups" in pair:
                value = pair["auth-groups"]

        self.assertFalse(value)

    def test_get(self):
        value = None
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

        self.assertDictEqual({"build-name": "value"},
                             build_info.parseLine(line))

    def test_parseLine_trims(self):
        line = "Build-Name: value"
        build_info = BuildInfo(self.buildinfo_file_path)

        self.assertDictEqual({"build-name": "value"},
                             build_info.parseLine(line))

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
        data = ["Format-Version: 2.0",
                "Files-Pattern: *.txt",
                "Build-Name: weehee",
                "Files-Pattern: *.tgz",
                "Build-Name: woohoo"]
        build_info.parseData(data)

        expected = [{
            'format-version': '2.0',
            '*.txt': [{'build-name': 'weehee'}],
            '*.tgz': [{'build-name': 'woohoo'}]
        }]
        self.assertEquals(expected, build_info.build_info_array)

    def test_parseData_block_multiple_patterns(self):
        build_info = BuildInfo(self.buildinfo_file_path)
        build_info.build_info_array = [{}]
        data = ["Format-Version: 2.0",
                "Files-Pattern: *.txt,*.tgz",
                "Build-Name: weehee"]
        build_info.parseData(data)

        expected = [{
            'format-version': '2.0',
            '*.txt': [{'build-name': 'weehee'}],
            '*.tgz': [{'build-name': 'weehee'}]
        }]
        self.assertEquals(expected, build_info.build_info_array)

    def test_parseContinuation_no_continuation(self):
        build_info = BuildInfo(self.buildinfo_file_path)
        build_info.line_no = 0

        self.assertEquals("", build_info.parseContinuation(["no-space"]))

    def test_parseContinuation_indexed(self):
        build_info = BuildInfo(self.buildinfo_file_path)
        build_info.line_no = 0

        self.assertEquals("",
                          build_info.parseContinuation(["no-space", " space"]))

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

        self.assertEqual(
            values,
            [{"format-version": "2.0", "license-text": "line1\nline2"}])

    def test_parseData_extra_fields(self):
        build_info = BuildInfo(self.buildinfo_file_path)
        build_info.build_info_array = [{}]
        data = ["Format-Version: 2.0",
                "Files-Pattern: *.txt",
                "Build-Name: woohoo"]
        build_info.parseData(data)

        self.assertEqual(
            build_info.build_info_array,
            [{"format-version": "2.0", '*.txt': [{'build-name': 'woohoo'}]}])

    def test_parseData_format_version(self):
        build_info = BuildInfo(self.buildinfo_file_path)
        build_info.build_info_array = [{}]
        data = ["Format-Version: 2.0"]
        build_info.parseData(data)

        self.assertEqual(
            build_info.build_info_array, [{"format-version": "2.0"}])

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

    def test_remove_false_positives_real(self):
        build_info = BuildInfo(self.buildinfo_file_path)
        build_info.build_info_array = [{}]
        build_info.file_info_array = [{}]
        data = ["Format-Version: 2.0",
                "Files-Pattern: *.txt",
                "License-Type: protected",
                "Files-Pattern: *.txt",
                "License-Type: open"]
        build_info.parseData(data)
        build_info.file_info_array = build_info.getInfoForFile()
        build_info.remove_false_positives()

        self.assertEquals(
            build_info.file_info_array, [{'license-type': 'protected'}])

    def test_remove_false_positives_none(self):
        build_info = BuildInfo(self.buildinfo_file_path)
        build_info.build_info_array = [{}]
        build_info.file_info_array = [{}]
        data = ["Format-Version: 2.0",
                "Files-Pattern: *.txt",
                "License-Type: protected",
                "Files-Pattern: *.txt",
                "License-Type: protected"]
        build_info.parseData(data)
        build_info.file_info_array = build_info.getInfoForFile()
        build_info.remove_false_positives()

        self.assertEquals(
            build_info.file_info_array,
            [{'license-type': 'protected'}, {'license-type': 'protected'}])

    def test_get_search_path(self):
        dir_path = THIS_DIRECTORY + '/testserver_root/build-info/subdir'
        search_path = BuildInfo.get_search_path(dir_path)
        self.assertEquals(dir_path, search_path)

        file_path = dir_path + '/testfile.txt'
        search_path = BuildInfo.get_search_path(file_path)
        self.assertEquals(dir_path, search_path)

    def test_getInfoForFile_no_block_for_file(self):
        file_path = os.path.abspath(__file__)
        build_info = BuildInfo(self.buildinfo_file_path)
        build_info.full_file_name = file_path
        build_info.build_info_array = [{}]
        build_info.file_info_array = [{}]
        data = ["Format-Version: 2.0",
                "Files-Pattern: *.txt",
                "License-Type: protected"]
        build_info.parseData(data)
        build_info.file_info_array = build_info.getInfoForFile()

        self.assertEquals(build_info.file_info_array, [{}])

    def test_getInfoForFile(self):
        file_path = os.path.abspath(__file__)
        build_info = BuildInfo(self.buildinfo_file_path)
        build_info.full_file_name = file_path
        build_info.build_info_array = [{}]
        build_info.file_info_array = [{}]
        data = ["Format-Version: 2.0",
                "Files-Pattern: *.py*",
                "License-Type: protected"]
        build_info.parseData(data)
        build_info.file_info_array = build_info.getInfoForFile()

        self.assertEquals(build_info.file_info_array,
                          [{'license-type': 'protected'}])

    def test_remove_false_positives_no_blocks_in_array(self):
        file_path = os.path.abspath(__file__)
        build_info = BuildInfo(self.buildinfo_file_path)
        build_info.full_file_name = file_path
        build_info.build_info_array = [{}]
        build_info.file_info_array = [{}]
        data = ["Format-Version: 2.0",
                "Files-Pattern: *.txt",
                "License-Type: protected"]
        build_info.parseData(data)
        build_info.file_info_array = build_info.getInfoForFile()
        build_info.remove_false_positives()

        self.assertEquals(build_info.file_info_array, [{}])

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
