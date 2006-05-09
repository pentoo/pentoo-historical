# Copyright 1999-2005 Gentoo Foundation
# This source code is distributed under the terms of version 2 of the GNU
# General Public License as published by the Free Software Foundation, a copy
# of which can be found in the main directory of this project.
import dialog, platform, string, os, glob, copy, re
import GLIInstallProfile
import GLIClientConfiguration
import GLIStorageDevice
import GLIUtility
from GLIException import GLIException
import gettext
_ = gettext.gettext
#This is a parent class to centralize the code between UserGenCC and UserGenIP

class GLIGen(object):
	def __init__(self):
		self._d = dialog.Dialog()
		self._DLG_OK = 0
		self._DLG_YES = 0
		self._DLG_CANCEL = 1
		self._DLG_NO = 1
		self._DLG_ESC = 2
		self._DLG_ERROR = 3
		self._DLG_EXTRA = 4
		self._DLG_HELP = 5
	
	def _dmenu_list_to_choices(self, list):
		choices = []
		for i in range(0, len(list)):
			choices.append((str(i + 1), list[i]))

		return choices
		
	def client_profile(self):
		return self._client_profile
	
	def install_profile(self):
		return self._install_profile

#This class will generate a client config and return it as a xml string
class GLIGenCF(GLIGen):
	def __init__(self, client_profile, local_install=True, advanced_mode=True, networkless=False):
		GLIGen.__init__(self)
		self._client_profile = client_profile
		self.local_install = local_install
		self.advanced_mode = advanced_mode
		self._networkless = networkless
		
	def serialize(self):
		return self._client_profile.serialize()
	#-----------------------------------------------
	#Functions for generating a client configuration
	#-----------------------------------------------	
	def set_arch_template(self):
		subarches = { 'i386': 'x86', 'i486': 'x86', 'i586': 'x86', 'i686': 'x86', 'x86_64': 'amd64', 'parisc': 'hppa' }
		arch = platform.machine()
		if arch in subarches: 
			arch = subarches[arch]
		if self.local_install:
			try:
				self._client_profile.set_architecture_template(None, arch, None)
			except:
				self._d.msgbox(_(u"Error!  Undefined architecture template specified or found on the current machine"))
		else:
			template_choices = ["x86", "amd64", "sparc", "alpha", "hppa", "ppc"]
			arch_template_string = _(u"Please select the architecture of the computer that gentoo will be installed on.  For pentium and AMD 32-bit processors, choose x86.  If you don't know your architecture, you should consider another Linux distribution.")
			code, menuitem = self._d.menu(arch_template_string, choices=self._dmenu_list_to_choices(template_choices), default_item=str(template_choices.index(arch)+1), height=20)
			if code == self._DLG_OK:
				menuitem = template_choices[int(menuitem)-1]
				try:
					self._client_profile.set_architecture_template(None, menuitem, None)
				except: 
					self._d.msgbox(_(u"Error!  Undefined architecture template specified or found on the current machine"))
	def set_verbose(self):
		#Don't show unless advanced.
		if self.advanced_mode:
			#Change the Yes/No buttons back.
			self._d.add_persistent_args(["--yes-label", _(u"Yes")])
			self._d.add_persistent_args(["--no-label", _(u"No")])
			if self._d.yesno(_(u"Do you want debugging output enabled during the install?  This is mainly meant to help the developers debug any bugs."), width=60) == self._DLG_YES:
				self._client_profile.set_verbose(None, True, None)
			else:
				self._client_profile.set_verbose(None, False, None)

	def set_logfile(self):
		#If not advanced, the default will suffice.
		if self.advanced_mode:
			logfile_string = _(u"""The installer logs all important events during the install process to a logfile for debugging purposes.
The file gets copied to the new system once the install is complete.
Enter the desired filename and path for the install log (the default is recommended):""")
			initval = self._client_profile.get_log_file()
			code, logfile = self._d.inputbox(logfile_string, init=initval, width=60, height=15)
			if code == self._DLG_OK:
				self._client_profile.set_log_file(None, logfile, None)

	def set_root_mount_point(self):
		#If not advanced, the default will suffice.
		if self.advanced_mode:
			root_mount_point_string = _(u"Enter the mount point to be used to mount the partition(s) where the new system will be installed.  The default is /mnt/gentoo and is greatly recommended, but any mount point will do.")	
			initval = self._client_profile.get_root_mount_point()
			code, rootmountpoint = self._d.inputbox(root_mount_point_string, init=initval, width=60, height=11)
			if code == self._DLG_OK: 
				self._client_profile.set_root_mount_point(None, rootmountpoint, None)

	def set_client_networking(self):
		if self._networkless: return
		if GLIUtility.ping("www.gentoo.org") and self.local_install:	#If an active connection exists, ignore this step if doing a local install.
			return
		if self.local_install:
			device_list = GLIUtility.get_eth_devices()
		else:
			device_list = []
		choice_list = []
		for device in device_list:
			choice_list.append((device, GLIUtility.get_interface_realname(device)))
		choice_list.append(("Other",_(u"Type your own.")))
		cnet_string1 = _(u"In order to complete most installs, an active Internet connection is required.  Listed are the network devices already detected.  In this step you will need to setup one network connection for GLI to use to connect to the Internet.  If your desired device does not show up in the list, you can select Other and input the device name manually.")
		code, interface = self._d.menu(cnet_string1, width=75, height=20, choices=choice_list)
		if code != self._DLG_OK: 
			return
		if interface == "Other":
			code, interface = self._d.inputbox(_(u"Enter the interface (NIC) you would like to use for installation (e.g. eth0):"))
			if code != self._DLG_OK: 
				return
		
		dhcp_options = ""
		
		#Change the Yes/No buttons to new labels for this question.
		self._d.add_persistent_args(["--yes-label", _(u"DHCP")])
		self._d.add_persistent_args(["--no-label", _(u"Static IP/Manual")])
		cnet_string2 = _(u"To setup your network interface, you can either use DHCP if enabled, or manually enter your network information.\n  DHCP (Dynamic Host Configuration Protocol) makes it possible to automatically receive networking information (IP address, netmask, broadcast address, gateway, nameservers etc.). This only works if you have a DHCP server in your network (or if your provider provides a DHCP service).  If you do not, you must enter the information manually.  Please select your networking configuration method:")
		if self._d.yesno(cnet_string2, height=15, width=60) == self._DLG_YES: #DHCP
			network_type = 'dhcp'
			code, dhcp_options = self._d.inputbox(_(u"If you have any additional DHCP options to pass, type them here in a space-separated list.  If you have none, just press Enter."), height=13, width=50)
		else:
			network_type = 'static'
			code, data = self._d.form(_(u'Enter your networking information: (See Chapter 3 of the Handbook for more information)  Your broadcast address is probably your IP address with 255 as the last tuple.  Do not press Enter until all fields you intend to fill out are complete!'), 
			((_(u'Enter your IP address:'), 15),
			 (_(u'Enter your Broadcast address:'), 15),
			 (_(u'Enter your Netmask:'),15,'255.255.255.0'),
			 (_(u'Enter your default gateway:'),15), 
			 (_(u'Enter a DNS server:'),15,'128.118.25.3'),
			 (_(u'Enter a HTTP Proxy IP:'), 15,self._client_profile.get_http_proxy()),
			 (_(u'Enter a FTP Proxy IP:'), 15, self._client_profile.get_ftp_proxy()), 
			 (_(u'Enter a RSYNC Proxy:'),15,self._client_profile.get_rsync_proxy())
			))
			(ip_address, broadcast, netmask, gateway, dnsservers, http_proxy, ftp_proxy, rsync_proxy) = data[:-1].split('\n')
			if code != self._DLG_OK: 
				return
		#Set the info now that it's all gathered.
		try:
			self._client_profile.set_network_type(None, network_type, None)
			self._client_profile.set_network_interface(None, interface, None)
			if not network_type == 'dhcp':
				self._client_profile.set_network_ip(None, ip_address, None)
				self._client_profile.set_network_broadcast(None, broadcast, None)
				self._client_profile.set_network_netmask(None, netmask, None)
				self._client_profile.set_network_gateway(None, gateway, None)
				self._client_profile.set_dns_servers(None, dnsservers, None)
			else:
				if dhcp_options:
					self._client_profile.set_network_dhcp_options(None, dhcp_options, None)
			if http_proxy:
				self._client_profile.set_http_proxy(None, http_proxy, None)
			if ftp_proxy:
				self._client_profile.set_ftp_proxy(None, ftp_proxy, None)
			if rsync_proxy:
				self._client_profile.set_rsync_proxy(None, rsync_proxy, None)
								
		except: 
			self._d.msgbox(_(u"ERROR! Could not set networking information!"))

	def set_enable_ssh(self):
		#Change the Yes/No buttons back.
		self._d.add_persistent_args(["--yes-label", _(u"Yes")])
		self._d.add_persistent_args(["--no-label", _(u"No")])
		if self.advanced_mode and not self._networkless:
			if self._d.yesno(_(u"Do you want SSH enabled during the install?  This will allow you to login remotely during the installation process.  If choosing Yes, be sure you select a new LiveCD root password!"), width=60) == self._DLG_YES:
				self._client_profile.set_enable_ssh(None, True, None)
			else:
				self._client_profile.set_enable_ssh(None, False, None)

	def set_livecd_password(self):
		# The root password will be set here only if in advanced mode.  Otherwise it is auto-scrambled.
		if self.advanced_mode:
			match = False;
			while not match:
				livecd_password_string = _(u"""If you want to be able to login to your machine from another console during the installation,
you will want to enter a new root password for the LIVECD.
Note that this can be different from your new system's root password.
Presss Enter twice to skip this step.
Enter the new LIVECD root password:	""")
				code, passwd1 = self._d.passwordbox(livecd_password_string, width=60, height=16)
				if code != self._DLG_OK: 
					return
				code, passwd2 = self._d.passwordbox(_(u"Enter the new LIVECD root password again to verify:"))
				if code != self._DLG_OK: 
					return
				if passwd1 != passwd2:
					self._d.msgbox(_(u"The passwords do not match.  Please try again."))
					return
				else:
					match = True;
					if passwd1 != "":  #don't want to hash an empty password.
						try:
							self._client_profile.set_root_passwd(None, GLIUtility.hash_password(passwd1), None)
						except:
							d.msgbox(_(u"ERROR! Could not set the root password on the LiveCD!"))
						self._d.msgbox(_(u"Password saved.  Press Enter to continue."))
						
	def set_client_kernel_modules(self):
		if self.advanced_mode:
			status, output = GLIUtility.spawn("lsmod", return_output=True)
			cmodules_string1 = _(u"Here is a list of modules currently loaded on your machine.\n  Please look through and see if any modules are missing\n that you would like loaded.\n\n")
			self._d.add_persistent_args(["--exit-label", _(u"Continue")])
			self._d.scrollbox(cmodules_string1+output, height=20, width=70, title=_(u"Loaded Modules"))
			cmodules_string2 = _(u"\nIf you have additional modules you would like loaded before the installation begins (ex. a network driver), enter them in a space-separated list.")
			code, kernel_modules_list = self._d.inputbox(cmodules_string2, init="", width=60, height=12)
			if code == self._DLG_OK:
				try:
					self._client_profile.set_kernel_modules(None, kernel_modules_list, None)
				except:
					d.msgbox(_(u"ERROR! Could not set the list of kernel modules!"))

	def save_client_profile(self, xmlfilename="", askforfilename=True):
		code = 0
		filename = xmlfilename
		if askforfilename:
			code, filename = self._d.inputbox(_(u"Enter a filename for the XML file.  Use the full path!"), init=xmlfilename)
			if code != self._DLG_OK or not filename: 
				return
		if GLIUtility.is_file(filename):
			#Change the Yes/No buttons back.
			self._d.add_persistent_args(["--yes-label", _(u"Yes")])
			self._d.add_persistent_args(["--no-label", _(u"No")])
			if not self._d.yesno(_(u"The file %s already exists. Do you want to overwrite it?") % filename) == self._DLG_YES:
				return
		try:
			configuration = open(filename ,"w")
			configuration.write(self._client_profile.serialize())
			configuration.close()
		except:
			self._d.msgbox(_(u"Error.  File couldn't be saved.  It will be saved automatically to /tmp before the install."))

