# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'UCEngineProfile'
        db.create_table('ucengine_connect_ucengineprofile', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('ucengine_uid', self.gf('django.db.models.fields.CharField')(default='', max_length=64, null=True, blank='')),
            ('ucengine_password', self.gf('django.db.models.fields.CharField')(default='', max_length=64)),
        ))
        db.send_create_signal('ucengine_connect', ['UCEngineProfile'])


    def backwards(self, orm):
        
        # Deleting model 'UCEngineProfile'
        db.delete_table('ucengine_connect_ucengineprofile')


    models = {
        'ucengine_connect.ucengineprofile': {
            'Meta': {'object_name': 'UCEngineProfile'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ucengine_password': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '64'}),
            'ucengine_uid': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '64', 'null': 'True', 'blank': "''"})
        }
    }

    complete_apps = ['ucengine_connect']
