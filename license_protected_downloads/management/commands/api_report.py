import datetime
import json

from django.core.management.base import BaseCommand, CommandError

from license_protected_downloads.models import APILog


def _process_entry(results, entry):
    results['counters'].setdefault(entry.label, 0)
    results['counters'][entry.label] += 1

    results['by-attribute']['ip'].setdefault(entry.ip, 0)
    results['by-attribute']['ip'][entry.ip] += 1

    key = 'null'
    if entry.key:
        key = entry.key.key
    results['by-attribute']['apikey'].setdefault(key, 0)
    results['by-attribute']['apikey'][key] += 1

    if entry.label == 'FILE_UPLOAD':
        path_parts = entry.path.split('/')
        if path_parts[-2].isdigit():
            # we have a "build" like kernel-hwpack/24/blah.img
            results['by-attribute']['builds']['/'.join(path_parts[:-1])] = 1


def _generate_report(start, end):
    results = {
        'counters': {},
        'by-attribute': {'ip': {}, 'apikey': {}, 'builds': {}},
    }
    entries = APILog.objects.filter(timestamp__range=(start, end))
    for entry in entries:
        _process_entry(results, entry)

    results['by-attribute']['builds'] = len(results['by-attribute']['builds'])
    return results


class Command(BaseCommand):
    args = '<start> <end>'
    help = 'Generate a simple usage report of the REST api. Start and end' \
           'are an integer value of days to go back. ie: 7 is one week back.'

    def handle(self, *args, **options):
        if len(args) > 2:
            raise CommandError('too many arguments')

        start = 1  # default to one day back
        end = 0
        if len(args) > 0:
            start = args[0]
            if len(args) > 1:
                end = args[1]

        start = self._to_dt(start)
        end = self._to_dt(end)
        if start > end:
            raise CommandError('start day must be *before* end day')

        self._generate_report(start, end)

    def _to_dt(self, val):
        try:
            val = int(val) * -1
        except:
            raise CommandError('Invalid numeric value: %s' % val)

        return datetime.datetime.now() + datetime.timedelta(days=val)

    def _generate_report(self, start, end):
        print('API Usage from %s - %s' % (start, end))
        print(json.dumps(_generate_report(start, end), indent=2))
