from django.conf import settings
from django.core.management.base import BaseCommand
from license_protected_downloads.models import Download
from django.db import DatabaseError
import os
import time
import glob
import logging
import csv

logging.getLogger().setLevel(logging.INFO)


class Command(BaseCommand):
    help = 'Process csv file to postgres and do some log rotating'

    def handle(self, *args, **options):

        def str2bool(self):
            # http://stackoverflow.com/questions/715417
            return self.lower() in ("yes", "true", "t", "1")

        try:
            filename, file_extension = os.path.splitext(settings.REPORT_CSV)
            timestamp = time.strftime('%H%M-%Y%m%d')
            os.rename(settings.REPORT_CSV, filename + '_' + timestamp +
                      file_extension)
        except OSError as e:
            if e.errno != os.errno.EEXIST:
                raise

        # Process any report files that have failed in the pass.
        for name in glob.glob(filename+'_*.csv'):
            print name
            try:
                for row in csv.reader(open(name)):
                    logging.info('Processing %s', name)
                    Download.objects.create(ip=row[0], name=row[1],
                                            link=str2bool(row[2]))
                os.remove(name)
            except (csv.Error, DatabaseError):
                logging.exception('unable to process csv %s', name)
