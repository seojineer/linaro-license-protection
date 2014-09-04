# -*- coding: utf-8 -*-
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'APILog'
        db.create_table('license_protected_downloads_apilog', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('ip', self.gf('django.db.models.fields.CharField')(max_length=40)),
            ('key', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['license_protected_downloads.APIKeyStore'], null=True, blank=True)),
            ('label', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('path', self.gf('django.db.models.fields.CharField')(max_length=256)),
        ))
        db.send_create_signal('license_protected_downloads', ['APILog'])


    def backwards(self, orm):
        # Deleting model 'APILog'
        db.delete_table('license_protected_downloads_apilog')


    models = {
        'license_protected_downloads.apikeystore': {
            'Meta': {'object_name': 'APIKeyStore'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '80'}),
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