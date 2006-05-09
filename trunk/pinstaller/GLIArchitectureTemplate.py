"""
# Copyright 1999-2005 Gentoo Foundation
# This source code is distributed under the terms of version 2 of the GNU
# General Public License as published by the Free Software Foundation, a copy
# of which can be found in the main directory of this project.
Gentoo Linux Installer

$Id: GLIArchitectureTemplate.py,v 1.277 2006/05/09 12:16:52 agaffney Exp $

The ArchitectureTemplate is largely meant to be an abstract class and an 
interface (yes, it is both at the same time!). The purpose of this is to create 
subclasses that populate all the methods with working methods for that architecture. 
The only definitions that are filled in here are architecture independent. 

"""

import GLIUtility, GLILogger, os, string, sys, shutil, re, time
import GLIPortage
from GLIException import *

class ArchitectureTemplate:
	##
	# Initialization of the ArchitectureTemplate.  Called from some other arch template.
	# @param selfconfiguration=None    A Client Configuration
	# @param install_profile=None      An Install Profile
	# @param client_controller=None    Client Controller.  not same as configuration.
	def __init__(self,configuration=None, install_profile=None, client_controller=None):
		self._client_configuration = configuration
		self._install_profile = install_profile
		self._cc = client_controller

		# This will get used a lot, so it's probably
		# better to store it in a variable than to call
		# this method 100000 times.
		self._chroot_dir = self._client_configuration.get_root_mount_point()
		self._logger = GLILogger.Logger(self._client_configuration.get_log_file())
		self._compile_logfile = "/tmp/compile_output.log"
		self._debug = self._client_configuration.get_verbose()

		self._portage = GLIPortage.GLIPortage(self._chroot_dir, self._install_profile.get_grp_install(), self._logger, self._debug, self._cc, self._compile_logfile)

		# This will cleanup the logfile if it's a dead link (pointing
		# to the chroot logfile when partitions aren't mounted, else
		# no action needs to be taken

		if os.path.islink(self._compile_logfile) and not os.path.exists(self._compile_logfile):
			os.unlink(self._compile_logfile)

		# cache the list of successfully mounted swap devices here
		self._swap_devices = []

		# These must be filled in by the subclass. _steps is a list of
		# functions, that will carry out the installation. They must be
		# in order.
		#
		# For example, self._steps might be: [preinstall, stage1, stage2, stage3, postinstall],
		# where each entry is a function (with no arguments) that carries out the desired actions.
		# Of course, steps will be different depending on the install_profile
		
		self._architecture_name = "generic"
		self._install_steps = [
			{ 'function': self.partition, 'name': "Partition", 'modes': ("normal", "stage4") },
			{ 'function': self.mount_local_partitions, 'name': "Mount local partitions", 'modes': ("normal", "stage4") },
			{ 'function': self.mount_network_shares, 'name': "Mount network (NFS) shares", 'modes': ("normal", "stage4") },
			{ 'function': self.unpack_stage_tarball, 'name': "Unpack stage tarball", 'modes': ("normal", "stage4", "chroot") },
			{ 'function': self.update_config_files, 'name': "Updating config files", 'modes': ("normal", "chroot") },
			{ 'function': self.configure_make_conf, 'name': "Configure /etc/make.conf", 'modes': ("normal", "chroot") },
			{ 'function': self.prepare_chroot, 'name': "Preparing chroot", 'modes': ("normal", "stage4", "chroot") },
			{ 'function': self.install_portage_tree, 'name': "Syncing the Portage tree", 'modes': ("normal", "chroot") },
			{ 'function': self.stage1, 'name': "Performing bootstrap", 'modes': ("normal", "chroot") },
			{ 'function': self.stage2, 'name': "Performing 'emerge system'", 'modes': ("normal", "chroot") },
			{ 'function': self.set_root_password, 'name': "Set the root password", 'modes': ("normal", "chroot") },
			{ 'function': self.set_timezone, 'name': "Setting timezone", 'modes': ("normal", "chroot") },
			{ 'function': self.emerge_kernel_sources, 'name': "Emerge kernel sources", 'modes': ("normal", "chroot") },
			{ 'function': self.build_kernel, 'name': "Building kernel", 'modes': ("normal", "chroot") },
			{ 'function': self.install_distcc, 'name': "Install distcc", 'modes': ("normal", "chroot") },
			{ 'function': self.install_mta, 'name': "Installing MTA", 'modes': ("normal", "chroot") },
			{ 'function': self.install_logging_daemon, 'name': "Installing system logger", 'modes': ("normal", "chroot") },
			{ 'function': self.install_cron_daemon, 'name': "Installing Cron daemon", 'modes': ("normal", "chroot") },
			{ 'function': self.install_filesystem_tools, 'name': "Installing filesystem tools", 'modes': ("normal", "chroot") },
			{ 'function': self.setup_network_post, 'name': "Configuring post-install networking", 'modes': ("normal", "chroot") },
			{ 'function': self.install_bootloader, 'name': "Configuring and installing bootloader", 'modes': ("normal", "chroot") },
			{ 'function': self.setup_and_run_bootloader, 'name': "Setting up and running bootloader", 'modes': ( "normal", "stage4") },
			{ 'function': self.update_config_files, 'name': "Re-Updating config files", 'modes': ("normal", "chroot") },
#			{ 'function': self.configure_rc_conf, 'name': "Updating /etc/rc.conf", 'modes': ("normal", "stage4", "chroot") },
			{ 'function': self.set_users, 'name': "Add additional users.", 'modes': ("normal", "chroot") },
			{ 'function': self.install_packages, 'name': "Installing additional packages.", 'modes': ("normal", "chroot") },
			# services for startup need to come after installing extra packages
			# otherwise some of the scripts will not exist.
			{ 'function': self.set_services, 'name': "Setting up services for startup", 'modes': ("normal", "chroot") },
			{ 'function': self.run_post_install_script, 'name': "Running custom post-install script", 'modes': ("normal", "stage4", "chroot") },
			{ 'function': self.finishing_cleanup, 'name': "Cleanup and unmounting local filesystems.", 'modes': ("normal", "stage4", "chroot") }
		]


	##
	# Returns the steps and their comments in an array
	def get_install_steps(self):
		return self._install_steps

	##
	# Tells the frontend something
	# @param type type of data
	# @param data the data itself.  usually a number.
	def notify_frontend(self, type, data):
		self._cc.addNotification(type, data)

	# It is possible to override these methods in each Arch Template.
	# It might be necessary to do so, if the arch needs something 'weird'.

	##
	# Private function to add a /etc/init.d/ script to the given runlevel in the chroot environement
	# @param script_name the script to be added
	# @param runlevel="default" the runlevel to add to
	def _add_to_runlevel(self, script_name, runlevel="default"):
		if not GLIUtility.is_file(self._chroot_dir + '/etc/init.d/' + script_name):
			#raise GLIException("RunlevelAddError", 'fatal', '_add_to_runlevel', "Failure adding " + script_name + " to runlevel " + runlevel + "!")
			#This is not a fatal error.  If the init script is important it will exist.
			self._logger.log("ERROR! Failure adding " + script_name + " to runlevel " + runlevel + " because it was not found!")
			if self._debug:	self._logger.log("DEBUG: running rc-update add " + script_name + " " + runlevel + " in chroot.")
		status = GLIUtility.spawn("rc-update add " + script_name + " " + runlevel, display_on_tty8=True, chroot=self._chroot_dir, logfile=self._compile_logfile, append_log=True)
		if not GLIUtility.exitsuccess(status):
			#raise GLIException("RunlevelAddError", 'fatal', '_add_to_runlevel', "Failure adding " + script_name + " to runlevel " + runlevel + "!")
			#Again, an error here will not prevent a new system from booting.  But it is important to log the error.
			self._logger.log("ERROR! Could not add " + script_name + " to runlevel " + runlevel + ". returned a bad status code.")
		else:
			self._logger.log("Added "+script_name+" to runlevel "+runlevel)

	##
	# Private Function.  Will return a list of packages to be emerged for a given command.  Not yet used.
	# @param cmd full command to run ('/usr/portage/scripts/bootstrap.sh --pretend' or 'emerge -p system')
	def _get_packages_to_emerge(self, cmd):
		if self._debug:	self._logger.log("DEBUG: _get_packages_to_emerge() called with '%s'" % cmd)
		return GLIUtility.spawn(cmd + r" 2>/dev/null | grep -e '\[ebuild' | sed -e 's:\[ebuild .\+ \] ::' -e 's: \[.\+\] ::' -e 's: \+$::'", chroot=self._chroot_dir, return_output=True)[1].strip().split("\n")

	##
	# Private Function.  Will emerge a given package in the chroot environment.
	# @param package package to be emerged
	# @param binary=False defines whether to try a binary emerge (if GRP this gets ignored either way)
	# @param binary_only=False defines whether to only allow binary emerges.
	def _emerge(self, package, binary=True, binary_only=False):
		#Error checking of this function is to be handled by the parent function.
