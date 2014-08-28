from django.db import models


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


class APILog(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    # we are on an old version of django missing an ipv6 friendly field
    # so just use a charfield to keep it simple
    ip = models.CharField(max_length=40)
    key = models.ForeignKey(APIKeyStore, blank=True, null=True)
    label = models.CharField(max_length=32)
    path = models.CharField(max_length=256)

    @staticmethod
    def mark(request, label, key=None):
        ip = request.META.get('REMOTE_ADDR')
        ip = request.META.get('HTTP_X_FORWARDED_FOR', ip).split(',')[0]
        APILog.objects.create(label=label, ip=ip, path=request.path, key=key)
        if key:
            key.save()  # bump the last_used timestamp
