# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'APIKeyStore.description'
        db.add_column('license_protected_downloads_apikeystore', 'description',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=40),
                      keep_default=False)

        # Adding field 'APIKeyStore.last_used'
        db.add_column('license_protected_downloads_apikeystore', 'last_used',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now=True, null=True, blank=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'APIKeyStore.description'
        db.delete_column('license_protected_downloads_apikeystore', 'description')

        # Deleting field 'APIKeyStore.last_used'
        db.delete_column('license_protected_downloads_apikeystore', 'last_used')


    models = {
        'license_protected_downloads.apikeystore': {
            'Meta': {'object_name': 'APIKeyStore'},
            'description': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '40'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '80'}),
            'last_used': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'blank': 'True'}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'license_protected_downloads.apilog': {
            'Meta': {'object_name': 'APILog'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ip': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
            'key': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['license_protected_downloads.APIKeyStore']", 'null': 'True', 'blank': 'True'}),
            'label': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'path': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
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