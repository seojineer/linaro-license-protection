from django.conf import settings
from django.core.management.base import BaseCommand

import logging
import datetime
import fnmatch
from boto.s3.connection import S3Connection
from boto.s3 import deletemarker

logging.getLogger().setLevel(logging.INFO)


class Command(BaseCommand):

    help = 'Mark files as deleted or delete files for good, which are older \
            than X days'

    @staticmethod
    def add_arguments(parser):
        parser.add_argument('--dryrun', action='store_true',
                            help='Do not perform any actions, just report')
        parser.add_argument('--markdays', default=90,
                            help='Number of days to mark files as deleted')
        parser.add_argument('--deletedays', default=180,
                            help='Number of days to delete files for good')
        parser.add_argument('--prefix', default='snapshots/',
                            help='Custom prefix path')
        parser.add_argument('--forcedelete', action='store_true',
                            help='Permanently remove files from given prefix')
        parser.add_argument('--cleanup_releases', action='store_true',
                            help='Cleanup releases/ prefix. Needs to be used \
                            --forcedelete as it permanently deletes files')

    @staticmethod
    def x_days_ago(days):
        date = datetime.datetime.now() - datetime.timedelta(days=days)
        return date.isoformat()

    @staticmethod
    def handle_permanent_deletes(key, dryrun, delete_by, bucket):
        if isinstance(key, deletemarker.DeleteMarker) and key.is_latest and \
                key.last_modified < delete_by and key.version_id:
            if dryrun:
                logging.info('DRYRUN: Will permanently delete %s, %s, %s', key.name,
                             key.version_id, isinstance(key, deletemarker.DeleteMarker))
            else:
                logging.info('Permanently deleted %s, %s',
                             key.name, key.version_id)
                return bucket.delete_key(key.name, version_id=key.version_id)

    def handle(self, *args, **options):
        conn = S3Connection(settings.AWS_ACCESS_KEY_ID,
                            settings.AWS_SECRET_ACCESS_KEY)
        bucket = conn.get_bucket(settings.S3_BUCKET, validate=False)
        bucket_key = bucket.list(options['prefix'])
        now_mark = self.x_days_ago(int(options['markdays']))
        now_delete = self.x_days_ago(int(options['deletedays']))

        for key in bucket_key:
            if key.last_modified < now_mark:
                if not any(fnmatch.fnmatch(key.name, p) for p in
                           settings.S3_PURGE_EXCLUDES):
                    if options['dryrun'] and not options['forcedelete']:
                        logging.info(
                            'DRYRUN: Will set delete marker %s', key.name)
                    elif options['forcedelete'] and not options['cleanup_releases']:
                        for v_key in bucket.list_versions(prefix='snapshots/'):
                            self.handle_permanent_deletes(
                                v_key, options['dryrun'], now_delete, bucket)
                        break
                    elif options['cleanup_releases']:
                        """ Clean up the releases/ prefix """
                        for r_key in bucket.list_versions(prefix='releases/'):
                            self.handle_permanent_deletes(
                                r_key, options['dryrun'], now_delete, bucket)
                        break
                    else:
                        try:
                            logging.debug('Delete marker set %s', key.name)
                            bucket.delete_key(key)
                        except Exception:
                            logging.exception(
                                'S3Connection error for %s', key.name)
