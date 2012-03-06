#!/usr/bin/env python

import argparse
from testtools import TestCase
from testtools.matchers import Mismatch
from scripts.publish_to_snapshots import (
    InvalidParametersException,
    SnapshotsPublisher,
    )


class TestSnapshotsPublisher(TestCase):
    '''Tests for publishing files to the snapshots.l.o www are.'''

    def setUp(self):
        self.parser =  argparse.ArgumentParser()
        self.parser.add_argument("-j", "--job_type", dest="job_type")
        self.parser.add_argument("-a", "--archive_info", dest="archive_info")
        self.parser.add_argument("-n", "--build_num", dest="build_num", type=int)
        super(TestSnapshotsPublisher, self).setUp()

    def tearDown(self):
        super(TestSnapshotsPublisher, self).tearDown()

    def test_valid_job_values(self):
        self.publisher = SnapshotsPublisher()
        param = self.parser.parse_args(['-j', 'android', '-a', 'fun', '-n', '4'])
        self.publisher.validate_args(param)
   #     param = self.parser.parse_args(['-j', 'kernel-hwpack', '-a', 'fun', '-n', '4'])
   #     self.publisher.validate_args(param)

    def test_invalid_job_values(self):
        self.publisher = SnapshotsPublisher()
        param = self.parser.parse_args(['-a', 'fun', '-j', 'invalid_job', '-n', '4'])
        try:
            self.assertRaises(InvalidParametersException,
                          self.publisher.validate_args, param)
        except SystemExit, err:
            print "DEBUG invalid job value"

    def test_run_None_values(self):
        self.publisher = SnapshotsPublisher()
        try:
            param = self.parser.parse_args(['-a', None , '-j', None, '-n', 0 ])
            self.publisher.validate_args(param)
        except SystemExit, err:
            self.assertEqual(err.code, 2, "Expected result")

    def test_run_invalid_option(self):
        self.publisher = SnapshotsPublisher()
        try:
            param = self.parser.parse_args(['-x'])
            self.publisher.validate_args(param)
        except SystemExit, err:
            print "DEBUG exception ArgumentParser", err
            self.assertEqual(err.code, 2, "Expected result")

    def test_run_invalid_type(self):
        self.publisher = SnapshotsPublisher()
        try:
            param = self.parser.parse_args(['-n', "N"])
            self.publisher.validate_args(param)
        except argparse.ArgumentTypeError, details:
            print "DEBUG exception argparse.ArgumentTypeError"

