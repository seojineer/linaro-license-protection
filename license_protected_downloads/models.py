import calendar
import datetime
import logging
import uuid
import csv

from django.conf import settings
from django.db import models
from django.db.models import Count


def ip_field(required=True):
    # we are on an old version of django missing an ipv6 friendly field
    # so just use a charfield to keep it simple
    if required:
        return models.CharField(max_length=40)
    return models.CharField(max_length=40, blank=True, null=True)


def get_ip(request):
    # fields taken from:
    #  https://github.com/un33k/django-ipware/blob/master/ipware/defaults.py
    ip_meta_vals = (
        'HTTP_X_FORWARDED_FOR',
        'HTTP_CLIENT_IP',
        'HTTP_X_REAL_IP',
        'HTTP_X_FORWARDED',
        'HTTP_X_CLUSTER_CLIENT_IP',
        'HTTP_FORWARDED_FOR',
        'HTTP_FORWARDED',
        'X_FORWARDED_FOR',
        'REMOTE_ADDR',
    )
    for field in ip_meta_vals:
        ip = request.META.get(field)
        if ip and ip != 'unknown':
            return ip.split(',')[0]

    logging.warn('Unable to find request ip: %r', request.META)
    return 'unknown'


class LicenseManager(models.Manager):
    """
    Model manager for License model.

    Provides additional convenience method
    """

    def all_with_hashes(self, hash_list):
        """
        Produce a list of licenses that match the specified list of hashes.
        The main use case is to convert license digest to something the user
        can relate to.
        """
        return self.all().filter(digest__in=hash_list)


class License(models.Model):
    digest = models.CharField(max_length=40)
    text = models.TextField()
    theme = models.CharField(max_length=60)

    objects = LicenseManager()

    def __unicode__(self):
        return self.digest


class APIKeyStore(models.Model):
    key = models.CharField(max_length=80)
    public = models.BooleanField()

    description = models.CharField(max_length=256, default='')
    last_used = models.DateTimeField(auto_now=True, blank=True, null=True)

    def __unicode__(self):
        return '%s: %s' % (self.description, self.public)


class APIToken(models.Model):
    '''Represents an API token that will be valid under certain restrictions'''
    token = models.CharField(primary_key=True, max_length=40)
    key = models.ForeignKey(APIKeyStore)
    expires = models.DateTimeField(
        blank=True, null=True, help_text='Limit the duration of this token')
    not_valid_til = models.DateTimeField(
        blank=True, null=True,
        help_text='Prevent this token from being immediately available')
    ip = ip_field(required=False)

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = str(uuid.uuid4())
        return super(APIToken, self).save(*args, **kwargs)

    def valid_request(self, request):
        if self.expires and self.expires < datetime.datetime.now():
            return False
        if self.not_valid_til and self.not_valid_til > datetime.datetime.now():
            return False
        if self.ip and get_ip(request) != self.ip:
            return False

        return True


class APILog(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    ip = ip_field()
    key = models.ForeignKey(APIKeyStore, blank=True, null=True)
    label = models.CharField(max_length=32)
    path = models.CharField(max_length=256)

    @staticmethod
    def mark(request, label, key=None):
        ip = get_ip(request)
        APILog.objects.create(label=label, ip=ip, path=request.path, key=key)
        if key:
            key.save()  # bump the last_used timestamp


class Download(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    ip = ip_field()
    name = models.CharField(max_length=256)
    link = models.BooleanField(
        help_text='Was this a real path or a link like "latest"')

    country = models.CharField(max_length=256, blank=True, null=True)
    region_isp = models.CharField(max_length=256, blank=True, null=True)

    @staticmethod
    def mark(request, artifact):
        try:
            if not settings.TRACK_DOWNLOAD_STATS:
                return

            # Don't keep track of bot downloads.
            agent = request.META.get('HTTP_USER_AGENT', '')
            for bot in settings.BOT_USER_AGENTS:
                if bot in agent:
                    return

            ip = get_ip(request)
            name = artifact.get_real_name()
            link = name != artifact.url()
            with open(settings.REPORT_CSV, "a") as f:
                writer = csv.writer(f)
                writer.writerow([ip, name, link])
        except:
            logging.exception('unable to mark download')

    @staticmethod
    def next_month(ts):
        if ts.month < 12:
            next_month = ts.month + 1
            last_day = min(ts.day, calendar.monthrange(ts.year, next_month)[1])
            return ts.replace(month=next_month, day=last_day)
        return ts.replace(year=ts.year + 1, month=1)

    @staticmethod
    def month_queryset(year_month):
        start = datetime.datetime.strptime(year_month, '%Y.%m')
        end = Download.next_month(start)
        return Download.objects.filter(
            timestamp__gte=start, timestamp__lte=end).exclude(country=None)

    @staticmethod
    def report(year_month, column_name, **extra_filters):
        qs = Download.month_queryset(
            year_month
        )
        if extra_filters:
            qs = qs.filter(**extra_filters)

        return qs.values(
            column_name,
        ).annotate(
            count=Count(column_name)
        ).order_by(
            '-count'
        )
