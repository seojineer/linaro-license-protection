import datetime
import uuid

from django.db import models


def ip_field(required=True):
    # we are on an old version of django missing an ipv6 friendly field
    # so just use a charfield to keep it simple
    if required:
        return models.CharField(max_length=40)
    return models.CharField(max_length=40, blank=True, null=True)


def get_ip(request):
    ip = request.META.get('REMOTE_ADDR')
    return request.META.get('HTTP_X_FORWARDED_FOR', ip).split(',')[0]


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

    description = models.CharField(max_length=40, default='')
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
