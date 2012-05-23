# -*- coding: utf-8 -*-
from django.db import models
from django.contrib.auth.models import User


class UCEngineCredentials(models.Model):
    """
    Extend your custom User profile with this class
    to integrate UCEngine API credentials to your Users' DB
    """
    ucengine_uid = models.CharField(max_length=64, default="", null=True, blank="", editable=False)
    ucengine_password = models.CharField(max_length=64, default="", editable=False)

    def save_ucengine_user(self, uid, password):
        self.ucengine_uid = uid
        self.ucengine_password = password
        self.save()

    def get_ucengine_user(self):
        return self.ucengine_uid, self.ucengine_password
    
    def get_ucengineuid(self):
        return self.ucengine_uid
    
    def get_ucenginepassword(self):
        return self.ucengine_password


class UCEngineProfile(UCEngineCredentials):
    """
    Default User profile
    """
    user = models.OneToOneField(User, verbose_name='Attached User', related_name='ucengine_connect_profile')
