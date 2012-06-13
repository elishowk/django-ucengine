# -*- coding: utf-8 -*-
from django.conf import settings
# TODO implement post_delete signal handler
from django.db.models.signals import post_save, post_delete, m2m_changed
from django.db.models import get_model
from django.contrib.auth.models import User as DjangoUser
from django.contrib.auth.models import Group
from django.contrib.auth.signals import user_logged_in
from django.contrib.auth.signals import user_logged_out
from django.dispatch import receiver
from ucengine import UCEngine, User as UCUser
import uuid
from hashlib import md5
from django_ucengine.models import UCEngineProfile

DEFAULT_GROUP = getattr(settings, "DEFAULT_GROUP", "participant")
UCENGINE = getattr(settings, "UCENGINE",\
        {'host': 'http://localhost', 'port':8000,\
        'user': 'djangobrick', 'pwd': ''})

import logging
_logger = logging.getLogger('coecms.Logger')


def get_profile_model():
    """
    Return the model class for the currently-active user profile
    model, as defined by the ``AUTH_PROFILE_MODULE`` setting.
    If AUTH_PROFILE_MODULE does not exist, returns the default UCEngineProfile
    Inspired from django-userena

    :return: The model that is used as profile.

    """
    if (not hasattr(settings, 'AUTH_PROFILE_MODULE')) or \
           (not settings.AUTH_PROFILE_MODULE):
        return UCEngineProfile

    profile_mod = get_model(*settings.AUTH_PROFILE_MODULE.split('.'))
    if profile_mod is None:
        return UCEngineProfile
    return profile_mod


def _gen_password():
    """
    Auto generated passwords for UCEngine users
    Valid only for one session
    """
    return "%s"%uuid.uuid4()


def _get_or_create_profile(instance, created=False):
    """
    Tries to get your own profile, otherwise gets or creates a UCEngineProfile instance
    """
    profile_model = get_profile_model()
    try:
        return instance.get_profile()
    except profile_model.DoesNotExist, exc:
        new_profile = profile_model(user=instance)
        new_profile.save()
        return new_profile


def _add_default_group(instance):
    """
    Adds DEFAULT_GROUP to User's Group
    """
    if not instance.groups.filter(name__exact=DEFAULT_GROUP):
        try:
            default_group_instance = Group.objects.get(name=DEFAULT_GROUP)
            instance.groups.add(default_group_instance)
        except Exception, exc:
            logging.error(exc)
            return

def find_user_by_name(rootsession, djangouser):
    """
    Common method fetching a UCE User instance
    """
    status, result = rootsession.find_user_by_name(djangouser.username)
    if status == 200:
        ucengineuser = UCUser(result['result']['name'],
            uid=result['result']['uid'],
            metadata=result['result']['metadata'],
            auth=result['result']['auth'])
    else:
        ucengineuser = UCUser(djangouser.username, auth="password")
    return ucengineuser


def _sync_user_credentials(rootsession, djangouser, sync=True, created=False, ucengineuser=None):
    """
    finds or creates the ucengine user with a fresh credentials
    """
    if ucengineuser is None:
        ucengineuser = find_user_by_name(rootsession, djangouser)
        ucengineuser.credential= _gen_password()
    # writes the new credentials to the django user
    if sync is True:
        profile = _get_or_create_profile(djangouser, created)
        profile.save_ucengine_user(ucengineuser.uid, ucengineuser.credential)
        profile.save()
    _copy_metadata(rootsession, djangouser, created=False, ucengineuser=ucengineuser)
    return ucengineuser

def _obfuscate_user(ucengineuser):
    """
    Cleans User data
    """
    if 'password' in ucengineuser.metadata:
        del ucengineuser.metadata['password']
    if '_state' in ucengineuser.metadata:
        del ucengineuser.metadata['_state']
    if '_user_cache' in ucengineuser.metadata:
        del ucengineuser.metadata['_user_cache']
    if '_profile_cache' in ucengineuser.metadata:
        del ucengineuser.metadata['_profile_cache']
    if 'email' in ucengineuser.metadata:
        md5hash = md5()
        cleandemail = ucengineuser.metadata['email'].strip()
        md5hash.update(cleandemail.lower())
        ucengineuser.metadata['md5'] = md5hash.hexdigest()
        del ucengineuser.metadata['email']
    else:
        ucengineuser.metadata['md5'] = ""
    return ucengineuser

