# -*- coding: utf-8 -*-
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'License'
        db.create_table('license_protected_downloads_license', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('digest', self.gf('django.db.models.fields.CharField')(max_length=40)),
            ('text', self.gf('django.db.models.fields.TextField')()),
            ('theme', self.gf('django.db.models.fields.CharField')(max_length=60)),
        ))
        db.send_create_signal('license_protected_downloads', ['License'])

        # Adding model 'APIKeyStore'
        db.create_table('license_protected_downloads_apikeystore', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('key', self.gf('django.db.models.fields.CharField')(max_length=80)),
            ('public', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('license_protected_downloads', ['APIKeyStore'])


    def backwards(self, orm):
        # Deleting model 'License'
        db.delete_table('license_protected_downloads_license')

        # Deleting model 'APIKeyStore'
        db.delete_table('license_protected_downloads_apikeystore')


    models = {
        'license_protected_downloads.apikeystore': {
            'Meta': {'object_name': 'APIKeyStore'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '80'}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'license_protected_downloads.license': {
            'Meta': {'object_name': 'License'},
            'digest': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'text': ('django.db.models.fields.TextField', [], {}),
            'theme': ('django.db.models.fields.CharField', [], {'max_length': '60'})
        }
    }

    complete_apps = ['license_protected_downloads']