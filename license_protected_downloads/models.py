from django.db import models
from django.contrib.sites.models import Site
from django.contrib.sites.managers import CurrentSiteManager


class LicenseManager(models.Manager):
    """
    Model manager for License model.

    Provides additional convenience method
    """

    def all_with_hashes(self, hash_list, site_id):
        """
        Produce a list of licenses that match the specified list of hashes.
        The main use case is to convert license digest to something the user
        can relate to.
        """
        return self.all().filter(
                digest__in=hash_list, sites__id__exact=site_id)


class License(models.Model):
    digest = models.CharField(max_length=40)
    text = models.TextField()
    theme = models.CharField(max_length=60)
    sites = models.ForeignKey(Site)
    on_site = CurrentSiteManager()

    objects = LicenseManager()

    def __unicode__(self):
        return self.digest
