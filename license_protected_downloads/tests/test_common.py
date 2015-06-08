__author__ = 'dooferlad'

import unittest

from license_protected_downloads import common


class CommonTests(unittest.TestCase):
    def test_sizeof_fmt(self):
        self.assertEqual(common._sizeof_fmt(1), '1')
        self.assertEqual(common._sizeof_fmt(1234), '1.2K')
        self.assertEqual(common._sizeof_fmt(1234567), '1.2M')
        self.assertEqual(common._sizeof_fmt(1234567899), '1.1G')
        self.assertEqual(common._sizeof_fmt(1234567899999), '1.1T')

    def test_sort_artifacts(self):
        patterns = [
            (['b', 'a', 'latest', 'c'], ['latest', 'a', 'b', 'c']),
            (['10', '1', '100', 'latest'], ['latest', '1', '10', '100']),
            (['10', 'foo', '100', 'latest'], ['latest', '10', '100', 'foo']),
        ]
        for files, expected in patterns:
            artifacts = [common.Artifact('', x, True, '') for x in files]
            artifacts.sort(common._sort_artifacts)
            self.assertEqual(expected, [x.file_name for x in artifacts])

if __name__ == '__main__':
    unittest.main()
