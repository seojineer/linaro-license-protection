from django.db import models


class License(models.Model):
    digest = models.CharField(max_length=40)
    text = models.TextField()
    theme = models.CharField(max_length=60)

    def __unicode__(self):
        return self.digest