#		self._logger.log("_emerge() called with: package='%s', binary='%s', binary_only='%s', grp_install='%s'" % (package, str(binary), str(binary_only), str(self._install_profile.get_grp_install())))
		# now short-circuit for GRP
		if self._install_profile.get_grp_install():
			cmd="emerge -k " + package
		# now normal installs
		else:
			if binary_only:
				cmd="emerge -K " + package
			elif binary:
				cmd="emerge -k " + package
			else:
				cmd="emerge " + package

		self._logger.log("Calling emerge: "+cmd)
		return GLIUtility.spawn(cmd, display_on_tty8=True, chroot=self._chroot_dir, logfile=self._compile_logfile, append_log=True)

	##
	# Private Function.  Will edit a config file and insert a value or two overwriting the previous value
	# (actually it only just comments out the old one)
	# @param filename 			file to be edited
	# @param newvalues 			a dictionary of VARIABLE:VALUE pairs
	# @param delimeter='=' 			what is between the key and the value
	# @param quotes_around_value=True 	whether there are quotes around the value or not (ex. "local" vs. localhost)
	# @param only_value=False		Ignore the keys and output only a value.
	# @param create_file=True		Create the file if it does not exist.
	def _edit_config(self, filename, newvalues, delimeter='=', quotes_around_value=True, only_value=False,create_file=True):
		# don't use 'file' as a normal variable as it conflicts with the __builtin__.file
		newvalues = newvalues.copy()
		if self._debug: self._logger.log("DEBUG: _edit_config() called with " + str(newvalues)+" and flags: "+delimeter + "quotes: "+str(quotes_around_value)+" value: "+str(only_value))
		if GLIUtility.is_file(filename):
			f = open(filename)
			contents = f.readlines()
			f.close()
		elif create_file:
			contents = []
		else:
			raise GLIException("NoSuchFileError", 'notice','_edit_config',filename + ' does not exist!')
	
		for key in newvalues.keys():
			newline = ""
			if key == "SPACER":
				newline = "\n"
			elif key == "COMMENT":
				newline = '# ' + newvalues[key] + "\n"
			elif newvalues[key] == "##comment##" or newvalues[key] == "##commented##":
				newline = '#' + key + delimeter + '""' + "\n"
			else:
				if quotes_around_value:
					newvalues[key] = '"' + newvalues[key] + '"'
				#Only the printing of values is required.
				if only_value:
					newline = newvalues[key] + "\n"
				else:
					newline = key + delimeter + newvalues[key] + "\n"
			add_at_line = len(contents)
			for i in range(len(contents)):
				if newline == contents[i]:
					break
				if contents[i].startswith(key + delimeter):
					contents[i] = "#" + contents[i]
					add_at_line = i + 1
			else:
				contents.insert(add_at_line, newline)
		if self._debug: self._logger.log("DEBUG: Contents of file "+filename+": "+str(contents))
		f = open(filename,'w')
		f.writelines(contents)
		f.flush()
		f.close()
		self._logger.log("Edited Config file "+filename)

	##
	# Stage 1 install -- bootstraping the system
	# If we are doing a stage 1 install, then bootstrap 
	def stage1(self):
		if self._install_profile.get_install_stage() == 1:
			self._logger.mark()
			self._logger.log("Starting bootstrap.")
			pkgs = self._get_packages_to_emerge("/usr/portage/scripts/bootstrap.sh --pretend")
			if self._debug: self._logger.log("DEBUG: Packages to emerge: "+str(pkgs)+". Now running bootstrap.sh")
			exitstatus = GLIUtility.spawn("env-update && source /etc/profile && /usr/portage/scripts/bootstrap.sh", chroot=self._chroot_dir, display_on_tty8=True, logfile=self._compile_logfile, append_log=True)
			if not GLIUtility.exitsuccess(exitstatus):
				raise GLIException("Stage1Error", 'fatal','stage1', "Bootstrapping failed!")
			self._logger.log("Bootstrap complete.")

	##
	# Stage 2 install -- emerge -e system
	# If we are doing a stage 1 or 2 install, then emerge system
	def stage2(self):
		if self._install_profile.get_install_stage() in [ 1, 2 ]:
			self._logger.mark()
			self._logger.log("Starting emerge system.")
			pkgs = self._get_packages_to_emerge("emerge -p system")  #currently quite the useless
			if self._debug: self._logger.log("DEBUG: Packages to emerge: "+str(pkgs)+"/ Now running emerge --emptytree system")
#			exitstatus = self._emerge("--emptytree system")
			exitstatus = GLIUtility.spawn("env-update && source /etc/profile && emerge -e system", chroot=self._chroot_dir, display_on_tty8=True, logfile=self._compile_logfile, append_log=True)
			if not GLIUtility.exitsuccess(exitstatus):
				raise GLIException("Stage2Error", 'fatal','stage2', "Building the system failed!")
			self._logger.log("Emerge system complete.")

	##
	# Unpacks the stage tarball that has been specified in the profile (it better be there!)
	def unpack_stage_tarball(self):
		if not os.path.isdir(self._chroot_dir):
			if self._debug: self._logger.log("DEBUG: making the chroot dir:"+self._chroot_dir)
			os.makedirs(self._chroot_dir)
		if self._install_profile.get_install_stage() == 3 and self._install_profile.get_dynamic_stage3():
			# stage3 generation code here
			if not GLIUtility.is_file("/usr/livecd/systempkgs.txt"):
				raise GLIException("CreateStage3Error", "fatal", "unpack_stage_tarball", "Required file /usr/livecd/systempkgs.txt does not exist")
			try:
				syspkgs = open("/usr/livecd/systempkgs.txt", "r")
				systempkgs = syspkgs.readlines()
				syspkgs.close()
			except:
				raise GLIException("CreateStage3Error", "fatal", "unpack_stage_tarball", "Could not open /usr/livecd/systempkgs.txt")

			# Pre-create /lib (and possible /lib32 and /lib64)
			if os.path.islink("/lib") and os.readlink("/lib") == "lib64":
				if self._debug: self._logger.log("DEBUG: unpack_stage_tarball(): precreating /lib64 dir and /lib -> /lib64 symlink because glibc/portage sucks")
				if not GLIUtility.exitsuccess(GLIUtility.spawn("mkdir " + self._chroot_dir + "/lib64 && ln -s lib64 " + self._chroot_dir + "/lib")):
					raise GLIException("CreateStage3Error", "fatal", "unpack_stage_tarball", "Could not precreate /lib64 dir and /lib -> /lib64 symlink")

			syspkglen = len(systempkgs)
			for i, pkg in enumerate(systempkgs):
				pkg = pkg.strip()
				self.notify_frontend("progress", (float(i) / (syspkglen+1), "Copying " + pkg + " (" + str(i+1) + "/" + str(syspkglen) + ")"))
				self._portage.copy_pkg_to_chroot(pkg, True, ignore_missing=True)
			self.notify_frontend("progress", (float(syspkglen) / (syspkglen+1), "Finishing"))
			GLIUtility.spawn("cp /etc/make.conf " + self._chroot_dir + "/etc/make.conf")
			GLIUtility.spawn("ln -s `readlink /etc/make.profile` " + self._chroot_dir + "/etc/make.profile")
			GLIUtility.spawn("cp -f /etc/inittab.old " + self._chroot_dir + "/etc/inittab")

			# Nasty, nasty, nasty hack because vapier is a tool
			for tmpfile in ("/etc/passwd", "/etc/group", "/etc/shadow"):
				GLIUtility.spawn("grep -ve '^gentoo' " + tmpfile + " > " + self._chroot_dir + tmpfile)

			chrootscript = r"""
			#!/bin/bash

			source /etc/make.conf
			export LDPATH="/usr/lib/gcc-lib/${CHOST}/$(cd /usr/lib/gcc-lib/${CHOST} && ls -1 | head -n 1)"

			ldconfig $LDPATH
			gcc-config 1
			env-update
			source /etc/profile
			modules-update
			[ -f /usr/bin/binutils-config ] && binutils-config 1
			source /etc/profile
			#mount -t proc none /proc
			#cd /dev
			#/sbin/MAKEDEV generic-i386
			#umount /proc
			[ -f /lib/udev-state/devices.tar.bz2 ] && tar -C /dev -xjf /lib/udev-state/devices.tar.bz2
			"""
			script = open(self._chroot_dir + "/tmp/extrastuff.sh", "w")
			script.write(chrootscript)
			script.close()
			GLIUtility.spawn("chmod 755 /tmp/extrastuff.sh && /tmp/extrastuff.sh", chroot=self._chroot_dir, display_on_tty8=True, logfile=self._compile_logfile, append_log=True)
			GLIUtility.spawn("rm -rf /var/tmp/portage/* /usr/portage /tmp/*", chroot=self._chroot_dir)
			self.notify_frontend("progress", (1, "Done"))
			self._logger.log("Stage3 was generated successfully")
		else:
			self._logger.log("Fetching and unpacking tarball: "+self._install_profile.get_stage_tarball_uri())
			GLIUtility.fetch_and_unpack_tarball(self._install_profile.get_stage_tarball_uri(), self._chroot_dir, temp_directory=self._chroot_dir, keep_permissions=True, cc=self._cc)
			self._logger.log(self._install_profile.get_stage_tarball_uri()+" was fetched and unpacked.")

	##
	# Prepares the Chroot environment by copying /etc/resolv.conf and mounting proc and dev
	def prepare_chroot(self):
		# Copy resolv.conf to new env
		try:
			if self._debug: self._logger.log("DEBUG: copying /etc/resolv.conf over.")
			shutil.copy("/etc/resolv.conf", self._chroot_dir + "/etc/resolv.conf")
		except:
			pass
		if self._debug: self._logger.log("DEBUG: mounting proc")
		ret = GLIUtility.spawn("mount -t proc none "+self._chroot_dir+"/proc")
		if not GLIUtility.exitsuccess(ret):
			raise GLIException("MountError", 'fatal','prepare_chroot','Could not mount /proc')
		bind_mounts = [ '/dev' ]
		uname = os.uname()
		if uname[0] == 'Linux' and uname[2].split('.')[1] == '6':
			bind_mounts.append('/sys')
		if self._debug: self._logger.log("DEBUG: bind-mounting " + ", ".join(bind_mounts))
		for mount in bind_mounts:
			ret = GLIUtility.spawn('mount -o bind %s %s%s' % (mount,self._chroot_dir,mount))
			if not GLIUtility.exitsuccess(ret):
				raise GLIException("MountError", 'fatal','prepare_chroot','Could not mount '+mount)
		if self._debug: self._logger.log("DEBUG: copying logfile to new system!")
		GLIUtility.spawn("mv " + self._compile_logfile + " " + self._chroot_dir + self._compile_logfile + " && ln -s " + self._chroot_dir + self._compile_logfile + " " + self._compile_logfile)
		self._logger.log("Chroot environment ready.")

	##
	# Installs a list of packages specified in the profile. Will install any extra software!
	# In the future this function will lead to better things.  It may even wipe your ass for you.
	def install_packages(self):
		installpackages = self._install_profile.get_install_packages()
		if installpackages:
