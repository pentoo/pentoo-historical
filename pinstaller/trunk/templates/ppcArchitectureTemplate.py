"""
# Copyright 1999-2005 Gentoo Foundation
# This source code is distributed under the terms of version 2 of the GNU
# General Public License as published by the Free Software Foundation, a copy
# of which can be found in the main directory of this project.
Gentoo Linux Installer

$Id: ppcArchitectureTemplate.py,v 1.5 2005/10/15 17:24:46 agaffney Exp $
Copyright 2004 Gentoo Technologies Inc.


This fills in ppc specific functions.
"""

import GLIUtility, string
from x86ArchitectureTemplate import x86ArchitectureTemplate
from GLIException import *
import parted

class ppcArchitectureTemplate(x86ArchitectureTemplate):
	def __init__(self,configuration=None, install_profile=None, client_controller=None):
		ppcArchitectureTemplate.__init__(self, configuration, install_profile, client_controller)
		self._architecture_name = 'ppc'

	
	def install_bootloader(self):
		"Installs and configures bootloader"
		#
		# THIS IS ARCHITECTURE DEPENDANT!!!
		# This is the ppc way.. it uses yaboot for new world.
		
		if self._install_profile.get_boot_loader_pkg() or self._install_profile.get_boot_loader_pkg() == "none":
			exitstatus = self._emerge(self._install_profile.get_boot_loader_pkg())
			if exitstatus != 0:
				raise GLIException("BootLoaderEmergeError", 'fatal', 'install_bootloader', "Could not emerge bootloader!")
		else:
			pass
		
		if self._install_profile.get_boot_loader_pkg() == "yaboot":
			self._configure_yaboot()
		else:
			raise Exception("BootLoaderError",'fatal','install_bootloader',"Invalid bootloader selected:"+self._install_profile.get_boot_loader_pkg())

	def _configure_yaboot(self):
		build_mode = self._install_profile.get_kernel_build_method()
		root_device = ""
		root_minor = ""
		parts = self._install_profile.get_partition_tables()
		for device in parts:
			tmp_partitions = parts[device]
			for partition in tmp_partitions:
				mountpoint = tmp_partitions[partition]['mountpoint']
				if mountpoint == "/":
					root_minor = str(int(tmp_partitions[partition]['minor']))
					root_device = device
		if self._install_profile.get_bootloader_kernel_args(): bootloader_kernel_args = self._install_profile.get_bootloader_kernel_args()
		else: bootloader_kernel_args = ""
		#Assuming the config program works as specified, it should do the majority of the work.
		#this is the white rabbit object.  antarus: it expects a full fstab, /proc mounted, and a kernel in /boot/vmlinux.  The manaul also says /dev must be bind-mounted.
		exitstatus = GLIUtility.spawn("yabootconfig --chroot "+self._chroot_dir+" --quiet", display_on_tty8=True)
		if not GLIUtility.exitsuccess(exitstatus):
			raise GLIException("YabootError",'fatal','_configure_yaboot',"Could not successfully run the yabootconfig command.")
		#Hopefully now an /etc/yaboot.conf exists but does not have the correct kernel/Sysmap information.
		#We must gather that info like we have done for the other bootloaders.
		file_name = self._chroot_dir + "/boot/kernel_name"
		file_name2 = self._chroot_dir + "/boot/initrd_name"
		exitstatus2 = GLIUtility.spawn("ls "+root+"/boot/kernel-* > "+file_name)
		if build_mode == "genkernel":
			exitstatus3 = GLIUtility.spawn("ls "+root+"/boot/initramfs-* > "+file_name2)
		else:
			exitstatus3 = GLIUtility.spawn("touch "+file_name2)
		if (exitstatus2 != 0) or (exitstatus3 != 0):
			raise GLIException("BootloaderError", 'fatal', '_configure_yaboot', "Error in one of THE TWO run commands")
		self._logger.log("Bootloader: the three information gathering commands have been run")
		g = open(file_name)
		h = open(file_name2)
		initrd_name = h.readlines()
		kernel_name = g.readlines()
		g.close()
		h.close()
		if not kernel_name[0]:
			raise GLIException("BootloaderError", 'fatal', '_configure_yaboot',"Error: We have no kernel in /boot to put in the yaboot.conf file!")
		kernel_name = map(string.strip, kernel_name)
		initrd_name = map(string.strip, initrd_name)
		for i in range(len(kernel_name)):
			kernel_name = kernel_name[i].split(root)[1]
		for i in range(len(initrd_name)):
			initrd_name = initrd_name[i].split(root)[1]
		#Open the file and edit the right lines
		f = open(self._chroot_dir+"/etc/yaboot.conf")
		contents = f.readlines()
		f.close()
		for i in range(0, len(contents)):
			if contents[i] == "image=/boot/vmlinux":
				contents[i] = "image=/boot/"+kernel_name[5:]
				if build_mode == "genkernel":
					#insert /dev/ram0 line
					contents.insert("root=/dev/ram0",i+2)
					#insert partition line.
					contents.insert("partition="+root_minor,i+3)
					#edit append line. use root_device and root_minor.
					contents.insert("append=\"real_root="+root_device+root_minor+ " init=/linuxrc "+bootloader_kernel_args + "\" \n", i+4)
		f = open(self._chroot_dir+"/etc/yaboot.conf",'w')
		f.writelines(contents)
		f.close()
