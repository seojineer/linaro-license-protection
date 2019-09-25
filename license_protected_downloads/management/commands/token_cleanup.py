from django.conf import settings
from django.core.management.base import BaseCommand
from license_protected_downloads.models import (
    APIToken,
    APILog
)
import logging
import datetime

logging.getLogger().setLevel(logging.INFO)


class Command(BaseCommand):
    @staticmethod
    def add_arguments(parser):
        parser.add_argument('--dryrun', action='store_true',
                            help='Do not perform any actions, just report')
        parser.add_argument('--deletedays', default=30,
                            help='Number of days to delete files for good')

    @staticmethod
    def x_days_ago(days):
        date = datetime.datetime.now() - datetime.timedelta(days=days)
        return date.isoformat()

    def handle(self, *args, **options):
        now_delete = self.x_days_ago(int(options['deletedays']))
        keys = APIToken.objects.filter(expires__lte=now_delete).delete()

        if options['dryrun']:
            logging.info('DRYRUN: DELETE %s, EXPIRE: %s', key.token, key.expires)
        else:
            APIToken.objects.filter(expires__lte=now_delete).delete()
            APILog.objects.filter(timestamp__lte=now_delete).delete()
