# -*- coding: utf-8 -*-
"""Init and utils."""
from plone import api
from zope.i18nmessageid import MessageFactory


_ = MessageFactory('imio.patterns')
HAS_PLONE_5_AND_MORE = int(api.env.plone_version()[0]) >= 5
