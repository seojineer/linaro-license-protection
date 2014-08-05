#!/usr/bin/env python

import unittest

import version

import mock


class TestVersion(unittest.TestCase):
    '''ensure the version module behaves well.'''

    def setUp(self):
        super(TestVersion, self).setUp()
        m = mock.patch('subprocess.check_output')
        self.addCleanup(m.stop)
        self.subprocess = m.start()

    def test_no_tags(self):
        self.subprocess.return_value = 'fakehash ('
        self.assertEquals('fakehash', version._get_version())

    def test_short_tag(self):
        self.subprocess.return_value = 'fakehash  (HEAD, tag: 2014.07, refs'
        self.assertEquals('2014.07', version._get_version())

    def test_longer_tag(self):
        self.subprocess.return_value = 'fakehash  (HEAD, tag: 2014.07.02, refs'
        self.assertEquals('2014.07.02', version._get_version())

    def test_precise_tag(self):
        # older git versions on precise don't include "tag:" in the git-log
        self.subprocess.return_value = 'fakehash  (HEAD, 2014.07.2, origin'
        self.assertEquals('2014.07.2', version._get_version())

    def test_invalid_tag(self):
        self.subprocess.return_value = 'fakehash  (HEAD, tag: aaaa.bb, refs'
        self.assertEquals('fakehash', version._get_version())