#			pkglist = self._portage.get_deps(" ".join(installpackages))
#			if self._debug: self._logger.log("install_packages(): pkglist is " + str(pkglist))
#			for i, pkg in enumerate(pkglist):
#				if self._debug: self._logger.log("install_packages(): processing package " + pkg)
#				self.notify_frontend("progress", (float(i) / len(pkglist), "Emerging " + pkg + " (" + str(i) + "/" + str(len(pkglist)) + ")"))
#				if not self._portage.get_best_version_vdb("=" + pkg):
#					status = self._emerge("=" + pkg)
#					if not GLIUtility.exitsuccess(status):
#						raise GLIException("ExtraPackagesError", "fatal", "install_packages", "Could not emerge " + pkg + "!")
#				else:
#					try:
#						self._portage.copy_pkg_to_chroot(pkg)
#					except:
#						raise GLIException("ExtraPackagesError", "fatal", "install_packages", "Could not emerge " + pkg + "!")
			self._portage.emerge(installpackages)

		if GLIUtility.is_file(self._chroot_dir + "/etc/X11"):
			# Copy the xorg.conf from the LiveCD if they installed xorg-x11
			exitstatus = GLIUtility.spawn("cp /etc/X11/xorg.conf " + self._chroot_dir + "/etc/X11/xorg.conf")
			if not GLIUtility.exitsuccess(exitstatus):
				self._logger.log("Could NOT copy the xorg configuration from the livecd to the new system!")
			else:
				self._logger.log("xorg.conf copied to new system.  X should be ready to roll!")
		if GLIUtility.is_file(self._chroot_dir + "/etc/X11/gdm/gdm.conf"):
			GLIUtility.spawn("cp -f /etc/X11/gdm/gdm.conf.old " + self._chroot_dir + "/etc/X11/gdm/gdm.conf")

	##
	# Will set the list of services to runlevel default.  This is a temporary solution!
	def set_services(self):
		services = self._install_profile.get_services()
		for service in services:
			if service:
				self._add_to_runlevel(service)
				
	##
	# Will grab partition info from the profile and mount all partitions with a specified mountpoint (and swap too)
	def mount_local_partitions(self):
		parts = self._install_profile.get_partition_tables()
		parts_to_mount = {}
		for device in parts:
			tmp_partitions = parts[device] #.get_install_profile_structure()
			tmp_minor = -1
			for minor in tmp_partitions: #.get_ordered_partition_list():
				if not tmp_partitions[minor]['type'] in ("free", "extended"):
					tmp_minor = minor
					break
			time.sleep(1)
			if tmp_minor == -1: continue
			# now sleep until it exists
			while not GLIUtility.is_file(tmp_partitions[minor]['devnode']):
				if self._debug: self._logger.log("DEBUG: Waiting for device node " + tmp_partitions[minor]['devnode'] + " to exist...")
				time.sleep(1)
			# one bit of extra sleep is needed, as there is a blip still
			time.sleep(1)
			for partition in tmp_partitions: #.get_ordered_partition_list():
				mountpoint = tmp_partitions[partition]['mountpoint']
				mountopts = tmp_partitions[partition]['mountopts']
				minor = str(int(tmp_partitions[partition]['minor']))
				partition_type = tmp_partitions[partition]['type']
				if mountpoint:
					if mountopts:
						mountopts = "-o " + mountopts + " "
					if partition_type:
						if partition_type == "fat32" or partition_type == "fat16": partition_type = "vfat"
						partition_type = "-t " + partition_type + " "
					parts_to_mount[mountpoint] = (mountopts, partition_type, tmp_partitions[partition]['devnode'])
					
				if partition_type == "linux-swap":
					ret = GLIUtility.spawn("swapon " + tmp_partitions[partition]['devnode'])
					if not GLIUtility.exitsuccess(ret):
						self._logger.log("ERROR! : Could not activate swap (" + tmp_partitions[partition]['devnode'] + ")!")
					else:
						self._swap_devices.append(tmp_partitions[partition]['devnode'])
		sorted_list = parts_to_mount.keys()
		sorted_list.sort()
		
		if not GLIUtility.is_file(self._chroot_dir):
			if self._debug: self._logger.log("DEBUG: making the chroot dir")
			exitstatus = GLIUtility.spawn("mkdir -p " + self._chroot_dir)
			if not GLIUtility.exitsuccess(exitstatus):
				raise GLIException("MkdirError", 'fatal','mount_local_partitions', "Making the ROOT mount point failed!")
			else:
				self._logger.log("Created root mount point")
		for mountpoint in sorted_list:
			mountopts = parts_to_mount[mountpoint][0]
			partition_type = parts_to_mount[mountpoint][1]
			partition = parts_to_mount[mountpoint][2]
			if not GLIUtility.is_file(self._chroot_dir + mountpoint):
				if self._debug: self._logger.log("DEBUG: making mountpoint: "+mountpoint)
				exitstatus = GLIUtility.spawn("mkdir -p " + self._chroot_dir + mountpoint)
				if not GLIUtility.exitsuccess(exitstatus):
					raise GLIException("MkdirError", 'fatal','mount_local_partitions', "Making the mount point failed!")
				else:
					self._logger.log("Created mountpoint " + mountpoint)
			ret = GLIUtility.spawn("mount " + partition_type + mountopts + partition + " " + self._chroot_dir + mountpoint, display_on_tty8=True, logfile=self._compile_logfile, append_log=True)
			if not GLIUtility.exitsuccess(ret):
				raise GLIException("MountError", 'fatal','mount_local_partitions','Could not mount a partition')
			# double check in /proc/mounts
			# This current code doesn't work and needs to be fixed, because there is a case that it is needed for - robbat2
			#ret, output = GLIUtility.spawn('awk \'$2 == "%s" { print "Found" }\' /proc/mounts | head -n1' % (self._chroot_dir + mountpoint), display_on_tty8=True, return_output=True)
			#if output.strip() != "Found":
			#	raise GLIException("MountError", 'fatal','mount_local_partitions','Could not mount a partition (failed in double-check)')
			self._logger.log("Mounted mountpoint: " + mountpoint)

	##
	# Mounts all network shares to the local machine
	def mount_network_shares(self):
		"""
		<agaffney> it'll be much easier than mount_local_partitions
		<agaffney> make sure /etc/init.d/portmap is started
		<agaffney> then mount each one: mount -t nfs -o <mountopts> <host>:<export> <mountpoint>
		"""
		nfsmounts = self._install_profile.get_network_mounts()
		for netmount in nfsmounts:
			if netmount['type'] == "NFS" or netmount['type'] == "nfs":
				mountopts = netmount['mountopts']
				if mountopts:
					mountopts = "-o " + mountopts
				host = netmount['host']
				export = netmount['export']
				mountpoint = netmount['mountpoint']
				if not GLIUtility.is_file(self._chroot_dir + mountpoint):
					exitstatus = GLIUtility.spawn("mkdir -p " + self._chroot_dir + mountpoint)
					if not GLIUtility.exitsuccess(exitstatus):
						raise GLIException("MkdirError", 'fatal','mount_network_shares', "Making the mount point failed!")
					else:
						if self._debug: self._logger.log("DEBUG: mounting nfs mount")
				ret = GLIUtility.spawn("mount -t nfs " + mountopts + " " + host + ":" + export + " " + self._chroot_dir + mountpoint, display_on_tty8=True, logfile=self._compile_logfile, append_log=True)
				if not GLIUtility.exitsuccess(ret):
					raise GLIException("MountError", 'fatal','mount_network_shares','Could not mount an NFS partition')
				self._logger.log("Mounted netmount at mountpoint: " + mountpoint)
			else:
				self._logger.log("Netmount type " + netmount['type'] + " not supported...skipping " + netmount['mountpoint'])


	##
	# Configures the new /etc/make.conf
	def configure_make_conf(self):
		# Get make.conf options
		make_conf = self._install_profile.get_make_conf()
		
		# For each configuration option...
		filename = self._chroot_dir + "/etc/make.conf"
