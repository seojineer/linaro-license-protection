import unittest
import tests.test_click_through_license


def test_suite():
    module_names = [
        'tests.test_click_through_license.TestLicense',
        'tests.test_publish_to_snapshots.TestSnapshotsPublisher',
        ]
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromNames(module_names)
    return suite
