import datetime

from django.conf import settings
from django.core.management.base import BaseCommand

from IP2Location import IP2Location

from license_protected_downloads.models import Download


class Command(BaseCommand):
    help = 'Go through downloads and fill out empty region/isp information'

    def handle(self, *args, **options):
        ipl = IP2Location(settings.IP2LOCATION_FILE)
        dups = self._find_dups()
        self._remove_dups(dups)
        for download in Download.objects.filter(country=None):
            try:
                loc = ipl.get_all(download.ip)
                download.country = loc.country_short
                download.region_isp = '%s / %s' % (loc.region, loc.isp)
            except:
                if ':' in download.ip:
                    print 'Inserting ipv6-unknown for', download.id
                    download.country = download.region_isp = 'ipv6-unknown'
                else:
                    print "Unable to get IP location data for:", download.id
                    raise
            download.save()

    def _find_dups(self):
        '''Find duplicate entries caused by multi-part downloads.
           Some browsers will do multiple requests for a single "download".
           This method attempts to find the "dups" and remove them. So that
           we can tally true downloads'''
        dups = []
        downloads = {}
        download_duration = datetime.timedelta(hours=2)
        qs = Download.objects.filter(country=None).order_by('timestamp')
        for download in qs:
            file_downloads = downloads.setdefault(download.name, {})
            ip_downloads = file_downloads.setdefault(download.ip, [])
            window = download.timestamp - download_duration
            if len(ip_downloads) == 0 or ip_downloads[-1].timestamp < window:
                # First entry, or the last download happened > 2 hours since
                # the previous
                ip_downloads.append(download)
            else:
                dups.append(download.id)
        return dups

    def _remove_dups(self, dups):
        Download.objects.filter(id__in=dups).delete()