#		self._edit_config(filename, {"COMMENT": "GLI additions ===>"})
		for key in make_conf.keys():
			# Add/Edit it into make.conf
			self._edit_config(filename, {key: make_conf[key]})
#		self._edit_config(filename, {"COMMENT": "<=== End GLI additions"})

		self._logger.log("Make.conf configured")
		# now make any directories that emerge needs, otherwise it will fail
		# this must take place before ANY calls to emerge.
		# otherwise emerge will fail (for PORTAGE_TMPDIR anyway)
		# defaults first
		# this really should use portageq or something.
		PKGDIR = '/usr/portage/packages'
		PORTAGE_TMPDIR = '/var/tmp'
		PORT_LOGDIR = None
		PORTDIR_OVERLAY = None
		# now other stuff
		if 'PKGDIR' in make_conf: PKGDIR = make_conf['PKGDIR']
		if 'PORTAGE_TMPDIR' in make_conf: PORTAGE_TMPDIR = make_conf['PORTAGE_TMPDIR']
		if 'PORT_LOGDIR' in make_conf: PORT_LOGDIR = make_conf['PORT_LOGDIR']
		if 'PORTDIR_OVERLAY' in make_conf: PORTDIR_OVERLAY = make_conf['PORTDIR_OVERLAY']
		if self._debug: self._logger.log("DEBUG: making PKGDIR if necessary: "+PKGDIR)
		GLIUtility.spawn("mkdir -p " + self._chroot_dir + PKGDIR, logfile=self._compile_logfile, append_log=True)
		if self._debug: self._logger.log("DEBUG: making PORTAGE_TMPDIR if necessary: "+PORTAGE_TMPDIR)
		GLIUtility.spawn("mkdir -p " + self._chroot_dir + PORTAGE_TMPDIR, logfile=self._compile_logfile, append_log=True)
		if PORT_LOGDIR != None: 
			if self._debug: self._logger.log("DEBUG: making PORT_LOGDIR if necessary: "+PORT_LOGDIR)
			GLIUtility.spawn("mkdir -p " + self._chroot_dir + PORT_LOGDIR, logfile=self._compile_logfile, append_log=True)
		if PORTDIR_OVERLAY != None: 
			if self._debug: self._logger.log("DEBUG: making PORTDIR_OVERLAY if necessary "+PORTDIR_OVERLAY)
			GLIUtility.spawn("mkdir -p " + self._chroot_dir + PORTDIR_OVERLAY, logfile=self._compile_logfile, append_log=True)

	##
	# This will get/update the portage tree.  If you want to snapshot or mount /usr/portage use "custom".
	def install_portage_tree(self):
		# Check the type of portage tree fetching we'll do
		# If it is custom, follow the path to the custom tarball and unpack it

		# This is a hack to copy the LiveCD's rsync into the chroot since it has the sigmask patch
		if self._debug: self._logger.log("DEBUG: Doing the hack where we copy the LiveCD's rsync into the chroot since it has the sigmask patch")
		GLIUtility.spawn("cp -a /usr/bin/rsync " + self._chroot_dir + "/usr/bin/rsync")
		GLIUtility.spawn("cp -a /usr/lib/libpopt* " + self._chroot_dir + "/usr/lib")
		
		sync_type = self._install_profile.get_portage_tree_sync_type()
		if sync_type == "snapshot" or sync_type == "custom": # Until this is finalized
		
			# Get portage tree info
			portage_tree_snapshot_uri = self._install_profile.get_portage_tree_snapshot_uri()
			if portage_tree_snapshot_uri:
				# Fetch and unpack the tarball
				if self._debug: self._logger.log("DEBUG: grabbing custom snapshot uri: "+portage_tree_snapshot_uri)
				GLIUtility.fetch_and_unpack_tarball(portage_tree_snapshot_uri, self._chroot_dir + "/usr/", self._chroot_dir + "/", cc=self._cc)
				if GLIUtility.is_file("/usr/livecd/metadata.tar.bz2"):
					GLIUtility.fetch_and_unpack_tarball("/usr/livecd/metadata.tar.bz2", self._chroot_dir + "/", self._chroot_dir + "/", cc=self._cc)
			self._logger.log("Portage tree install was custom.")
		elif sync_type == "sync":
			if self._debug: self._logger.log("DEBUG: starting emerge sync")
			exitstatus = GLIUtility.spawn("emerge sync", chroot=self._chroot_dir, display_on_tty8=True, logfile=self._compile_logfile, append_log=True)
			if not GLIUtility.exitsuccess(exitstatus):
				self._logger.log("ERROR!  Could not sync the portage tree using emerge sync.  Falling back to emerge-webrsync as a backup.")
				sync_type = "webrsync"
			else:
				self._logger.log("Portage tree sync'd")
		# If the type is webrsync, then run emerge-webrsync
		elif sync_type == "webrsync":
			if self._debug: self._logger.log("DEBUG: starting emerge webrsync")
			exitstatus = GLIUtility.spawn("emerge-webrsync", chroot=self._chroot_dir, display_on_tty8=True, logfile=self._compile_logfile, append_log=True)
			if not GLIUtility.exitsuccess(exitstatus):
				raise GLIException("EmergeWebRsyncError", 'fatal','install_portage_tree', "Failed to retrieve portage tree using webrsync!")
			self._logger.log("Portage tree sync'd using webrsync")
		# Otherwise, spit out a message because its probably a bad thing.
		else:
			self._logger.log("NOTICE!  No valid portage tree sync method was selected.  This will most likely result in a failed installation unless the tree is mounted.")
			
	##
	# Sets the timezone for the new environment
	def set_timezone(self):
		
		# Set symlink
		if os.access(self._chroot_dir + "/etc/localtime", os.W_OK):
			if self._debug: self._logger.log("DEBUG: /etc/localtime already exists, removing it so it can be symlinked")
			GLIUtility.spawn("rm "+self._chroot_dir + "/etc/localtime")
		if self._debug: self._logger.log("DEBUG: running ln -s ../usr/share/zoneinfo/" + self._install_profile.get_time_zone() + " /etc/localtime")
		GLIUtility.spawn("ln -s ../usr/share/zoneinfo/" + self._install_profile.get_time_zone() + " /etc/localtime", chroot=self._chroot_dir)
		if not (self._install_profile.get_time_zone() == "UTC"):
			if self._debug: self._logger.log("DEBUG: timezone was not UTC, setting CLOCK to local.  This may be overwritten later.")
			self._edit_config(self._chroot_dir + "/etc/conf.d/clock", {"CLOCK":"local"})
		self._logger.log("Timezone set.")
		
	##
	# Configures /etc/fstab on the new envorinment 
	def configure_fstab(self):
		newfstab = ""
		parts = self._install_profile.get_partition_tables()
		for device in parts:
			tmp_partitions = parts[device] #.get_install_profile_structure()
			for partition in tmp_partitions: #.get_ordered_partition_list():
				mountpoint = tmp_partitions[partition]['mountpoint']
				minor = str(int(tmp_partitions[partition]['minor']))
				partition_type = tmp_partitions[partition]['type']
				mountopts = tmp_partitions[partition]['mountopts']
				if not mountopts.strip(): mountopts = "defaults"
				if mountpoint:
					if not GLIUtility.is_file(self._chroot_dir+mountpoint):
						if self._debug: self._logger.log("DEBUG: making mountpoint: "+mountpoint)
						exitstatus = GLIUtility.spawn("mkdir -p " + self._chroot_dir + mountpoint)
						if not GLIUtility.exitsuccess(exitstatus):
							raise GLIException("MkdirError", 'fatal','configure_fstab', "Making the mount point failed!")
					newfstab += tmp_partitions[partition]['devnode']+"\t "+mountpoint+"\t "+partition_type+"\t "+mountopts+"\t\t "
					if mountpoint == "/boot":
						newfstab += "1 2\n"
					elif mountpoint == "/":
						newfstab += "0 1\n"
					else:
						newfstab += "0 0\n"
				if partition_type == "linux-swap":
					newfstab += tmp_partitions[partition]['devnode']+"\t none            swap            sw              0 0\n"
		newfstab += "none        /proc     proc    defaults          0 0\n"
		newfstab += "none        /dev/shm  tmpfs   defaults          0 0\n"
		if GLIUtility.is_device("/dev/cdroms/cdrom0"):
			newfstab += "/dev/cdroms/cdrom0    /mnt/cdrom    auto      noauto,user    0 0\n"

		for netmount in self._install_profile.get_network_mounts():
			if netmount['type'] == "nfs":
				newfstab += netmount['host'] + ":" + netmount['export'] + "\t" + netmount['mountpoint'] + "\tnfs\t" + netmount['mountopts'] + "\t0 0\n"
			
		file_name = self._chroot_dir + "/etc/fstab"	
		try:
			if self._debug: self._logger.log("DEBUG: backing up original fstab")
			shutil.move(file_name, file_name + ".OLDdefault")
		except:
			self._logger.log("ERROR: could not backup original fstab.")
		if self._debug: self._logger.log("DEBUG: Contents of new fstab: "+newfstab)
		f = open(file_name, 'w')
		f.writelines(newfstab)
		f.close()
		self._logger.log("fstab configured.")

	##
	# Fetches desired kernel sources, unless you're using a livecd-kernel in which case it does freaky stuff.
	def emerge_kernel_sources(self):
		self._logger.log("Starting emerge_kernel")
		kernel_pkg = self._install_profile.get_kernel_source_pkg()
