#!/usr/bin/env python

from testtools import TestCase
from testtools.matchers import Mismatch
from scripts.publish_to_snapshots import (
    InvalidParametersException,
    SnapshotsPublisher,
    )

class TestSnapshotsPublisher(TestCase):
    '''Tests for publishing files to the snapshots.l.o www are.'''

    def setUp(self):
        super(TestSnapshotsPublisher, self).setUp()

    def tearDown(self):
        super(TestSnapshotsPublisher, self).tearDown()

    def test_run_invalid_parameters(self):
        publisher = SnapshotsPublisher()
        # There have to be at least 3 arguments passed to the run method.
        self.assertRaises(InvalidParametersException,
                          publisher.run, None)
        self.assertRaises(InvalidParametersException,
                          publisher.run, [1, 2])

    def test_run_invalid_job_type(self):
        publisher = SnapshotsPublisher()
        self.assertRaises(InvalidParametersException,
                          publisher.run, ["foo", "build-name", "4"])

    def test_run_valid_job_types(self):
        publisher = SnapshotsPublisher()
        publisher.run(["android", "build-name", "4"])
        publisher.run(["kernel-hwpack", "build-name", "4"])

