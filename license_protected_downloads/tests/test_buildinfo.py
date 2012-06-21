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
        expected_values["format-version"] = "0.1"
        expected_values["files-pattern"] = "*snowball*"
        expected_values["build-name"] = "landing-snowball"
        expected_values["theme"] = "ste"
        expected_values["license-type"] = "protected"

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
        expected_values["license-text"] = " ".join(license)

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
        expected_values[0]["format-version"] = "0.1"
        expected_values[0]["files-pattern"] = "*snowball*"
        expected_values[0]["build-name"] = "landing-snowball"
        expected_values[1]["files-pattern"] = "*foo*"
        expected_values[1]["build-name"] = "landing-foo"

        build_info.parse_buildinfo_lines(variables)

        self.assertDictEqual(build_info.data[0], expected_values[0])
        self.assertDictEqual(build_info.data[1], expected_values[1])

if __name__ == '__main__':
    unittest.main()
