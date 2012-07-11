import unittest
import tests.test_click_through_license
import tests.test_publish_to_snapshots


def test_suite():
    modules = [
        tests.test_click_through_license,
        tests.test_publish_to_snapshots,
        ]
    loader = unittest.TestLoader()
    return loader.discover('tests', top_level_dir='tests')
