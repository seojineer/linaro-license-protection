from django.db import models

class License(models.Model):
    digest = models.CharField(max_length=40)
    text = models.TextField()

    def __unicode__(self):
        return self.digest