#		if kernel_pkg:
		# Special case, no kernel installed
		if kernel_pkg == "none":
			return
		# Special case, livecd kernel
		elif kernel_pkg == "livecd-kernel":
			if self._debug: self._logger.log("DEBUG: starting livecd-kernel setup")
			self.notify_frontend("progress", (0, "Copying livecd-kernel to chroot"))
			self._portage.copy_pkg_to_chroot(self._portage.get_best_version_vdb("livecd-kernel"))
			self.notify_frontend("progress", (1, "Done copying livecd-kernel to chroot"))

			exitstatus = self._portage.emerge("coldplug")
			self._logger.log("Coldplug emerged.  Now they should be added to the boot runlevel.")
			self._add_to_runlevel("coldplug", runlevel="boot")

			if self._install_profile.get_kernel_bootsplash():
				self._logger.log("Bootsplash enabled for livecd-kernel...this is currently broken, so we're skipping the package install")
#				self._logger.log("Bootsplash enabled...emerging necessary packages")
#				self._portage.emerge(["splashutils", "splash-themes-livecd"])

			# Extra modules from kernelpkgs.txt...disabled until I can figure out why it sucks
#			try:
#				kernpkgs = open("/usr/livecd/kernelpkgs.txt", "r")
#				pkgs = ""
#				for line in kernpkgs.readlines():
#					pkgs += line.strip() + " "
#				kernpkgs.close()
#			except:
#				raise GLIException("EmergeColdplugError", 'fatal','build_kernel', "Could not read kernelpkgs.txt")
#			exitstatus = self._emerge(pkgs)
#			if not GLIUtility.exitsuccess(exitstatus):
#				raise GLIException("EmergeExtraKernelModulesError", 'fatal','build_kernel', "Could not emerge extra kernel packages")
#			self._logger.log("Extra kernel packages emerged.")

		# normal case
		else:
			exitstatus = self._portage.emerge(kernel_pkg)
#			if not GLIUtility.exitsuccess(exitstatus):
#				raise GLIException("EmergeKernelSourcesError", 'fatal','emerge_kernel_sources',"Could not retrieve kernel sources!")
			try:
				os.stat(self._chroot_dir + "/usr/src/linux")
			except:
				kernels = os.listdir(self._chroot_dir+"/usr/src")
				if self._debug: self._logger.log("DEBUG: no /usr/src/linux found.  found kernels: "+kernels)
				found_a_kernel = False
				counter = 0
				while not found_a_kernel:
					if (len(kernels[counter]) > 6)  and (kernels[counter][0:6]=="linux-"):
						if self._debug: self._logger.log("DEBUG: found one.  linking it. running: ln -s /usr/src/"+kernels[counter]+ " /usr/src/linux in the chroot.")
						exitstatus = GLIUtility.spawn("ln -s /usr/src/"+kernels[counter]+ " /usr/src/linux",chroot=self._chroot_dir)
						if not GLIUtility.exitsuccess(exitstatus):
							raise GLIException("EmergeKernelSourcesError", 'fatal','emerge_kernel_sources',"Could not make a /usr/src/linux symlink")
						found_a_kernel = True
					else:
						counter = counter + 1
			self._logger.log("Kernel sources:"+kernel_pkg+" emerged and /usr/src/linux symlinked.")

	##
	# Builds the kernel using genkernel or regularly if given a custom .config file in the profile
	def build_kernel(self):
		self._logger.mark()
		self._logger.log("Starting build_kernel")

		build_mode = self._install_profile.get_kernel_build_method()

		# No building necessary if using the LiveCD's kernel/initrd
		# or using the 'none' kernel bypass
		if self._install_profile.get_kernel_source_pkg() in ["livecd-kernel","none"]:
			if self._debug: self._logger.log("DEBUG: using "+self._install_profile.get_kernel_source_pkg()+ " so skipping this function.")		
			return
		# Get the uri to the kernel config
		kernel_config_uri = self._install_profile.get_kernel_config_uri()

		# is there an easier way to do this?
		if self._debug: self._logger.log("DEBUG: running command: awk '/^PATCHLEVEL/{print $3}' /usr/src/linux/Makefile in chroot.")
		ret, kernel_major = GLIUtility.spawn("awk '/^PATCHLEVEL/{print $3}' /usr/src/linux/Makefile",chroot=self._chroot_dir,return_output=True)
		# 6 == 2.6 kernel, 4 == 2.4 kernel
		kernel_major = int(kernel_major)
		if self._debug: self._logger.log("DEBUG: kernel major version is: "+str(kernel_major))
		#Copy the kernel .config to the proper location in /usr/src/linux
		if kernel_config_uri != '':
			try:
				if self._debug: self._logger.log("DEBUG: grabbing kernel config from "+kernel_config_uri+" and putting it in "+self._chroot_dir + "/var/tmp/kernel_config")
				GLIUtility.get_uri(kernel_config_uri, self._chroot_dir + "/var/tmp/kernel_config")
			except:
				raise GLIException("KernelBuildError", 'fatal', 'build_kernel', "Could not copy kernel config!")
			
		# the && stuff is important so that we can catch any errors.
		kernel_compile_script =  "#!/bin/bash\n"
		kernel_compile_script += "cp /var/tmp/kernel_config /usr/src/linux/.config && "
		kernel_compile_script += "cd /usr/src/linux && "
		# required for 2.[01234] etc kernels
		if kernel_major in [0,1,2,3,4]:
			kernel_compile_script += " yes 'n' | make oldconfig && make symlinks && make dep"
		# not strictly needed, but recommended by upstream
		else: #elif kernel_major in [5,6]:
			kernel_compile_script += "make prepare"
		
		# bypass to install a kernel, but not compile it
		if build_mode == "none":
			return
		# this mode is used to install kernel sources, and have then configured
		# but not actually build the kernel. This is needed for netboot
		# situations when you have packages that require kernel sources
		# to build.
		elif build_mode == "prepare-only":
			if self._debug: self._logger.log("DEBUG: writing kernel script with contents: "+kernel_compile_script)
			f = open(self._chroot_dir+"/var/tmp/kernel_script", 'w')
			f.writelines(kernel_compile_script)
			f.close()
			#Build the kernel
			if self._debug: self._logger.log("DEBUG: running: chmod u+x "+self._chroot_dir+"/var/tmp/kernel_script")
			exitstatus1 = GLIUtility.spawn("chmod u+x "+self._chroot_dir+"/var/tmp/kernel_script")
			if self._debug: self._logger.log("DEBUG: running: /var/tmp/kernel_script in chroot.")
			exitstatus2 = GLIUtility.spawn("/var/tmp/kernel_script", chroot=self._chroot_dir, display_on_tty8=True, logfile=self._compile_logfile, append_log=True)
			if not GLIUtility.exitsuccess(exitstatus1):
				raise GLIException("KernelBuildError", 'fatal', 'build_kernel', "Could not handle prepare-only build! died on chmod.")
			if not GLIUtility.exitsuccess(exitstatus2):
				raise GLIException("KernelBuildError", 'fatal', 'build_kernel', "Could not handle prepare-only build! died on running of kernel script.")
			#i'm sure i'm forgetting something here.
			#cleanup
			exitstatus = GLIUtility.spawn("rm -f "+self._chroot_dir+"/var/tmp/kernel_script "+self._chroot_dir+"/var/tmp/kernel_config")
			#it's not important if this fails.
			self._logger.log("prepare-only build complete")
		# Genkernel mode, including custom kernel_config. Initrd always on.
		elif build_mode == "genkernel":
			if self._debug: self._logger.log("DEBUG: build_kernel(): starting emerge genkernel")		
			exitstatus = self._portage.emerge("genkernel")
#			if not GLIUtility.exitsuccess(exitstatus):
#				raise GLIException("EmergeGenKernelError", 'fatal','build_kernel', "Could not emerge genkernel!")
			self._logger.log("Genkernel emerged.  Beginning kernel compile.")
			# Null the genkernel_options
			genkernel_options = ""
	
			# If the uri for the kernel config is not null, then
			if kernel_config_uri != "":
				if self._debug: self._logger.log("DEBUG: build_kernel(): getting kernel config "+kernel_config_uri)
				GLIUtility.get_uri(kernel_config_uri, self._chroot_dir + "/var/tmp/kernel_config")
				genkernel_options = genkernel_options + " --kernel-config=/var/tmp/kernel_config"
				
			# Decide whether to use bootsplash or not
			if self._install_profile.get_kernel_bootsplash():
				genkernel_options = genkernel_options + " --gensplash"
			else:
				genkernel_options = genkernel_options + " --no-gensplash"
			# Run genkernel in chroot
			#print "genkernel all " + genkernel_options
			if self._debug: self._logger.log("DEBUG: build_kernel(): running: genkernel all " + genkernel_options + " in chroot.")
			exitstatus = GLIUtility.spawn("genkernel all " + genkernel_options, chroot=self._chroot_dir, display_on_tty8=True, logfile=self._compile_logfile, append_log=True)
			if not GLIUtility.exitsuccess(exitstatus):
				raise GLIException("KernelBuildError", 'fatal', 'build_kernel', "Could not build kernel!")
			
#			exitstatus = self._emerge("hotplug")
#			if not GLIUtility.exitsuccess(exitstatus):
#				raise GLIException("EmergeHotplugError", 'fatal','build_kernel', "Could not emerge hotplug!")
#			self._logger.log("Hotplug emerged.")
			exitstatus = self._portage.emerge("coldplug")
