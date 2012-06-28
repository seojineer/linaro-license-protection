import unittest


def test_suite():
    module_names = [
        'tests.test_publish_to_snapshots.TestSnapshotsPublisher',
        ]
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromNames(module_names)
    return suite
