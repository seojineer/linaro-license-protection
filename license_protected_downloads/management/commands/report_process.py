from django.conf import settings
from django.core.management.base import BaseCommand
from license_protected_downloads.models import Download
from django.db import DatabaseError
import os
import time
import glob
import logging
import csv
import fcntl
import sys

logging.getLogger().setLevel(logging.WARN)


class Command(BaseCommand):
    help = 'Process csv file to postgres and do some log rotating'

    def handle(self, *args, **options):
        # Ensure only one script is running at a time
        f = open(os.path.join(settings.REPORT_CSV + '.lock'), 'w+')
        try:
            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except IOError:
            sys.exit('Script is already running')

        def str2bool(self):
            # http://stackoverflow.com/questions/715417
            return self.lower() in ("yes", "true", "t", "1")

        try:
            filename, file_extension = os.path.splitext(settings.REPORT_CSV)
            timestamp = time.strftime('%H%M-%Y%m%d')
            os.rename(settings.REPORT_CSV, filename + '_' + timestamp +
                      file_extension)
        except OSError as e:
            if e.errno != os.errno.ENOENT:
                raise

        # Process any report files that have failed in the pass.
        for name in glob.glob(filename+'_*.csv'):
            try:
                logging.info('Processing %s', name)
                for row in csv.reader(open(name)):
                    # This looks odd, but we sometimes get URLs with newlines
                    # in them and we need the real file name
                    download = row[1].replace('\n', '')
                    Download.objects.create(
                        ip=row[0], name=download, link=str2bool(row[2]))
                os.remove(name)
            except (csv.Error, DatabaseError):
                logging.exception('unable to process csv %s', name)