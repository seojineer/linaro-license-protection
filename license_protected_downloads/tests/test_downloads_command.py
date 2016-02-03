import datetime

from django.test import TestCase

from license_protected_downloads.models import Download
from license_protected_downloads.management.commands.downloads_report import (
    Command,
)


def _create_download(ip, name, hours_ago=0):
    d = Download.objects.create(ip=ip, name=name, link=False)
    if hours_ago > 0:
        d.timestamp = datetime.datetime.now() - datetime.timedelta(
            hours=hours_ago)
    d.save()


class TestDownloadsCommand(TestCase):
    def test_find_dups(self):
        '''Ensure we can filter out multipart downloads.'''
        # Create 4 downloads from 1.1.1.1 for foo/bar
        # 2 are in one 2 hour window, and 2 are in another
        _create_download('1.1.1.1', '/foo/bar', 4)
        _create_download('1.1.1.1', '/foo/bar', 3)  # dup
        _create_download('1.1.1.1', '/foo/bar', 1)
        _create_download('1.1.1.1', '/foo/bar', 0)  # dup

        # Now have 1.1.1.1 download foo/BAR
        _create_download('1.1.1.1', '/foo/BAR', 0)
        _create_download('1.1.1.2', '/foo/BAR', 1)
        _create_download('1.1.1.2', '/foo/BAR', 0)  # dup

        self.assertEqual([2, 4, 7], Command()._find_dups())

    def test_remove_dups(self):
        _create_download('1.1.1.1', '/foo/bar', 4)
        _create_download('1.1.1.1', '/foo/bar', 3)
        _create_download('1.1.1.1', '/foo/bar', 1)
        _create_download('1.1.1.1', '/foo/bar', 0)

        Command()._remove_dups([1, 2])
        self.assertEqual([3, 4], [x.id for x in Download.objects.all()])
