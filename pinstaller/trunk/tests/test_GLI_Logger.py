"""
# Copyright 1999-2005 Gentoo Foundation
# This source code is distributed under the terms of version 2 of the GNU
# General Public License as published by the Free Software Foundation, a copy
# of which can be found in the main directory of this project.
Gentoo Linux Installer Test Suite
$Header: /var/cvsroot/gentoo/src/installer/src/tests/test_GLI_Logger.py,v 1.2 2005/08/22 18:35:52 codeman Exp $
"""

import unittest
import os
import GLILogger

class test_GLILogger (unittest.TestCase):

	def setUp(self):
		self.failUnless(os.path.exists("GLILogger.py"), "Please run tests from src")

	def testInstantiate(self):
		logger = GLILogger.Logger.shared_logger();

		self.failUnless(logger, "Could not get shared logger");

	def testLogMessage(self):
		logger = GLILogger.Logger.shared_logger();

		self.failUnless(logger, "Could not get shared logger");

		logger.log("Test log message one.")

	def testMark(self):
		logger = GLILogger.Logger.shared_logger();

		self.failUnless(logger, "Could not get shared logger");

		logger.mark()

if __name__ == '__main__':
	unittest.main()
