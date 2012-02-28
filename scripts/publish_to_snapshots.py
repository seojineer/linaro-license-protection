#!/usr/bin/env python

import optparse


class InvalidParametersException(Exception):
    pass

acceptable_job_types = [
    'android',
    'kernel-hwpack',
    ]

class SnapshotsPublisher(object):
    def run(self, arguments):
        if (arguments is None or len(arguments) < 3 or 
            arguments[0] not in acceptable_job_types):
            raise InvalidParametersException


if __name__ == '__main__':
    pass
