__author__ = 'dooferlad'

import os
import tempfile
import unittest

from license_protected_downloads.artifact import LocalArtifact
from license_protected_downloads.artifact.base import _sizeof_fmt, cached_prop
from license_protected_downloads.common import _sort_artifacts
from license_protected_downloads.tests.test_views import TESTSERVER_ROOT


class CommonTests(unittest.TestCase):
    def test_sizeof_fmt(self):
        self.assertEqual(_sizeof_fmt(1), '1')
        self.assertEqual(_sizeof_fmt(1234), '1.2K')
        self.assertEqual(_sizeof_fmt(1234567), '1.2M')
        self.assertEqual(_sizeof_fmt(1234567899), '1.1G')
        self.assertEqual(_sizeof_fmt(1234567899999), '1.1T')

    def test_sort_artifacts(self):
        patterns = [
            (['b', 'a', 'latest', 'c'], ['latest', 'a', 'b', 'c']),
            (['10', '1', '100', 'latest'], ['latest', '1', '10', '100']),
            (['10', 'foo', '100', 'latest'], ['latest', '10', '100', 'foo']),
        ]
        for files, expected in patterns:
            artifacts = [LocalArtifact(None, '', x, True, '')
                         for x in files]
            artifacts.sort(_sort_artifacts)
            self.assertEqual(expected, [x.file_name for x in artifacts])

    def test_cached_property(self):
        class Foo(object):
            def __init__(self):
                self.count = 0

            @cached_prop
            def bar(self):
                v = self.count
                self.count += 1
                return v

        f = Foo()
        self.assertEqual(0, f.bar)
        self.assertEqual(0, f.bar)


class ArtifactTests(unittest.TestCase):
    def setUp(self):
        self.artifact = LocalArtifact(
            None, '/', 'readme', False, TESTSERVER_ROOT)

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
        ret = self.artifact._process_include_tags(
            'Test <linaro:include file="README" /> html')
        self.assertEqual(ret, r"Test Included from README html")

    def test_replace_self_closing_tag1(self):
        ret = self.artifact._process_include_tags(
            'Test <linaro:include file="README"/> html')
        self.assertEqual(ret, r"Test Included from README html")

    def test_replace_with_closing_tag(self):
        ret = self.artifact._process_include_tags(
            'Test <linaro:include file="README">README is missing'
            '</linaro:include> html')
        self.assertEqual(ret, r"Test Included from README html")

    def test_replace_non_existent_file(self):
        ret = self.artifact._process_include_tags(
            'Test <linaro:include file="NON_EXISTENT_FILE" /> html')
        self.assertEqual(ret, r"Test  html")

    def test_replace_empty_file_property(self):
        ret = self.artifact._process_include_tags(
            'Test <linaro:include file="" /> html')
        self.assertEqual(ret, r"Test  html")

    def test_replace_parent_dir(self):
        ret = self.artifact._process_include_tags(
            'Test <linaro:include file="../README" /> html')
        self.assertEqual(ret, r"Test  html")

    def test_replace_subdir(self):
        ret = self.artifact._process_include_tags(
            'Test <linaro:include file="subdir/README" /> html')
        self.assertEqual(ret, r"Test  html")

    def test_replace_subdir_parent_dir(self):
        ret = self.artifact._process_include_tags(
            'Test <linaro:include file="subdir/../README" /> html')
        self.assertEqual(ret, r"Test Included from README html")

    def test_replace_full_path(self):
        tmp = self.make_temporary_file("Included from /tmp", root="/tmp")
        ret = self.artifact._process_include_tags(
            'Test <linaro:include file="/tmp/%s" /> html' % tmp)
        self.assertEqual(ret, r"Test  html")

    def test_replace_self_dir(self):
        ret = self.artifact._process_include_tags(
            'Test <linaro:include file="./README" /> html')
        self.assertEqual(ret, r"Test Included from README html")

    def test_replace_self_parent_dir(self):
        ret = self.artifact._process_include_tags(
            'Test <linaro:include file="./../README" /> html')
        self.assertEqual(ret, r"Test  html")

    def test_replace_symlink(self):
        ret = self.artifact._process_include_tags(
            'Test <linaro:include file="READMELINK" /> html')
        self.assertEqual(ret, r"Test  html")

if __name__ == '__main__':
    unittest.main()
