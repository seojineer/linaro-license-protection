#!/usr/bin/env python

import os
import sys
import shutil
import tempfile
import argparse
from StringIO import StringIO
from testtools import TestCase
from scripts.publish_to_snapshots import SnapshotsPublisher

class TestSnapshotsPublisher(TestCase):
    '''Tests for publishing files to the snapshots.l.o www are.'''

    uploads_path = "./uploads/"
    target_path = "./www/"

    def setUp(self):
        self.parser =  argparse.ArgumentParser()
        self.parser.add_argument("-t", "--job-type", dest="job_type")
        self.parser.add_argument("-j", "--job-name", dest="job_name")
        self.parser.add_argument("-n", "--build-num", dest="build_num", type=int)
        if not os.path.isdir(self.uploads_path):
            os.mkdir(self.uploads_path)
        
        if not os.path.isdir(self.target_path):
            os.mkdir(self.target_path)
        super(TestSnapshotsPublisher, self).setUp()

    def tearDown(self):
        if os.path.isdir(self.uploads_path):
            shutil.rmtree(self.uploads_path)

        if os.path.isdir(self.target_path):
            shutil.rmtree(self.target_path)
        super(TestSnapshotsPublisher, self).tearDown()

    def test_validate_args_valid_job_values(self):
        self.publisher = SnapshotsPublisher()
        param = self.parser.parse_args(['-t', 'android', '-j', 'dummy_job_name', 
                                        '-n', '1'])
        self.publisher.validate_args(param)
        param = self.parser.parse_args(['-t', 'kernel-hwpack', '-j', 'dummy_job_name', 
                                        '-n', '1'])
        self.publisher.validate_args(param)

    def test_validate_args_invalid_job_type(self):
        orig_stderr = sys.stderr
        stderr = sys.stderr = StringIO()
        self.publisher = SnapshotsPublisher()
        param = self.parser.parse_args(['-t', 'invalid_job_type',  '-j', 'dummy_job_name', 
                                        '-n', '1'])
        try:
            self.publisher.validate_args(param)
        except SystemExit, err:
            self.assertEqual(err.code, 2, "Expected result")
        finally:
            sys.stderr = orig_stderr
        stderr.seek(0)
        self.assertIn("Invalid job type", stderr.read())


    def test_validate_args_run_invalid_argument(self):
        orig_stderr = sys.stderr
        stderr = sys.stderr = StringIO()
        self.publisher = SnapshotsPublisher()
        try:
            param = self.parser.parse_args(['-a'])
            self.publisher.validate_args(param)
        except SystemExit, err:
            self.assertEqual(err.code, 2, "Invalid argument passed")
        finally:
            sys.stderr = orig_stderr
        stderr.seek(0)
        self.assertIn("unrecognized arguments: -a\n", stderr.read())

    def test_validate_args_run_invalid_value(self):
        orig_stderr = sys.stderr
        stderr = sys.stderr = StringIO()
        self.publisher = SnapshotsPublisher()
        try:
            param = self.parser.parse_args(['-n', "N"])
            self.publisher.validate_args(param)
        except SystemExit, err:
            self.assertEqual(err.code, 2, "Invalid value passed")
        finally:
            sys.stderr = orig_stderr
        stderr.seek(0)
        self.assertIn("argument -n/--build-num: invalid int value: 'N'", 
                      stderr.read())

    def test_validate_args_run_none_values(self):
        orig_stderr = sys.stderr
        stderr = sys.stderr = StringIO()
        self.publisher = SnapshotsPublisher()
        try:
            param = self.parser.parse_args(['-t', None , '-j', None , '-n' , 0])
            self.publisher.validate_args(param)
        except SystemExit, err:
            self.assertEqual(err.code, 2, "None values are not acceptable")
        finally:
            sys.stderr = orig_stderr
        stderr.seek(0)
        self.assertIn("You must specify job-type, job-name and build-num", 
                      stderr.read())

    def test_validate_paths_invalid_uploads_path(self):
        orig_stdout = sys.stdout
        stdout = sys.stdout = StringIO()
        self.publisher = SnapshotsPublisher()
        param = self.parser.parse_args(['-t', 'android', '-j', 'dummy_job_name', 
                                        '-n', '1'])

        self.publisher.validate_args(param)
        self.uploads_path = "./dummy_uploads_path"
        try:
            self.publisher.validate_paths(param, self.uploads_path, self.target_path)
        finally:
            sys.stdout = orig_stdout
        stdout.seek(0)
        self.assertIn("Missing build path", stdout.read())

    def test_validate_paths_invalid_target_path(self):
        orig_stdout = sys.stdout
        stdout = sys.stdout = StringIO()
        self.publisher = SnapshotsPublisher()
        param = self.parser.parse_args(['-t', 'android', '-j', 'dummy_job_name', 
                                        '-n', '1'])

        self.publisher.validate_args(param)
        self.target_path = "./dummy_target_path"
        try:
            self.publisher.validate_paths(param, self.uploads_path, self.target_path)
        finally:
            sys.stdout = orig_stdout
        stdout.seek(0)
        self.assertIn("Missing target path", stdout.read())

    def test_move_artifacts_kernel_successful_move(self):
        orig_stdout = sys.stdout
        stdout = sys.stdout = StringIO()
        self.publisher = SnapshotsPublisher()
        param = self.parser.parse_args(['-t', 'kernel-hwpack', '-j', 'dummy_job_name', 
                                        '-n', '1'])
        self.publisher.validate_args(param)
        build_path = os.path.join(self.uploads_path, param.job_type, param.job_name,
                                  str(param.build_num))
        os.makedirs(build_path)
        tempfiles = tempfile.mkstemp(dir=build_path)
        try:
            uploads_dir_path, target_dir_path = self.publisher.validate_paths(param, 
                                                self.uploads_path, self.target_path)
            self.publisher.move_artifacts(param, uploads_dir_path, target_dir_path)
        finally:
            sys.stdout = orig_stdout
            pass
         
        stdout.seek(0)
        self.assertIn("Moved the files from", stdout.read())

    def test_move_artifacts_android_successful_move(self):
        orig_stdout = sys.stdout
        stdout = sys.stdout = StringIO()
        self.publisher = SnapshotsPublisher()
        param = self.parser.parse_args(['-t', 'android', '-j', 'dummy_job_name', 
                                        '-n', '1'])
        self.publisher.validate_args(param)
        build_dir = '/'.join([param.job_type, param.job_name, str(param.build_num)])
        build_path = os.path.join(self.uploads_path, build_dir)
        os.makedirs(build_path)
        tempfiles = tempfile.mkstemp(dir=build_path)
        try:
            uploads_dir_path, target_dir_path = self.publisher.validate_paths(param, 
                                                self.uploads_path, self.target_path)
            self.publisher.move_artifacts(param, uploads_dir_path, target_dir_path)
        finally:
            sys.stdout = orig_stdout
            pass
         
        stdout.seek(0)
        self.assertIn("Moved the files from", stdout.read())
