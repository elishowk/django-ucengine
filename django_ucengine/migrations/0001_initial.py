# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'UCEngineCredentials'
        db.create_table('django_ucengine_ucenginecredentials', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('ucengine_uid', self.gf('django.db.models.fields.CharField')(default='', max_length=64, null=True, blank='')),
            ('ucengine_password', self.gf('django.db.models.fields.CharField')(default='', max_length=64)),
        ))
        db.send_create_signal('django_ucengine', ['UCEngineCredentials'])

        # Adding model 'UCEngineProfile'
        db.create_table('django_ucengine_ucengineprofile', (
            ('ucenginecredentials_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['django_ucengine.UCEngineCredentials'], unique=True, primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.OneToOneField')(related_name='ucengine_profile', unique=True, to=orm['auth.User'])),
        ))
        db.send_create_signal('django_ucengine', ['UCEngineProfile'])


    def backwards(self, orm):
        # Deleting model 'UCEngineCredentials'
        db.delete_table('django_ucengine_ucenginecredentials')

        # Deleting model 'UCEngineProfile'
        db.delete_table('django_ucengine_ucengineprofile')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'django_ucengine.ucenginecredentials': {
            'Meta': {'object_name': 'UCEngineCredentials'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ucengine_password': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '64'}),
            'ucengine_uid': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '64', 'null': 'True', 'blank': "''"})
        },
        'django_ucengine.ucengineprofile': {
            'Meta': {'object_name': 'UCEngineProfile', '_ormbases': ['django_ucengine.UCEngineCredentials']},
            'ucenginecredentials_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['django_ucengine.UCEngineCredentials']", 'unique': 'True', 'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'ucengine_profile'", 'unique': 'True', 'to': "orm['auth.User']"})
        }
    }

    complete_apps = ['django_ucengine']