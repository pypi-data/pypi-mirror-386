# -*- coding: utf-8 -*-
"""Setup tests for this package."""
from imio.patterns import HAS_PLONE_5_AND_MORE
from imio.patterns.testing import IMIO_PATTERNS_INTEGRATION_TESTING  # noqa: E501
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID

import unittest

try:
    from Products.CMFPlone.utils import get_installer
except ImportError:
    get_installer = None


class TestSetup(unittest.TestCase):
    """Test that imio.patterns is properly installed."""

    layer = IMIO_PATTERNS_INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer['portal']
        if not HAS_PLONE_5_AND_MORE:
            self.installer = api.portal.get_tool('portal_quickinstaller')
        else:
            self.installer = get_installer(self.portal, self.layer["request"])

    def test_product_installed(self):
        """Test if imio.patterns is installed with portal_quickinstaller."""
        if not HAS_PLONE_5_AND_MORE:
            self.assertTrue(self.installer.isProductInstalled('imio.patterns'))
        else:
            self.assertTrue(self.installer.is_product_installed('imio.patterns'))

    def test_browserlayer(self):
        """Test that IImioPatternsLayer is registered."""
        from imio.patterns.interfaces import (
            IImioPatternsLayer)
        from plone.browserlayer import utils
        self.assertIn(
            IImioPatternsLayer,
            utils.registered_layers())


class TestUninstall(unittest.TestCase):

    layer = IMIO_PATTERNS_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        roles_before = api.user.get_roles(TEST_USER_ID)
        if not HAS_PLONE_5_AND_MORE:
            self.installer = api.portal.get_tool('portal_quickinstaller')
            self.installer.uninstallProducts(['imio.patterns'])
        else:
            self.installer = get_installer(self.portal, self.layer["request"])
            self.installer.uninstall_product('imio.patterns')
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        setRoles(self.portal, TEST_USER_ID, roles_before)

    def test_product_uninstalled(self):
        """Test if imio.patterns is cleanly uninstalled."""
        if not HAS_PLONE_5_AND_MORE:
            self.assertFalse(self.installer.isProductInstalled('imio.patterns'))
        else:
            self.assertFalse(self.installer.is_product_installed('imio.patterns'))

    def test_browserlayer_removed(self):
        """Test that IImioPatternsLayer is removed."""
        from imio.patterns.interfaces import \
            IImioPatternsLayer
        from plone.browserlayer import utils
        self.assertNotIn(
            IImioPatternsLayer,
            utils.registered_layers())
