import os
import unittest

def test_suite():
    module_names = [
        'license_protected_downloads.tests.test_buildinfo',
        ]
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromNames(module_names)
    return suite
