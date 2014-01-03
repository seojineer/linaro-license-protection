#!/usr/bin/env python
# Move artifacts from a temporary location to a permanent location on s.l.o

import argparse
import fnmatch
import os
import os.path
import shutil
import sys
import tempfile

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__),
                                 "../license_protected_downloads")))
from splice_build_infos import SpliceBuildInfos

uploads_path = '/srv/snapshots.linaro.org/uploads/'
target_path = '/srv/snapshots.linaro.org/www/'
staging_uploads_path = '/srv/staging.snapshots.linaro.org/uploads/'
staging_target_path = '/srv/staging.snapshots.linaro.org/www/'
PRODUCT_DIR = 'target/product'
PASS = 0
FAIL = 1
BUILDINFO = 'BUILD-INFO.txt'
acceptable_job_types = [
    'android',
    'prebuilt',
    'kernel-hwpack',
    'ubuntu-hwpacks',
    'ubuntu-images',
    'ubuntu-restricted',
    'ubuntu-sysroots',
    'openembedded',
    'binaries'
    ]
open_buildinfo_files = [
    'MANIFEST',
    'MD5SUMS',
    'HOWTO_*',
    'lava-job-info*'
    ]
open_buildinfo = '\nFiles-Pattern: %s\nLicense-Type: open\n'


def append_open_buildinfo(buildinfo_path, files=open_buildinfo_files):
    """Append BUILD-INFO.txt with open section for open_buildinfo_files"""
    if os.path.exists(os.path.join(buildinfo_path, BUILDINFO)):
        try:
            bifile = open(os.path.join(buildinfo_path, BUILDINFO), "a")
            try:
                bifile.write(open_buildinfo % ', '.join(files))
            finally:
                bifile.close()
        except IOError:
            print "Unable to write to BUILD-INFO.txt"
            pass


