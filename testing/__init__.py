import os
import unittest

def test_suite():
    module_names = [
        'testing.test_click_through_license',
        ]
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromNames(module_names)
    return suite

