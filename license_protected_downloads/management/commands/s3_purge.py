from django.conf import settings
from django.core.management.base import BaseCommand

import logging
import datetime
from boto.s3.connection import S3Connection

logging.getLogger().setLevel(logging.INFO)


class Command(BaseCommand):

    help = 'Delete any prefix in S3 when the files are older than X days'

    @staticmethod
    def add_arguments(parser):
        parser.add_argument('--dryrun', action='store_true',
                            help='Do not perform any actions, just report')
        parser.add_argument('--days', default=90,
                            help='Number of days to delete files')
        parser.add_argument('--prefix', default='snapshots/',
                            help='Custom prefix path')
    @staticmethod
    def x_days_ago(days):
        date = datetime.datetime.now() - datetime.timedelta(days=days)
        return date.isoformat()

    def handle(self, *args, **options):
        conn = S3Connection(settings.AWS_ACCESS_KEY_ID,
                            settings.AWS_SECRET_ACCESS_KEY)
        bucket = conn.get_bucket(settings.S3_BUCKET, validate=False)
        bucket_key = bucket.list(options['prefix'])

        now = self.x_days_ago(int(options['days']))

        for key in bucket_key:
            if not any(map(key.name.startswith, settings.S3_PURGE_EXCLUDES)):
                if key.last_modified < now:
                    if options['dryrun']:
                        logging.info('Will delete %s', key.name)
                    else:
                        try:
                            logging.debug('Deleted %s', key.name)
                            bucket.delete_key(key)
                        except Exception:
                            logging.exception('S3Connection error for %s',
                                              key.name)
