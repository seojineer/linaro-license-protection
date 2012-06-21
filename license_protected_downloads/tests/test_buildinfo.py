__author__ = 'dooferlad'

import unittest
from license_protected_downloads.buildinfo import BuildInfo

class BuildInfoTests(unittest.TestCase):
    def test_single_line_variables(self):
        build_info = BuildInfo()

        variables = ["Format-Version: 0.1",
                     "Files-Pattern: *snowball*",
                     "Build-Name: landing-snowball",
                     "Theme: ste",
                     "License-Type: protected"]

        expected_values = {}
        expected_values["Format-Version"] = "0.1"
        expected_values["Files-Pattern"] = "*snowball*"
        expected_values["Build-Name"] = "landing-snowball"
        expected_values["Theme"] = "ste"
        expected_values["License-Type"] = "protected"

        build_info.parse_buildinfo_lines(variables)

        self.assertDictEqual(build_info.data[0], expected_values)

    def test_multi_line_variables(self):
        build_info = BuildInfo()

        license = ["The Creative Commons copyright licenses and tools forge a",
         "balance inside the traditional \"all rights reserved\" setting that",
         "copyright law creates. Our tools give everyone from individual",
         "creators to large companies and institutions a simple, standarized",
         "way to grant copyright permissions to their creative work. The",
         "combination of our tools and our users is a vast and growing",
         "digital commons, a pool of content that can be copied,",
         "distributed, edited,remixed, and built upon, all within the",
         "boundaries of copyright law."]

        variables = ["License-Text: " + license[0]]
        variables += license[1:]
        expected_values = {}
        expected_values["License-Text"] = " ".join(license)

        build_info.parse_buildinfo_lines(variables)

        self.assertDictEqual(build_info.data[0], expected_values)

    def test_multiple_licenses(self):
        build_info = BuildInfo()

        variables = ["Format-Version: 0.1",
                     "Files-Pattern: *snowball*",
                     "Build-Name: landing-snowball",
                     "Files-Pattern: *foo*",
                     "Build-Name: landing-foo",]

        expected_values = [{}, {}]
        expected_values[0]["Format-Version"] = "0.1"
        expected_values[0]["Files-Pattern"] = "*snowball*"
        expected_values[0]["Build-Name"] = "landing-snowball"
        expected_values[1]["Files-Pattern"] = "*foo*"
        expected_values[1]["Build-Name"] = "landing-foo"

        build_info.parse_buildinfo_lines(variables)

        self.assertDictEqual(build_info.data[0], expected_values[0])
        self.assertDictEqual(build_info.data[1], expected_values[1])

if __name__ == '__main__':
    unittest.main()
