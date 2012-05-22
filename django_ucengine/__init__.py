# -*- coding: utf-8 -*-
from django.conf import settings
# TODO implement post_delete signal handler
from django.db.models.signals import post_save, post_delete, m2m_changed
from django.contrib.auth.models import User as DjangoUser
from django.contrib.auth.models import Group
from django.contrib.auth.signals import user_logged_in
from django.contrib.auth.signals import user_logged_out
from django.dispatch import receiver
from ucengine import UCEngine, User as UCUser
import uuid
from django_ucengine.models import UCEngineProfile

DEFAULT_GROUP = getattr(settings, "DEFAULT_GROUP", "participant")

from django.contrib.auth.models import SiteProfileNotAvailable

import logging
_logger = logging.getLogger('coecms.Logger')

def _genPassword():
    return "%s"%uuid.uuid4()

def _get_or_create_profile(instance, created=False):
    """
    Tries to get your own profile, otherwise gets or creates a UCEngineProfile instance
    """
    try:
        return instance.get_profile()
    except SiteProfileNotAvailable, profexc:
        _logger.error("%s"%profexc)
        return UCEngineProfile.objects.get_or_create(user=instance)[0]

def _sync_user_credentials(rootsession, djangouser, sync=True):
    """
    finds or creates the ucengine user with a fresh credentials
    """
    status, result = rootsession.find_user_by_name(djangouser.username)
    if status == 200:
        uid = result['result']['uid']
    else:
        uid=None
    ucengineuser = UCUser(djangouser.username, uid=uid, credential=_genPassword(), auth="password")
    # writes the new credential to the django user
    if sync is True:
        profile = _get_or_create_profile(djangouser)
        profile.save_ucengine_user(uid, ucengineuser.credential)
        profile.save()
    try:
        rootsession.save(ucengineuser)
    except Exception, exc:
        _logger.error("unable to save UCEngine user : %s"%exc)
    return ucengineuser

def _copy_metadata(rootsession, djangouser):
    """
    Sync django profile with ucengine user metadata
    """
    status, result = rootsession.find_user_by_name(djangouser.username)
    if status == 200:
        ucengineuser = UCUser(result['result']['name'],
            uid=result['result']['uid'],
            metadata=result['result']['metadata'],
            auth=result['result']['auth'])
    else:
        ucengineuser = UCUser(djangouser.username)
    try:
        ucengineuser.metadata.update(djangouser.__dict__)
        profile = _get_or_create_profile(djangouser)
        ucengineuser.credential=profile.get_ucenginepassword()
        ucengineuser.metadata.update(profile.__dict__)
        groups = ["%s"%group for group in djangouser.groups.all()]
        if DEFAULT_GROUP not in groups:
            groups += [DEFAULT_GROUP]
        ucengineuser.metadata['groups'] = ",".join(groups)
        if '_state' in ucengineuser.metadata:
            del ucengineuser.metadata['_state']
        if '_user_cache' in ucengineuser.metadata:
            del ucengineuser.metadata['_user_cache']
        if '_profile_cache' in ucengineuser.metadata:
            del ucengineuser.metadata['_profile_cache']
    except Exception, exc:
        _logger.error("errror copying user %s metadata %s"%(djangouser.username,exc))
        pass
    # writes the updated UCUser to UCEngine database
    try:
        rootsession.save(ucengineuser)
    except Exception, err:
        _logger.error("error saving UCUser : %s"%err)
    return ucengineuser

def _add_default_group(instance):
    if not instance.groups.filter(name__exact=DEFAULT_GROUP):
        try:
            default_group_instance = Group.objects.get(name=DEFAULT_GROUP)
            instance.groups.add(default_group_instance)
        except Exception, exc:
            _logger.warn("%s"%exc)

@receiver(post_save, sender=DjangoUser, dispatch_uid="ucengine_connect.__init__")
def post_save_user(sender, instance, created=None, **kwargs):
    """
    creates the BaseUSerProfile after every User creation of if it does not exists
    then updates ucengine user metadata
    """
    _add_default_group(instance)
    rootsession = UCEngine(settings.UCENGINE['host'], settings.UCENGINE['port'])\
            .connect(UCUser(settings.UCENGINE['user']), credential=settings.UCENGINE['pwd'])
    _get_or_create_profile(instance, created)
    _sync_user_credentials(rootsession, instance, sync=True)
    ucengineuser = _copy_metadata(rootsession, instance)
    rootsession.add_user_role(ucengineuser.uid, DEFAULT_GROUP, '')

@receiver(m2m_changed, sender=DjangoUser.groups.through)
def post_changed_groups(sender, instance, action, **kwargs):
    rootsession = UCEngine(settings.UCENGINE['host'], settings.UCENGINE['port'])\
            .connect(UCUser(settings.UCENGINE['user']), credential=settings.UCENGINE['pwd'])
    if action == "pre_clear" or action == "pre_remove":
        _delete_ucengine_roles(rootsession, instance)
    if action == "post_add":
        _add_ucengine_roles(rootsession, instance)
    rootsession.close()

def _delete_ucengine_roles(rootsession, instance):
    """ delete all django groups to uce user roles """
    status, result = rootsession.find_user_by_name(instance.username)
    if status == 200:
        uid=result['result']['uid']
        for grp in instance.groups.all():
            groupname = "%s"%grp
            try:
                rootsession.delete_user_role(uid, groupname, "")
            except Exception, exc:
                _logger.error("ucengine_connect._delete_ucengine_roles() failed %s"%exc)
        _copy_metadata(rootsession, instance)
    else:
        _logger.warning("Could not delete uce roles on unexistent user")

def _add_ucengine_roles(rootsession, instance):
    """ add all django groups to uce user roles """
    status, result = rootsession.find_user_by_name(instance.username)
    if status == 200:
        uid=result['result']['uid']
        for grp in instance.groups.all():
            groupname = "%s"%grp
            try:
                rootsession.add_user_role(uid, groupname, "")
            except Exception, exc:
                _logger.error("ucengine_connect._add_ucengine_roles() failed %s"%exc)
        _copy_metadata(rootsession, instance)
    else:
        _logger.warning("Could not add uce roles on unexistent user")

@receiver(user_logged_in)
def createUCEngineSession(sender, **kwargs):
    """
    override the user's UCEngine's password
    uses a random/unique password
    stores it in into the user's Django's session

    sender = Signal()
    kwargs = {'request': Request(), 'user': User()}
    """
    djangouser = kwargs['user']
    if djangouser is not None:
        rootsession = UCEngine(settings.UCENGINE['host'], settings.UCENGINE['port'])\
            .connect(UCUser(settings.UCENGINE['user']), credential=settings.UCENGINE['pwd'])
        _sync_user_credentials(rootsession, djangouser, sync=True)
        _copy_metadata(rootsession, djangouser)
        rootsession.close()

@receiver(user_logged_out)
def destroyUCEngineSession(sender, **kwargs):
    """
    override the user's UCEngine's password
    uses a random/unique password different from the one already in the profile

    sender = Signal()
    kwargs = {'request': Request(), 'user': User()}
    """  
    djangouser = kwargs['user']
    if djangouser is not None:
        rootsession = UCEngine(settings.UCENGINE['host'], settings.UCENGINE['port'])\
            .connect(UCUser(settings.UCENGINE['user']), credential=settings.UCENGINE['pwd'])
        _sync_user_credentials(rootsession, djangouser, sync=False)
        rootsession.close()
