# -*- coding: utf-8 -*-
from django.conf import settings

def ucengine(request):
    '''
    This context processor adds ucengine API config
    '''
    return { 'ucengine': settings.UCENGINE_API }