def setup_parser():
    """Set up the argument parser for publish_to_snapshots script."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-s", "--staging", dest="staging", default=False,
        action='store_true',
        help=("Perform sanitization on the file to not expose any"
              "potentially sensitive data.  Used for staging deployment."))
    parser.add_argument(
        "-t", "--job-type", dest="job_type",
        help="Specify the job type (Ex: android/kernel-hwpack)")
    parser.add_argument(
        "-j", "--job-name", dest="job_name",
        help=("Specify the job name which resulted the archive to "
              "be stored. Ex: ${JOB_NAME} should be specified for "
              "android/ubuntu-{hwpacks,images,sysroots}/binaries and for"
              "kernel-hwpack ${KERNEL_JOB_NAME}"))
    parser.add_argument(
            "-n", "--build-num", dest="build_num", type=int,
            help=("Specify the job build number for android/"
                  "ubuntu-{hwpacks,images,sysroots}/binaries"))
    parser.add_argument(
        "-m", "--manifest", dest="manifest",
        action='store_true',
        help="Optional parameter to generate MANIFEST file")
    return parser


class PublisherArgumentException(Exception):
    """There was a problem with one of the publisher arguments."""
    pass


class BuildInfoException(Exception):
    """BUILD-INFO.txt is absent."""

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class SnapshotsPublisher(object):

    # Files that need no sanitization even when publishing to staging.
    STAGING_ACCEPTABLE_FILES = [
        'BUILD-INFO.txt',
        'EULA.txt',
        'OPEN-EULA.txt',
        '*.EULA.txt.*',
        'README',
        'README.textile',
        'INSTALL',
        'HACKING',
        '*HOWTO_*.txt',
        ]

    def __init__(self, argument_parser=None):
        """Allow moving files around for publishing on snapshots.l.o."""
        self.argument_parser = argument_parser

    @classmethod
    def is_ok_for_staging(cls, filename):
        """Can filename be published on staging as is, or requires obfuscation?"""
        filename = os.path.basename(filename)
        for accepted_names in cls.STAGING_ACCEPTABLE_FILES:
            if fnmatch.fnmatch(filename, accepted_names):
                return True
        return False

    @classmethod
    def sanitize_file(cls, file_path):
        """This truncates the file and fills it with its own filename."""
        assert not cls.is_ok_for_staging(file_path)
        if not os.path.isdir(file_path):
            base_file_name = os.path.basename(file_path)
            protected_file = open(file_path, "w")
            # Nice property of this is that we are also saving on disk space
            # needed.
            protected_file.truncate()
            # To help distinguish files more easily when they are downloaded,
            # we write out the base file name as the contents.
            protected_file.write(base_file_name)
            protected_file.close()

    def validate_args(self, args):
        # Validate that all the required information
        # is passed on the command line
        if (args.job_type is None or args.job_name is None or
            args.build_num is None):
            raise PublisherArgumentException(
                "\nYou must specify job-type, job-name and build-num")

        if (args.job_type not in acceptable_job_types):
            raise PublisherArgumentException("Invalid job type")
        return True

    def jobname_to_target_subdir(self, args, jobname):
        ret_val = None
        if args.job_type == "android":
            ret_val = jobname.split("_")
        elif args.job_type == "kernel-hwpack":
            ret_val = jobname.split('_')[0].replace(".", "_")
        elif (args.job_type == "ubuntu-hwpacks" or
              args.job_type == "ubuntu-images" or
              args.job_type == "ubuntu-restricted" or
              args.job_type == "ubuntu-sysroots"):
            ret_val = jobname.split('-', 2)
        elif args.job_type == "openembedded":
            ret_val = jobname.split('-', 2)
        elif args.job_type == "prebuilt":
            # Return value must not be None when we want to ignore it.
            ret_val = ''
        elif args.job_type == "binaries":
            ret_val = jobname.split('-', 2)
        return ret_val

    def validate_paths(self, args, uploads_path, target_path):
        build_dir_path = target_dir_path = None
        ret_val = self.jobname_to_target_subdir(args, args.job_name)
        if ret_val is not None:
            if args.job_type == "android":
                build_path = '/'.join([args.job_type, args.job_name,
                                      str(args.build_num)])
                build_dir_path = os.path.join(uploads_path, build_path)
                user_name = ret_val[0]
                job_name = '_'.join(ret_val[1:])
                target_dir = '/'.join([args.job_type, "~%s" % user_name,
                                       job_name, str(args.build_num)])
                target_dir_path = os.path.join(target_path, target_dir)
            elif args.job_type == "kernel-hwpack":
                kernel_tree = ret_val
                build_path = '/'.join([args.job_type, args.job_name,
                                       str(args.build_num)])
                build_dir_path = os.path.join(uploads_path, build_path)
                target_dir = '/'.join([args.job_type, kernel_tree,
                                       args.job_name])
                target_dir_path = os.path.join(target_path, target_dir)
            elif (args.job_type == "ubuntu-hwpacks" or
                  args.job_type == "ubuntu-images" or
                  args.job_type == "ubuntu-restricted" or
                  args.job_type == "ubuntu-sysroots"):
                dist_name = ret_val[0]
                hwpack_image = args.job_type.split("-")[1]
                board_rootfs_name = ret_val[2]
                build_dir_path = os.path.join(uploads_path, args.job_name,
                                              str(args.build_num))
                target_dir = '/'.join(
                    [dist_name, hwpack_image, board_rootfs_name,
                     str(args.build_num)])
                target_dir_path = os.path.join(target_path, target_dir)
            elif args.job_type == "openembedded":
                build_dir_path = os.path.join(uploads_path,
                                              args.job_type,
                                              args.job_name)
                target_dir_path = os.path.join(target_path,
                                              args.job_type,
                                              args.job_name)
            elif args.job_type == "prebuilt":
                build_path = '%s/%d' % (args.job_name, args.build_num)
                build_dir_path = os.path.join(uploads_path, build_path)
                target_dir_path = target_path
            elif args.job_type == "binaries":
                build_dir_path = os.path.join(uploads_path,
                                              args.job_name,
                                              str(args.build_num))
                ts_file = os.path.join(build_dir_path, 'TIMESTAMP')
                # FIXME: test file and content
                f = open(ts_file)
                timestamp = f.read().strip()
                f.close()
                os.remove(ts_file)
                target_dir_path = os.path.join(
                    target_path, 'android', args.job_type, ret_val[0],
                    timestamp)
        else:
            return None, None

        if not os.path.isdir(build_dir_path):
            build_paths = "'%s' or '%s'" % (uploads_path, build_dir_path)
            print "Missing build paths: ", build_paths
            return None, None

        if not os.path.isdir(target_path):
            print "Missing target path", target_path
            return None, None

        return build_dir_path, target_dir_path

    def create_latest_symlink(self, args, build_dir_path, target_dir_path):
        if args.job_type == "prebuilt":
            for root, dirs, files in os.walk(build_dir_path):
                for dir in dirs:
                    target_dir_path = os.path.join(target_dir_path, dir)
        symlink_path = os.path.dirname(target_dir_path)
        if args.job_type == "android":
            symlink_path = os.path.join(symlink_path, "lastSuccessful")
        else:
            symlink_path = os.path.join(symlink_path, "latest")

        header_path = os.path.join(target_path, "HEADER.html")
        header_symlink_path = os.path.join(target_dir_path, "HEADER.html")
        try:
            if os.path.islink(symlink_path):
                os.unlink(symlink_path)

            if os.path.islink(header_symlink_path):
                os.unlink(header_symlink_path)

            os.symlink(header_path, header_symlink_path)
            os.symlink(target_dir_path, symlink_path)
            print "The latest build is now linked to ", target_dir_path
            return PASS
        except Exception, details:
            print "Failed to create symlink", symlink_path, ":", details
            return FAIL

    def create_manifest_file(self, target_dir):
        orig_dir = os.getcwd()
        os.chdir(target_dir)
        fn = os.path.join(target_dir, "MANIFEST")
        lines = []

        try:
            for path, subdirs, files in os.walk("."):
                for name in files:
                    lines.append(
                        os.path.join(path, name).split("./")[1] + "\n")

            if len(lines) != 0:
                fd = open(fn, "w+")
                for line in lines:
                    if not "MANIFEST" or not "HEADER.html" in line:
                        fd.write(line)
                fd.close()
            else:
                raise Exception("Uploads directory was empty, "
                                "nothing got moved to destination")

            os.chdir(orig_dir)

            if os.path.isfile(fn):
                print "Manifest file", fn, "generated"
                return PASS
        except Exception, details:
            print "Got Exception in create_manifest_file: ", details
            os.chdir(orig_dir)
            return FAIL

    def reshuffle_android_artifacts(self, src_dir):
        dst_dir = src_dir
        full_product_path = os.path.join(src_dir, PRODUCT_DIR)
        if os.path.isdir(full_product_path):
            filelist = os.listdir(full_product_path)
            try:
                for file in filelist:
                    src = os.path.join(full_product_path, file)
                    if os.path.isdir(src):
                        for artifact in os.listdir(src):
                            dest = os.path.join(dst_dir, artifact)
                            if os.path.exists(dest):
                                if os.path.isdir(dest):
                                    continue
                                else:
                                    os.remove(dest)
                            shutil.move(os.path.join(src, artifact), dest)
            except shutil.Error:
                print "Error while reshuffling the content"
            try:
                shutil.rmtree(os.path.dirname(full_product_path))
            except shutil.Error:
                print "Error removing empty product dir"

    def move_dir_content(self, src_dir, dest_dir, sanitize=False):
        filelist = os.listdir(src_dir)
        try:
            for file in filelist:
                src = os.path.join(src_dir, file)
                dest = os.path.join(dest_dir, file)
                if os.path.isdir(src):
                    if not os.path.exists(dest):
                        os.makedirs(dest)
                    self.move_dir_content(src, dest, sanitize)
                    continue
                if os.path.exists(dest):
                    if os.path.isdir(dest):
                        continue
                    else:
                        os.remove(dest)
                if sanitize and not self.is_ok_for_staging(src):
                    # Perform the sanitization before moving the file
                    # into place.
                    print "Sanitizing contents of '%s'." % src
                    self.sanitize_file(src)
                shutil.move(src, dest)
        except shutil.Error:
            print "Error while moving the content"

    def move_artifacts(self, args, build_dir_path, target_dir_path):
        try:
            if not os.path.isdir(target_dir_path):
                # umask 0 is required, otherwise mode value of
                #  makedirs won't take effect
                os.umask(0)
                # Set write permission to the group explicitly,
                # as default umask is 022
                os.makedirs(target_dir_path, 0775)
                if not os.path.isdir(target_dir_path):
                    raise OSError

# Disabled per LAVA-933. See below.
#            if (args.job_type == "android"):
#                self.reshuffle_android_artifacts(build_dir_path)

            self.move_dir_content(build_dir_path, target_dir_path,
                                  sanitize=args.staging)

            if (args.job_type == "android" or
                args.job_type == "prebuilt" or
                args.job_type == "ubuntu-hwpacks" or
                args.job_type == "ubuntu-images" or
                args.job_type == "ubuntu-restricted" or
                args.job_type == "ubuntu-sysroots"):
                ret = self.create_latest_symlink(
                    args, build_dir_path, target_dir_path)
                if ret != PASS:
                    return ret

            if args.manifest:
                ret = self.create_manifest_file(target_dir_path)
                if ret != PASS:
                    print "Failed to create manifest file"
                    return ret

            print (
                "Moved the files from '%s' to '%s'" % (
                    build_dir_path, target_dir_path))
            return PASS

        except OSError, details:
            print (
                "Failed to create the target path %s: %s" % (
                    target_dir_path, details))
            return FAIL

        except shutil.Error:
            print "Failed to move files destination path", target_dir_path
            return FAIL

    def check_buildinfo(self, build_dir_path, target_dir_path):
        bi_dirs = []
        for path, subdirs, files in os.walk(build_dir_path):
            for filename in files:
                if BUILDINFO in filename:
                    bi_dirs.append(path)
        for path, subdirs, files in os.walk(target_dir_path):
            for filename in files:
                if BUILDINFO in filename:
                    bi_dirs.append(path)

        if not bi_dirs:
            raise BuildInfoException(
                    "BUILD-INFO.txt is not present for build being published.")

    def combine_buildinfo(self, build_dir_path, target_dir_path, tmp_bi):
        bi_path = os.path.join(target_dir_path, BUILDINFO)
        bi_dirs = []
        for path, subdirs, files in os.walk(build_dir_path):
            for filename in files:
                if BUILDINFO in filename:
                    bi_dirs.append(path)
        if os.path.exists(bi_path):
            bi_dirs.append(target_dir_path)
        if bi_dirs:
            common_bi = SpliceBuildInfos(bi_dirs)
            common_bi.splice(tmp_bi)


def rewrite_build_info(build_dir_path, target_dir_path, tmp_bi):
    bi_path = os.path.join(target_dir_path, BUILDINFO)
    if os.path.getsize(tmp_bi) > 0:
        shutil.copy(tmp_bi, bi_path)

    append_open_buildinfo(target_dir_path)
    bi = SpliceBuildInfos([target_dir_path])
    bi.splice(bi_path)


def main():
    global uploads_path
    global target_path
    argument_parser = setup_parser()
    publisher = SnapshotsPublisher(argument_parser)

    args = argument_parser.parse_args()
    try:
        publisher.validate_args(args)
    except PublisherArgumentException as exception:
        argument_parser.error(exception.message)

    if args.staging:
        uploads_path = staging_uploads_path
        target_path = staging_target_path

    try:
        build_dir_path, target_dir_path = publisher.validate_paths(
            args, uploads_path, target_path)
        if build_dir_path is None or target_dir_path is None:
            print "Problem with build/target path, move failed"
            return FAIL

        try:
            publisher.check_buildinfo(build_dir_path, target_dir_path)
        except BuildInfoException as e:
            print e.value
            return FAIL

        fd, tmp_bi = tempfile.mkstemp()
        os.close(fd)
        os.chmod(tmp_bi, 0644)

        try:
# See below
#            if args.job_type == 'android':
#                publisher.combine_buildinfo(
#                    build_dir_path, target_dir_path, tmp_bi)

            ret = publisher.move_artifacts(
                args, build_dir_path, target_dir_path)

            if ret != PASS:
                print "Move Failed"
                return FAIL

# Disabled per LAVA-933. Once rest of migration happens on builds' side
# (proper BUILD-INFO.txt's prepared, etc.), this block and rewrite_build_info()
# can be removed.
#            if args.job_type == 'android':
#                rewrite_build_info(
#                    build_dir_path, target_dir_path, tmp_bi)
            print "Move succeeded"
            return PASS
        finally:
            os.remove(tmp_bi)
    except Exception, details:
        print "In main() Exception details:", details
        return FAIL

if __name__ == '__main__':
    sys.exit(main())
