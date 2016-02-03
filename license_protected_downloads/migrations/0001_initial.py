# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='APIKeyStore',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('key', models.CharField(max_length=80)),
                ('public', models.BooleanField()),
                ('description', models.CharField(default=b'', max_length=256)),
                ('last_used', models.DateTimeField(auto_now=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='APILog',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('ip', models.CharField(max_length=40)),
                ('label', models.CharField(max_length=32)),
                ('path', models.CharField(max_length=256)),
                ('key', models.ForeignKey(blank=True, to='license_protected_downloads.APIKeyStore', null=True)),
            ],
        ),
        migrations.CreateModel(
            name='APIToken',
            fields=[
                ('token', models.CharField(max_length=40, serialize=False, primary_key=True)),
                ('expires', models.DateTimeField(help_text=b'Limit the duration of this token', null=True, blank=True)),
                ('not_valid_til', models.DateTimeField(help_text=b'Prevent this token from being immediately available', null=True, blank=True)),
                ('ip', models.CharField(max_length=40, null=True, blank=True)),
                ('key', models.ForeignKey(to='license_protected_downloads.APIKeyStore')),
            ],
        ),
        migrations.CreateModel(
            name='Download',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('ip', models.CharField(max_length=40)),
                ('name', models.CharField(max_length=256)),
                ('link', models.BooleanField(help_text=b'Was this a real path or a link like "latest"')),
                ('country', models.CharField(max_length=256, null=True, blank=True)),
                ('region_isp', models.CharField(max_length=256, null=True, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='License',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('digest', models.CharField(max_length=40)),
                ('text', models.TextField()),
                ('theme', models.CharField(max_length=60)),
            ],
        ),
    ]
