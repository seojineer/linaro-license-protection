#!/usr/bin/python3

import json
import urllib.parse
import boto3
from datetime import datetime, timedelta
import fnmatch

EXPIRE_TAG = "LLP_Expires"
EXPIRE_TIME = timedelta(days=180)
PROTECTED_PATHS = [
    'releases/*',
    'snapshots/gnu-toolchain/*',
    'snapshots/android/binaries/*',
    'snapshots/components/kernel/leg-96boards-developerbox-edk2/*',
    'snapshots/components/toolchain/infrastructure/*',
    'snapshots/components/toolchain/gcc-linaro/*',
    'snapshots/components/toolchain/binaries/*',
    'snapshots/96boards/*/binaries/*',
    'snapshots/96boards/*/linaro/debian/*',
    'snapshots/components/pyarmnn-tests/*',
    'snapshots/android/lkft/protected/*BUILD-INFO',
]

s3 = boto.client('s3')
now = datetime.utcnow()

def lambda_handler(event, context):
    print("Received event" + json.dumps(event, indent=2))

    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        key = urllib.parse.unquote_plus(record['s3']['object']['key'],
            encoding='utf-8')

        # check if key in protected fields and exit if yes
        for protected in PROTECTED_PATHS:
            if fnmatch(key, protected):
                print(f"Key {key} protected by rule {protected}")
                return

        # No rule to protect the filepath, so let's tag it for expiration
        try:
            response = s3.put_object_tagging(
                Bucket = bucket,
                Tagging = {
                    'TagSet': [
                        'Key': EXPIRE_TAG,
                        'Value': str(now.date()+EXPIRE_TIME)
                    ]
                }
            )
        except Exception as e:
            print(f"Error setting tag for {key}")
            print(e)
        raise e