#			if not GLIUtility.exitsuccess(exitstatus):
#				raise GLIException("EmergeColdplugError", 'fatal','build_kernel', "Could not emerge coldplug!")
			self._logger.log("Coldplug emerged.  Now they should be added to the default runlevel.")
			
#			self._add_to_runlevel("hotplug")
			self._add_to_runlevel("coldplug", runlevel="boot")

			if self._install_profile.get_kernel_bootsplash():
				self._logger.log("Bootsplash enabled...emerging necessary packages")
				self._portage.emerge(["splashutils", "splash-themes-livecd"])

			self._logger.log("Genkernel complete.")
		elif build_mode == "custom":  #CUSTOM CONFIG
			
			kernel_compile_script += " && make && make modules && make modules_install"

			#Ok now that it's built, copy it to /boot/kernel-* for bootloader code to find it
			if self._client_configuration.get_architecture_template() == "x86":
				kernel_compile_script += " && cp /usr/src/linux/arch/i386/boot/bzImage /boot/kernel-custom\n"
			elif self._client_configuration.get_architecture_template() == "amd64":
				kernel_compile_script += " && cp /usr/src/linux/arch/x86_64/boot/bzImage /boot/kernel-custom\n"
			elif self._client_configuration.get_architecture_template() == "ppc":
				kernel_compile_script += " && cp /usr/src/linux/vmlinux /boot/kernel-custom\n"
			if self._debug: self._logger.log("DEBUG: build_kernel(): writing custom kernel script: "+kernel_compile_script)
			f = open(self._chroot_dir+"/var/tmp/kernel_script", 'w')
			f.writelines(kernel_compile_script)
			f.close()
			#Build the kernel
			if self._debug: self._logger.log("DEBUG: build_kernel(): running: chmod u+x "+self._chroot_dir+"/var/tmp/kernel_script")
			exitstatus1 = GLIUtility.spawn("chmod u+x "+self._chroot_dir+"/var/tmp/kernel_script")
			if self._debug: self._logger.log("DEBUG: build_kernel(): running: /var/tmp/kernel_script in chroot")
			exitstatus2 = GLIUtility.spawn("/var/tmp/kernel_script", chroot=self._chroot_dir, display_on_tty8=True, logfile=self._compile_logfile, append_log=True)
			if not GLIUtility.exitsuccess(exitstatus1):
				raise GLIException("KernelBuildError", 'fatal', 'build_kernel', "Could not build custom kernel! died on chmod.")
			if not GLIUtility.exitsuccess(exitstatus2):
				raise GLIException("KernelBuildError", 'fatal', 'build_kernel', "Could not build custom kernel! died on running of kernel script.")
						
			#i'm sure i'm forgetting something here.
			#cleanup
			exitstatus = GLIUtility.spawn("rm -f "+self._chroot_dir+"/var/tmp/kernel_script "+self._chroot_dir+"/var/tmp/kernel_config")
			#it's not important if this fails.

			if self._install_profile.get_kernel_bootsplash():
				self._logger.log("Bootsplash enabled...emerging necessary packages")
				self._portage.emerge(["splashutils", "splash-themes-livecd"])

			self._logger.log("Custom kernel complete")
			
	##
	# Installs and starts up distccd if the user has it set, so that it will get used for the rest of the install
	def install_distcc(self):
		if self._install_profile.get_install_distcc():
			if self._debug: self._logger.log("DEBUG: install_distcc(): we ARE installing distcc")
			if self._debug: self._logger.log("DEBUG: install_distcc(): running: USE='-*' emerge --nodeps sys-devel/distcc in chroot.")
			exitstatus = GLIUtility.spawn("USE='-*' emerge --nodeps sys-devel/distcc", chroot=self._chroot_dir, display_on_tty8=True, logfile=self._compile_logfile, append_log=True)
			if not GLIUtility.exitsuccess(exitstatus):
				self._logger.log("ERROR! : Could not emerge distcc!")
			else:
				self._logger.log("distcc emerged.")	
	
	##
	# Installs mail MTA. Does not put into runlevel, as this is not simple with MTAs.
	def install_mta(self):
		# Get MTA info
		mta_pkg = self._install_profile.get_mta_pkg()
		if mta_pkg:
			# Emerge MTA
			if self._debug: self._logger.log("DEBUG: install_mta(): installing mta: "+mta_pkg)
			exitstatus = self._portage.emerge(mta_pkg)
#			if not GLIUtility.exitsuccess(exitstatus):
#				raise GLIException("MTAError", 'fatal','install_mta', "Could not emerge " + mta_pkg + "!")
			self._logger.log("MTA installed: "+mta_pkg)

	##
	# Installs and sets up logging daemon on the new system.  adds to runlevel too.
	def install_logging_daemon(self):
		# Get loggin daemon info
		logging_daemon_pkg = self._install_profile.get_logging_daemon_pkg()
		if logging_daemon_pkg:
			# Emerge Logging Daemon
			if self._debug: self._logger.log("DEBUG: install_logging_daemon: emerging "+logging_daemon_pkg)
			exitstatus = self._portage.emerge(logging_daemon_pkg)
#			if not GLIUtility.exitsuccess(exitstatus):
#				raise GLIException("LoggingDaemonError", 'fatal','install_logging_daemon', "Could not emerge " + logging_daemon_pkg + "!")

			# Add Logging Daemon to default runlevel
			# After we find the name of it's initscript
			# This current code is a hack, and should be better.
			initscript = logging_daemon_pkg[(logging_daemon_pkg.find('/')+1):]
			if self._debug: self._logger.log("DEBUG: install_logging_daemon: adding "+initscript+" to runlevel")
			self._add_to_runlevel(initscript)
			self._logger.log("Logging daemon installed: "+logging_daemon_pkg)
	##
	# Installs and sets up cron package.
	def install_cron_daemon(self):
		# Get cron daemon info
		cron_daemon_pkg = self._install_profile.get_cron_daemon_pkg()
		if cron_daemon_pkg:
			if cron_daemon_pkg == "none":
				self._logger.log("Skipping installation of cron daemon")
			else:
				# Emerge Cron Daemon
				if self._debug: self._logger.log("DEBUG: install_cron_daemon: emerging "+cron_daemon_pkg)
				exitstatus = self._portage.emerge(cron_daemon_pkg)
#				if not GLIUtility.exitsuccess(exitstatus):
#					raise GLIException("CronDaemonError", 'fatal', 'install_cron_daemon', "Could not emerge " + cron_daemon_pkg + "!")

				# Add Cron Daemon to default runlevel
				# After we find the name of it's initscript
				# This current code is a hack, and should be better.
				initscript = cron_daemon_pkg[(cron_daemon_pkg.find('/')+1):]
				if self._debug: self._logger.log("DEBUG: install_cron_daemon: adding "+initscript+" to runlevel")
				self._add_to_runlevel(initscript)

				# If the Cron Daemon is not vixie-cron, run crontab			
				if "vixie-cron" not in cron_daemon_pkg:
					if self._debug: self._logger.log("DEBUG: install_cron_daemon: running: crontab /etc/crontab in chroot.")
					exitstatus = GLIUtility.spawn("crontab /etc/crontab", chroot=self._chroot_dir, display_on_tty8=True)
					if not GLIUtility.exitsuccess(exitstatus):
						raise GLIException("CronDaemonError", 'fatal', 'install_cron_daemon', "Failure making crontab!")
				self._logger.log("Cron daemon installed and configured: "+cron_daemon_pkg)
	
	##
	# This will parse the partitions looking for types that require fstools and emerge them if found.
	def install_filesystem_tools(self):
		"Installs and sets up fstools"
		# Get the list of file system tools to be installed
		parts = self._install_profile.get_partition_tables()
		# don't use an array, use a set instead
		filesystem_types = []
		for device in parts:
			tmp_partitions = parts[device] #.get_install_profile_structure()
			for partition in tmp_partitions: #.get_ordered_partition_list():
				partition_type = tmp_partitions[partition]['type'].lower()
				if tmp_partitions[partition]['mountpoint'] and partition_type not in filesystem_types:
					filesystem_types.append(partition_type)

		package_list = []
		for filesystem in filesystem_types:
			if filesystem == 'xfs':
				package_list.append('sys-fs/xfsprogs')
			elif filesystem == 'reiserfs':
				package_list.append('sys-fs/reiserfsprogs')
			elif filesystem == 'jfs':
				package_list.append('sys-fs/jfsutils')
			elif filesystem == 'ntfs':
				package_list.append('sys-fs/ntfsprogs')
			elif filesystem in ['fat','vfat', 'msdos', 'umsdos']:
				package_list.append('sys-fs/dosfstools')
			elif filesystem == 'hfs':
				# should check with the PPC guys on this
				package_list.append('sys-fs/hfsutils')
				package_list.append('sys-fs/hfsplusutils')
			#else:
			# should be code here for every FS type!
		failed_list = []
		for package in package_list:
			if self._debug: self._logger.log("DEBUG: install_filesystem_tools(): emerging "+package)
			exitstatus = self._portage.emerge(package)
