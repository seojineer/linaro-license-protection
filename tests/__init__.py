import os
import unittest

from tests.test_click_through_license import *
from tests.test_publish_to_snapshots import *


def test_suite():
    module_names = [
        'tests.test_click_through_license.TestLicense',
        'tests.test_publish_to_snapshots.TestSnapshotsPublisher',
        'tests.test_php_unit.PhpUnitTest',
        ]
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromNames(module_names)
    return suite