def _copy_metadata(rootsession, djangouser, created=False, ucengineuser=None):
    """
    Copies django user's profile to ucengine user's metadata
    """
    if ucengineuser is None:
        ucengineuser = find_user_by_name(rootsession, djangouser)
    try:
        ucengineuser.metadata.update(djangouser.__dict__)
        profile = _get_or_create_profile(djangouser, created)
        ucengineuser.credential = profile.get_ucenginepassword()
        ucengineuser.metadata.update(profile.__dict__)
        groups = ["%s"%group for group in djangouser.groups.all()]
        if DEFAULT_GROUP not in groups:
            groups += [DEFAULT_GROUP]
        ucengineuser.metadata['groups'] = ",".join(groups)
        ucengineuser = _obfuscate_user(ucengineuser)
    except Exception, exc:
        logging.error("errror copying user %s metadata %s"%(djangouser.username,exc))
        pass
    # writes the updated UCUser to UCEngine database
    try:
        rootsession.save(ucengineuser)
    except Exception, err:
        logging.error("error saving UCUser : %s"%err)
    return ucengineuser


@receiver(post_save, sender=DjangoUser, dispatch_uid="django_ucengine.__init__")
def post_save_user(sender, instance, created=None, **kwargs):
    """
    updates User's profile after every save operation
    then POST to ucengine the new user's metadata
    """
    rootsession = UCEngine(UCENGINE['host'], UCENGINE['port'])\
            .connect(UCUser(UCENGINE['user']), credential=UCENGINE['pwd'])
    ucengineuser = _sync_user_credentials(rootsession, instance, sync=True, created=created)

@receiver(m2m_changed, sender=DjangoUser.groups.through, dispatch_uid="django_ucengine.__init__.post_changed_groups")
def post_changed_groups(sender, instance, action, **kwargs):
    """
    Updated UCengine roles depending on Django's groups
    """
    rootsession = UCEngine(UCENGINE['host'], UCENGINE['port'])\
            .connect(UCUser(UCENGINE['user']), credential=UCENGINE['pwd'])
    if action == "pre_clear" or action == "pre_remove":
        _delete_ucengine_roles(rootsession, instance)
    if action == "post_add":
        _add_ucengine_roles(rootsession, instance)
    rootsession.close()

def _delete_ucengine_roles(rootsession, instance, ucengineuser=None):
    """ delete all django groups to uce user roles """
    if ucengineuser is None:
        ucengineuser = find_user_by_name(rootsession, instance)
    uid=ucengineuser.uid
    _add_default_group(instance)
    for grp in instance.groups.all():
        groupname = "%s"%grp
        try:
            rootsession.delete_user_role(uid, groupname, "")
        except Exception, exc:
            logging.error("_delete_ucengine_roles() failed %s"%exc)
    _copy_metadata(rootsession, instance, ucengineuser=ucengineuser)

def _add_ucengine_roles(rootsession, instance, ucengineuser=None):
    """ add all django groups to uce user roles """
    if ucengineuser is None:
        ucengineuser = find_user_by_name(rootsession, instance)
    uid=ucengineuser.uid
    _add_default_group(instance)
    for grp in instance.groups.all():
        groupname = "%s"%grp
        try:
            rootsession.add_user_role(uid, groupname, "")
        except Exception, exc:
            logging.error("_add_ucengine_roles() failed %s"%exc)
    _copy_metadata(rootsession, instance, ucengineuser=ucengineuser)

@receiver(user_logged_in, dispatch_uid="django_ucengine.__init__.createUCEngineSession")
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
        rootsession = UCEngine(UCENGINE['host'],\
            UCENGINE['port'])\
            .connect(UCUser(UCENGINE['user']),\
            credential=UCENGINE['pwd'])
        _sync_user_credentials(rootsession, djangouser, sync=True, created=False)
        rootsession.close()

@receiver(user_logged_out, dispatch_uid="django_ucengine.__init__.destroyUCEngineSession")
def destroyUCEngineSession(sender, **kwargs):
    """
    override the user's UCEngine's password
    uses a random/unique password different from the one already in the profile

    sender = Signal()
    kwargs = {'request': Request(), 'user': User()}
    """  
    djangouser = kwargs['user']
    if djangouser is not None:
        rootsession = UCEngine(UCENGINE['host'],\
            UCENGINE['port'])\
            .connect(UCUser(UCENGINE['user']),\
            credential=UCENGINE['pwd'])
        _sync_user_credentials(rootsession, djangouser, sync=False, created=False)
        rootsession.close()
