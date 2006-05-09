"""
# Copyright 1999-2005 Gentoo Foundation
# This source code is distributed under the terms of version 2 of the GNU
# General Public License as published by the Free Software Foundation, a copy
# of which can be found in the main directory of this project.
Gentoo Linux Installer Test Suite
$Header: /var/cvsroot/gentoo/src/installer/src/tests/test_GLI_InstallProfile.py,v 1.5 2005/08/22 18:35:52 codeman Exp $
"""

import unittest
import os
import GLIInstallProfile

class test_GLIInstallProfile (unittest.TestCase):

	def setUp(self):
		self.failUnless(os.path.exists("GLIInstallProfile.py"), "Please run tests from src")

	def testInstantiate(self):
		profile = GLIInstallProfile.InstallProfile();

		self.failUnless(profile, "Could not instantiate InstallProfile");

	def testParse(self):
		profile = GLIInstallProfile.InstallProfile()

		self.failUnless(profile, "Could not instantiate InstallProfile");

		path = os.getcwd()
		path = os.path.join(path, "tests", "gli_test_profile.xml")

		profile.parse("file://" + path)

		self.assertEquals(profile.get_time_zone(), "GMT")

if __name__ == '__main__':
	unittest.main()
