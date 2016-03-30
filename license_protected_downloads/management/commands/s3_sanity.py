from django.conf import settings
from django.core.management.base import BaseCommand

import logging
import time
from boto.s3.connection import S3Connection

logging.getLogger().setLevel(logging.INFO)


class Command(BaseCommand):
    help = 'Make sure S3 buckets are in sync and there are no issues'
    conn = S3Connection(settings.AWS_ACCESS_KEY_ID,
                        settings.AWS_SECRET_ACCESS_KEY)

    def slave_bucket(self, bucket):
        slave_bucket = self.conn.get_bucket(bucket, validate=False)
        slave_bucket_keys = slave_bucket.list(settings.S3_PREFIX_PATH)
        slave_keys = {(key_val.name, key_val.etag) for key_val in
                      slave_bucket_keys}
        return slave_keys

    def handle(self, *args, **options):
        master_bucket_name = 'publishing-linaro-org'
        slave_bucket_name = ['publishing-ap-linaro-org']

        master_bucket = self.conn.get_bucket(master_bucket_name,
                                             validate=False)
        master_bucket_keys = master_bucket.list(settings.S3_PREFIX_PATH)
        master_keys = {(key_val.name, key_val.etag) for key_val in
                       master_bucket_keys}

        changed = False
        for key in master_bucket_keys:
            if not key.name.endswith('/'):
                if '-' in key.etag:
                    logging.info('Multipart file found %s', key.name)
                    changed = True
                    # Setting metadata causes S3 to convert a multipart file
                    # into a valid md5sum.
                    key.set_remote_metadata({'linaro-checker': 'True'}, {},
                                          True)

        if changed:
            # Wait for the files to sync between buckets.
            time.sleep(480)

        for bucket_name in slave_bucket_name:
            for key, value in (master_keys - self.slave_bucket(bucket_name)):
                if not key.endswith('/'):
                    if '-' not in key:
                        logging.warn('file %s is out of sync in bucket %s'
                                     , (key, bucket_name))
