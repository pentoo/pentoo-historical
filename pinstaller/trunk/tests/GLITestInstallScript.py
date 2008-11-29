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
		
	def testINSTALL(self):
	#Lets start by instantiating our objects.
		logger = GLILogger.Logger.shared_logger();
		profile = GLIInstallProfile.InstallProfile()
		logger.log("Instantiated Profile")
		
		path = os.getcwd()
		path = os.path.join(path, "", "mytest.xml")
		profile.parse("file://" + path)
		logger.log("Profile parsed")
		
		template = GLIInstallTemplate.GLIInstallTemplate(profile,config);
		logger.log("Template Instantiated.  This means the profile is there, not the clientconfig")
		print "Welcome to this fake gentoo installer.  As you may yourself presently be aware of, my grammer sucks."
	#User should be prompted whether to install kernel modules not autodetected.
		
				
		template.partition_local_devices()
		
		logger.log( "Next comes the MAGIC partitioner.  I have no idea how this is going to work, but lets just assume for a second that it has done it's job correctly.")
		print "Next comes the MAGIC partitioner.  I have no idea how this is going to work, but lets just assume for a second that it has done it's job correctly."
		print "You should also mount the local partitions now."
#		GLIUtility.spawn_bash()
		
		template.mount_local_partitions()
		logger.log( "The profile should know the partition root is on.  For this demo all is assumed mounted.")
		print "The profile should know the partition root is on.  For this demo all is assumed mounted."
		
		template.mount_network_shares()
		logger.log( "If we had network shares to mount, they would have been mounted by now.")
		print "If we had network shares to mount, they would have been mounted by now."
		
		template.unpack_tarball()
		logger.log( "The tarball has now been fetched and unpacked in the chroot dir.")
		print "The tarball has now been fetched and unpacked in the chroot dir."
		
#		template.prepare_chroot()
		logger.log( "So lets go ahead and prepare that chroot.")
		print "So lets go ahead and prepare that chroot."
		
		logger.log( "5.e Configuring the Compile Options")
		template.configure_make_conf()
		logger.log( "/etc/make.conf should be good now.")
		print "/etc/make.conf should be good now."
		
		template.configure_fstab()
		logger.log( "Though out of the Template order, now would be a good time to configure /etc/fstab!")
		print "Though out of the Template order, now would be a good time to configure /etc/fstab!"
#		GLIUtility.spawn_bash()
		
		template.install_portage_tree()
		template.prepare_chroot()
		logger.log( "Portage tree has been updated (probably by emerge sync).")

		print "Portage tree has been updated (probably by emerge sync).  Now to bootstrap"

		template.bootstrap()
		logger.log( "Even if doing a stage 3, should run this bootstrap step.  It will do nothing for stage3 ppl.")
		logger.log( "System is at stage2")
		print "System is at stage2"
		
		template.emerge_system()
		logger.log( "Emerge system complete. System is at stage3.")
		print "Emerge system complete. System is at stage3."
		
		template.set_timezone()
		logger.log( "Yeah, we gotta do the stupid stuff like setting the timezone too.")
		print "Yeah, we gotta do the stupid stuff like setting the timezone too."
		
		template.emerge_kernel_sources()
		logger.log( "Kernel sources of your choice have been emerged.")
		print "Kernel sources of your choice have been emerged.  Now for the kernel"
		
		logger.log( "In an ideal world we'd now build the kernel using genkernel with a magic configuration somewhere.")
		logger.log( "Insert prompt here incase user is 1337 and likes to compile their own kernel")
		template.build_kernel()
		logger.log( "ADD hotplug supposedly here! and maybe offer prompt for extra kernel modules")
		logger.log( "where do the modules go?  do they get autodetected?")
		
		logger.log( "Now we're in the end-game.  Almost done!")
		print "Now we're in the end-game.  Almost done!"
		template.install_logging_daemon()
		logger.log( "Just have to install the logging daemon.")
		template.install_cron_daemon()
		logger.log( "cron daemon,")
		template.install_filesystem_tools
		logger.log( "and filesystem tools.")
		
		print "now to setup the post network info:"
		logger.log( "now to setup the post network info:")
		template.setup_network_post()
		
		#logger.log( "skipping bootloader.  too dangerous to mess w/ that")
		template.install_bootloader()
		logger.log( "Hopefully the bootloader has been installed.")
		print "Hopefully the bootloader has been installed."
		
		template.update_config_files()
		logger.log( "Config files updated.  Show me potato salad!")
		
		template.configure_rc_conf()
		logger.log( "/etc/rc.conf edited.  for things like clock local and use xdm")
		
		logger.log( "set root password here. create users.  I don't think this is stable enough to test.")
		
		template.unmount_devices()
		logger.log( "unmount and reboot.  If you say that's what she said one more time...")
		
		logger.log( "Forgot the step to install services.  like xdm, xfs, sshd")
		logger.log( "That's all folks.  If you actually see this, i'm impressed.")
		print "That's all folks.  If you actually see this, i'm impressed."
		
if __name__ == '__main__':
	unittest.main()
