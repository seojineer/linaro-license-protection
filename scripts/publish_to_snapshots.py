#!/usr/bin/env python
# This script moves the artifacts from tmp location to a
# to a permanent location on s.l.o

import os
import sys
import shutil
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("-t", "--job-type", dest="job_type",
                    help="Specify the job type (Ex: android/kernel-hwpack)")
parser.add_argument("-u", "--user", dest="user_name",
                    help="Specify the user who built the job")
parser.add_argument("-r", "--ktree", dest="kernel_tree",
                    help="Specify the kernel tree built by the job")
parser.add_argument("-j", "--job-name", dest="job_name",
                    help="Specify the job name which resulted the archive to be stored.\
                    Ex: ${JOB_NAME} should be specified for andriod and for \
                    kernel-hwpack ${KERNEL_JOB_NAME}")
parser.add_argument("-n", "--build-num", dest="build_num", type=int,
                    help="Specify the job build number for android builds only")

uploads_path = '/srv3/snapshots.linaro.org/uploads/'
target_path = '/srv3/snapshots.linaro.org/www/'
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
            parser.error("\nYou must specify job-type and job-name")
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

    def validate_paths(self, args, uploads_path, target_path):
        build_dir_path = target_dir_path = None
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
            build_paths = "'%s' or '%s'" % (uploads_path, build_dir_path)
            print "Missing build paths: ", build_paths
            return None, None
       
        if not os.path.isdir(target_path):
            print "Missing target path", target_path
            return None, None

        return build_dir_path, target_dir_path


    def move_artifacts(self, args, build_dir_path, target_dir_path):
        try:
            # Make a note of the contents of src dir so that 
            # it can be used to validate the move to destination
            uploads_dir_list = os.listdir(build_dir_path)

            if not os.path.isdir(target_dir_path):
                os.makedirs(target_dir_path)
                if not os.path.isdir(target_dir_path):
                    raise OSError

            for fname in uploads_dir_list:
                fname = os.path.join(build_dir_path, fname)
                shutil.copy2(fname, target_dir_path)

            target_dir_list = os.listdir(target_dir_path)
            for fname in uploads_dir_list:
                if not fname in target_dir_list:
                    print "Destination missing file", fname
                    return FAIL

            shutil.rmtree(build_dir_path)
            print "Moved the files from '",build_dir_path, "' to '",\
                  target_dir_path, "'"
            return PASS

        except OSError, details:
            print "Failed to create the target path", target_dir_path, ":" , details 
            return FAIL
        except shutil.Error:
            print "Failed to move files destination path", target_dir_path
            print "Target already exists, move failed"
            return FAIL

def main():
    publisher = SnapshotsPublisher()
    args = parser.parse_args()
    publisher.validate_args(args)
    build_dir_path, target_dir_path = publisher.validate_paths(args, uploads_path, 
                                                               target_path)
    if build_dir_path == None or target_dir_path == None:
        print "Problem with build/target path, move failed"
        return FAIL

    ret  = publisher.move_artifacts(args, build_dir_path, target_dir_path)
    if ret != PASS:
        print "Move Failed"
        return FAIL
    else:
        print "Move succeeded"
        return PASS
if __name__ == '__main__':
    sys.exit(main())
