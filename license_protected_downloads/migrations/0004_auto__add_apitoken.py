# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'APIToken'
        db.create_table('license_protected_downloads_apitoken', (
            ('token', self.gf('django.db.models.fields.CharField')(max_length=40, primary_key=True)),
            ('key', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['license_protected_downloads.APIKeyStore'])),
            ('expires', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
        ))
        db.send_create_signal('license_protected_downloads', ['APIToken'])


    def backwards(self, orm):
        
        # Deleting model 'APIToken'
        db.delete_table('license_protected_downloads_apitoken')


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
        'license_protected_downloads.apitoken': {
            'Meta': {'object_name': 'APIToken'},
            'expires': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'key': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['license_protected_downloads.APIKeyStore']"}),
            'token': ('django.db.models.fields.CharField', [], {'max_length': '40', 'primary_key': 'True'})
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