class GLIGenIP(GLIGen):
	def __init__(self, client_profile, install_profile, local_install=True, advanced_mode=True, networkless=False):
		GLIGen.__init__(self)
		self._client_profile = client_profile
		self._install_profile = install_profile
		self._networkless = networkless
		self.local_install = local_install
		self.advanced_mode = advanced_mode
		if self._networkless:
			try:
				self._install_profile.set_grp_install(None, True, None)
				self._install_profile.set_install_stage(None, "3", None)
				self._install_profile.set_dynamic_stage3(None, True, None)
				self._install_profile.set_portage_tree_sync_type(None,"snapshot", None)
				cd_snapshot_uri = GLIUtility.get_cd_snapshot_uri()
				self._install_profile.set_portage_tree_snapshot_uri(None, cd_snapshot_uri, None)
				self._install_profile.set_kernel_source_pkg(None, "livecd-kernel", None)
				self._install_profile.set_cron_daemon_pkg(None, "vixie-cron", None)
				self._install_profile.set_logging_daemon_pkg(None,"syslog-ng", None)
			except:
				self._d.msgbox("ERROR: Could not set networkless information in the profile")
				
	def serialize(self):
		return self._install_profile.serialize()
	#---------------------------------------
	#Functions to generate a install profile
	#---------------------------------------
	
	def set_partitions(self):
		partitions_string1 = _("""The first thing on the new system to setup is the partitoning.
You will first select a drive and then edit its partitions.
No changes will be saved until the end of the step.
No changes to your disk will be made until the installation.
NOTE: YOU MUST AT LEAST SELECT ONE PARTITION AS YOUR ROOT PARTITION "/"
If your drive is pre-partitioned, just select the mountpoints and make 
sure that the format option is set to FALSE or it will erase your data.
The installer does not yet support resizing of partitions (its not safe).
Please refer to the Gentoo Installation Handbook for more information
on partitioning and the various filesystem types available in Linux.""")
		self._d.msgbox(partitions_string1, height=17, width=78)
		devices = self._install_profile.get_partition_tables()
		drives = devices.keys()
		drives.sort()
		choice_list = []
		if not devices:
			tmp_drives = GLIStorageDevice.detect_devices()
			tmp_drives.sort()
			for drive in tmp_drives:
				devices[drive] = GLIStorageDevice.Device(drive)
				#if self.local_install:  #when uncommenting please indent the next line.
				devices[drive].set_partitions_from_disk()
				drives.append(drive)
				choice_list.append((drive, devices[drive].get_model()))
		else:
			for drive in drives:
				choice_list.append((drive, devices[drive].get_model()))
		#choice_list.append(("Other", "Type your own drive name))  # I DONT THINK GLISD CAN DO NONEXISTANT DRIVES
		while 1:
			code, drive_to_partition = self._d.menu(_(u"Which drive would you like to partition?\n Info provided: Type, mkfs Options, Mountpoint, Mountopts, Size in MB"), choices=choice_list, cancel=_(u"Save and Continue"))
			if code != self._DLG_OK: break
			while 1:
#				partitions = devices[drive_to_partition].get_partitions()
				partlist = devices[drive_to_partition].get_ordered_partition_list()
				tmpparts = devices[drive_to_partition] #.get_partitions()
				partsmenu = []
				for part in partlist:
					tmppart = tmpparts[part]
					entry = ""
					if tmppart.get_type() == "free":
						#partschoice = "New"
						entry = _(u" - Unallocated space (")
						if tmppart.is_logical():
							entry += _(u"logical, ")
						entry += str(tmppart.get_mb()) + "MB)"
					elif tmppart.get_type() == "extended":
						entry = str(int(tmppart.get_minor()))
						entry += _(u" - Extended Partition (") + str(tmppart.get_mb()) + "MB)"
					else:
						entry = str(int(tmppart.get_minor())) + " - "
						# Type: " + tmppart.get_type() + ", Mountpoint: " + tmppart.get_mountpoint() + ", Mountopts: " + tmppart.get_mountopts() + "("
						if tmppart.is_logical():
							entry += _(u"Logical (")
						else:
							entry += _(u"Primary (")
						entry += tmppart.get_type() + ", "
						entry += (tmppart.get_mkfsopts() or "none") + ", "
						entry += (tmppart.get_mountpoint() or "none") + ", "
						entry += (tmppart.get_mountopts() or "none") + ", "
						entry += str(tmppart.get_mb()) + "MB)"
					partsmenu.append(entry)
				#Add recommended partitioning option and clear option
				partsmenu.append(_(u"Set Recommended Layout (needs 4GB+)"))
				partsmenu.append(_(u"Clear Partitions On This Drive."))
				code, part_to_edit = self._d.menu(_(u"Select a partition or unallocated space to edit\nKey: Minor, Pri/Ext, Filesystem, MkfsOpts, Mountpoint, MountOpts, Size."), width=70, choices=self._dmenu_list_to_choices(partsmenu), cancel=_(u"Back"))
				if code != self._DLG_OK: break
				partmenuchoice = partsmenu[int(part_to_edit)-1]
				#Check for recommended and clear here before setting the tmppart
				if partmenuchoice == _(u"Set Recommended Layout (needs 4GB+)"):
					try:
						devices[drive_to_partition].do_recommended()
					except GLIException, error:
						self._d.msgbox(_(u"The recommended layout could NOT be set.  The following message was received:")+error.get_error_msg(), width=70, height=15)
					continue
				if partmenuchoice == _(u"Clear Partitions On This Drive."):
					try:
						devices[drive_to_partition].clear_partitions()
						self._d.msgbox(_(u"Partition table cleared successfully"))
					except:
						self._d.msgbox(_(u"ERROR: could not clear the partition table!"))
					continue
				#all other cases (partitions)
				part_to_edit = partlist[int(part_to_edit)-1]
				tmppart = tmpparts[part_to_edit]
				if tmppart.get_type() == "free":
					# partition size first
					free_mb = tmppart.get_mb()
					code, new_mb = self._d.inputbox(_(u"Enter the size of the new partition in MB (max %s MB).  If creating an extended partition input its entire size (not just the first logical size):") % str(free_mb), init=str(free_mb))
					if code != self._DLG_OK: continue
					if int(new_mb) > free_mb:
						self._d.msgbox(_(u"The size you entered (%s MB) is larger than the maximum of %s MB") % (new_mb, str(free_mb)))
						continue
					# partition type
					part_types = [("ext2", _(u"Old, stable, but no journaling")),
					("ext3", _(u"ext2 with journaling and b-tree indexing (RECOMMENDED)")),
					("linux-swap", _(u"Swap partition for memory overhead")),
					("fat32", _(u"Windows filesystem format used in Win9X and XP")),
					("ntfs", _(u"Windows filesystem format used in Win2K and NT")),
					("jfs", _(u"IBM's journaling filesystem.  stability unknown.")),
					("xfs", _(u"Don't use this unless you know you need it.")),
					("reiserfs", _(u"B*-tree based filesystem. great performance. Only V3 supported.")),
					("extended", _(u"Create an extended partition containing other logical partitions")),
					("Other", _(u"Something else we probably don't support."))]
					code, type = self._d.menu(_(u"Choose the filesystem type for this new partition."), height=20, width=77, choices=part_types)
					if code != self._DLG_OK: continue
										
					# 'other' partition type
					if type == "Other":
						code, type = self._d.inputbox(_(u"Please enter the new partition's type:"))
					if code != self._DLG_OK: continue
					
					# now add it to the data structure
					devices[drive_to_partition].add_partition(part_to_edit, int(new_mb), 0, 0, type)
				else:
					while 1:
						tmppart = tmpparts[part_to_edit]
						tmptitle = drive_to_partition + str(part_to_edit) + " - "
						if tmppart.is_logical():
							tmptitle += _(u"Logical (")
						else:
							tmptitle += _(u"Primary (")
						tmptitle += tmppart.get_type() + ", "
						tmptitle += (tmppart.get_mkfsopts() or "none") + ", "
						tmptitle += (tmppart.get_mountpoint() or "none") + ", "
						tmptitle += (tmppart.get_mountopts() or "none") + ", "
						tmptitle += str(tmppart.get_mb()) + "MB)"
						menulist = [_(u"Delete"), _(u"Mount Point"), _(u"Mount Options"), _(u"Format"), _(u"Extra mkfs.* Parameters")]
						code, part_action = self._d.menu(tmptitle, choices=self._dmenu_list_to_choices(menulist), cancel=_(u"Back"))
						if code != self._DLG_OK: break
						part_action = menulist[int(part_action)-1]
						if part_action == _(u"Delete"):
							answer = (self._d.yesno(_(u"Are you sure you want to delete the partition ") + drive_to_partition + str(part_to_edit) + "?") == self._DLG_YES)
							if answer == True:
								tmpdev = tmppart.get_device()
								tmpdev.remove_partition(part_to_edit)
								break
						elif part_action == _(u"Mount Point"):
							mountpoint_menu = ["/","/boot","/etc","/home","/lib","/mnt","/mnt/windows","/opt","/root","/usr","/usr/local","/usr/portage","/var",_(u"Other")]
							code, mountpt = self._d.menu(_(u"Choose a mountpoint from the list or choose Other to type your own for partition ")+str(part_to_edit)+_(u".  It is currently set to:")+tmppart.get_mountpoint(), choices=self._dmenu_list_to_choices(mountpoint_menu)) #may have to make that an integer
							if code == self._DLG_OK:
								mountpt = mountpoint_menu[int(mountpt)-1]
								if mountpt == _(u"Other"):
									code, mountpt = self._d.inputbox(_(u"Enter a mountpoint for partition ") + str(part_to_edit), init=tmppart.get_mountpoint())
							try: tmppart.set_mountpoint(mountpt)
							except: self._d.msgbox(_(u"ERROR! Could not set mountpoint!"))
						elif part_action == _(u"Mount Options"):
							code, answer = self._d.inputbox(_(u"Enter your mount options for partition ") + str(part_to_edit), init=(tmppart.get_mountopts() or "defaults"))
							if code == self._DLG_OK: tmppart.set_mountopts(answer)
						elif part_action == _(u"Format"):
							#Change the Yes/No buttons back.
							self._d.add_persistent_args(["--yes-label", _(u"Yes")])
							self._d.add_persistent_args(["--no-label", _(u"No")])
							code = self._d.yesno(_(u"Do you want to format this partition?"))
							if code == self._DLG_YES: 
								tmppart.set_format(True)
							else:
								tmppart.set_format(False)
						elif part_action == _(u"Extra mkfs.* Parameters"):
							new_mkfsopts = tmppart.get_mkfsopts()
							# extra mkfs options
							if tmppart.get_type() != "extended":
								code, new_mkfsopts = self._d.inputbox(_(u"Extra mkfs.* Parameters"), init=new_mkfsopts)
								if code == self._DLG_OK: tmppart.set_mkfsopts(new_mkfsopts)							
		try:										
			self._install_profile.set_partition_tables(devices)
		except:
			self._d.msgbox(_(u"ERROR:  The partition tables could not be set correctly!"))

	def set_network_mounts(self):
	# This is where any NFS mounts will be specified
		network_mounts = copy.deepcopy(self._install_profile.get_network_mounts())
		while 1:
			menulist = []
			for mount in network_mounts:
				menulist.append(mount['host'] + ":" + mount['export'])
			menulist.append(_(u"Add a new network mount"))
			choices = self._dmenu_list_to_choices(menulist)
			code, menuitemidx = self._d.menu(_(u"If you have any network shares you would like to mount during the install and for your new system, define them here. Select a network mount to edit or add a new mount.  Currently GLI only supports NFS mounts."), choices=choices, cancel=_(u"Save and Continue"), height=18)
			if code == self._DLG_CANCEL:
				try:
					self._install_profile.set_network_mounts(network_mounts)
				except:
					self._d.msgbox(_(u"ERROR: Could net set network mounts!"))
				break
			menuitem = menulist[int(menuitemidx)-1]
			if menuitem == _(u"Add a new network mount"):
				code, nfsmount = self._d.inputbox(_(u"Enter NFS mount or just enter the IP/hostname to search for available mounts"), height=13, width=50)
				if code != self._DLG_OK: 
					continue
				if not GLIUtility.is_nfs(nfsmount):
					if GLIUtility.is_ip(nfsmount) or GLIUtility.is_hostname(nfsmount):
						status, remotemounts = GLIUtility.spawn("/usr/sbin/showmount -e " + nfsmount + " 2>&1 | egrep '^/' | cut -d ' ' -f 1 && echo", return_output=True)
						remotemounts = remotemounts.strip().split("\n")
						if (not GLIUtility.exitsuccess(status)) or (not len(remotemounts)) or not remotemounts[0]:
							self._d.msgbox(_(u"No NFS exports were detected on ") + nfsmount)
							continue
						code, nfsmount2 = self._d.menu(_(u"Select a NFS export"), choices=self._dmenu_list_to_choices(remotemounts), cancel=_(u"Back"))
						if code != self._DLG_OK: 
							continue
						nfsmount2 = remotemounts[int(nfsmount2)-1]
					else:
						self._d.msgbox(_(u"The address you entered, %s, is not a valid IP or hostname.  Please try again.") % nfsmount)
						continue
				else:
					colon_location = nfsmount.find(':')
					menuitem = nfsmount
					nfsmount = menuitem[:colon_location]
					nfsmount2 = menuitem[colon_location+1:]
				for mount in network_mounts:
					if nfsmount == mount['host'] and nfsmount2 == mount['export']:
						self._d.msgbox(_(u"There is already an entry for ") + nfsmount + ":" + nfsmount2 + ".")
						nfsmount = None
						break
				if nfsmount == None: 
					continue
				network_mounts.append({'export': nfsmount2, 'host': nfsmount, 'mountopts': '', 'mountpoint': '', 'type': 'nfs'})
				menuitem = nfsmount + ":" + nfsmount2
				menuitemidx = len(network_mounts)

			if menuitem.find(':') != -1:
				colon_location = menuitem.find(':')
				tmpmount = network_mounts[int(menuitemidx)-1]
				code, mountpoint = self._d.inputbox(_(u"Enter a mountpoint"), init=tmpmount['mountpoint'])
				if code == self._DLG_OK: 
					tmpmount['mountpoint'] = mountpoint
				code, mountopts = self._d.inputbox(_(u"Enter mount options"), init=tmpmount['mountopts'])
				if code == self._DLG_OK: 
					tmpmount['mountopts'] = mountopts
				network_mounts[int(menuitemidx)-1] = tmpmount

	def set_install_stage(self):
		if self._networkless: return
	# The install stage and stage tarball will be selected here
		install_stages = (("1",_(u"Stage1 is used when you want to bootstrap&build from scratch.")),
						("2",_(u"Stage2 is used for building from a bootstrapped semi-compiled state.")),
						("3",_(u"Stage3 is a basic system that has been built for you (no compiling).")), 
						("3+GRP", _(u"A Stage3 install but using binaries from the LiveCD when able.")))
		code, install_stage = self._d.menu(_(u"Which stage do you want to start at?"), choices=install_stages, cancel=_(u"Back"), width=78)
		stage3warning = ""
		if code == self._DLG_OK:
			if install_stage == "3+GRP":
				stage3warning = "\nWARNING: Since you are doing a GRP install it is HIGHLY recommended you choose Create from CD to avoid a potentially broken installation."
				try:
					self._install_profile.set_grp_install(None, True, None)
				except:
					self._d.msgbox(_(u"ERROR! Could not set install stage!"))
				install_stage = "3"
			try:			
				self._install_profile.set_install_stage(None, install_stage, None)
			except:
				self._d.msgbox(_(u"ERROR! Could not set install stage!"))
		has_systempkgs = GLIUtility.is_file("/usr/livecd/systempkgs.txt")
		if install_stage == "3" and has_systempkgs:
			#Change the Yes/No buttons to new labels for this question.
			self._d.add_persistent_args(["--yes-label", _(u"Create from CD")])
			self._d.add_persistent_args(["--no-label", _(u"Specify URI")])
			if self._d.yesno(_(u"Do you want to generate a stage3 on the fly using the files on the LiveCD (fastest) or do you want to grab your stage tarball from the Internet?"+stage3warning), width=55) == self._DLG_YES:
				#Generate on the FLY				
				try:
					self._install_profile.set_dynamic_stage3(None, True, None)
				except:
					self._d.msgbox(_(u"ERROR: Could not set the stage tarball URI!"))
				return
		#Specify URI
		#subarches = { 'x86': ("x86", "i686", "pentium3", "pentium4", "athlon-xp"), 'hppa': ("hppa1.1", "hppa2.0"), 'ppc': ("g3", "g4", "g5", "ppc"), 'sparc': ("sparc32", "sparc64")}
		type_it_in = False
		stage_tarball = ""
		if GLIUtility.ping("www.gentoo.org"):  #Test for network connectivity
			mirrors = GLIUtility.list_mirrors()
			mirrornames = []
			mirrorurls = []
			for item in mirrors:
				mirrornames.append(item[1])
				mirrorurls.append(item[0])
			code, mirror = self._d.menu(_(u"Select a mirror to grab the tarball from or select Cancel to enter an URI manually."), choices=self._dmenu_list_to_choices(mirrornames), width=77, height=20)
			if code != self._DLG_OK:
				type_it_in = True
			else:
				mirror = mirrorurls[int(mirror)-1]
				arch = self._client_profile.get_architecture_template()
				subarches = GLIUtility.list_subarch_from_mirror(mirror,arch)
				if subarches:
					code, subarch = self._d.menu(_(u"Select the sub-architecture that most closely matches your system (this changes the amount of optimization):"), choices=self._dmenu_list_to_choices(subarches))
					if code != self._DLG_OK:
						type_it_in = True
					else:
						subarch = subarches[int(subarch)-1]	
				else:
					subarch = ""
				if not type_it_in:
					tarballs = GLIUtility.list_stage_tarballs_from_mirror(mirror, arch, subarch)
					code, stage_tarball = self._d.menu(_(u"Select your desired stage tarball:"), choices=self._dmenu_list_to_choices(tarballs))
					if (code != self._DLG_OK):
						type_it_in = True
					else:
						stage_tarball = mirror + "/releases/" + arch + "/current/stages/" + subarch + tarballs[int(stage_tarball)-1]
		#get portageq envvar value of cflags and look for x86, i686,etc.
			#URL SYNTAX
			#http://gentoo.osuosl.org/releases/ARCHITECTURE/current/stages/SUB-ARCH/
		else:
			type_it_in = True
		if type_it_in:
			code, stage_tarball = self._d.inputbox(_(u"Specify the stage tarball URI or local file:"), init=self._install_profile.get_stage_tarball_uri())
			if code != self._DLG_OK:
				return
		#If Doing a local install, check for valid file:/// uri
		if stage_tarball:
			if not GLIUtility.is_uri(stage_tarball, checklocal=self.local_install):
				self._d.msgbox(_(u"The specified URI is invalid.  It was not saved.  Please go back and try again."));
			else: self._install_profile.set_stage_tarball_uri(None, stage_tarball, None)
		else: self._d.msgbox(_(u"No URI was specified!"))
			#if d.yesno("The specified URI is invalid. Use it anyway?") == DLG_YES: install_profile.set_stage_tarball_uri(None, stage_tarball, None)
	
	def set_portage_tree(self):
	# This section will ask whether to sync the tree, whether to use a snapshot, etc.
		if self._install_profile.get_dynamic_stage3():  #special case
			try:
				self._install_profile.set_portage_tree_sync_type(None,"snapshot", None)
				cd_snapshot_uri = GLIUtility.get_cd_snapshot_uri()
				self._install_profile.set_portage_tree_snapshot_uri(None, cd_snapshot_uri, None)
			except:
				self._d.msgbox(_(u"ERROR! Could not set the portage cd snapshot URI!"))
			return
			
		#Normal case
		menulist = [("Sync", _(u"Normal. Use emerge sync RECOMMENDED!")),
		("Webrsync", _(u"HTTP daily snapshot. Use when rsync is firewalled.")),
		("Snapshot", _(u"Use a portage snapshot, either a local file or a URL")),
		("None", _(u"Extra cases such as if /usr/portage is an NFS mount"))]
		code, portage_tree_sync = self._d.menu(_(u"Which method do you want to use to sync the portage tree for the installation?  If choosing a snapshot you will need to provide the URI for the snapshot if it is not on the livecd."),width=75, height=17, choices=menulist)
		if code != self._DLG_OK: 
			return
		self._install_profile.set_portage_tree_sync_type(None, portage_tree_sync.lower(), None)
		if portage_tree_sync == "Snapshot":
			if self._install_profile.get_portage_tree_snapshot_uri():
				initval = self._install_profile.get_portage_tree_snapshot_uri()
			else:
				initval = GLIUtility.get_cd_snapshot_uri()
			code, snapshot = self._d.inputbox(_(u"Enter portage tree snapshot URI"), init=initval)
			if code == self._DLG_OK:
				if snapshot: 
					if not GLIUtility.is_uri(snapshot, checklocal=self.local_install):
						self._d.msgbox(_(u"The specified URI is invalid.  It was not saved.  Please go back and try again."))
					else: 
						self._install_profile.set_portage_tree_snapshot_uri(None, snapshot, None)
			
				else: 
					self._d.msgbox(_(u"No URI was specified! Returning to default emerge sync."))
			#if d.yesno("The specified URI is invalid. Use it anyway?") == DLG_YES: install_profile.set_stage_tarball_uri(None, stage_tarball, None)



	def set_make_conf(self):
	# This section will be for setting things like CFLAGS, ACCEPT_KEYWORDS, and USE
		#special case for dynamic stage3
		if self._install_profile.get_dynamic_stage3() or not self.advanced_mode:
			return
		
		etc_files = self._install_profile.get_etc_files()
		if etc_files.has_key("make.conf"):
			make_conf = etc_files['make.conf']
		else:
			make_conf = {}
		
		self._d.msgbox(_(u"""The installer will now gather information regarding the contents of /etc/make.conf
One of the unique (and best) features of Gentoo is the ability to
define flags (called USE flags) that define what components are 
compiled into applications.  For example, you can enable the alsa
flag and programs that have alsa capability will use it.  
The result is a finely tuned OS with no unnecessary components to
slow you down.
The installer divides USE flag selection into two screens, one for
global USE flags and one for local flags specific to each program.
Please be patient while the screens load. It may take awhile."""), width=73, height=16)
					
		#First set the USE flags, this is a biggie.
		if make_conf.has_key("USE"): 
			system_use_flags = make_conf["USE"]
		else:  #not a preloaded config.  this is the NORMAL case.
			system_use_flags = GLIUtility.spawn("portageq envvar USE", return_output=True)[1].strip().split()
		use_flags = []
		use_local_flags = []
		use_desc = GLIUtility.get_global_use_flags()
		use_local_desc = GLIUtility.get_local_use_flags()
		
		#populate the choices list
		sorted_use = use_desc.keys()
		sorted_use.sort()
		for flagname in sorted_use:
			use_flags.append((flagname, use_desc[flagname], int(flagname in system_use_flags)))
		#present the menu
		code, use_flags = self._d.checklist(_(u"Choose which *global* USE flags you want on the new system"), height=25, width=80,list_height=17, choices=use_flags)	
		
		#populate the chocies list
		sorted_use = use_local_desc.keys()
		sorted_use.sort()
		for flagname in sorted_use:
			use_local_flags.append((flagname, use_local_desc[flagname], int(flagname in system_use_flags)))
		#present the menu
		code, use_local_flags = self._d.checklist(_(u"Choose which *local* USE flags you want on the new system"), height=25, width=80,list_height=17, choices=use_local_flags)	
		temp_use = ""
		for flag in use_flags:
			temp_use += flag + " "
		for flag in use_local_flags:
			temp_use += flag + " "
		make_conf["USE"] = temp_use
		
		if not self._install_profile.get_dynamic_stage3() and self.advanced_mode:
			#Second, set the ACCEPT_KEYWORDS
			#Change the Yes/No buttons to new labels for this question.
			self._d.add_persistent_args(["--yes-label", _(u"Stable")])
			self._d.add_persistent_args(["--no-label", _(u"Unstable")])
			if self._d.yesno(_(u"Do you want to run the normal stable portage tree, or the bleeding edge unstable (i.e. ACCEPT_KEYWORDS=arch)?  If unsure select stable.  Stable is required for GRP installs."), height=12, width=55) == self._DLG_YES:
				#Stable
				make_conf["ACCEPT_KEYWORDS"] = ""
			else:  #Unstable
				make_conf["ACCEPT_KEYWORDS"] = "~" + self._client_profile.get_architecture_template()
		#Third, misc. stuff.
		while self.advanced_mode:
			menulist = [("CFLAGS",_(u"Edit your C Flags and Optimization level")),
			("CHOST", _(u"Change the Host Setting")),
			("MAKEOPTS", _(u"Specify number of parallel makes (-j) to perform.")),
			("FEATURES", _(u"Change portage functionality settings. (distcc/ccache)")),
			("GENTOO_MIRRORS", _(u"Specify mirrors to use for source retrieval.")),
			("SYNC", _(u"Specify server used by rsync to sync the portage tree.")),
			(_(u"Other"), _(u"Specify your own variable and value."))]
			if self._install_profile.get_dynamic_stage3():  #SPECIAL LIST WITHOUT CHOST
				menulist = [("CFLAGS",_(u"Edit your C Flags and Optimization level")),
					("MAKEOPTS", _(u"Specify number of parallel makes (-j) to perform.")),
					("FEATURES", _(u"Change portage functionality settings. (distcc/ccache)")),
					("GENTOO_MIRRORS", _(u"Specify mirrors to use for source retrieval.")),
					("SYNC", _(u"Specify server used by rsync to sync the portage tree.")),
					(_(u"Other"), _(u"Specify your own variable and value."))]
			code, menuitem = self._d.menu(_(u"For experienced users, the following /etc/make.conf variables can also be defined.  Choose a variable to edit or Done to continue."), choices=menulist, cancel=_(u"Done"), width=77)
			if code != self._DLG_OK: 
				break
			if menuitem == _(u"Other"):
				code,menuitem = self._d.inputbox(_(u"Enter the variable name: "))
				if code != self._DLG_OK:
					continue
			oldval = ""
			if make_conf.has_key(menuitem): 
				oldval = make_conf[menuitem]
				if oldval:
					code, newval = self._d.inputbox(_(u"Enter new value for ") + menuitem, init=oldval)
					if code == self._DLG_OK:
						make_conf[menuitem] = newval
					continue
			#SPECIAL CASES here with their own menus.
			if menuitem == "CFLAGS":
				if not make_conf.has_key("CFLAGS"):
					try:
						cflags = GLIUtility.get_value_from_config("/etc/make.conf","CFLAGS")
					except:
						cflags = ""
				else:
					cflags = make_conf['CFLAGS']
				while 1:
					choices_list = [
					("CLEAR",_(u"Erase the current value and start over.")),
					("-mcpu",_(u"Add a CPU optimization (deprecated in GCC 3.4)")),
					("-mtune",_(u"Add a CPU optimization (GCC 3.4+)")),
					("-march",_(u"Add an Architecture optimization")),
					("-O",_(u"Add optimization level (please do NOT go over 2)")),
					("-fomit-frame-pointer",_(u"For advanced users only.")),
					("-pipe",_(u"Common additional flag")),
					(_(u"Manual"),_(u"Specify your CFLAGS manually"))
					]
					code, choice = self._d.menu(_(u"Choose a flag to add to the CFLAGS variable or Done to go back.  The current value is: ")+ cflags, choices=choices_list, cancel=_(u"Done"), width=70)
					if code != self._DLG_OK:
						break
					if choice == "CLEAR":
						cflags = ""
					elif choice == _(u"Manual"):
						code, cflags = self._d.inputbox(_(u"Enter new value for ") + menuitem)
						break
					elif choice in ["-fomit-frame-pointer","-pipe"]:
						cflags += " "+choice
					else:
						code, newval = self._d.inputbox(_(u"Enter the new value for %s (value only):") % choice)
						if code != self._DLG_OK or not newval:
							continue
						if choice == "-O":
							cflags += " "+choice+newval
						else:
							cflags += " "+choice+"="+newval
				if cflags:
					make_conf['CFLAGS'] = cflags
			elif menuitem == "CHOST":
				choices_list = GLIUtility.get_chosts(self._client_profile.get_architecture_template())
				code, chost = self._d.menu(_(u"Choose from the available CHOSTs for your architecture."), choices=self._dmenu_list_to_choices(choices_list), width=77)
				if code != self._DLG_OK: 
					continue
				chost = choices_list[int(chost)-1]
				make_conf['CHOST'] = chost
			elif menuitem == "MAKEOPTS":
				makeopt_string = _(u"Presently the only use is for specifying the number of parallel makes (-j) to perform. The suggested number for parallel makes is CPUs+1.  Enter the NUMBER ONLY:")
				code, newval = self._d.inputbox(makeopt_string, width=60)
				if code != self._DLG_OK:
					continue
				make_conf['MAKEOPTS'] = "-j "+str(newval)
			elif menuitem == "FEATURES":
				choices_list = [("sandbox",_(u"enables sandboxing when running emerge and ebuild."),0),
				("ccache",_(u"enables ccache support via CC."),0),
				("distcc",_(u"enables distcc support via CC."),0),
				("distlocks",_(u"enables distfiles locking using fcntl or hardlinks."),0),
				("buildpkg",_(u"create binaries of all packages emerged"),0),
				(_(u"Other"),_(u"Input your list of FEATURES manually."),0)	]
				features_string = _(u"FEATURES are settings that affect the functionality of portage. Most of these settings are for developer use, but some are available to non-developers as well.")
				code, choices = self._d.checklist(features_string, choices=choices_list, width=75)
				if code != self._DLG_OK:
					continue
				if _(u"Other") in choices:
					code, features = self._d.inputbox(_(u"Enter the value of FEATURES: "))
				elif choices:
					features = string.join(choices, ' ')
				else:
					features = ""
				if features:
					make_conf['FEATURES'] = features
			else:
				code, newval = self._d.inputbox(_(u"Enter new value for ") + menuitem)
				if code == self._DLG_OK and newval:
					make_conf[menuitem] = newval

		try:
			if make_conf:
				etc_files['make.conf'] = make_conf
				self._install_profile.set_etc_files(etc_files)
		except:
			self._d.msgbox(_(u"ERROR! Could not set the make_conf correctly!"))

	def set_distcc(self):
		#Change the Yes/No buttons for this question.
		self._d.add_persistent_args(["--yes-label", _(u"Yes")])
		self._d.add_persistent_args(["--no-label", _(u"No")])
		if self._d.yesno(_(u"Do you want to use distcc to compile your extra packages during the install and for future compilations as well?"), height=12, width=60) == self._DLG_YES:
			#Add distcc to the services list.
			if self._install_profile.get_services():
				services = self._install_profile.get_services()
				if isinstance(services, str):
					services = services.split(',')
			else:
				services = []
			if not "distccd" in services:
				services.append("distccd")
			try:
				services = string.join(services, ',')
				if services:
					self._install_profile.set_services(None, services, None)
			except:
				self._d.msgbox(_(u"ERROR! Could not set the services list."))
				return
			#Set the distcc flag to emerge earlier than other packages.
			try:
				self._install_profile.set_install_distcc(None, True, None)
			except:
				self._d.msgbox(_(u"ERROR! Could not set the install distcc flag!"))
				return

			#Add distcc to the FEATURES in make.conf and add DISTCC_HOSTS too.
			etc_files = self._install_profile.get_etc_files()
			#load up the make.conf
			if etc_files.has_key("make.conf"):
				make_conf = etc_files['make.conf']
			else:
				make_conf = {}
			#Check for FEATURES and add if not already there.
			if make_conf.has_key("FEATURES"):
				if not "distcc" in make_conf['FEATURES']:
					make_conf['FEATURES'] += " distcc"
			else:
				make_conf['FEATURES'] = "distcc"
			#Now while still working in make.conf, figure out what HOSTS to set.
			if make_conf.has_key("DISTCC_HOSTS"):
				initval = make_conf['DISTCC_HOSTS']
			else:
				initval = "localhost "
			distcc_string = _(u"Enter the hosts to be used by distcc for compilation:\nExample: localhost    192.168.0.2     192.168.0.3:4000/10")
			code, hosts = self._d.inputbox(distcc_string, width=75, init=initval)
			if code != self._DLG_OK:
				hosts = initval
			make_conf['DISTCC_HOSTS'] = hosts
			try:
				etc_files['make.conf'] = make_conf
				self._install_profile.set_etc_files(etc_files)
			except:
				self._d.msgbox(_(u"ERROR! Could not set the make_conf correctly!"))	

	def set_etc_portage(self):
		if self._networkless: return
	#This section will be for editing the /etc/portage/* files and other /etc/* files.  This should be for advanced users only.
		etc_files = self._install_profile.get_etc_files()
		while self.advanced_mode:
			
			menulist = [("portage/package.mask",_(u"A list of DEPEND atoms to mask.")),
			("portage/package.unmask",_(u"A list of packages to unmask.")),
			("portage/package.keywords",_(u"Per-package KEYWORDS (like ACCEPT_KEYWORDS).")),
			("portage/package.use",_(u"Per-package USE flags.")),
			(_(u"Other"),_(u"Type your own name of a file to edit in /etc/"))]
			code, menuitem = self._d.menu(_(u"For experienced users, the following /etc/* variables can also be defined.  Choose a variable to edit or Done to continue."), choices=menulist, cancel=_(u"Done"), width=77)
			if code != self._DLG_OK: 
				break  #get out of the while loop. then save and continue
			
			if menuitem == _(u"Other"):
				code, menuitem = self._d.inputbox(_(u"Enter the name of the /etc/ file you would like to edit (DO NOT type /etc/)"))
				if code != self._DLG_OK:
					return
			oldval = ""
			if etc_files.has_key(menuitem): 
				oldval = etc_files[menuitem]
				
			code, newval = self._d.inputbox(_(u"Enter new contents (use \\n for newline) of ") + menuitem, init=oldval)
			if code == self._DLG_OK:
				etc_files[menuitem] = []
				etc_files[menuitem].append(newval)
		try:
			self._install_profile.set_etc_files(etc_files)
		except:
			self._d.msgbox(_(u"ERROR! Could not set etc/portage/* correctly!"))

		

	def set_kernel(self):
		if self._networkless: return
	# This section will be for choosing kernel sources, choosing (and specifying) a custom config or genkernel, modules to load at startup, etc.
		kernel_sources = [("livecd-kernel", _(u"Copy over the current running kernel (fastest)")),
		("vanilla-sources", _(u"The Unaltered Linux Kernel ver 2.6+ (safest)")),
		("gentoo-sources", _(u"Gentoo's optimized 2.6+ kernel. (less safe)")),
		("hardened-sources", _(u"Hardened sources for the 2.6 kernel tree")),
		("grsec-sources",_(u"Vanilla sources with grsecurity patches")),
		(_(u"Other"), _(u"Choose one of the other sources available."))]
		code, menuitem = self._d.menu(_(u"Choose which kernel sources to use for your system.  If using a previously-made kernel configuration, make sure the sources match the kernel used to create the configuration."), choices=kernel_sources, width=77, height=17)
		if code != self._DLG_OK: 
			return
		if menuitem == _(u"Other"):
			code, menuitem = self._d.inputbox(_(u"Please enter the desired kernel sources package name:"))
			if code != self._DLG_OK: return
		try:
			self._install_profile.set_kernel_source_pkg(None, menuitem, None)
		except:
			self._d.msgbox(_(u"ERROR! Could not set the kernel source package!"))
		if not menuitem == "livecd-kernel":
			#Change the Yes/No buttons to new labels for this question.
			self._d.add_persistent_args(["--yes-label", _(u"Genkernel")])
			self._d.add_persistent_args(["--no-label", _(u"Traditional (requires a config!)")])
			kernel_string1 = _(u"There are currently two ways the installer can compile a kernel for your new system.  You can either provide a previously-made kernel configuration file and use the traditional kernel-compiling procedure (no initrd) or have genkernel automatically create your kernel for you (with initrd).  \n\n If you do not have a previously-made kernel configuration, YOU MUST CHOOSE Genkernel.  Choose which method you want to use.")
			if self._d.yesno(kernel_string1, width=76,height=13) == self._DLG_YES:   #Genkernel
				self._install_profile.set_kernel_build_method(None,"genkernel", None)
				if self.advanced_mode:
					#Change the Yes/No buttons back.
					self._d.add_persistent_args(["--yes-label", _(u"Yes")])
					self._d.add_persistent_args(["--no-label", _(u"No")])
					if self._d.yesno(_(u"Do you want the bootsplash screen to show up on bootup?")) == self._DLG_YES:
						self._install_profile.set_kernel_bootsplash(None, True, None)
					else:
						self._install_profile.set_kernel_bootsplash(None, False, None)
			else: 	#Custom
				self._install_profile.set_kernel_build_method(None,"custom", None)
			if self.advanced_mode:
				code, custom_kernel_uri = self._d.inputbox(_(u"If you have a custom kernel configuration, enter its location (otherwise just press Enter to continue):"), height=13, width=50)
				if code == self._DLG_OK: 
					if custom_kernel_uri: 
						if not GLIUtility.is_uri(custom_kernel_uri, checklocal=self.local_install):
							self._d.msgbox(_(u"The specified URI is invalid.  It was not saved.  Please go back and try again."))
						else: 
							try:
								self._install_profile.set_kernel_config_uri(None, custom_kernel_uri, None)
							except:
								self._d.msgbox(_(u"ERROR! Could not set the kernel config URI!"))
				#else: self._d.msgbox(_(u"No URI was specified!  Reverting to using genkernel"))
				
	def set_boot_loader(self):
		arch = self._client_profile.get_architecture_template()
		parts = self._install_profile.get_partition_tables()
		#Bootloader code yanked from the x86ArchTemplate
		if self._install_profile.get_boot_device():
			boot_device = self._install_profile.get_boot_device()
		else:
			boot_device = ""
			foundboot = False
			for device in parts:
				tmp_partitions = parts[device] #.get_install_profile_structure()
				for partition in tmp_partitions:
					mountpoint = tmp_partitions[partition]['mountpoint']
					if (mountpoint == "/boot"):
						foundboot = True
					if (( (mountpoint == "/") and (not foundboot) ) or (mountpoint == "/boot")):
						boot_device = device

		arch_loaders = { 'x86': [
			("grub",_(u"GRand Unified Bootloader, newer, RECOMMENDED")),
			("lilo",_(u"LInux LOader, older, traditional.(detects windows partitions)"))],
		'amd64': [
			("grub",_(u"GRand Unified Bootloader, newer, RECOMMENDED"))]} #FIXME ADD OTHER ARCHS
		boot_loaders = arch_loaders[arch]
		boot_loaders.append(("none", _(u"Do not install a bootloader.  (System may be unbootable!)")))
		boot_string1 = _(u"To boot successfully into your new Linux system, a bootloader will be needed.  If you already have a bootloader you want to use you can select None here.  The bootloader choices available are dependent on what GLI supports and what architecture your system is.  Choose a bootloader")
		code, menuitem = self._d.menu(boot_string1, choices=boot_loaders, height=16, width=74)
		if code != self._DLG_OK: 
			return
		try:
			self._install_profile.set_boot_loader_pkg(None, menuitem, None)
		except:
			self._d.msgbox(_(u"ERROR! Could not set boot loader pkg! ")+menuitem)
		if menuitem != "none" and self.advanced_mode:
			#Reset the Yes/No labels.
			self._d.add_persistent_args(["--yes-label", _(u"Yes")])
			self._d.add_persistent_args(["--no-label",_(u"No")])
			boot_string2 = _(u"Most bootloaders have the ability to install to either the Master Boot Record (MBR) or some other partition.  Most people will want their bootloader installed on the MBR for successful boots, but if you have special circumstances, you can have the bootloader installed to the /boot partition instead.  Do you want the boot loader installed in the MBR? (YES is RECOMMENDED)")
			if self._d.yesno(boot_string2, height=13, width=55) == self._DLG_YES:
				self._install_profile.set_boot_loader_mbr(None, True, None)
			else:
				self._install_profile.set_boot_loader_mbr(None, False, None)
		if self._install_profile.get_boot_loader_mbr():  #If we're installing to MBR gotta check the device.
			if self.advanced_mode or (boot_device[-1] != 'a'):
				#show the menu.
				boot_string3_std = _(u"Your boot device may not be correct.  It is currently set to %s, but this device may not be the first to boot.  Usually boot devices end in 'a' such as hda or sda.") % boot_device
				boot_string3 = _(u"  Please confirm your boot device by choosing it from the menu.")
				if not self.advanced_mode:
					boot_string3 = boot_string3_std + boot_string3
				#grab choies from the partiton list.
				boot_drive_choices = []
				for device in parts:
					boot_drive_choices.append(device)
				if not boot_drive_choices:
					self._d.msgbox(_(u"ERROR: No drives set up.  Please complete the Partitioning screen first!"))
					return
				code, boot_drive_choice = self._d.menu(boot_string3, choices=self._dmenu_list_to_choices(boot_drive_choices), height=16, width=70)
				if code != self._DLG_OK:
					return
				boot_drive_choice = boot_drive_choices[int(boot_drive_choice)-1]
				try:
					self._install_profile.set_boot_device(None,boot_drive_choice,None)
				except:
					self._d.msgbox(_(u"ERROR! Could not set the boot device!")+boot_drive_choice)
		if self.advanced_mode:
			code, bootloader_kernel_args = self._d.inputbox(_(u"If you have any additional optional arguments you want to pass to the kernel at boot, type them here or just press Enter to continue:"), height=12, width=55)
			if code == self._DLG_OK:
				try:
					self._install_profile.set_bootloader_kernel_args(None, bootloader_kernel_args, None)
				except:
					self._d.msgbox(_(u"ERROR! Could not set bootloader kernel arguments! ")+bootloader_kernel_args)
				

	def set_timezone(self):
	# This section will be for setting the timezone.
		zonepath = "/usr/share/zoneinfo"
		skiplist = ["zone.tab","iso3166.tab","posixrules"]
		while 1:
			tzlist = []
			for entry in os.listdir(zonepath):
				if entry not in skiplist:
					if os.path.isdir(zonepath + "/" + entry): entry += "/"
					tzlist.append(entry)
			tzlist.sort()
			timezone_string = _(u"Please select the timezone for the new installation.  Entries ending with a / can be selected to reveal a sub-list of more specific locations. For example, you can select America/ and then Chicago.")
			code, tznum = self._d.menu(timezone_string, choices=self._dmenu_list_to_choices(tzlist), height=20, cancel="Back")
			if code == self._DLG_OK:
				zonepath = os.path.join(zonepath,tzlist[int(tznum)-1])
				if tzlist[int(tznum)-1][-1:] != "/": 
					break
			else:
				if zonepath == "/usr/share/zoneinfo": 
					return
				slashloc = zonepath[:-1].rfind("/")
				zonepath = zonepath[:slashloc]
		try:
			self._install_profile.set_time_zone(None, zonepath[20:], None)
		except:
			self._d.msgbox(_(u"ERROR: Could not set that timezone!"))

	def set_networking(self):
	# This section will be for setting up network interfaces
		interfaces = self._install_profile.get_network_interfaces()
		CC_iface = self._client_profile.get_network_interface()
		if CC_iface and (CC_iface not in interfaces):
			#The CC has a network config that's not already there.  Preload it.
			CC_net_type = self._client_profile.get_network_type()
			if CC_net_type == 'dhcp':
				try:
					interfaces[CC_iface] = ('dhcp', self._client_profile.get_network_dhcp_options(), None)
				except:
					pass
			else:
				try:
					interfaces[CC_iface] = (self._client_profile.get_network_ip(), self._client_profile.get_network_broadcast(), self._client_profile.get_network_netmask())
				except:
					pass
			
		while 1:
			net_string1 = _(u"Here you will enter all of your network interface information for the new system.  You can either choose a network interface to edit, add a network interface, delete an interface, or edit the miscellaneous options such as hostname and proxy servers.")
			net_string2 = _(u"To setup your network interface, you can either use DHCP if enabled, or manually enter your network information.\n  DHCP (Dynamic Host Configuration Protocol) makes it possible to automatically receive networking information (IP address, netmask, broadcast address, gateway, nameservers etc.). This only works if you have a DHCP server in your network (or if your provider provides a DHCP service).  If you do not, you must enter the information manually.  Please select your networking configuration method:")
			choice_list = []
			for iface in interfaces:
				if interfaces[iface][0] == 'dhcp':
					choice_list.append((iface, _(u"Settings: DHCP. Options: ")+ interfaces[iface][1]))
				else:
					choice_list.append((iface, _(u"IP: ")+interfaces[iface][0]+_(u" Broadcast: ")+interfaces[iface][1]+_(u" Netmask: ")+interfaces[iface][2]))
			choice_list.append(("Add",_(u"Add a new network interface")))
			code, iface_choice = self._d.menu(net_string1, choices=choice_list, cancel=_(u"Save and Continue"), height=18, width=77)
			if code != self._DLG_OK:
				try:
					self._install_profile.set_network_interfaces(interfaces)
				except:
					self_d.msgbox(_(u"ERROR! Could not set the network interfaces!"))
				break  #This should hopefully move the user down to part two of set_networking
			if iface_choice == "Add":
				if self.local_install:
					device_list = GLIUtility.get_eth_devices()
					newchoice_list = []
					for device in device_list:
						if device not in interfaces:
							newchoice_list.append((device, GLIUtility.get_interface_realname(device)))
					newchoice_list.append((_(u"Other"),_(u"Type your own.")))
					code, newnic = self._d.menu(_("Choose an interface from the list or Other to type your own if it was not detected."), choices=newchoice_list, width=75)
				else:
					newnic == _(u"Other")
				if newnic == _(u"Other"):
					code, newnic = self._d.inputbox(_(u"Enter name for new interface (eth0, ppp0, etc.)"))
					if code != self._DLG_OK: 
						continue
					if newnic in interfaces:
						self._d.msgbox(_(u"An interface with the name is already defined."))
						continue
				#create the interface in the data structure.
				#interfaces[newnic] = ("", "", "")
				#Change the Yes/No buttons to new labels for this question.
				self._d.add_persistent_args(["--yes-label", _(u"DHCP")])
				self._d.add_persistent_args(["--no-label", _(u"Static IP/Manual")])
				if self._d.yesno(net_string2, height=15, width=60) == self._DLG_YES: #DHCP
					dhcp_options = ""
					if self.advanced_mode:
						code, dhcp_options = self._d.inputbox(_(u"If you have any additional DHCP options to pass, type them here in a space-separated list.  If you have none, just press Enter."), height=13, width=50)
					interfaces[newnic] = ('dhcp', dhcp_options, None)
				else:
					network_type = 'static'
					code, data = self._d.form(_(u'Enter your networking information: (See Chapter 3 of the Handbook for more information)  Your broadcast address is probably your IP address with 255 as the last tuple.  Do not press Enter until all fields are complete!'),
					((_(u'Enter your IP address:'), 15),
					 (_(u'Enter your Broadcast address:'), 15),
					 (_(u'Enter your Netmask:'),15,'255.255.255.0')))
					(ip_address, broadcast, netmask) = data[:-1].split('\n')
					if code != self._DLG_OK: 
						continue
					#Set the info now that it's all gathered.
					interfaces[newnic] = (ip_address, broadcast, netmask)
			else:  #they have chosen an interface, present them with edit/delete
				#Change the Yes/No buttons to new labels for this question.
				self._d.add_persistent_args(["--yes-label", _(u"Edit")])
				self._d.add_persistent_args(["--no-label", _(u"Delete")])
				if self._d.yesno(_(u"For interface %s, you can either edit the interface information (IP Address, Broadcast, Netmask) or Delete the interface.") % iface_choice) == self._DLG_YES:
					#Edit
					#Change the Yes/No buttons to new labels for this question.
					self._d.add_persistent_args(["--yes-label", _(u"DHCP")])
					self._d.add_persistent_args(["--no-label", _(u"Static IP/Manual")])
					if self._d.yesno(net_string2, height=15, width=60) == self._DLG_YES: #DHCP
						dhcp_options = ""
						if self.advanced_mode:
							code, dhcp_options = self._d.inputbox(_(u"If you have any additional DHCP options to pass, type them here in a space-separated list.  If you have none, just press Enter."), height=13, width=50)
						interfaces[iface_choice] = ('dhcp', dhcp_options, None)
					else:
						network_type = 'static'
						code, data = self._d.form(_(u'Enter your networking information: (See Chapter 3 of the Handbook for more information)  Your broadcast address is probably your IP address with 255 as the last tuple.  Do not press Enter until all fields are complete!'), 
						((_(u'Enter your IP address:'), 15, interfaces[iface_choice][0]),
						 (_(u'Enter your Broadcast address:'), 15, interfaces[iface_choice][1]),
						 (_(u'Enter your Netmask:'),15,interfaces[iface_choice][2])))
						(ip_address, broadcast, netmask) = data[:-1].split('\n')
						if code != self._DLG_OK: 
							continue
						#Set the info now that it's all gathered.
						interfaces[iface_choice] = (ip_address, broadcast, netmask)
				else:
					#Delete
					#Reset the Yes/No buttons
					self._d.add_persistent_args(["--yes-label", _(u"Yes")])
					self._d.add_persistent_args(["--no-label", _(u"No")])
					if self._d.yesno(_(u"Are you sure you want to remove the interface ") + iface_choice + "?") == self._DLG_YES:
						del interfaces[iface_choice]
			
		#This section is for defining DNS servers, default routes/gateways, hostname, etc.
		#First ask for the default gateway device and IP
		interfaces = self._install_profile.get_network_interfaces()
		choice_list = []
		for iface in interfaces:
			if interfaces[iface][0] == 'dhcp':
				choice_list.append((iface, _(u"Settings: DHCP. Options: ")+ interfaces[iface][1],0))
			else:
				choice_list.append((iface, _(u"IP: ")+interfaces[iface][0]+_(u" Broadcast: ")+interfaces[iface][1]+_(u" Netmask: ")+interfaces[iface][2],0))
		net_string3 = _("To be able to surf on the internet, you must know which host shares the Internet connection. This host is called the gateway.  It is usually similar to your IP address, but ending in .1\nIf you have DHCP then just select your primary Internet interface (no IP will be needed)  Start by choosing which interface accesses the Internet:")
		if choice_list:
			code, gateway_iface = self._d.radiolist(net_string3, choices=choice_list, height=20, width=67)
			if (code == self._DLG_OK) and gateway_iface:  #They made a choice.  Ask the IP if not DHCP.
				while interfaces[gateway_iface][0] != 'dhcp':
					code, ip = self._d.inputbox(_(u"Enter the gateway IP address for ") + gateway_iface, init=interfaces[gateway_iface][0])
					if code != self._DLG_OK:
						break
					if not GLIUtility.is_ip(ip):
						self._d.msgbox(_(u"Invalid IP Entered!  Please try again."))
						continue
					try:
						self._install_profile.set_default_gateway(None, ip,{'interface': gateway_iface})
					except:
						self._d.msgbox(_(u"ERROR! Coult not set the default gateway with IP %s for interface %s") % (ip, gateway_iface))
					break
		#Now ask for the other info in a large form.
		error = True
		hostname = ""
		domainname = ""
		nisdomainname = ""
		primary_dns = ""
		backup_dns = ""
		http_proxy = ""
		ftp_proxy = ""
		rsync_proxy = ""
		while error:
			error = False
			if self.advanced_mode:
				code, data = self._d.form(_(u'Fill out the remaining networking settings.  The hostname is manditory as that is the name of your computer.  Leave the other fields blank if you are not using them.  If using DHCP you do not need to enter DNS servers.  Do not press Enter until all fields are complete!'),
				((_(u'Enter your Hostname:'), 25, self._install_profile.get_hostname()),
				 (_(u'Enter your Domain Name:'), 25, self._install_profile.get_domainname()),
				 (_(u'Enter your NIS Domain Name:'),25,self._install_profile.get_nisdomainname()),
				 (_(u'Enter a primary DNS server:'),15),
				 (_(u'Enter a backup DNS server:'),15),
				 (_(u'Enter a HTTP Proxy IP:'), 15,self._install_profile.get_http_proxy()),
				 (_(u'Enter a FTP Proxy IP:'), 15, self._install_profile.get_ftp_proxy()), 
				 (_(u'Enter a RSYNC Proxy:'),15,self._install_profile.get_rsync_proxy())))
				if code != self._DLG_OK:
					return
				(hostname, domainname, nisdomainname, primary_dns, backup_dns, http_proxy, ftp_proxy, rsync_proxy) = data[:-1].split('\n')
			else: #standard mode
				code, data = self._d.form(_(u'Fill out the remaining networking settings.  The hostname is manditory as that is the name of your computer.  Leave the other fields blank if you are not using them.  If using DHCP you do not need to enter DNS servers.  Do not press Enter until all fields are complete!'),
				((_(u'Enter your Hostname:'), 25, self._install_profile.get_hostname()),
				 (_(u'Enter your Domain Name:'), 25, self._install_profile.get_domainname()),
				 (_(u'Enter a primary DNS server:'),15),
				 (_(u'Enter a backup DNS server:'),15)))
				if code != self._DLG_OK:
					return
				(hostname, domainname, primary_dns, backup_dns) = data[:-1].split('\n')
			#Check the data before entering it.				
			if hostname:
				if type(hostname) != str:
					self._d.msgbox(_(u"Incorrect hostname!  It must be a string.  Not saved."))
					error = True	
				else:
					try:			
						self._install_profile.set_hostname(None, hostname, None)
					except:
						self._d.msgbox(_(u"ERROR! Could not set the hostname:")+hostname)
						error = True
			if domainname:
				if type(domainname) != str:
					self._d.msgbox(_(u"Incorrect domainname!  It must be a string.  Not saved."))
					error = True	
				else:
					try:			
						self._install_profile.set_domainname(None, domainname, None)
					except:
						self._d.msgbox(_(u"ERROR! Could not set the domainname:")+domainname)
						error = True
			if nisdomainname:
				if type(nisdomainname) != str:
					self._d.msgbox(_(u"Incorrect nisdomainname!  It must be a string.  Not saved."))
					error = True	
				else:
					try:			
						self._install_profile.set_nisdomainname(None, nisdomainname, None)
					except:
						self._d.msgbox(_(u"ERROR! Could not set the nisdomainname:")+nisdomainname)
						error = True					
			if primary_dns:
				if not GLIUtility.is_ip(primary_dns):
					self._d.msgbox(_(u"Incorrect Primary DNS Server! Not saved."))
					error = True
				else:
					if backup_dns:
						if not GLIUtility.is_ip(backup_dns):
							self._d.msgbox(_(u"Incorrect Backup DNS Server! Not saved."))
							error = True
						else:
							primary_dns = primary_dns + " " + backup_dns
					try:			
						self._install_profile.set_dns_servers(None, primary_dns, None)
					except:
						self._d.msgbox(_(u"ERROR! Could not set the DNS Servers:")+primary_dns)
						error = True
			if http_proxy:
				if not GLIUtility.is_uri(http_proxy):
					self._d.msgbox(_(u"Incorrect HTTP Proxy! It must be a uri. Not saved."))
					error = True
				else:
					try:
						self._install_profile.set_http_proxy(None, http_proxy, None)
					except:
						self._d.msgbox(_(u"ERROR! Could not set the HTTP Proxy:")+http_proxy)
						error = True					
			if ftp_proxy:
				if not GLIUtility.is_uri(ftp_proxy):
					self._d.msgbox(_(u"Incorrect FTP Proxy! It must be a uri. Not saved."))
					error = True
				else:
					try:
						self._install_profile.set_ftp_proxy(None, ftp_proxy, None)
					except:
						self._d.msgbox(_(u"ERROR! Could not set the FTP Proxy:")+ftp_proxy)
						error = True
			if rsync_proxy:
				if not GLIUtility.is_uri(rsync_proxy):
					self._d.msgbox(_(u"Incorrect RSYNC Proxy! It must be a uri. Not saved."))
					error = True
				else:
					try:
						self._install_profile.set_rsync_proxy(None, rsync_proxy, None)
					except:
						self._d.msgbox(_(u"ERROR! Could not set the RSYNC Proxy:")+rsync_proxy)
						error = True


	def set_cron_daemon(self):
		if self._networkless: return
		cron_daemons = (("vixie-cron", _(u"Paul Vixie's cron daemon, fully featured, RECOMMENDED.")),
		("dcron",_(u"A cute little cron from Matt Dillon.")), 
		("fcron", _(u"A scheduler with extended capabilities over cron & anacron")), 
		("None", _(u"Don't use a cron daemon. (NOT Recommended!)")))
		cron_string = _(u"A cron daemon executes scheduled commands. It is very handy if you need to execute some command regularly (for instance daily, weekly or monthly).  Gentoo offers three possible cron daemons: dcron, fcron and vixie-cron. Installing one of them is similar to installing a system logger. However, dcron and fcron require an extra configuration command, namely crontab /etc/crontab. If you don't know what to choose, use vixie-cron.  If doing a networkless install, choose vixie-cron.  Choose your cron daemon:")
		code, menuitem = self._d.menu(cron_string, choices=cron_daemons, height=21, width=77)
		if code == self._DLG_OK:
			if menuitem == "None": 
				menuitem = ""
			self._install_profile.set_cron_daemon_pkg(None, menuitem, None)

	def set_logger(self):
		if self._networkless: return
		loggers = (("syslog-ng", _(u"An advanced system logger.")), 
		("metalog", _(u"A Highly-configurable system logger.")), 
		("syslogkd", _(u"The traditional set of system logging daemons.")))
		logger_string = _(u"Linux has an excellent history of logging capabilities -- if you want you can log everything that happens on your system in logfiles. This happens through the system logger. Gentoo offers several system loggers to choose from.  If you plan on using sysklogd or syslog-ng you might want to install logrotate afterwards as those system loggers don't provide any rotation mechanism for the log files.  If doing networkless, choose syslog-ng.  Choose a system logger:")
		code, menuitem = self._d.menu(logger_string, choices=loggers, height=21, width=68)
		if code == self._DLG_OK:
			self._install_profile.set_logging_daemon_pkg(None, menuitem, None)

	def set_extra_packages(self):
		#d.msgbox("This section is for selecting extra packages (pcmcia-cs, rp-pppoe, xorg-x11, etc.) and setting them up")
		if self._install_profile.get_install_packages():
			install_packages = self._install_profile.get_install_packages()
			if isinstance(install_packages, str):
				install_packages = install_packages.split()
		else:
			install_packages = []
		package_list = self._install_profile.get_install_package_list()
		highlevel_menu = []
		for group in package_list:
			highlevel_menu.append( (group, package_list[group][0]) )
		highlevel_menu.append( ("Manual", "Type your own space-separated list of packages.") )

		while 1:
			extra_string1 = _(u"There are thousands of applications available to Gentoo users through Portage, Gentoo's package management system.  Select some of the more common ones below or add your own additional package list by choosing 'Manual'.")
			code, submenu = self._d.menu(extra_string1+ _(u"\nYour current package list is: ")+string.join(install_packages, ','), choices=highlevel_menu, cancel=_(u"Save and Continue"), width=70, height=23)
			if code != self._DLG_OK:  #Save and move on.
				try:
					packages = string.join(install_packages, ' ')
					if packages:
						self._install_profile.set_install_packages(None, packages, None)
				except:
					self._d.msgbox(_(u"ERROR! Could not set the install packages! List of packages:"))
				return
			#Popular Desktop Applications
			choices_list = []
			#pkgs = {}
			
			#Special case first.
			if submenu == "Manual":
				code, tmp_install_packages = self._d.inputbox(_(u"Enter a space-separated list of extra packages to install on the system"), init=string.join(install_packages, ' '), width=70) 
				if code == self._DLG_OK:
					install_packages = tmp_install_packages.split()
				continue
				
			#All other cases load pkgs and GRP
			pkgs = package_list[submenu][1]
			grp_list = GLIUtility.get_grp_pkgs_from_cd()
			for pkg in pkgs:
				if pkg in grp_list:
					choices_list.append((pkg, "(GRP) "+pkgs[pkg], int(pkg in install_packages)))
				else:
					if not self._networkless:
						choices_list.append((pkg, pkgs[pkg], int(pkg in install_packages)))
			if not choices_list: continue
			code, choices = self._d.checklist(_(u"Choose from the listed packages.  If doing a networkless install, only choose (GRP) packages."), choices=choices_list, height=19, list_height=10, width=77)
			if code != self._DLG_OK: 
				continue
			for pkg in pkgs:  #clear out packages from this list that are already in install_packages so that you can uncheck packages and they will be removed.  the ones that remain checked will be re-added.
				for i, tmppkg in enumerate(install_packages):
					if tmppkg == pkg:
						del install_packages[i]
					
			for package in choices:
				install_packages.append(package)
				#special cases for desktop environments
				if package in ["xorg-x11", "gnome","kde","blackbox","enlightenment","fluxbox","xfce4"]:  #ask about X
					#Reset the Yes/No buttons
					self._d.add_persistent_args(["--yes-label", _(u"Yes")])
					self._d.add_persistent_args(["--no-label", _(u"No")])
					if not self.advanced_mode or self._d.yesno(_(u"Do you want to start X on bootup?")) == self._DLG_YES:
						services = self._install_profile.get_services() or 'xdm'
						if isinstance(services, list):
							services = string.join(services, ',')
						if 'xdm' not in services:
							services += ',xdm'
						try:
							self._install_profile.set_services(None, services, None)
						except:
							self._d.msgbox(_(u"ERROR! Could not set the services list."))
					#rc.conf changes specific to packages.
					if package == "gnome":
						etc_files = self._install_profile.get_etc_files()
						if not "rc.conf" in etc_files:
							etc_files['rc.conf'] = {}
						etc_files['rc.conf']['DISPLAYMANAGER'] = "gdm"
						self._install_profile.set_etc_files(etc_files)
					if package == "kde":
						etc_files = self._install_profile.get_etc_files()
						if not "rc.conf" in etc_files:
							etc_files['rc.conf'] = {}
						etc_files['rc.conf']['DISPLAYMANAGER'] = "kdm"
						self._install_profile.set_etc_files(etc_files)
					if package == "enlightenment":
						etc_files = self._install_profile.get_etc_files()
						if not "rc.conf" in etc_files:
							etc_files['rc.conf'] = {}
						etc_files['rc.conf']['DISPLAYMANAGER'] = "entrance"
						self._install_profile.set_etc_files(etc_files)
					if package == "fluxbox":
						etc_files = self._install_profile.get_etc_files()
						if not "rc.conf" in etc_files:
							etc_files['rc.conf'] = {}
						etc_files['rc.conf']['XSESSION'] = "fluxbox"
						self._install_profile.set_etc_files(etc_files)	
						
						

	def set_services(self):
		if self._install_profile.get_services():
			services = self._install_profile.get_services()
			if isinstance(services, str):
				services = services.split(',')
		else:
			services = []
		choice_list = [("alsasound", _(u"ALSA Sound Daemon"),int("alsasound" in services)),
		("apache", _(u"Common web server (version 1.x)"),int("apache" in services)),
		("apache2", _(u"Common web server (version 2.x)"),int("apache2" in services)),
		("distccd", _(u"Distributed Compiling System"),int("distccd" in services)),
		("esound", _(u"ESD Sound Daemon"),int("esound" in services)),
		("hdparm", _(u"Hard Drive Tweaking Utility"),int("hdparm" in services)),
		("local", _(u"Run scripts found in /etc/conf.d/local.start"),int("local" in services)),
		("portmap", _(u"Port Mapping Service"),int("portmap" in services)),
		("proftpd", _(u"Common FTP server"),int("proftpd" in services)),
		("sshd", _(u"SSH Daemon (allows remote logins)"),int("sshd" in services)),
		("xfs", _(u"X Font Server"),int("xfs" in services)),
		("xdm", _(u"X Daemon"),int("xdm" in services)),
		(_(u"Other"),_(u"Manually specify your services in a comma-separated list."),0)]
		services_string = _(u"Choose the services you want started on bootup.  Note that depending on what packages are selected, some services listed will not exist.")
		code, services_list = self._d.checklist(services_string, choices=choice_list, height=21, list_height=12, width=77)
		if code != self._DLG_OK:
			return
		services = []
		for service in services_list:
			services.append(service)
		if _(u"Other") in services_list:
			code, services = self._d.inputbox(_(u"Enter a comma-separated list of services to start on boot"), init=string.join(services, ','))
		if code != self._DLG_OK: 
			return
		try:
			services = string.join(services, ',')
			if services:
				self._install_profile.set_services(None, services, None)
		except:
			self._d.msgbox(_(u"ERROR! Could not set the services list."))
			return
		
	def set_rc_conf(self):
	# This section is for editing /etc/rc.conf
		if not self.advanced_mode:
			return
		etc_files = self._install_profile.get_etc_files()
		keymap = ""
		windowkeys = ""
		ext_keymap = ""
		font = ""
		trans = ""
		clock = ""
		editor = ""
		disp_manager = ""
		xsession = ""
		rc_string1 = _(u"Additional configuration settings for Advanced users (rc.conf)\nHere are some other variables you can set in various configuration files on the new system.  If you don't know what a variable does, don't change it!")
		menulist = [("KEYMAP",_(u"Use KEYMAP to specify the default console keymap.")),
		("SET_WINDOWSKEYS", _(u"Decision to first load the 'windowkeys' console keymap")),
		("EXTENDED_KEYMAPS", _(u"maps to load for extended keyboards.  Most users will leave this as is.")),
		("CONSOLEFONT", _(u"Specifies the default font that you'd like Linux to use on the console.")),
		("CONSOLETRANSLATION", _(u"The charset map file to use.")),
		("CLOCK", _(u"Set the clock to either UTC or local")),
		("EDITOR", _(u"Set EDITOR to your preferred editor.")),
		("DISPLAYMANAGER", _(u"What display manager do you use ?  [ xdm | gdm | kdm | entrance ]")),
		("XSESSION", _(u"a new variable to control what window manager to start default with X"))]
		while 1:
			code, variable = self._d.menu(rc_string1, choices=menulist, cancel=_(u"Save and Continue"), width=77, height=19)
			if code != self._DLG_OK: 
				break
			if variable == "KEYMAP":
				keymap_list = GLIUtility.generate_keymap_list()
				code, keymap = self._d.menu(_(u"Choose your desired keymap:"), choices=self._dmenu_list_to_choices(keymap_list), height=19)
				if code != self._DLG_OK:
					continue
				keymap = keymap_list[int(keymap)-1]
				
			elif variable == "SET_WINDOWSKEYS":
				#Reset the Yes/No buttons
				self._d.add_persistent_args(["--yes-label", _(u"Yes")])
				self._d.add_persistent_args(["--no-label", _(u"No")])
				if self._d.yesno(_(u"Should we first load the 'windowkeys' console keymap?  Most x86 users will say 'yes' here.  Note that non-x86 users should leave it as 'no'.")) == self._DLG_YES:
					windowkeys = "yes"
				else:
					windowkeys = "no"
			elif variable == "EXTENDED_KEYMAPS":
				code, ext_keymap = self._d.inputbox(_(u"This sets the maps to load for extended keyboards.  Most users will leave this as is.  Enter new value for EXTENDED_KEYMAPS"), width=60)
			elif variable == "CONSOLEFONT":
				font_list = GLIUtility.generate_consolefont_list()
				code, font = self._d.menu(_(u"Choose your desired console font:"), choices=self._dmenu_list_to_choices(font_list), height=19)
				if code != self._DLG_OK:
					continue
				font = font_list[int(font)-1]
			elif variable == "CONSOLETRANSLATION":
				trans_list = GLIUtility.generate_consoletranslation_list()
				code, trans = self._d.menu(_(u"Choose your desired console translation:"), choices=self._dmenu_list_to_choices(trans_list), height=19)
				if code != self._DLG_OK:
					continue
				trans = trans_list[int(trans)-1]
			elif variable == "CLOCK":
				#Change the Yes/No buttons to new labels for this question.
				self._d.add_persistent_args(["--yes-label", "UTC"])
				self._d.add_persistent_args(["--no-label", "local"])
				if self._d.yesno(_(u"Should CLOCK be set to UTC or local?  Unless you set your timezone to UTC you will want to choose local.")) == self._DLG_YES:
					clock = "UTC"
				else:
					clock = "local"
			elif variable == "EDITOR":
				choice_list = [("/bin/nano", _(u"Default editor.")), ("/usr/bin/vim", _(u"vi improved editor.")), ("/usr/bin/emacs", _(u"The emacs editor."))]
				code, editor = self._d.menu(_(u"Choose your default editor: "), choices=choice_list)
			elif variable == "DISPLAYMANAGER":
				choice_list = [("xdm", _(u"X Display Manager")), 
				("gdm", _(u"Gnome Display Manager")), 
				("kdm", _(u"KDE Display Manager")), 
				("entrance", _(u"Login Manager for Enlightenment"))]
				code, disp_manager = self._d.menu(_(u"Choose your desired display manager to use when starting X (note you must make sure that package also gets installed for it to work):"), choices=choice_list, width=65)
			elif variable == "XSESSION":
				code, xsession = self._d.inputbox(_(u"Choose what window manager you want to start default with X if run with xdm, startx, or xinit. (common options are Gnome or Xsession:"), width=65, height=12)
			
		if not "conf.d/keymaps" in etc_files: 
			if keymap or windowkeys or ext_keymap:
				etc_files['conf.d/keymaps'] = {}
		if not "conf.d/consolefont" in etc_files: 
			if font or trans:
				etc_files['conf.d/consolefont'] = {}
		if not "conf.d/clock" in etc_files: 
			if clock:
				etc_files['conf.d/clock'] = {}
		if not "rc.conf" in etc_files: 
			if editor or disp_manager or xsession:
				etc_files['rc.conf'] = {}
		if keymap:
			etc_files['conf.d/keymaps']['KEYMAP'] = keymap
		if windowkeys:
			etc_files['conf.d/keymaps']['SET_WINDOWSKEYS'] = windowkeys
		if ext_keymap:
			etc_files['conf.d/keymaps']['EXTENDED_KEYMAPS'] = ext_keymap
		if font:	
			etc_files['conf.d/consolefont']['CONSOLEFONT'] = font
		if trans:
			etc_files['conf.d/consolefont']['CONSOLETRANSLATION'] = trans
		if clock:
			etc_files['conf.d/clock']['CLOCK'] = clock
		if editor:
			etc_files['rc.conf']['EDITOR'] = editor
		if disp_manager:
			etc_files['rc.conf']['DISPLAYMANAGER'] = disp_manager
		if xsession:
			etc_files['rc.conf']['XSESSION'] = xsession
		self._install_profile.set_etc_files(etc_files)
	
	def set_root_password(self):
	# The root password will be set here
		while 1:
			code, passwd1 = self._d.passwordbox(_(u"Please enter your desired password for the root account.  (note it will not show the password.  Also do not try to use backspace.):"))
			if code != self._DLG_OK: 
				return
			code, passwd2 = self._d.passwordbox(_(u"Enter the new root password again for confirmation"))
			if code != self._DLG_OK: 
				return
			if passwd1 != passwd2:
				self._d.msgbox(_(u"The passwords do not match.  Please try again or cancel."))
			else:
				try:
					self._install_profile.set_root_pass_hash(None, GLIUtility.hash_password(passwd1), None)
				except:
					self._d.msgbox(_(u"ERROR! Could not set the new system root password!"))
				self._d.msgbox(_(u"Password saved.  Press Enter to continue."))
				return

	def set_additional_users(self):
	# This section will be for adding non-root users
		users = {}
		for user in self._install_profile.get_users():
			users[user[0]] = (user[0], user[1], user[2], user[3], user[4], user[5], user[6])
		while 1:
			menu_list = []
			for user in users:
				menu_list.append(user)
			menu_list.sort()
			menu_list.append(_(u"Add user"))
			users_string1 = _(u"Working as root on a Unix/Linux system is dangerous and should be avoided as much as possible. Therefore it is strongly recommended to add a user for day-to-day use.  Choose a user to edit:")
			code, menuitem = self._d.menu(users_string1, choices=self._dmenu_list_to_choices(menu_list), cancel="Save and Continue", height=19)
			if code != self._DLG_OK:
				#if self._d.yesno("Do you want to save changes?") == self._DLG_YES:
				tmpusers = []
				for user in users:
					tmpusers.append(users[user])
				try:
					self._install_profile.set_users(tmpusers)
				except:
					self._d.msgbox(_(u"ERROR! Could not set the additional users!"))
				break
			menuitem = menu_list[int(menuitem)-1]
			if menuitem == _(u"Add user"):
				code, newuser = self._d.inputbox(_(u"Enter the username for the new user"))
				if code != self._DLG_OK: 
					continue
				if newuser in users:
					self._d.msgbox(_(u"A user with that name already exists"))
					continue
				code, passwd1 = self._d.passwordbox(_(u"Enter the new password for user ")+ newuser)
				code, passwd2 = self._d.passwordbox(_(u"Enter the new password again for confirmation"))
				if code == self._DLG_OK: 
					if passwd1 != passwd2:
						self._d.msgbox(_(u"The passwords do not match! Go to the menu and try again."))
				#Create the entry for the new user
				new_user = [newuser, GLIUtility.hash_password(passwd1), ('users',), '/bin/bash', '/home/' + newuser, '', '']
				users[newuser] = new_user
				menuitem = newuser
			while 1:
				menulist = [_(u"Password"), _(u"Group Membership"), _(u"Shell"), _(u"Home Directory"), _(u"UID"), _(u"Comment"), _(u"Delete")]
				code, menuitem2 = self._d.menu(_(u"Choose an option for user ") + menuitem, choices=self._dmenu_list_to_choices(menulist), cancel=_(u"Back"))
				if code != self._DLG_OK: 
					break
				menuitem2 = menulist[int(menuitem2)-1]
				if menuitem2 == _(u"Password"):
					code, passwd1 = self._d.passwordbox(_(u"Enter the new password"))
					if code != self._DLG_OK: 
						continue
					code, passwd2 = self._d.passwordbox(_(u"Enter the new password again"))
					if code != self._DLG_OK: 
						continue
					if passwd1 != passwd2:
						self._d.msgbox(_(u"The passwords do not match! Try again."))
						continue
					self._d.msgbox(_(u"Password saved.  Press Enter to continue."))
					users[menuitem][1] = GLIUtility.hash_password(passwd1)
				elif menuitem2 == _(u"Group Membership"):
					prechk = users[menuitem][2]
					choice_list = [("users", _(u"The usual group for normal users."), int("users" in prechk)),
					("wheel", _(u"Allows users to attempt to su to root."), int("wheel" in prechk)),
					("audio", _(u"Allows access to audio devices."), int("audio" in prechk)),
					("games", _(u"Allows access to games."), int("games" in prechk)),
					("apache", _(u"For users who know what they're doing only."), int("apache" in prechk)),
					("cdrom", _(u"For users who know what they're doing only."), int("cdrom" in prechk)),
					("ftp", _(u"For users who know what they're doing only."), int("ftp" in prechk)),
					("video", _(u"For users who know what they're doing only."), int("video" in prechk)),
					(_(u"Other"), _(u"Manually specify your groups in a comma-separated list."), 0)]
					users_string2 = _(u"Select which groups you would like the user %s to be in." % menuitem)
					code, group_list = self._d.checklist(users_string2, choices=choice_list, height=19, list_height=10, width=77)
					if code != self._DLG_OK:
						break
					groups = ""
					for group in group_list:
						groups += group + ","
					if groups:
						groups = groups[:-1]
					if _(u"Other") in group_list:
						code, groups = self._d.inputbox(_(u"Enter a comma-separated list of groups the user is to be in"), init=",".join(users[menuitem][2]))
						if code != self._DLG_OK: continue
					users[menuitem][2] = string.split(groups, ",")
				elif menuitem2 == _(u"Shell"):
					code, shell = self._d.inputbox(_(u"Enter the shell you want the user to use.  default is /bin/bash.  "), init=users[menuitem][3])
					if code != self._DLG_OK: 
						continue
					users[menuitem][3] = shell
				elif menuitem2 == _(u"Home Directory"):
					code, homedir = self._d.inputbox(_(u"Enter the user's home directory. default is /home/username.  "), init=users[menuitem][4])
					if code != self._DLG_OK: 
						continue
					users[menuitem][4] = homedir
				elif menuitem2 == _(u"UID"):
					code, uid = self._d.inputbox(_(u"Enter the user's UID. If left blank the system will choose a default value (this is recommended)."), init=users[menuitem][5], height=11, width=55)
					if code != self._DLG_OK: 
						continue
					if type(uid) != int: 
						continue
					users[menuitem][5] = uid
				elif menuitem2 == _(u"Comment"):
					code, comment = self._d.inputbox(_(u"Enter the user's comment.  This is completely optional."), init=users[menuitem][6])
					if code != self._DLG_OK: 
						continue
					users[menuitem][6] = comment
				elif menuitem2 == _(u"Delete"):
					#Reset the Yes/No buttons
					self._d.add_persistent_args(["--yes-label", _(u"Yes")])
					self._d.add_persistent_args(["--no-label", _(u"No")])
					if self._d.yesno(_(u"Are you sure you want to delete the user ") + menuitem + "?") == self._DLG_YES:
						del users[menuitem]
						break

			
	def save_install_profile(self, xmlfilename="", askforfilename=True):
		code = 0
		filename = xmlfilename
		if askforfilename:
			code, filename = self._d.inputbox(_(u"Enter a filename for the XML file. Use full path!"), init=xmlfilename)
			if code != self._DLG_OK or not filename: 
				return None
		if GLIUtility.is_file(filename):
			if not self._d.yesno(_(u"The file %s already exists. Do you want to overwrite it?") % filename) == self._DLG_YES:
				return None
		try:
			configuration = open(filename ,"w")
			configuration.write(self._install_profile.serialize())
			configuration.close()
		except:
			self._d.msgbox(_(u"Error.  File couldn't be saved.  It will be saved automatically to /tmp before the install."))
		return filename
	def show_settings(self):
		settings = _(u"Look carefully at the following settings to check for mistakes.\nThese are the installation settings you have chosen:\n\n")
		#Partitioning
		settings += "Partitioning:  \n  Key: Minor, Pri/Ext, Filesystem, MkfsOpts, Mountpoint, MountOpts, Size.\n"
		devices = self._install_profile.get_partition_tables()
		drives = devices.keys()
		drives.sort()
		for drive in drives:
			settings += "  Drive: " + drive + devices[drive].get_model() + "\n"
			partlist = devices[drive].get_ordered_partition_list()
			tmpparts = devices[drive] #.get_partitions()
			for part in partlist:
				tmppart = tmpparts[part]
				entry = "    "
				if tmppart.get_type() == "free":
					#partschoice = "New"
					entry += _(u" - Unallocated space (")
					if tmppart.is_logical():
						entry += _(u"logical, ")
					entry += str(tmppart.get_mb()) + "MB)"
				elif tmppart.get_type() == "extended":
					entry += str(int(tmppart.get_minor()))
					entry += _(u" - Extended Partition (") + str(tmppart.get_mb()) + "MB)"
				else:
					entry += str(int(tmppart.get_minor())) + " - "
					if tmppart.is_logical():
						entry += _(u"Logical (")
					else:
						entry += _(u"Primary (")
					entry += tmppart.get_type() + ", "
					entry += (tmppart.get_mkfsopts() or "none") + ", "
					entry += (tmppart.get_mountpoint() or "none") + ", "
					entry += (tmppart.get_mountopts() or "none") + ", "
					entry += str(tmppart.get_mb()) + "MB)"
				settings += entry + "\n"
			
		#Network Mounts:
		network_mounts = copy.deepcopy(self._install_profile.get_network_mounts())
		settings += "\nNetwork Mounts: \n"
		for mount in network_mounts:
			settings += "  "+mount['host']+":"+mount['export']+"\n"
			
		#Install Stage:
		settings += "\nInstall Stage: " + str(self._install_profile.get_install_stage()) + "\n"
		if self._install_profile.get_dynamic_stage3():
			settings += "  Tarball will be generated on the fly from the CD.\n"
		else:
			settings += "  Tarball URI: " + self._install_profile.get_stage_tarball_uri() + "\n"
			
		#Portage Tree Sync Type:
		settings += "\nPortage Tree Sync Type: " + self._install_profile.get_portage_tree_sync_type() + "\n"
		if self._install_profile.get_portage_tree_sync_type() == "snapshot":
			settings += "  Portage snapshot URI: " + self._install_profile.get_portage_tree_snapshot_uri() + "\n"
			
		#Kernel Settings:
		settings += "\nKernel Settings:\n"
		settings += "  Kernel Sources: " + self._install_profile.get_kernel_source_pkg() + "\n"
		if self._install_profile.get_kernel_source_pkg() != "livecd-kernel":
			settings += "  Kernel Build Method: " + self._install_profile.get_kernel_build_method() + "\n"
			if self._install_profile.get_kernel_build_method() == "genkernel":
				settings += "  Kernel Bootsplash Option: " + str(self._install_profile.get_kernel_bootsplash()) + "\n"
		if self._install_profile.get_kernel_config_uri():
			settings += "  Kernel Configuration URI: " + self._install_profile.get_kernel_config_uri() + "\n"
				
		#Bootloader Settings:
		settings += "\nBootloader Settings:\n"
		settings += "  Bootloader package: " + self._install_profile.get_boot_loader_pkg() + "\n"
		if self._install_profile.get_boot_loader_pkg() != "none":
			settings += "  Install bootloader to MBR: " + str(self._install_profile.get_boot_loader_mbr()) + "\n"
			settings += "  Bootloader kernel arguments: " +self._install_profile.get_bootloader_kernel_args() + "\n"
			
		#Timezone:
		settings += "\nTimezone: " + self._install_profile.get_time_zone() + "\n"
		
		#Networking Settings:
		settings += "\nNetworking Settings: \n"
		interfaces = self._install_profile.get_network_interfaces()
		for iface in interfaces:
			if interfaces[iface][0] == 'dhcp':
				settings += "  " + iface + _(u":  Settings: DHCP. Options: ") + interfaces[iface][1] + "\n"
			else:
				settings += "  " + iface + _(u"IP: ") + interfaces[iface][0] + _(u" Broadcast: ") + interfaces[iface][1] + _(u" Netmask: ") + interfaces[iface][2] + "\n"
		default_gateway = self._install_profile.get_default_gateway()
		if default_gateway:
			settings += "  Default Gateway: " + default_gateway[0] + "/" + default_gateway[1] + "\n"
		settings += "  Hostname: " + self._install_profile.get_hostname() + "\n"
		if self._install_profile.get_domainname():
			settings += "  Domainname: " +self._install_profile.get_domainname() + "\n"
		if self._install_profile.get_nisdomainname():
			settings += "  NIS Domainname: " +self._install_profile.get_nisdomainname() + "\n"
		if self._install_profile.get_dns_servers():
			for dns_server in self._install_profile.get_dns_servers():
				settings += "  DNS Server: " +dns_server + "\n"
		if self._install_profile.get_http_proxy():
			settings += "  HTTP Proxy: " +self._install_profile.get_http_proxy() + "\n"
		if self._install_profile.get_ftp_proxy():
			settings += "  FTP Proxy: " +self._install_profile.get_ftp_proxy() + "\n"
		if self._install_profile.get_rsync_proxy():
			settings += "  RSYNC Proxy: " +self._install_profile.get_rsync_proxy() + "\n"
			
		#Cron Daemon:
		settings += "\nCron Daemon: " + self._install_profile.get_cron_daemon_pkg() + "\n"
		
		#Logger:
		settings += "\nLogging Daemon: " + self._install_profile.get_logging_daemon_pkg() + "\n"
		
		#Extra packages:
		if self._install_profile.get_install_packages():
			install_packages = self._install_profile.get_install_packages()
		else:
			install_packages = []
		settings += "\nExtra Packages: "
		for package in install_packages:
			settings += package + " "
		settings += "\n"
		#Services:
		if self._install_profile.get_services():
			services = self._install_profile.get_services()
		else:
			services = []
		settings += "\nAdditional Services: "
		for service in services:
			settings += service + " "
		settings += "\n"
		
		#Other Configuration Settings (rc.conf):
		#Make.conf Settings:
		settings += "\nConfiguration Files Settings:\n"
		etc_files = self._install_profile.get_etc_files()
		for etc_file in etc_files:
			settings += "  File:" + etc_file + "\n"
			if isinstance(etc_files[etc_file], dict):
				for name in etc_files[etc_file]:
					settings += "    Variable: " + name + "   Value: " + etc_files[etc_file][name] + "\n"
			else:
				for entry in etc_files[etc_file]:
					settings += "    Value: "+ entry + "\n"
		
		#Additional Users:
		settings += "\nAdditional Users:\n"
		users = {}
		for user in self._install_profile.get_users():
			users[user[0]] = (user[0], user[1], user[2], user[3], user[4], user[5], user[6])
		for user in users:
			settings += "  Username: " + user
			settings += "\n    Group Membership: " + string.join(users[user][2], ",")
			settings += "\n    Shell: " + users[user][3]
			settings += "\n    Home Directory: " + users[user][4]
			if users[user][5]:
				settings += "\n    User Id: " + users[user][5]
			if users[user][6]:
				settings += "\n    User Comment: " + users[user][6]

		self._d.scrollbox(settings, height=20, width=77, title=_(u"A Review of your settings"))
