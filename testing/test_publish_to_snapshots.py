#!/usr/bin/env python

from testtools import TestCase
from testtools.matchers import Mismatch
from scripts.publish_to_snapshots import SnapshotsPublisher


class TestSnapshotsPublisher(TestCase):
    '''Tests for publishing files to the snapshots.l.o www are.'''

    def setUp(self):
        super(TestSnapshotsPublisher, self).setUp()

    def tearDown(self):
        super(TestSnapshotsPublisher, self).tearDown()

    def test_run(self):
        publisher = SnapshotsPublisher()
        publisher.run()

