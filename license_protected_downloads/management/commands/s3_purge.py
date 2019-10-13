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
    def find_last_modified(keys):
        for k in keys:
            if not isinstance(k, deletemarker.DeleteMarker):
                return k.last_modified

    @staticmethod
    def process_s3_object(bucket, this_key, s3obj_buffer, options, mark_day, delete_day):

        logging.debug("processing key %s" % this_key)

        if this_key is '' or s3obj_buffer is []:
            return

        if any(fnmatch.fnmatch(this_key, p) for p in
              settings.S3_PURGE_EXCLUDES):
            logging.debug("SKIP: file in S3_PURGE_EXCLUDES: %s" % this_key)
            return

        last_modified = Command.find_last_modified(s3obj_buffer)

        # delete an object if:  --forcedelete was specified, the first key is a deletemarker,
        #  and last_modified for deletemarker is outside of the delete window
        if options['forcedelete'] is True:
            if isinstance(s3obj_buffer[0], deletemarker.DeleteMarker):
                if last_modified < delete_day:
                    if not options['dryrun']:
                        try:
                            logging.info('DELETE: permanently deleting %s' % this_key)
                            bucket.delete_keys(s3obj_buffer)
                        except Exception:
                            logging.exception('S3Connection error for %s', this_key)
                    else:
                        logging.info('DRYRUN: would permanently delete %s' % this_key)
                else:
                    logging.debug('SKIP: deletemarker set, but not expired on %s (last_modified: %s, delete_day: %s)' % (this_key, last_modified, delete_day))
                return

        # if we're still here, check to see if we need to mark file for deletion based
        # on most recent key

        # if it's already a deletemarker, skip it
        if isinstance(s3obj_buffer[0], deletemarker.DeleteMarker):
            logging.debug('SKIP: file already marked for deletion but no forcedelete: %s'%this_key)
            return

        # if in mark window, send delete on the filename to set deletemarker
        if last_modified < mark_day:
            if not options['dryrun']:
                try:
                    logging.debug('MARK: set deletemarker on %s'%this_key)
                    bucket.delete_key(this_key)
                except Exception:
                    logging.exception('S3Connection error for %s', this_key)
            else:
                logging.info('DRYRUN: would have marked for delete %s' % this_key)

    def handle(self, *args, **options):
        conn = S3Connection(settings.AWS_ACCESS_KEY_ID,
                            settings.AWS_SECRET_ACCESS_KEY)
        bucket = conn.get_bucket(settings.S3_BUCKET, validate=False)
        now_mark = self.x_days_ago(int(options['markdays']))
        now_delete = self.x_days_ago(int(options['deletedays']))

        this_key = ''
        s3obj_buffer = []

        for key in bucket.list_versions(options['prefix']):
            # if the key.name changes, we've gotten all the versions for the previous
            # file and should clear our the s3obj_buffer
            if key.name != this_key:
                self.process_s3_object(bucket, this_key, s3obj_buffer, options, now_mark, now_delete)
                this_key = key.name
                s3obj_buffer = []

            s3obj_buffer.append(key)

        # call one last time to ensure last key in the bucket gets processed
        self.process_s3_object(bucket, this_key, s3obj_buffer, options, now_mark, now_delete)
