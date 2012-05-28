import os
import tempfile
import subprocess
import xml.etree.ElementTree

from testtools import TestCase
from testtools.matchers import Equals
from testtools.matchers import AllMatch

from tests.test_click_through_license import CommandNotFoundException


class BuildInfoTest(TestCase):
    '''Tests for executing the BuildInfo PHP Unit tests'''

    def setUp(self):
        super(BuildInfoTest, self).setUp()

        self.build_info_xml_path = tempfile.mkstemp()[1]
        rc = subprocess.Popen(['phpunit', '--log-junit',
                             self.build_info_xml_path, 'tests/BuildInfoTest'],
                stdout=open('/dev/null', 'w'),
                stderr=subprocess.STDOUT).wait()
        if rc == -1:
            raise CommandNotFoundException("phpunit command not found. Please "
                "install phpunit package and rerun tests.")
        self.build_info_xml_data = xml.etree.ElementTree.parse(self.build_info_xml_path)

    def tearDown(self):
        super(BuildInfoTest, self).tearDown()
        if os.path.exists(self.build_info_xml_path):
            os.unlink(self.build_info_xml_path)

    def test_run_buildinfo_tests(self):
        self.assertThat(
            [
            self.build_info_xml_data.getroot()[0].attrib['failures'],
            self.build_info_xml_data.getroot()[0].attrib['errors']
            ],
            AllMatch(Equals("0"))
        )
