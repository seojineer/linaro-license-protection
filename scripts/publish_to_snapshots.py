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
        if (args.job_type == None or  args.job_name == None or \
            args.build_num == None): 
            parser.error("\nYou must specify job-type, job-name and build-num")
            return FAIL

        if (args.job_type not in acceptable_job_types):
            parser.error("Invalid job type")
            return FAIL

    def jobname_to_target_subdir(self, args, jobname):
        ret_val = None
        if args.job_type == "android":
            ret_val = jobname.split("_")    
        elif args.job_type == "kernel-hwpack":
            ret_val = jobname.split('_')[0].replace(".", "_")
        return ret_val 

    def validate_paths(self, args, uploads_path, target_path):
        build_dir_path = target_dir_path = None
        ret_val = self.jobname_to_target_subdir(args, args.job_name)
        if ret_val != None:
            if args.job_type == "android":
                build_path = '/'.join([args.job_type, args.job_name,
                                      str(args.build_num)])
                build_dir_path = os.path.join(uploads_path, build_path) 
                user_name = ret_val[0]
                job_name = '_'.join(ret_val[1:])
                target_dir = '/'.join([args.job_type, user_name, job_name,
                                       str(args.build_num)])
                target_dir_path = os.path.join(target_path, target_dir)
            elif args.job_type == "kernel-hwpack":
                kernel_tree = ret_val
                build_path = '/'.join([args.job_type, args.job_name, 
                                       str(args.build_num)])
                build_dir_path = os.path.join(uploads_path, build_path)
                target_dir = '/'.join([args.job_type, kernel_tree, 
                                       args.job_name])
                target_dir_path = os.path.join(target_path, target_dir)
        else:
            return None, None

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
