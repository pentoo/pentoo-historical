# Copyright 1999-2005 Gentoo Foundation
# This source code is distributed under the terms of version 2 of the GNU
# General Public License as published by the Free Software Foundation, a copy
# of which can be found in the main directory of this project.

import unittest
import os
import GLIInstallProfile
import GLIInstallTemplate
import GLILogger
import GLIClientController
import GLIClientConfiguration
import GLIUtility
from GLIClientConfiguration import ClientConfiguration

config = ClientConfiguration()

class test_GLIInstall (unittest.TestCase):

	def setUp(self):
		self.failUnless(os.path.exists("GLITestInstallScript.py"), "Please run tests from src")
		self.failUnless(os.path.exists("GLIInstallTemplate.py"), "Please run tests from src")

	def testTheLogger(self):
		logger = GLILogger.Logger.shared_logger();
		self.failUnless(logger, "Could not get shared logger");
		logger.log("Test log message one.")
		logger.mark()
		
	def testCLIENTCONTROLLER(self):
		logger = GLILogger.Logger.shared_logger();
		self.failUnless(logger, "Could not get shared logger");	
		logger.mark()
		logger.log("Starting the client configuration.")
		print "Starting the client configuration."
		configuration = GLIClientConfiguration.ClientConfiguration()
		configuration.parse('./laptop.config.xml')
		controller = GLIClientController.GLIClientController(configuration)
		logger.log("Controller Instantiated.  Setting root password.")
		print "Controller Instantiated.  Setting root password."
		controller.set_root_passwd()
		
		logger.log("Now configuring the networking (pre) of the livecd")
		print "Now configuring the networking (pre) of the livecd"
		controller.configure_networking()
		
		logger.log("Now startign up SSH if you have it enabled during the install.")
		print "Now startign up SSH if you have it enabled during the install."
		controller.enable_ssh()
if __name__ == '__main__':
	unittest.main()