#			if not GLIUtility.exitsuccess(exitstatus):
#				self._logger.log("ERROR! : Could not emerge "+package+"!")
#				failed_list.append(package)
#			else:
			self._logger.log("FileSystemTool "+package+" was emerged successfully.")
		# error checking is important!
		if len(failed_list) > 0:
			raise GLIException("InstallFileSystemToolsError", 'warning', 'install_filesystem_tools', "Could not emerge " + failed_list + "!")
					
	##
	# Installs rp-pppoe but does not configure it.  This function is quite the unknown.
	def install_rp_pppoe(self):
		# If user wants us to install rp-pppoe, then do so
		if self._install_profile.get_install_rp_pppoe():
			if self._debug: self._logger.log("DEBUG: install_rp_pppoe: emerging rp-pppoe")
			exitstatus = self._portage.emerge("rp-pppoe")
#			if not GLIUtility.exitsuccess(exitstatus):
#				self._logger.log("ERROR! : Could not emerge rp-pppoe!")
			#	raise GLIException("RP_PPPOEError", 'warning', 'install_rp_pppoe', "Could not emerge rp-pppoe!")
#			else:
			self._logger.log("rp-pppoe emerged but not set up.")	
		# Should we add a section here to automatically configure rp-pppoe?
		# I think it should go into the setup_network_post section
		# What do you guys think? <-- said by unknown. samyron or npmcallum
				
	##
	# Installs and sets up pcmcia-cs if selected in the profile
	def install_pcmcia_cs(self):
		if self._debug: self._logger.log("DEBUG: install_pcmcia_cs(): emerging pcmcia-cs")
		exitstatus = self._portage.emerge("pcmcia-cs")
#		if not GLIUtility.exitsuccess(exitstatus):
#			self._logger.log("ERROR! : Could not emerge pcmcia-cs!")
			
		# Add pcmcia-cs to the default runlevel
#		else:
		self._add_to_runlevel('pcmcia')
		self._logger.log("PCMCIA_CS emerged and configured.")
			
	##
	# This runs etc-update and then re-overwrites the files by running the configure_*'s to keep our values.
	def update_config_files(self):
		"Runs etc-update (overwriting all config files), then re-configures the modified ones"
		# Run etc-update overwriting all config files
		if self._debug: self._logger.log("DEBUG: update_config_files(): running: "+'echo "-5" | chroot '+self._chroot_dir+' etc-update')
		status = GLIUtility.spawn('echo "-5" | chroot '+self._chroot_dir+' etc-update', display_on_tty8=True, logfile=self._compile_logfile, append_log=True)
		if not GLIUtility.exitsuccess(status):
			self._logger.log("ERROR! : Could not update the config files!")
		else:	
#			self.configure_make_conf()
			self.configure_fstab()
#			self.configure_rc_conf()
			etc_files = self._install_profile.get_etc_files()
			for etc_file in etc_files:
				if self._debug: self._logger.log("DEBUG: update_config_files(): updating config file: "+etc_file)
				if isinstance(etc_files[etc_file], dict):
					self._edit_config(self._chroot_dir + "/etc/" + etc_file, etc_files[etc_file])
				else:
					for entry in etc_files[etc_file]:
						self._edit_config(self._chroot_dir + "/etc/" + etc_file, { "0": entry }, only_value=True)
			self._logger.log("Config files updated using etc-update.  make.conf/fstab/rc.conf restored.")

	##
	# Configures /etc/rc.conf (deprecated by above code)
	def configure_rc_conf(self):
		
		# Get make.conf options
		options = self._install_profile.get_rc_conf()
		
		# For each configuration option...
		filename = self._chroot_dir + "/etc/rc.conf"
#		self._edit_config(filename, {"COMMENT": "GLI additions ===>"})
		for key in options.keys():
			# Add/Edit it into rc.conf
			self._edit_config(filename, {key: options[key]})
#		self._edit_config(filename, {"COMMENT": "<=== End GLI additions"})
		self._logger.log("rc.conf configured.")
		
	##
	# Sets up the network for the first boot
	def setup_network_post(self):
		if self._debug: self._logger.log("DEBUG: setup_network_post(): starting network configuration")
		# Get hostname, domainname and nisdomainname
		hostname = self._install_profile.get_hostname()
		domainname = self._install_profile.get_domainname()
		nisdomainname = self._install_profile.get_nisdomainname()
		
		# Write the hostname to the hostname file		
		#open(self._chroot_dir + "/etc/hostname", "w").write(hostname + "\n")
		self._edit_config(self._chroot_dir + "/etc/conf.d/hostname", {"HOSTNAME": hostname})
		
		# Write the domainname to the nisdomainname file
		if domainname:
			#open(self._chroot_dir + "/etc/dnsdomainname", "w").write(domainname + "\n")
			self._edit_config(self._chroot_dir + "/etc/conf.d/domainname", {"DNSDOMAIN": domainname})
			self._add_to_runlevel("domainname")
		
		# Write the nisdomainname to the nisdomainname file
		if nisdomainname:
			#open(self._chroot_dir + "/etc/nisdomainname", "w").write(nisdomainname + "\n")
			self._edit_config(self._chroot_dir + "/etc/conf.d/domainname", {"NISDOMAIN": nisdomainname})
			self._add_to_runlevel("domainname")
			
		#
		# EDIT THE /ETC/HOSTS FILE
		#
			
		# The address we are editing is 127.0.0.1
		hosts_ip = "127.0.0.1"

		# If the hostname is localhost
		if hostname == "localhost":
			# If a domainname is set
			if domainname:
				hosts_line = hostname + "." + domainname + "\t" + hostname
			else:
				hosts_line = hostname
		# If the hostname is not localhost
		else:
			# If a domainname is set
			if domainname:
				hosts_line = hostname + "." + domainname + "\t" + hostname + "\tlocalhost"
			else:
				hosts_line = "localhost\t" + hostname

		# Write to file
		self._edit_config(self._chroot_dir + "/etc/hosts", {hosts_ip: hosts_line}, delimeter='\t', quotes_around_value=False)

		#
		# SET DEFAULT GATEWAY
		#

		# Get default gateway
		default_gateway = self._install_profile.get_default_gateway()
		
		# If the default gateway exists, add it
		if default_gateway:
			default_gateway_string = '( "default via ' + default_gateway[1] + '" )'
			if self._debug: self._logger.log("DEBUG: setup_network_post(): found gateway. adding to confing. "+default_gateway_string)
			self._edit_config(self._chroot_dir + "/etc/conf.d/net", {"routes_"+default_gateway[0]: default_gateway_string})
			
		#
		# SET RESOLV INFO
		#

		# Get dns servers
		dns_servers = self._install_profile.get_dns_servers()
		
		# Clear the list
		resolv_output = []
		
		# If dns servers are set
		if dns_servers:
			
			
			# Parse each dns server
			for dns_server in dns_servers:
				# Add the server to the output
				resolv_output.append("nameserver " + dns_server +"\n")
			
			# If the domainname is set, then also output it
			if domainname:
				resolv_output.append("search " + domainname + "\n")
				
			# Output to file
			if self._debug: self._logger.log("DEBUG: setup_network_post(): writing resolv.conf with contents: " + str(resolv_output))
			resolve_conf = open(self._chroot_dir + "/etc/resolv.conf", "w")
			resolve_conf.writelines(resolv_output)
			resolve_conf.close()
		
		#
		# PARSE INTERFACES
		#

		# Fetch interfaces
		interfaces = self._install_profile.get_network_interfaces()
		emerge_dhcp = False
		# Parse each interface
		for interface in interfaces.keys():
			if self._debug: self._logger.log("DEBUG: setup_network_post(): configuring interface: "+ interface)
			# Set what kind of interface it is
			interface_type = interface[:3]
		
			# Check to see if there is a startup script for this interface, if there isn't link to the proper script
			try:
				os.stat(self._chroot_dir + "/etc/init.d/net." + interface)
			except:
				if self._debug: self._logger.log("DEBUG: setup_network_post(): /etc/init.d/net." + interface + " didn't exist, symlinking it.")
				os.symlink("net." + interface_type +  "0", self._chroot_dir + "/etc/init.d/net." + interface)
		
			# If we are going to load the network at boot...
			#if interfaces[interface][2]:  #THIS FEATURE NO LONGER EXISTS
				
			# Add it to the default runlevel
			if self._debug: self._logger.log("DEBUG: setup_network_post(): adding net."+interface+" to runlevel.")
			self._add_to_runlevel("net."+interface)	# moved a bit <-- for indentation

			#
			# ETHERNET
			#
			if interface_type == "eth":

				#
				# STATIC IP
				#
				# If the post-install device info is not None, then it is a static ip addy
				if interfaces[interface][0] != "dhcp":
					ip = interfaces[interface][0]
					broadcast = interfaces[interface][1]
					netmask = interfaces[interface][2]
			#		aliases = interfaces[interface][1][3]
			#		alias_ips = []
			#		alias_broadcasts = []
			#		alias_netmasks = []
					
					# Write the static ip config to /etc/conf.d/net
					self._edit_config(self._chroot_dir + "/etc/conf.d/net", {"iface_" + interface: ip + " broadcast " + broadcast + " netmask " + netmask})
					
					# If aliases are set
			#		if aliases:
					
						# Parse aliases to format alias info
			#			for alias in aliases:
			#				alias_ips.append(alias[0])
			#				alias_broadcasts.append(alias[1])
			#				alias_netmasks.append(allias[2])
						
						# Once the alias info has been gathered, then write it out
						# Alias ips first
			#			self._edit_config(self._chroot_dir + "/etc/conf.d/net", "alias_" + interface, string.join(alias_ips))
						# Alias broadcasts next
			#			self._edit_config(self._chroot_dir + "/etc/conf.d/net", "broadcast_" + interface, string.join(alias_broadcasts))
						# Alias netmasks last
			#			self._edit_config(self._chroot_dir + "/etc/conf.d/net", "netmask_" + interface, string.join(alias_netmasks))

				#
				# DHCP IP
				#
				else:
					dhcpcd_options = interfaces[interface][1]
					if not dhcpcd_options:
						dhcpcd_options = ""
					self._edit_config(self._chroot_dir + "/etc/conf.d/net", {"iface_" + interface: "dhcp", "dhcpcd_" + interface: dhcpcd_options})
					emerge_dhcp = True
		if emerge_dhcp:
			if self._debug: self._logger.log("DEBUG: setup_network_post(): emerging dhcpcd.")
			exitstatus = self._portage.emerge("dhcpcd")
