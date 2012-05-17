import os
import tempfile
import subprocess
import xml.etree.ElementTree

from testtools import TestCase
from testtools.matchers import Equals
from testtools.matchers import AllMatch

from tests.test_click_through_license import CommandNotFoundException


class PhpUnitTest(TestCase):
    '''Tests for executing the PHP Unit tests'''

    def setUp(self):
        super(PhpUnitTest, self).setUp()
        self.xml_path = tempfile.mkstemp()[1]
        if subprocess.Popen(['phpunit', '--log-junit',
                             self.xml_path, 'tests/LicenseHelperTest'],
                stdout=open('/dev/null', 'w'),
                stderr=subprocess.STDOUT).wait():
            raise CommandNotFoundException("phpunit command not found. Please "
                "install phpunit package and rerun tests.")
        self.xml_data = xml.etree.ElementTree.parse(self.xml_path)

    def tearDown(self):
        super(PhpUnitTest, self).tearDown()
        if os.path.exists(self.xml_path):
            os.unlink(self.xml_path)

    def test_run_php_unit_tests(self):
        self.assertThat(
            [
            self.xml_data.getroot()[0].attrib['failures'],
            self.xml_data.getroot()[0].attrib['errors']
            ],
            AllMatch(Equals("0"))
        )
