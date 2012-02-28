#!/usr/bin/env python

import optparse
import sys


acceptable_job_types = [
    'android',
    'kernel-hwpack',
    ]

uploads_path = '/srv3/snapshots.linaro.org/uploads'
target_path = '/srv3/snapshots.linaro.org/www'


class InvalidParametersException(Exception):
    pass


class SnapshotsPublisher(object):
    def run(self, arguments):
        optparse...
        if (arguments is None or len(arguments) < 3 or
            arguments[0] not in acceptable_job_types):
            raise InvalidParametersException


if __name__ == '__main__':
    publisher = SnapshotsPublisher()
    publisher.run(sys.argv)
