import unittest


def test_suite():
    module_names = [
        'tests.test_click_through_license.TestLicense',
        'tests.test_publish_to_snapshots.TestSnapshotsPublisher',
        'tests.test_php_unit.PhpUnitTest',
        'tests.test_build_info.BuildInfoTest',
        ]
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromNames(module_names)
    return suite
