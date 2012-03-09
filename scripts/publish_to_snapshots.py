#!/usr/bin/env python
# This script moves the artifacts from tmp location to a
# to a permanent location on s.l.o

import os
import sys
import shutil
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("-j", "--job_type", dest="job_type",
                    help="Specifiy the job type (Ex: android/kernel-hwpack)")
parser.add_argument("-u", "--user", dest="user_name",
                    help="Specifiy the user who built the job")
parser.add_argument("-t", "--ktree", dest="kernel_tree",
                    help="Specifiy the kernel tree built by the job")
parser.add_argument("-n", "--job_name", dest="job_name",
                    help="Specify the job name which resulted the archive to be stored.\
                    Ex: ${JOB_NAME} should be specified for andriod and for \
                    kernel-hwpack ${KERNEL_JOB_NAME}")
parser.add_argument("-i", "--build_num", dest="build_num", type=int,
                    help="Specify the job build number for android builds only")

PASS = 0 
FAIL = 1
acceptable_job_types = [
    'android',
    'kernel-hwpack',
    ]

class SnapshotsPublisher(object):
 
    def validate_args(self, args):
        # Validate that all the required information 
        # is passed on the command line
        if (args.job_type == None or  args.job_name == None): 
            parser.error("\nYou must specify job_type and job_name")
            raise InvalidParametersException
            return FAIL

        if (args.job_type == "android" and (args.build_num == None or \
            args.user_name == None)):
            parser.error("You must specify build number and owner of the job")
            return FAIL

        if (args.job_type == "kernel-hwpack" and args.kernel_tree == None):
            parser.error("You must specify kernel tree name built by the job")
            return FAIL

        if (args.job_type not in acceptable_job_types):
            parser.error("Invalid job type")
            return FAIL

    def validate_paths_move_artifacts(self, args, uploads_path, target_path):
        if args.job_type == "android":
           build_path = '/'.join([args.job_type, args.user_name, args.job_name])
           build_dir_path = os.path.join(uploads_path, build_path, 
                                         str(args.build_num))
           target_dir_path = os.path.join(target_path, build_path,
                                          str(args.build_num))
        else:
           build_path = '/'.join([args.job_type, args.kernel_tree, args.job_name])
           build_dir_path = os.path.join(uploads_path, build_path)
           target_dir_path = os.path.join(target_path, build_path)

        if not (os.path.isdir(uploads_path) or os.path.isdir(build_dir_path)):
            print "Missing build path", build_dir_path
            return FAIL
       
        if not os.path.isdir(target_path):
            print "Missing target path", target_path
            return FAIL

        try:
            # Make a note of the contents of src dir so that 
            # it can be used to validate the move to destination
            uploads_dirList = os.listdir(build_dir_path)

            if not os.path.isdir(target_dir_path):
                os.makedirs(target_dir_path)
                if not os.path.isdir(target_dir_path):
                    raise OSError

            for fname in uploads_dirList:
                fname = os.path.join(build_dir_path, fname)
                shutil.copy2(fname, target_dir_path)
            target_dirList = os.listdir(target_dir_path)

            for fname in uploads_dirList:
                if not fname in target_dirList:
                    print "Destination missing file", fname
                    return FAIL

            shutil.rmtree(build_dir_path)
            print "Moved the files from", build_dir_path, "to ",target_dir_path
            return PASS

        except OSError, details:
            print "Failed to create the target path", target_dir_path, ":" , details 
            return FAIL
        except shutil.Error:
            print "Failed to move files destination path", target_dir_path
            print "Target already exists, move failed"
            return FAIL

def main():
    uploads_path = '/srv3/snapshots.linaro.org/uploads/'
    target_path = '/srv3/snapshots.linaro.org/www/'
    uploads_path = '/tmp/uploads/'
    target_path = '/tmp/www/'

    publisher = SnapshotsPublisher()
    args = parser.parse_args()
    publisher.validate_args(args)
    ret = publisher.validate_paths_move_artifacts(args, uploads_path,
                                                  target_path)
    if ret != PASS:
        print "Problem with build/target path, move failed"
        return FAIL
    else:
        print "Move succeeded"
        return PASS
if __name__ == '__main__':
    sys.exit(main())
