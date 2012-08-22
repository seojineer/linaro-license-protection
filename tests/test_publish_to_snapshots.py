#!/usr/bin/env python

import os
import sys
import shutil
import tempfile
import argparse
from StringIO import StringIO
from testtools import TestCase
from scripts.publish_to_snapshots import (
    PublisherArgumentException,
    SnapshotsPublisher,
    setup_parser,
    )


class TestSnapshotsPublisher(TestCase):
    '''Tests for publishing files to the snapshots.l.o www area.'''

    uploads_path = "uploads/"
    target_path = "www/"
    orig_dir = os.getcwd()

    def setUp(self):
        self.parser = setup_parser()

        if not os.path.isdir(self.uploads_path):
            os.mkdir(self.uploads_path)

        if not os.path.isdir(self.target_path):
            os.mkdir(self.target_path)
        super(TestSnapshotsPublisher, self).setUp()

    def tearDown(self):
        os.chdir(self.orig_dir)
        if os.path.isdir(self.uploads_path):
            shutil.rmtree(self.uploads_path)

        if os.path.isdir(self.target_path):
            shutil.rmtree(self.target_path)
        super(TestSnapshotsPublisher, self).tearDown()

    def test_validate_args_valid_job_values(self):
        self.publisher = SnapshotsPublisher()
        param = self.parser.parse_args(
            ['-t', 'android', '-j', 'dummy_job_name', '-n', '1'])
        self.publisher.validate_args(param)
        param = self.parser.parse_args(
            ['-t', 'kernel-hwpack', '-j', 'dummy_job_name', '-n', '1'])
        self.publisher.validate_args(param)

        param = self.parser.parse_args(
            ['-t', 'prebuilt', '-j', 'dummy_job_name', '-n', '1'])
        self.publisher.validate_args(param)
        param = self.parser.parse_args(
            ['-t', 'ubuntu-hwpacks', '-j', 'dummy_job_name', '-n', '1'])
        self.publisher.validate_args(param)
        param = self.parser.parse_args(
            ['-t', 'ubuntu-images', '-j', 'dummy_job_name', '-n', '1'])
        self.publisher.validate_args(param)
        param = self.parser.parse_args(
            ['-t', 'ubuntu-restricted', '-j', 'dummy_job_name', '-n', '1'])
        self.publisher.validate_args(param)
        param = self.parser.parse_args(
            ['-t', 'ubuntu-sysroots', '-j', 'dummy_job_name', '-n', '1'])
        self.publisher.validate_args(param)
        param = self.parser.parse_args(
            ['-t', 'openembedded', '-j', 'dummy_job_name', '-n', '1'])
        self.publisher.validate_args(param)
        param = self.parser.parse_args(
            ['-t', 'binaries', '-j', 'dummy_job_name', '-n', '1'])
        self.publisher.validate_args(param)

    def test_validate_args_invalid_job_type(self):
        self.publisher = SnapshotsPublisher()
        param = self.parser.parse_args(
            ['-t', 'invalid_job_type', '-j', 'dummy_job_name', '-n', '1'])
        self.assertRaisesRegexp(
            PublisherArgumentException, "Invalid job type",
            self.publisher.validate_args, param)

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
        self.publisher = SnapshotsPublisher()
        param = self.parser.parse_args(
            ['-t', None, '-j', None, '-n', 0])
        self.assertRaisesRegexp(
            PublisherArgumentException,
            "You must specify job-type, job-name and build-num",
            self.publisher.validate_args, param)

    def test_validate_paths_invalid_uploads_path(self):
        orig_stdout = sys.stdout
        stdout = sys.stdout = StringIO()
        self.publisher = SnapshotsPublisher()
        param = self.parser.parse_args(
            ['-t', 'android', '-j', 'dummy_job_name', '-n', '1'])

        self.publisher.validate_args(param)
        uploads_path = "./dummy_uploads_path"
        try:
            self.publisher.validate_paths(param, uploads_path,
                                          self.target_path)
        finally:
            sys.stdout = orig_stdout

        stdout.seek(0)
        self.assertIn("Missing build path", stdout.read())

    def test_validate_paths_invalid_target_path(self):
        orig_stdout = sys.stdout
        stdout = sys.stdout = StringIO()
        self.publisher = SnapshotsPublisher()
        param = self.parser.parse_args(
            ['-t', 'android', '-j', 'dummy_job_name', '-n', '1'])

        self.publisher.validate_args(param)
        build_path = os.path.join(
            self.uploads_path, param.job_type, param.job_name,
            str(param.build_num))
        os.makedirs(build_path)
        self.target_path = "./dummy_target_path"
        try:
            self.publisher.validate_paths(param, self.uploads_path,
                                          self.target_path)
        finally:
            sys.stdout = orig_stdout

        stdout.seek(0)
        self.assertIn("Missing target path", stdout.read())

    def test_is_accepted_for_staging_EULA_txt(self):
        self.assertTrue(
            SnapshotsPublisher.is_accepted_for_staging("EULA.txt"))
        self.assertTrue(
            SnapshotsPublisher.is_accepted_for_staging("/path/to/EULA.txt"))
        # Full filename should be EULA.txt and nothing should be added to it.
        self.assertFalse(
            SnapshotsPublisher.is_accepted_for_staging(
                "/path/to/EULA.txt.something"))

    def test_is_accepted_for_staging_OPEN_EULA_txt(self):
        self.assertTrue(
            SnapshotsPublisher.is_accepted_for_staging(
                "OPEN-EULA.txt"))
        self.assertTrue(
            SnapshotsPublisher.is_accepted_for_staging(
                "/path/to/OPEN-EULA.txt"))
    def test_is_accepted_for_staging_per_file_EULA(self):
        self.assertTrue(
            SnapshotsPublisher.is_accepted_for_staging(
                "something.tar.gz.EULA.txt.ste"))
        self.assertTrue(
            SnapshotsPublisher.is_accepted_for_staging(
                "/path/to/something.tar.gz.EULA.txt.ste"))
        # We must have a "theme" for per-file license files in the
        # EULA-model.
        self.assertFalse(
            SnapshotsPublisher.is_accepted_for_staging(
                "something.tar.gz.EULA.txt"))

    def test_is_accepted_for_staging_build_info(self):
        self.assertTrue(
            SnapshotsPublisher.is_accepted_for_staging(
                "BUILD-INFO.txt"))
        self.assertTrue(
            SnapshotsPublisher.is_accepted_for_staging(
                "/path/to/BUILD-INFO.txt"))

    def test_sanitize_file_assert_on_accepted_files(self):
        # Since sanitize_file explicitely sanitizes a file,
        # one needs to ensure outside the function that it's
        # not being called on one of accepted file names.
        filename = '/path/to/EULA.txt'
        self.assertTrue(SnapshotsPublisher.is_accepted_for_staging(filename))
        self.assertRaises(
            AssertionError, SnapshotsPublisher.sanitize_file, filename)

    def make_temporary_file(self, data):
        """Creates a temporary file and fills it with data.

        Returns the full file path of the new temporary file.
        """
        tmp_file_handle, tmp_filename = tempfile.mkstemp()
        tmp_file = os.fdopen(tmp_file_handle, "w")
        tmp_file.write(data)
        tmp_file.close()
        return tmp_filename

    def test_sanitize_file_loses_original_contents(self):
        original_text = "Some garbage" * 100
        protected_filename = self.make_temporary_file(original_text)

        SnapshotsPublisher.sanitize_file(protected_filename)
        new_contents = open(protected_filename).read()
        self.assertNotEqual(original_text, new_contents)
        # Clean-up.
        os.remove(protected_filename)

    def test_sanitize_file_basename_as_contents(self):
        # It's useful to have an easy way to distinguish files by the content
        # as well, so we put the basename (filename without a path) in.
        protected_filename = self.make_temporary_file("Some contents")
        SnapshotsPublisher.sanitize_file(protected_filename)
        new_contents = open(protected_filename).read()
        # Incidentally, the contents are actually the file base name.
        self.assertEqual(os.path.basename(protected_filename), new_contents)
        # Clean-up.
        os.remove(protected_filename)

    def test_move_artifacts_kernel_successful_move(self):
        orig_stdout = sys.stdout
        stdout = sys.stdout = StringIO()
        self.publisher = SnapshotsPublisher()
        param = self.parser.parse_args(
            ['-t', 'kernel-hwpack', '-j', 'dummy_job_name', '-n', '1'])
        self.publisher.validate_args(param)
        build_path = os.path.join(
            self.uploads_path, param.job_type, param.job_name,
            str(param.build_num))
        os.makedirs(build_path)
        tempfile.mkstemp(dir=build_path)
        try:
            uploads_dir_path, target_dir_path = self.publisher.validate_paths(
                param, self.uploads_path, self.target_path)
            uploads_dir_path = os.path.join(self.orig_dir, uploads_dir_path)
            target_dir_path = os.path.join(self.orig_dir, target_dir_path)
            self.publisher.move_artifacts(param, uploads_dir_path,
                                          target_dir_path)
        finally:
            sys.stdout = orig_stdout
            pass

        stdout.seek(0)
        self.assertIn("Moved the files from", stdout.read())

    def test_move_artifacts_android_successful_move(self):
        orig_stdout = sys.stdout
        stdout = sys.stdout = StringIO()
        self.publisher = SnapshotsPublisher()
        param = self.parser.parse_args(
            ['-t', 'android', '-j', 'dummy_job_name', '-n', '1'])
        self.publisher.validate_args(param)
        build_dir = '/'.join(
            [param.job_type, param.job_name, str(param.build_num)])
        build_path = os.path.join(self.uploads_path, build_dir)
        os.makedirs(build_path)
        tempfile.mkstemp(dir=build_path)
        try:
            uploads_dir_path, target_dir_path = self.publisher.validate_paths(
                param, self.uploads_path, self.target_path)
            uploads_dir_path = os.path.join(self.orig_dir, uploads_dir_path)
            target_dir_path = os.path.join(self.orig_dir, target_dir_path)
            self.publisher.move_artifacts(param, uploads_dir_path,
                                          target_dir_path)
        finally:
            sys.stdout = orig_stdout
            pass

        stdout.seek(0)
        self.assertIn("Moved the files from", stdout.read())

    def test_move_artifacts_prebuilt_successful_move(self):
        orig_stdout = sys.stdout
        stdout = sys.stdout = StringIO()
        self.publisher = SnapshotsPublisher()
        param = self.parser.parse_args(
            ['-t', 'prebuilt', '-j', 'dummy_job_name', '-n', '1'])
        self.publisher.validate_args(param)
        build_dir = '/'.join([param.job_name, str(param.build_num)])
        build_path = os.path.join(self.uploads_path, build_dir, 'oneiric')
        os.makedirs(build_path)
        tempfile.mkstemp(dir=build_path)
        try:
            uploads_dir_path, target_dir_path = self.publisher.validate_paths(
                param, self.uploads_path, self.target_path)
            uploads_dir_path = os.path.join(self.orig_dir, uploads_dir_path)
            target_dir_path = os.path.join(self.orig_dir, target_dir_path)
            self.publisher.move_artifacts(param, uploads_dir_path,
                                          target_dir_path)
        finally:
            sys.stdout = orig_stdout
            pass

        stdout.seek(0)
        self.assertIn("Moved the files from", stdout.read())

    def test_move_artifacts_ubuntu_hwpacks_successful_move(self):
        orig_stdout = sys.stdout
        stdout = sys.stdout = StringIO()
        self.publisher = SnapshotsPublisher()
        param = self.parser.parse_args(['-t', 'ubuntu-hwpacks', '-j',
                                        'precise-armhf-lt-panda', '-n', '1'])
        self.publisher.validate_args(param)
        build_dir = '/'.join([param.job_name, str(param.build_num)])
        build_path = os.path.join(self.uploads_path, build_dir)
        os.makedirs(build_path)
        tempfile.mkstemp(dir=build_path)
        try:
            uploads_dir_path, target_dir_path = self.publisher.validate_paths(
                param, self.uploads_path, self.target_path)
            uploads_dir_path = os.path.join(self.orig_dir, uploads_dir_path)
            target_dir_path = os.path.join(self.orig_dir, target_dir_path)
            self.publisher.move_artifacts(param, uploads_dir_path,
                                          target_dir_path)
        finally:
            sys.stdout = orig_stdout
            pass

        stdout.seek(0)
        self.assertIn("Moved the files from", stdout.read())

    def test_move_artifacts_ubuntu_images_successful_move(self):
        orig_stdout = sys.stdout
        stdout = sys.stdout = StringIO()
        self.publisher = SnapshotsPublisher()
        param = self.parser.parse_args(
            ['-t', 'ubuntu-images', '-j', 'precise-armhf-ubuntu-desktop',
             '-n', '1'])
        self.publisher.validate_args(param)
        build_dir = '/'.join([param.job_name, str(param.build_num)])
        build_path = os.path.join(self.uploads_path, build_dir)
        os.makedirs(build_path)
        tempfile.mkstemp(dir=build_path)
        try:
            uploads_dir_path, target_dir_path = self.publisher.validate_paths(
                param, self.uploads_path, self.target_path)
            uploads_dir_path = os.path.join(self.orig_dir, uploads_dir_path)
            target_dir_path = os.path.join(self.orig_dir, target_dir_path)
            self.publisher.move_artifacts(param, uploads_dir_path,
                                          target_dir_path)
        finally:
            sys.stdout = orig_stdout
            pass

        stdout.seek(0)
        self.assertIn("Moved the files from", stdout.read())

    def test_move_artifacts_ubuntu_restricted_successful_move(self):
        orig_stdout = sys.stdout
        stdout = sys.stdout = StringIO()
        self.publisher = SnapshotsPublisher()
        param = self.parser.parse_args(
            ['-t', 'ubuntu-restricted', '-j',
             'precise-armhf-integrated-big.little-fastmodels', '-n', '1'])
        self.publisher.validate_args(param)
        build_dir = '/'.join([param.job_name, str(param.build_num)])
        build_path = os.path.join(self.uploads_path, build_dir)
        os.makedirs(build_path)
        tempfile.mkstemp(dir=build_path)
        try:
            uploads_dir_path, target_dir_path = self.publisher.validate_paths(
                param, self.uploads_path, self.target_path)
            uploads_dir_path = os.path.join(self.orig_dir, uploads_dir_path)
            target_dir_path = os.path.join(self.orig_dir, target_dir_path)
            self.publisher.move_artifacts(param, uploads_dir_path,
                                          target_dir_path)
        finally:
            sys.stdout = orig_stdout
            pass

        stdout.seek(0)
        self.assertIn("Moved the files from", stdout.read())

    def test_move_artifacts_ubuntu_sysroots_successful_move(self):
        orig_stdout = sys.stdout
        stdout = sys.stdout = StringIO()
        self.publisher = SnapshotsPublisher()
        param = self.parser.parse_args(
            ['-t', 'ubuntu-sysroots', '-j',
             'precise-armhf-ubuntu-desktop-dev', '-n', '1'])
        self.publisher.validate_args(param)
        build_dir = '/'.join([param.job_name, str(param.build_num)])
        build_path = os.path.join(self.uploads_path, build_dir)
        os.makedirs(build_path)
        tempfile.mkstemp(dir=build_path)
        try:
            uploads_dir_path, target_dir_path = self.publisher.validate_paths(
                param, self.uploads_path, self.target_path)
            uploads_dir_path = os.path.join(self.orig_dir, uploads_dir_path)
            target_dir_path = os.path.join(self.orig_dir, target_dir_path)
            self.publisher.move_artifacts(param, uploads_dir_path,
                                          target_dir_path)
        finally:
            sys.stdout = orig_stdout
            pass

        stdout.seek(0)
        self.assertIn("Moved the files from", stdout.read())

    def test_move_artifacts_openembedded_successful_move(self):
        orig_stdout = sys.stdout
        stdout = sys.stdout = StringIO()
        self.publisher = SnapshotsPublisher()
        param = self.parser.parse_args(['-t', 'openembedded',
                                        '-j', 'sources',
                                        '-n', '1'])
        self.publisher.validate_args(param)
        build_path = os.path.join(self.uploads_path,
                                  param.job_type,
                                  param.job_name)
        os.makedirs(build_path)
        tempfile.mkstemp(dir=build_path)
        try:
            uploads_dir_path, target_dir_path = self.publisher.validate_paths(
                param, self.uploads_path, self.target_path)
            uploads_dir_path = os.path.join(self.orig_dir, uploads_dir_path)
            target_dir_path = os.path.join(self.orig_dir, target_dir_path)
            self.publisher.move_artifacts(param, uploads_dir_path,
                target_dir_path)
        finally:
            sys.stdout = orig_stdout
            pass

        stdout.seek(0)
        self.assertIn("Moved the files from", stdout.read())

    def test_move_artifacts_binaries_successful_move(self):
        orig_stdout = sys.stdout
        stdout = sys.stdout = StringIO()
        self.publisher = SnapshotsPublisher()
        param = self.parser.parse_args(['-t', 'binaries', '-j',
                                        'snowball-binary-update', '-n', '1'])
        self.publisher.validate_args(param)
        build_path = os.path.join(self.uploads_path,
                                  param.job_name,
                                  str(param.build_num))
        os.makedirs(build_path)
        tempfile.mkstemp(dir=build_path)
        ts_file = os.path.join(build_path, 'TIMESTAMP')
        f = open(ts_file, "w")
        f.write('20120416')
        f.close()
        try:
            uploads_dir_path, target_dir_path = self.publisher.validate_paths(
                param, self.uploads_path, self.target_path)
            uploads_dir_path = os.path.join(self.orig_dir, uploads_dir_path)
            target_dir_path = os.path.join(self.orig_dir, target_dir_path)
            self.publisher.move_artifacts(param, uploads_dir_path,
                                          target_dir_path)
        finally:
            sys.stdout = orig_stdout
            pass

        stdout.seek(0)
        self.assertIn("Moved the files from", stdout.read())

    def test_move_artifacts_android_successful_move2(self):
        orig_stdout = sys.stdout
        stdout = sys.stdout = StringIO()
        self.publisher = SnapshotsPublisher()
        param = self.parser.parse_args(
            ['-t', 'android', '-j', 'dummy_job_name', '-n', '1'])
        self.publisher.validate_args(param)
        build_dir = '/'.join(
            [param.job_type, param.job_name, str(param.build_num)])
        build_path = os.path.join(self.uploads_path, build_dir)
        os.makedirs(build_path)
        tempfile.mkstemp(dir=build_path)
        try:
            uploads_dir_path, target_dir_path = self.publisher.validate_paths(
                param, self.uploads_path, self.target_path)
            uploads_dir_path = os.path.join(self.orig_dir, uploads_dir_path)
            target_dir_path = os.path.join(self.orig_dir, target_dir_path)
            self.publisher.move_artifacts(param, uploads_dir_path,
                                          target_dir_path)
        finally:
            sys.stdout = orig_stdout
            pass

        stdout.seek(0)
        self.assertIn("Moved the files from", stdout.read())

    def test_create_symlink(self):
        orig_stdout = sys.stdout
        stdout = sys.stdout = StringIO()
        self.publisher = SnapshotsPublisher()
        param = self.parser.parse_args(
            ['-t', 'android', '-j', 'dummy_job_name', '-n', '1'])
        self.publisher.validate_args(param)
        build_dir = '/'.join(
            [param.job_type, param.job_name, str(param.build_num)])
        build_path = os.path.join(self.uploads_path, build_dir)
        os.makedirs(build_path)
        tempfile.mkstemp(dir=build_path)
        try:
            uploads_dir_path, target_dir_path = self.publisher.validate_paths(
                param, self.uploads_path, self.target_path)
            uploads_dir_path = os.path.join(self.orig_dir, uploads_dir_path)
            target_dir_path = os.path.join(self.orig_dir, target_dir_path)
            self.publisher.move_artifacts(param, uploads_dir_path,
                                          target_dir_path)
        finally:
            sys.stdout = orig_stdout
            pass

        stdout.seek(0)
        msg = "The latest build is now linked to  " + target_dir_path
        self.assertIn(msg, stdout.read())

    def test_create_manifest_file_option(self):
        orig_stdout = sys.stdout
        stdout = sys.stdout = StringIO()
        self.publisher = SnapshotsPublisher()
        param = self.parser.parse_args(
            ['-t', 'android', '-j', 'dummy_job_name', '-n', '1', '-m'])
        self.publisher.validate_args(param)
        build_dir = '/'.join(
            [param.job_type, param.job_name, str(param.build_num)])
        build_path = os.path.join(self.uploads_path, build_dir)
        os.makedirs(build_path)
        tempfile.mkstemp(dir=build_path)
        lines = []
        try:
            uploads_dir_path, target_dir_path = self.publisher.validate_paths(
                param, self.uploads_path, self.target_path)
            uploads_dir_path = os.path.join(self.orig_dir, uploads_dir_path)
            target_dir_path = os.path.join(self.orig_dir, target_dir_path)
            os.chdir(uploads_dir_path)
            for path, subdirs, files in os.walk("."):
                for name in files:
                    lines.append(
                        os.path.join(path, name).split("./")[1] + "\n")
            os.chdir(self.orig_dir)
            self.publisher.move_artifacts(param, uploads_dir_path,
                                          target_dir_path)

            manifest_file = os.path.join(target_dir_path, "MANIFEST")
            dest = open(manifest_file, "r").read()

            if len(lines) != 0:
                tempfiles = tempfile.mkstemp(dir=target_dir_path)
                fd = open(tempfiles[1], "w+")
                for line in lines:
                    fd.write(line)
                fd.close()
                orig = open(tempfiles[1], "r").read()

        except:
            pass

        finally:
            sys.stdout = orig_stdout

        stdout.seek(0)
        res_output = stdout.read()
        self.assertIn("Moved the files from", res_output)
        msg = "Manifest file " + manifest_file + " generated"
        self.assertIn(msg, res_output)
        self.assertTrue(orig == dest)