#			if not GLIUtility.exitsuccess(exitstatus):
#				self._logger.log("ERROR! : Could not emerge dhcpcd!")
#			else:
			self._logger.log("dhcpcd emerged.")		
		
	##
	# Sets the root password
	def set_root_password(self):
		if self._debug: self._logger.log("DEBUG: set_root_password(): running: "+ 'echo \'root:' + self._install_profile.get_root_pass_hash() + '\' | chroot '+self._chroot_dir+' chpasswd -e')
		status = GLIUtility.spawn('echo \'root:' + self._install_profile.get_root_pass_hash() + '\' | chroot '+self._chroot_dir+' chpasswd -e')
		if not GLIUtility.exitsuccess(status):
			raise GLIException("SetRootPasswordError", 'fatal', 'set_root_password', "Failure to set root password!")
		self._logger.log("Root Password set on the new system.")
		
	##
	# Sets up the new users for the system
	def set_users(self):
		# Loop for each user
		for user in self._install_profile.get_users():
		
			# Get values from the tuple
			username = user[0]
			password_hash = user[1]
			groups = user[2]
			shell = user[3]
			home_dir = user[4]
			uid = user[5]
			comment = user[6]
			
			options = [ "-m", "-p '" + password_hash + "'" ]
			
			# If the groups are specified
			if groups:
			
				# If just one group is listed as a string, make it a list
				if groups == str:
					groups = [ groups ]
					
				# If only 1 group is listed
				if len(groups) == 1:
					options.append("-G " + groups[0])
					
				# If there is more than one group
				elif len(groups) > 1:
					options.append('-G "' + string.join(groups, ",") + '"')
					
				# Attempt to add the group (will return success when group exists)
				for group in groups:
					if not group: continue
					# Add the user
					if self._debug: self._logger.log("DEBUG: set_users(): adding user to groups with (in chroot): "+'groupadd -f ' + group)
					exitstatus = GLIUtility.spawn('groupadd -f ' + group, chroot=self._chroot_dir, logfile=self._compile_logfile, append_log=True, display_on_tty8=True)
					if not GLIUtility.exitsuccess(exitstatus):
						self._logger.log("ERROR! : Failure to add group " + group+" and it wasn't that the group already exists!")
					
			
			# If a shell is specified
			if shell:
				options.append("-s " + shell)
				
			# If a home dir is specified
			if home_dir:
				options.append("-d " + home_dir)
				
			# If a UID is specified
			if uid:
				options.append("-u " + str(uid))
				
			# If a comment is specified
			if comment:
				options.append('-c "' + comment + '"')
				
			# Add the user
			if self._debug: self._logger.log("DEBUG: set_users(): adding user with (in chroot): "+'useradd ' + string.join(options) + ' ' + username)
			exitstatus = GLIUtility.spawn('useradd ' + string.join(options) + ' ' + username, chroot=self._chroot_dir, logfile=self._compile_logfile, append_log=True, display_on_tty8=True)
			if not GLIUtility.exitsuccess(exitstatus):
				self._logger.log("ERROR! : Failure to add user " + username)
			#	raise GLIException("AddUserError", 'warning', 'set_users', "Failure to add user " + username)
			else:
				self._logger.log("User " + username + " was added.")
			
	##
	# This function will handle the various cleanup tasks as well as unmounting the filesystems for reboot.
	def finishing_cleanup(self):
		#These are temporary until I come up with a nicer idea.
		#get rid of the compile_output file so the symlink doesn't get screwed up.
		
		#we copy the log over to the new system.
		install_logfile = self._client_configuration.get_log_file()
		try:
			if self._debug: self._logger.log("DEBUG: finishing_cleanup(): copying logfile over to new system's root.")
			shutil.copy(install_logfile, self._chroot_dir + install_logfile)
		except:
			if self._debug: self._logger.log("DEBUG: finishing_cleanup(): ERROR! could not copy logfile over to /root.")
		#Now we're done logging as far as the new system is concerned.
		GLIUtility.spawn("cp /tmp/installprofile.xml " + self._chroot_dir + "/root/installprofile.xml")
		GLIUtility.spawn("cp /tmp/clientconfiguration.xml " + self._chroot_dir + "/root/clientconfiguration.xml")
		
		#Unmount mounted fileystems in preparation for reboot
		mounts = GLIUtility.spawn(r"mount | sed -e 's:^.\+ on \(.\+\) type .\+$:\1:' | grep -e '^" + self._chroot_dir + "' | sort -r", return_output=True)[1].split("\n")
		for mount in mounts:
			GLIUtility.spawn("umount -l " + mount)
			
		# now turn off all swap as well.
		# we need to find the swap devices
		for swap_device in self._swap_devices:
			ret = GLIUtility.spawn("swapoff "+swap_device)
			if not GLIUtility.exitsuccess(ret):
				self._logger.log("ERROR! : Could not deactivate swap ("+swap_device+")!")
		
		#OLD WAY: Unmount the /proc and /dev that we mounted in prepare_chroot
		#There really isn't a reason to log errors here.
		#ret = GLIUtility.spawn("umount "+self._chroot_dir+"/proc", display_on_tty8=True, logfile=self._compile_logfile, append_log=True)
		#ret = GLIUtility.spawn("umount "+self._chroot_dir+"/dev", display_on_tty8=True, logfile=self._compile_logfile, append_log=True)
		#temp hack to unmount the new root.
		#ret = GLIUtility.spawn("umount "+self._chroot_dir, display_on_tty8=True, logfile=self._compile_logfile, append_log=True)
		#insert code here to unmount the swap partition, if there is one.

		GLIUtility.spawn("rm /tmp/compile_output.log && rm " + install_logfile)
		
	##
	# This is a stub function to be done by the individual arch.  I don't think it's even needed here.
	# but it's nice having it just incase.
	def install_bootloader(self):
		"THIS FUNCTION MUST BE DONE BY THE INDIVIDUAL ARCH"
		pass

	def run_post_install_script(self):
		if self._install_profile.get_post_install_script_uri():
			try:
				if self._debug: self._logger.log("DEBUG: run_post_install_script(): getting script: "+self._install_profile.get_post_install_script_uri())
				GLIUtility.get_uri(self._install_profile.get_post_install_script_uri(), self._chroot_dir + "/var/tmp/post-install")
				if self._debug: self._logger.log("DEBUG: run_post_install_script(): running: chmod a+x /var/tmp/post-install && /var/tmp/post-install in chroot")
				GLIUtility.spawn("chmod a+x /var/tmp/post-install && /var/tmp/post-install", chroot=self._chroot_dir, display_on_tty8=True, logfile=self._compile_logfile, append_log=True)
			except:
				raise GLIException("RunPostInstallScriptError", 'fatal', 'run_post_install_script', "Failed to retrieve and/or execute post-install script")

	##
	# This function should only be called in the event of an install failure. It performs
	# general cleanup to prepare the system for another installer run.
	def install_failed_cleanup(self):
		if self._debug: self._logger.log("DEBUG: install_failed_cleanup(): gathering mounts to unmount")
		mounts = GLIUtility.spawn(r"mount | sed -e 's:^.\+ on \(.\+\) type .\+$:\1:' | grep -e '^" + self._chroot_dir + "' | sort -r", return_output=True)[1].split("\n")
		for mount in mounts:
			if self._debug: self._logger.log("DEBUG: install_failed_cleanup(): running: umount -l " + mount)
			GLIUtility.spawn("umount -l " + mount)
			
		# now turn off all swap as well.
		# we need to find the swap devices
		for swap_device in self._swap_devices:
			if self._debug: self._logger.log("DEBUG: install_failed_cleanup(): running: swapoff "+swap_device)
			ret = GLIUtility.spawn("swapoff "+swap_device)
			if not GLIUtility.exitsuccess(ret):
				self._logger.log("ERROR! : Could not deactivate swap ("+swap_device+")!")
		
		if self._debug: self._logger.log("DEBUG: install_failed_cleanup(): running: cp /tmp/compile_output.log /tmp/compile_output.log.failed then removing /tmp/compile_output.log")
		GLIUtility.spawn("mv " + self._compile_logfile + " " + self._compile_logfile + ".failed")
#		GLIUtility.spawn("rm /tmp/compile_output.log")
		GLIUtility.spawn("mv " + self._client_configuration.get_log_file() + " " + self._client_configuration.get_log_file() + ".failed")
#		GLIUtility.spawn("rm /var/log/installer.log")
