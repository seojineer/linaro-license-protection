_author__ = 'stevanr'

import os
import unittest
from license_protected_downloads.splice_build_infos import SpliceBuildInfos

THIS_DIRECTORY = os.path.dirname(os.path.abspath(__file__))


class SpliceBuildInfosTests(unittest.TestCase):
    def setUp(self):
        dir_path1 = THIS_DIRECTORY + \
          '/testserver_root/build-info/splice-build-info/build-info-open'
        dir_path2 = THIS_DIRECTORY + \
          '/testserver_root/build-info/splice-build-info/build-info-protected'
        self.splice_build_infos = SpliceBuildInfos([dir_path1, dir_path2])

    def test_merge_duplicates(self):
        build_info_dict = {
            'test-protected.txt':
            [{'license-type': 'protected',
              'build-name': 'landing-protected',
              'auth-groups': 'linaro'}],
            'test-protected-2.txt':
            [{'license-type': 'protected',
              'build-name': 'landing-protected',
              'auth-groups': 'linaro'}]}

        result = {'test-protected.txt, test-protected-2.txt':
                  [{'license-type': 'protected',
                    'build-name': 'landing-protected',
                    'auth-groups': 'linaro'}]}

        build_info_res = SpliceBuildInfos.merge_duplicates(build_info_dict)
        self.assertEquals(build_info_res, result)
