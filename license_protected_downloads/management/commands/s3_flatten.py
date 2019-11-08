from django.conf import settings
from django.core.management.base import BaseCommand

import logging
import datetime
from fnmatch import fnmatch
from boto.s3.connection import S3Connection
from boto.s3 import deletemarker,key

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
        parser.add_argument('--prefix', default='snapshots/aarch64laptops',
                            help='Custom prefix path')
        parser.add_argument('-V', '--verbose', action='store_true',
                            help='log detailed information on actions to INFO')

    @staticmethod
    def x_days_ago(days):
        date = datetime.datetime.now() - datetime.timedelta(days=days)
        return date.isoformat()

    @staticmethod
    def print_key(key):
        if key.is_latest:
            latest = "*"
        else:
            latest = " "

        if isinstance(key, deletemarker.DeleteMarker):
            dm = "DEL"
        else:
            dm = "   "
        return '%s: %s %s(%s) %s' %  (key.name, dm, latest,key.last_modified, key.version_id)

    @staticmethod
    def delete_objects(bucket, delete_list, excludes_list=[], dryrun=True, verbose=False):
        if verbose:
            for x in delete_list:
                if isinstance(x, key.Key) or isinstance(x, deletemarker.DeleteMarker):
                    logging.info("deleting: %s %s" % (x.name,x.version_id))
                else:
                    logging.info("deleting: %s" % (x))

        if not dryrun:
            bucket.delete_keys(delete_list)
        else:
            logging.info( "DRYRUN: delete_keys for %s keys" % len(delete_list) )

    def handle(self, *args, **options):
        conn = S3Connection(settings.AWS_ACCESS_KEY_ID,
                            settings.AWS_SECRET_ACCESS_KEY)
        bucket = conn.get_bucket(settings.S3_BUCKET, validate=False)
        now_mark = self.x_days_ago(int(options['markdays']))
        now_delete = self.x_days_ago(int(options['deletedays']))

        bucket_keys = bucket.list_versions(options['prefix'])

        objs = {}
        delete_list = []

        if options['verbose']:
            logging.info( "Delete day: %s" % now_delete)
            logging.info( "Mark day: %s" % now_mark)

        for key in bucket_keys:
            if options['verbose']:
                logging.info(self.print_key(key))

            if key.name not in objs:
                objs[key.name] = {'last':None, 'delete':None}

            # flatten everything by filtering out everything except the
            # latest versions of the key and/or deletemarker
            if isinstance(key, deletemarker.DeleteMarker):
                if objs[key.name]['delete'] is None:
                    objs[key.name]['delete'] = key
                elif key.last_modified > objs[key.name]['delete'].last_modified:
                    delete_list.append(objs[key.name]['delete'])
                    objs[key.name]['delete'] = key
                else:
                    delete_list.append(key)
            else:
                if objs[key.name]['last'] is None:
                    objs[key.name]['last'] = key
                elif key.last_modified > objs[key.name]['last'].last_modified:
                    delete_list.append(objs[key.name]['last'])
                    objs[key.name]['last'] = key
                else:
                    delete_list.append(key)

                # if the new 'last' is newer than an existing deletemarker,
                # delete the deletemarker
                if objs[key.name]['delete'] and \
                   objs[key.name]['last'].last_modified >= objs[key.name]['delete'].last_modified:
                    delete_list.append(objs[key.name]['delete'])
                    objs[key.name]['delete'] = None

            # purge as we go
            if len(delete_list) > 1000:
                while delete_list:
                    self.delete_objects(bucket, delete_list[0:1000], settings.S3_PURGE_EXCLUDES, options['dryrun'], options['verbose'])
                    delete_list = delete_list[1000:]

        if options['verbose']:
            logging.info("done with flatten")

        # search through everything w/ a delete marker to delete
        for candidate in [ x for x in objs if objs[x]['delete']]:
            # if in exclude we ignore it even if it has a delete marker
            if any(fnmatch(candidate, p) for p in settings.S3_PURGE_EXCLUDES):
                if options['verbose']:
                    logging.info("excluded: %s" % candidate)
                continue
            else:
                if objs[candidate]['last'] is None:
                    # no point in keeping around a delete marker that points to nothing
                    delete_list.append(objs[candidate]['delete'])
                else:
                    # check last_modified on the last real file, not delete marker
                    if objs[candidate]['last'].last_modified < now_delete:
                        delete_list.append(objs[candidate]['delete'])
                        delete_list.append(objs[candidate]['last'])

        if options['verbose']:
            logging.info("done with now_delete")

        # search through everything w/o a delete marker to possibly mark
        for candidate in [ x for x in objs if not objs[x]['delete']]:
            if any(fnmatch(candidate, p) for p in settings.S3_PURGE_EXCLUDES):
                if options['verbose']:
                    logging.info("excluded: %s" % candidate)
                continue
            else:
                if objs[candidate]['last'].last_modified < now_mark:
                    if not options['dryrun']:
                        # by appending only the name rather than the key
                        # object, S3 should insert a delete marker
                        delete_list.append(objs[candidate]['last'].name)
                    else:
                        logging.info("DRYRUN: setting deletemarker on %s - %s" % (objs[candidate]['last'].name, objs[candidate]['last'].version_id))

        if options['verbose']:
            logging.info("done with now_mark")


        while len(delete_list) > 1000:
            self.delete_objects(bucket, delete_list[0:1000], settings.S3_PURGE_EXCLUDES, options['dryrun'], options['verbose'])
            delete_list = delete_list[1000:]
        self.delete_objects(bucket, delete_list[0:1000], settings.S3_PURGE_EXCLUDES, options['dryrun'], options['verbose'])
        if options['verbose']:
            logging.info("done with cleanup.")
