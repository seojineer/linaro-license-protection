__author__ = 'dooferlad'

import os
import tempfile
import unittest
import shutil

from license_protected_downloads import common


class CommonTests(unittest.TestCase):
    def test_sizeof_fmt(self):
        self.assertEqual(common._sizeof_fmt(1), '1')
        self.assertEqual(common._sizeof_fmt(1234), '1.2K')
        self.assertEqual(common._sizeof_fmt(1234567), '1.2M')
        self.assertEqual(common._sizeof_fmt(1234567899), '1.1G')
        self.assertEqual(common._sizeof_fmt(1234567899999), '1.1T')

    def test_listdir(self):
        patterns = [
            (['b', 'a', 'latest', 'c'], ['latest', 'a', 'b', 'c']),
            (['10', '1', '100', 'latest'], ['latest', '1', '10', '100']),
            (['10', 'foo', '100', 'latest'], ['latest', '10', '100', 'foo']),
        ]
        for files, expected in patterns:
            path = tempfile.mkdtemp()
            self.addCleanup(shutil.rmtree, path)
            for file in files:
                with open(os.path.join(path, file), 'w') as f:
                    f.write(file)
            self.assertEqual(expected, common._listdir(path))

if __name__ == '__main__':
    unittest.main()
