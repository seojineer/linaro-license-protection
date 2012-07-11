import os
import unittest
import doctest


def test_suite():
    suite = unittest.TestSuite()
    for filename in os.listdir("testplans/"):
        suite.addTest(doctest.DocFileSuite(
            'testplans/' + filename, module_relative=False,
            optionflags=doctest.ELLIPSIS)
            )
    return suite
