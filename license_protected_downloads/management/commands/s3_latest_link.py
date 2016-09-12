from django.conf import settings
from django.core.management.base import BaseCommand

import logging
import os
from boto.s3.connection import S3Connection

logging.getLogger().setLevel(logging.INFO)


class Command(BaseCommand):
    help = 'Ensure the hidden dotfile is created in the latest_link folder'
    conn = S3Connection(settings.AWS_ACCESS_KEY_ID,
                        settings.AWS_SECRET_ACCESS_KEY)
    bucket = conn.get_bucket(settings.S3_BUCKET, validate=False)
    bucket_keys = bucket.list(settings.S3_PREFIX_PATH)

    def handle(self, *args, **options):
        paths = []
        for key in self.bucket_keys:
            if os.path.dirname(key.name).endswith('/latest'):
                paths.append(os.path.dirname(key.name))

        list1 = []
        list2 = []
        for i in set(paths):
            for key in self.bucket.list(prefix=os.path.split(i)[0]):
                # Need to replace "." for releases folder e.g. 15.06,16.06 etc
                build_no = os.path.split(os.path.dirname(key.name))[1]\
                    .replace(".", "", 1)
                parent_dir = os.path.split(os.path.dirname(key.name))[0]
                if build_no.isdigit():
                    list1.append(build_no)
                    list2.append(parent_dir)
            key_name = '.s3_linked_from'
            file_content = '%s/%s' % (', '.join(set(list2)), max(list1,
                                                                 key=int))
            new_file = os.path.join(i, key_name)
            k = self.bucket.new_key(new_file)
            k.set_contents_from_string(file_content)
            logging.info('creating file %s with contents %s', new_file,
                         file_content)
            list1 = []
            list2 = []
