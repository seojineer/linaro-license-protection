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
