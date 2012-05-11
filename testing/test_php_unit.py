#!/usr/bin/env python

import os
import subprocess
import xml.etree.ElementTree as etree

from testtools import TestCase
from testtools.matchers import Equals

class PhpUnitTest(TestCase):
    '''Tests for executing the PHP Unit tests'''

    def setUp(self):
        super(PhpUnitTest, self).setUp()
        self.xml_path = "testing/php_unit_test_result.xml"
        if subprocess.Popen(['phpunit', '--log-junit',
                             self.xml_path, 'testing/LicenseHelperTest'],
                stdout=open('/dev/null', 'w'),
                stderr=subprocess.STDOUT).wait():
            raise CommandNotFoundException("phpunit command not found. Please "
                "install phpunit package and rerun tests.")
        self.xml_data = etree.parse(self.xml_path)

    def tearDown(self):
        super(PhpUnitTest, self).tearDown()
        if os.path.exists(self.xml_path):
            os.unlink(self.xml_path)

    def test_run_php_unit_tests(self):
        self.assertThat(self.xml_data.getroot()[0].attrib['failures'],
                        Equals("0"))
        self.assertThat(self.xml_data.getroot()[0].attrib['errors'],
                        Equals("0"))
