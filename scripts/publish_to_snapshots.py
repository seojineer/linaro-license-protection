#!/usr/bin/env python

import sys
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("-j", "--job_type", dest="job_type",
                    help="Specifiy the job type (Ex: android/kernel-hwpack)")
parser.add_argument("-a", "--archive_info", dest="archive_info",
                    help="Specify the job which resulted the archive to be stored.\
                         Ex: ${JOB_NAME}/${BUILD_NUMBER} should be specified for \
                             andriod and for \
                             kernel-hwpack ${KERNEL_NAME}/${KERNEL_JOB_NAME}")
parser.add_argument("-n", "--build_num", dest="build_num", type=int,
                    help="Specify the job build number for android builds only")


acceptable_job_types = [
    'android',
    'kernel-hwpack',
    ]

uploads_path = '/srv3/snapshots.linaro.org/uploads'
target_path = '/srv3/snapshots.linaro.org/www'


class InvalidParametersException(Exception):
    pass

class SnapshotsPublisher(object):
 
    def validate_args(self, args):
        # Validate that all the required information is passed on the command line
        if (args.job_type == None or  args.archive_info == None): 
            parser.error("\nYou must specify job_type and archive_info")
            raise InvalidParametersException
            return 1

        if (args.job_type == "android" and args.build_num == None):
            parser.error("You must specify build number")
            raise InvalidParametersException
            return 1

        if (args.job_type not in acceptable_job_types):
            parser.error("Invalid job type")
            raise InvalidParametersException
            return 1

    def run(self, arguments):
        pass


if __name__ == '__main__':
    publisher = SnapshotsPublisher()
    args = parser.parse_args()
    publisher.validate_args(args)
