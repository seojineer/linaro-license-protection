import os
import unittest

from testing.test_click_through_license import *
from testing.test_publish_to_snapshots import *

def test_suite():
    module_names = [
        'testing.test_click_through_license.TestLicense',
        'testing.test_publish_to_snapshots.TestSnapshotsPublisher',
        'testing.test_php_unit.PhpUnitTest',
        ]
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromNames(module_names)
    return suite

