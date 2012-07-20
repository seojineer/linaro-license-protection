import unittest


def test_suite():
    loader = unittest.TestLoader()
    return loader.discover('tests', top_level_dir='tests')
