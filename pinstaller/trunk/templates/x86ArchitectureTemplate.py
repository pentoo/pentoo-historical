"""
# Copyright 1999-2005 Gentoo Foundation
# This source code is distributed under the terms of version 2 of the GNU
# General Public License as published by the Free Software Foundation, a copy
# of which can be found in the main directory of this project.
Gentoo Linux Installer

$Id: x86ArchitectureTemplate.py,v 1.136 2006/04/21 11:54:30 agaffney Exp $
Copyright 2004 Gentoo Technologies Inc.


This fills in x86 specific functions.
"""

import GLIUtility, string, time
from GLIArchitectureTemplate import ArchitectureTemplate
from GLIException import *
import parted
import GLIStorageDevice
		
MEGABYTE = 1024 * 1024

class x86ArchitectureTemplate(ArchitectureTemplate):
	def __init__(self,configuration=None, install_profile=None, client_controller=None):
		ArchitectureTemplate.__init__(self, configuration, install_profile, client_controller)
		self._architecture_name = 'x86'
		self._kernel_bzimage = "arch/i386/boot/bzImage"

	def install_bootloader(self):
		"Installs and configures bootloader"
		#
		# THIS IS ARCHITECTURE DEPENDANT!!!
		# This is the x86 way.. it uses grub

		bootloader_pkg = self._install_profile.get_boot_loader_pkg()

		# first install bootloader
		if bootloader_pkg and bootloader_pkg.lower() != "none":
			exitstatus = self._portage.emerge(bootloader_pkg)
#			if not GLIUtility.exitsuccess(exitstatus):
#				raise GLIException("BootLoaderEmergeError", 'fatal', 'install_bootloader', "Could not emerge bootloader!")
#			else:
			self._logger.log("Emerged the selected bootloader.")
		
		# now configure said bootloader
		# null boot-loader first
		if bootloader_pkg.lower() == "none":
			return
		elif "grub" in bootloader_pkg: # this catches 'grub-static' as well as '=sys-boot/grub-0.95*'
			self._configure_grub()
		elif "lilo" in bootloader_pkg:
			self._configure_lilo()
		# probably should add in some more bootloaders
		# dvhtool, raincoat, netboot, gnu-efi, cromwell, syslinux, psoload
		else:
			raise GLIException("BootLoaderError",'fatal','install_bootloader',"Don't know how to configure this bootloader: "+bootloader_pkg)
		
	def _sectors_to_megabytes(self, sectors, sector_bytes=512):
		return float((float(sectors) * sector_bytes)/ float(MEGABYTE))

	def _add_partition(self, disk, start, end, type, fs, name=""):
		if self._debug: self._logger.log("_add_partition(): type=%s, fstype=%s" % (type, fs))
		types = { 'primary': parted.PARTITION_PRIMARY, 'extended': parted.PARTITION_EXTENDED, 'logical': parted.PARTITION_LOGICAL }
		fsTypes = {}
		fs_type = parted.file_system_type_get_next ()
		while fs_type:
			fsTypes[fs_type.name] = fs_type
			fs_type = parted.file_system_type_get_next (fs_type)
		fstype = None
		if fs: fstype = fsTypes[fs]
		newpart = disk.partition_new(types[type], fstype, start, end)
		if self._debug: self._logger.log("_add_partition(): partition object created")
		constraint = disk.dev.constraint_any()
		if self._debug: self._logger.log("_add_partition(): constraint object created")
		disk.add_partition(newpart, constraint)
		if self._debug: self._logger.log("_add_partition(): partition added")

	def _delete_partition(self, parted_disk, minor):
		try:
			parted_disk.delete_partition(parted_disk.get_partition(minor))
		except:
			self._logger.log("_delete_partition(): could not delete partition...ignoring (for now)")

	def _check_table_changed(self, oldparts, newparts):
		for part in newparts:
			if not newparts[part]['origminor'] or not oldparts.get_partition(part):
				return True
			oldpart = oldparts[part]
			newpart = newparts[part]
			if oldpart['type'] == newpart['type'] and oldpart['mb'] == newpart['mb'] and not newpart['resized'] and not newpart['format']:
				continue
			else:
				return True
		return False

	def _check_table_layout_changed(self, oldparts, newparts):
		for part in newparts:
			if not newparts[part]['origminor'] or not oldparts.get_partition(part):
				return True
			oldpart = oldparts[part]
			newpart = newparts[part]
			if oldpart['type'] == newpart['type'] and oldpart['mb'] == newpart['mb']:
				continue
			else:
				return True
		return False

	def _find_existing_in_new(self, oldminor, newparts):
		for part in newparts:
			if newparts[part]['origminor'] == oldminor:
				return part
		return 0

	def _check_keeping_any_existing(self, newparts):
		for part in newparts:
			if newparts[part]['origminor']: return True
		return False

	def _find_next_partition(self, curminor, parts):
		foundmyself = False
		for part in parts:
			if not part == curminor and not foundmyself: continue
			if part == curminor:
				foundmyself = True
				continue
			if foundmyself:
				return part
		return 0

	def _partition_delete_step(self, parted_disk, oldparts, newparts):
		for oldpart in list(oldparts)[::-1]:
			tmppart_old = oldparts[oldpart]
			if oldparts.get_disklabel() != "mac" and tmppart_old['type'] == "free": continue
			if tmppart_old['type'] == "extended":
				# Iterate through logicals to see if any are being resized
				for logpart in tmppart_old.get_logicals():
					newminor = self._find_existing_in_new(logpart, newparts)
					if newminor and newparts['resized']:
						self._logger.log("  Logical partition " + str(logpart) + " to be resized...can't delete extended")
						break
				else:
					self._logger.log("  No logical partitions are being resized...deleting extended")
					self._delete_partition(parted_disk, oldpart)
			else:
				newminor = self._find_existing_in_new(oldpart, newparts)
				if newminor and not newparts[newminor]['format']:
					if newparts[newminor]['resized']:
						self._logger.log("  Ignoring old minor " + str(oldpart) + " to resize later")
						continue
					else:
						self._logger.log("  Deleting old minor " + str(oldpart) + " to be recreated later")
				else:
						self._logger.log("  No match in new layout for old minor " + str(oldpart) + "...deleting")
				self._delete_partition(parted_disk, oldpart)
		parted_disk.commit()

	def _partition_resize_step(self, parted_disk, device, oldparts, newparts):
		for oldpart in oldparts:
			tmppart_old = oldparts[oldpart]
			devnode = tmppart_old['devnode']
			newminor = self._find_existing_in_new(oldpart, newparts)
			if not newminor or not newparts[newminor]['resized']:
				continue
			tmppart_new = newparts[newminor]
			type = tmppart_new['type']
			start = tmppart_new['start']
			end = start + (long(tmppart['mb']) * MEGABYTE / 512) - 1
			total_sectors = end - start + 1
			total_bytes = long(total_sectors) * 512
			# Make sure calculated end sector doesn't overlap start sector of next partition
			nextminor = self._find_next_partition(newminor, newparts)
			if nextminor:
				if newparts[nextminor]['start'] and end >= newparts[nextminor]['start']:
					self._logger.log("  End sector for growing partition overlaps with start of next partition...fixing")
					end = newparts[nextminor]['start'] - 1
			# sleep a bit first
			time.sleep(3)
			# now sleep until it exists
			while not GLIUtility.is_file(device + str(minor)):
				self._logger.log("Waiting for device node " + devnode + " to exist before resizing")
				time.sleep(1)
			# one bit of extra sleep is needed, as there is a blip still
			time.sleep(3)
			if type in ("ext2", "ext3"):
				ret = GLIUtility.spawn("resize2fs " + devnode + " " + str(total_sectors) + "s", logfile=self._compile_logfile, append_log=True)
				if not GLIUtility.exitsuccess(ret): # Resize error
					raise GLIException("PartitionResizeError", 'fatal', 'partition', "could not resize ext2/3 filesystem on " + devnode)
			elif type == "ntfs":
				ret = GLIUtility.spawn("yes | ntfsresize -v --size " + str(total_bytes) + " " + devnode, logfile=self._compile_logfile, append_log=True)
				if not GLIUtility.exitsuccess(ret): # Resize error
					raise GLIException("PartitionResizeError", 'fatal', 'partition', "could not resize NTFS filesystem on " + devnode)
			elif type in ("linux-swap", "fat32", "fat16"):
				parted_fs = parted_disk.get_partition(part).geom.file_system_open()
				resize_constraint = parted_fs.get_resize_constraint()
				if total_sectors < resize_constraint.min_size or start != resize_constraint.start_range.start:
					raise GLIException("PartitionError", 'fatal', 'partition', "New size specified for " + device + str(minor) + " is not within allowed boundaries (blame parted)")
				new_geom = resize_constraint.start_range.duplicate()
				new_geom.set_start(start)
				new_geom.set_end(end)
				try:
					parted_fs.resize(new_geom)
				except:
					raise GLIException("PartitionResizeError", 'fatal', 'partition', "could not resize " + device + str(minor))
			self._logger.log("  Deleting old minor " + str(oldpart) + " to be recreated in 3rd pass")
			self._delete_partition(parted_disk, oldpart)
		parted_disk.delete_all()
		parted_disk.commit()

	def _partition_recreate_step(self, parted_disk, newparts):
		start = 0
		end = 0
		extended_start = 0
		extended_end = 0
		device_sectors = newparts.get_num_sectors()
		self._logger.log("  Drive has " + str(device_sectors) + " sectors")
		for part in newparts:
			newpart = newparts[part]
			self._logger.log("  Partition " + str(part) + " has " + str(newpart['mb']) + "MB")
			if newpart['start']:
				self._logger.log("    Old start sector " + str(newpart['start']) + " retrieved")
				if start != newpart['start']:
					self._logger.log("    Retrieved start sector is not the same as the calculated next start sector (usually not an issue)")
				start = newpart['start']
			else:
				self._logger.log("    Start sector calculated to be " + str(start))
			if extended_end and not newpart.is_logical() and start <= extended_end:
				self._logger.log("    Start sector for primary is less than the end sector for previous extended")
				start = extended_end + 1
			if newpart['end']:
				self._logger.log("    Old end sector " + str(newpart['end']) + " retrieved")
				end = newpart['end']
				part_sectors = end - start + 1
			else:
				part_sectors = long(newpart['mb']) * MEGABYTE / 512
				end = start + part_sectors
				self._logger.log("    End sector calculated to be " + str(end))
			# Make sure end doesn't overlap next partition's existing start sector
			nextminor = self._find_next_partition(newpart, newparts)
			if nextminor:
				if newparts[nextminor]['start'] and end >= newparts[nextminor]['start']:
					self._logger.log("  End sector for partition overlaps with start of next partition...fixing")
					end = newparts[nextminor]['start'] - 1
			# cap to end of device
			if end >= device_sectors:
				end = device_sectors - 1
			# now the actual creation
			if newpart['type'] == "free":
				if newparts.get_disklabel() == "mac":
					# Create a dummy partition to be removed later because parted sucks
					self._logger.log("  Adding dummy partition to fool parted " + str(part) + " from " + str(start) + " to " + str(end))
					self._add_partition(parted_disk, start, end, "primary", "ext2", "free")
			elif newpart['type'] == "extended":
				self._logger.log("  Adding extended partition " + str(part) + " from " + str(start) + " to " + str(end))
				self._add_partition(parted_disk, start, end, "extended", "")
				extended_start = start
				extended_end = end
			elif not newpart.is_logical():
				self._logger.log("  Adding primary partition " + str(part) + " from " + str(start) + " to " + str(end))
				self._add_partition(parted_disk, start, end, "primary", newpart['type'])
			elif newpart.is_logical():
				if start >= extended_end:
					start = extended_start + 1
					end = start + part_sectors
				if nextminor and not newparts[nextminor].is_logical() and end > extended_end:
					end = extended_end
				self._logger.log("  Adding logical partition " + str(part) + " from " + str(start) + " to " + str(end))
				self._add_partition(parted_disk, start, end, "logical", newpart['type'])
			if self._debug: self._logger.log("partition(): flags: " + str(newpart['flags']))
			for flag in newpart['flags']:
				if parted_disk.get_partition(part).is_flag_available(flag):
					parted_disk.get_partition(part).set_flag(flag, True)
			if newpart['name'] and parted_disk.type.check_feature(parted.DISK_TYPE_PARTITION_NAME):
				parted_disk.set_name(newpart['name'])
			# write to disk
			if self._debug: self._logger.log("partition(): committing change to disk")
			parted_disk.commit()
			if self._debug: self._logger.log("partition(): committed change to disk")
			start = end + 1

	def _partition_format_step(self, parted_disk, device, newparts):
		for part in newparts:
			newpart = newparts[part]
			devnode = newpart['devnode']
			# This little hack is necessary because parted sucks goat nuts
			if newparts.get_disklabel() == "mac" and newpart['type'] == "free":
				self._delete_partition(parted_disk, newpart)
				continue
			if newpart['format'] and newpart['type'] not in ('extended', 'free'):
#				devnode = device + str(int(part))
				if self._debug: self._logger.log("_partition_format_step(): devnode is %s in formatting code" % devnode)
				# if you need a special command and
				# some base options, place it here.
				format_cmds = { 'linux-swap': "mkswap", 'fat16': "mkfs.vfat -F 16", 'fat32': "mkfs.vfat -F 32",
				                'ntfs': "mkntfs", 'xfs': "mkfs.xfs -f", 'jfs': "mkfs.jfs -f",
				                'reiserfs': "mkfs.reiserfs -f", 'ext2': "mkfs.ext2", 'ext3': "mkfs.ext3"
				              }
				if newpart['type'] in format_cmds:
					cmdname = format_cmds[newpart['type']]
				else: # this should catch everything else
					raise GLIException("PartitionFormatError", 'fatal', '_partition_format_step', "Unknown partition type " + newpart['type'])
				# sleep a bit first
				time.sleep(1)
				for tries in range(10):
					cmd = "%s %s %s" % (cmdname, newpart['mkfsopts'], devnode)
					self._logger.log("  Formatting partition %s as %s with: %s" % (str(part),newpart['type'],cmd))
					ret = GLIUtility.spawn(cmd, logfile=self._compile_logfile, append_log=True)
					if not GLIUtility.exitsuccess(ret):
						self._logger.log("Try %d failed formatting partition %s...waiting 5 seconds" % (tries+1, devnode))
						time.sleep(5)
					else:
						break
				else:
					raise GLIException("PartitionFormatError", 'fatal', '_partition_format_step', "Could not create %s filesystem on %s" % (newpart['type'], devnode))

	def partition(self):
		"""
		TODO:
		before step 3, wipe drive and use the default disklabel for arch
		skip fixed partitions in all passes (in GLISD maybe?)
		"""
		parts_old = {}
		parts_new = self._install_profile.get_partition_tables()
		for device in GLIStorageDevice.detect_devices():
			parts_old[device] = GLIStorageDevice.Device(device, arch=self._client_configuration.get_architecture_template())
			parts_old[device].set_partitions_from_disk()

		self.notify_frontend("progress", (0, "Examining partitioning data"))
		total_steps = float(len(parts_new) * 4) # 4 for the number of passes over each device
		cur_progress = 0
		for device in parts_new:
			# Skip this device in parts_new if device isn't detected on current system
			if not device in parts_old:
				self._logger.log("There is no physical device " + device + " detected to match the entry in the install profile...skipping")
				continue

			# This just makes things simpler in the code
			newparts = parts_new[device]
			oldparts = parts_old[device]

			# Check to see if the old and new partition table structures are the same...skip if they are
			if not self._check_table_changed(oldparts, newparts):
				self._logger.log("Partition table for " + device + " is unchanged...skipping")
				continue

			self._logger.log("partition(): Processing " + device + "...")

			# Commit ritual sepuku if there are any mounted filesystems on this device
			if GLIUtility.spawn("mount | grep '^" + device + "'", return_output=True)[1].strip():
				raise GLIException("PartitionsMountedError", 'fatal', 'partition', "Cannot partition " + device + " due to filesystems being mounted")

			# We also can't handle "unknown" partitions
			for part in newparts:
				if newparts[part]['type'] == "unknown":
					raise GLIException("UnknownPartitionTypeError", 'fatal', 'partition', "Refusing to partition this drive due to the presence of an unknown type of partition")

			# Create pyparted objects for this device
			parted_dev = parted.PedDevice.get(device)
			try:
				parted_disk = parted.PedDisk.new(parted_dev)
			except:
				if self._debug: self._logger.log("partition(): could not load existing disklabel...creating new one")
				parted_disk = parted_dev.disk_new_fresh(parted.disk_type_get((newparts.get_disklabel() or GLIStorageDevice.archinfo[self._architecture_name])))

			# Iterate through new partitions and check for 'origminor' and 'format' == False
			for part in newparts:
				tmppart_new = newparts[part]
				if not tmppart_new['origminor'] or tmppart_new['format']: continue
				if not tmppart_new['origminor'] in oldparts:
					raise GLIException("MissingPartitionsError", 'fatal', 'partition', "Cannot find the existing partition that a new one refers to. This is not a bug. This is in fact your (the user's) fault. You should not reuse the installprofile.xml from a previous install that started the partitioning step.")
				tmppart_old = oldparts[tmppart_new['origminor']]
				if parted_disk.type.check_feature(parted.DISK_TYPE_PARTITION_NAME):
					tmppart_new['name'] = tmppart_old['name']
				tmppart_new['flags'] = tmppart_old['flags']
				if tmppart_new['resized']:
					# Partition is being resized in the new layout
					self._logger.log("  Partition " + str(part) + " has origminor " + str(tmppart_new['origminor']) + " and it being resized...saving start sector " + str(tmppart_old['start']))
					tmppart_new['start'] = tmppart_old['start']
					tmppart_new['end'] = 0
				else:
					# Partition is untouched in the new layout
					self._logger.log("  Partition " + str(part) + " has origminor " + str(tmppart_new['origminor']) + "...saving start sector " + str(tmppart_old['start']) + " and end sector " + str(tmppart_old['end']))
					tmppart_new['start'] = tmppart_old['start']
					tmppart_new['end'] = tmppart_old['end']

			if self._check_table_layout_changed(parts_old[device], parts_new[device]):
				# First pass to delete old partitions that aren't resized
				self.notify_frontend("progress", (cur_progress / total_steps, "Deleting partitioning that aren't being resized for " + device))
				cur_progress += 1
				self._partition_delete_step(parted_disk, oldparts, newparts)

				# Second pass to resize old partitions that need to be resized
				self._logger.log("Partitioning: Second pass...")
				self.notify_frontend("progress", (cur_progress / total_steps, "Resizing remaining partitions for " + device))
				cur_progress += 1
				self._partition_resize_step(parted_disk, device, oldparts, newparts)

				# Wiping disk and creating blank disklabel
				try:
					parted_disk = parted_dev.disk_new_fresh(parted.disk_type_get(newparts.get_disklabel()))
					parted_disk.commit()
				except:
					raise GLIException("DiskLabelCreationError", 'fatal', 'partition', "Could not create a blank disklabel!")

				# Third pass to create new partition table
				self._logger.log("Partitioning: Third pass....creating partitions")
				self.notify_frontend("progress", (cur_progress / total_steps, "Recreating partition table for " + device))
				cur_progress += 1
				self._partition_recreate_step(parted_disk, newparts)
			else:
				cur_progress += 3

			# Fourth pass to format partitions
			self._logger.log("Partitioning: formatting partitions")
			self.notify_frontend("progress", (cur_progress / total_steps, "Formatting partitions for " + device))
			cur_progress += 1
			self._partition_format_step(parted_disk, device, newparts)

			# All done for this device
			self.notify_frontend("progress", (cur_progress / total_steps, "Done with partitioning for " + device))
			cur_progress += 1

	def _configure_grub(self):
		self.build_mode = self._install_profile.get_kernel_build_method()
		self._gather_grub_drive_info()
		root = self._chroot_dir
		exitstatus2, kernel_names = GLIUtility.spawn("ls -1 --color=no " + root + "/boot/kernel-*", return_output=True)
		self._logger.log("Output of Kernel Names:\n"+kernel_names)
		if not GLIUtility.exitsuccess(exitstatus2):
			raise GLIException("BootloaderError", 'fatal', '_configure_grub', "Error listing the kernels in /boot")
		if self.build_mode == "genkernel" or self._install_profile.get_kernel_source_pkg() == "livecd-kernel":
			exitstatus3, initrd_names = GLIUtility.spawn("ls -1 --color=no " + root + "/boot/init*", return_output=True)
			self._logger.log("Output of Initrd Names:\n"+initrd_names)
		if not GLIUtility.exitsuccess(exitstatus3):
			raise GLIException("BootloaderError", 'fatal', '_configure_grub', "Error listing the initrds")
		self._logger.log("Bootloader: the three information gathering commands have been run")
		
		if not kernel_names[0]:
			raise GLIException("BootloaderError", 'fatal', '_configure_grub',"Error: We have no kernel in /boot to put in the grub.conf file!")
			
		#-------------------------------------------------------------
		#OK, now that we have all the info, let's build that grub.conf
		newgrubconf = ""
		newgrubconf += "default 0\ntimeout 30\n"
		if self.foundboot:  #we have a /boot
			newgrubconf += "splashimage=(" + self.grub_boot_drive + "," + self.grub_boot_minor + ")/grub/splash.xpm.gz\n"
		else: #we have / and /boot needs to be included
			newgrubconf += "splashimage=(" + self.grub_boot_drive + "," + self.grub_boot_minor + ")/boot/grub/splash.xpm.gz\n"
		if self._install_profile.get_bootloader_kernel_args(): 
			bootloader_kernel_args = self._install_profile.get_bootloader_kernel_args()
		else: bootloader_kernel_args = ""

		kernel_names = map(string.strip, kernel_names.strip().split("\n"))
		initrd_names = map(string.strip, initrd_names.strip().split("\n"))
		grub_kernel_name = kernel_names[-1].split(root)[-1]
		if initrd_names: grub_initrd_name = initrd_names[-1].split(root)[-1]
#		for i in range(len(kernel_names)):
#			grub_kernel_name = kernel_names[i].split(root)[-1]
#		for i in range(len(initrd_names)):  #this should be okay if blank.
#			grub_initrd_name = initrd_names[i].split(root)[-1]
		#i think this means take the last one it finds.. i.e. the newest.
		
		newgrubconf += "title=Gentoo Linux\n"
		newgrubconf += "root (" + self.grub_boot_drive + "," + self.grub_boot_minor + ")\n"
		if self.build_mode != "genkernel" and self._install_profile.get_kernel_source_pkg() != "livecd-kernel":  #using CUSTOM kernel
			if self.foundboot:
				newgrubconf += "kernel " + grub_kernel_name[5:] + " root="+self.root_device+self.root_minor+"\n"
			else:
				newgrubconf += "kernel /boot"+ grub_kernel_name[5:] + " root="+self.root_device+self.root_minor+"\n"
		else: #using genkernel so it has an initrd.
			if self.foundboot:
				newgrubconf += "kernel " + grub_kernel_name[5:] + " root=/dev/ram0 init=/linuxrc ramdisk=8192 real_root="
				newgrubconf += self.root_device + self.root_minor + " " + bootloader_kernel_args + "\n"
				newgrubconf += "initrd " + grub_initrd_name[5:] + "\n"
			else:
				newgrubconf += "kernel /boot" + grub_kernel_name[5:] + " root=/dev/ram0 init=/linuxrc ramdisk=8192 real_root="
				newgrubconf += self.root_device + self.root_minor + " " + bootloader_kernel_args + "\n"
				newgrubconf += "initrd /boot" + grub_initrd_name[5:] + "\n"
		newgrubconf = self._grub_add_windows(newgrubconf)
		#now make the grub.conf file
		file_name = root + "/boot/grub/grub.conf"	
		try:
			shutil.move(file_name, file_name + ".OLDdefault")
		except:
			pass
		f = open(file_name, 'w')
		f.writelines(newgrubconf)
		f.close()
		self._logger.log("Grub installed and configured. Contents of grub.conf:\n"+newgrubconf)
		self._logger.log("Grub has not yet been run.  If a normal install, it will now be run.")
		
	def _gather_grub_drive_info(self):
		self.boot_minor = ""
		self.boot_device = ""
		self.root_device = ""
		self.root_minor = ""
		self.mbr_device = ""
		self.grub_root_minor = ""
		self.grub_boot_minor = ""
		self.grub_boot_drive = ""
		self.grub_root_drive = ""
		self.grub_mbr_drive = ""
		minornum = 0
		#Assign root to the root mount point to make lines more readable
		root = self._chroot_dir


		self.foundboot = False
		parts = self._install_profile.get_partition_tables()
		for device in parts:
			tmp_partitions = parts[device] #.get_install_profile_structure()
			for partition in tmp_partitions:
				mountpoint = tmp_partitions[partition]['mountpoint']
				if (mountpoint == "/boot"):
					self.foundboot = True
				if (( (mountpoint == "/") and (not self.foundboot) ) or (mountpoint == "/boot")):
					self.boot_minor = str(int(tmp_partitions[partition]['minor']))
					self.grub_boot_minor = str(int(tmp_partitions[partition]['minor']) - 1)
					self.boot_device = device
					self.mbr_device = device
				if mountpoint == "/":
					self.root_minor = str(int(tmp_partitions[partition]['minor']))
					self.grub_root_minor = str(int(tmp_partitions[partition]['minor']) - 1)
					self.root_device = device
		#RESET the boot device if one is stored already
		if self._install_profile.get_boot_device():
			self.mbr_device = self._install_profile.get_boot_device()
			self._logger.log("Found a mbr device: " + self.mbr_device)
		
		self.grub_boot_drive = self._map_device_to_grub_device(self.boot_device)
		self.grub_root_drive = self._map_device_to_grub_device(self.root_device)
		self.grub_mbr_drive = self._map_device_to_grub_device(self.mbr_device)
		
		if (not self.grub_root_drive) or (not self.grub_boot_drive):
			raise GLIException("BootloaderError", 'fatal', '_gather_grub_drive_info',"Couldn't find the drive num in the list from the device.map")

	def _grub_add_windows(self, newgrubconf):
		parts = self._install_profile.get_partition_tables()
		for device in parts:
			tmp_partitions = parts[device] #.get_install_profile_structure()
			for partition in tmp_partitions:
				if (tmp_partitions[partition]['type'] == "fat32") or (tmp_partitions[partition]['type'] == "ntfs"):
					grub_dev = self._map_device_to_grub_device(device)
					newgrubconf += "\ntitle=Possible Windows P"+str(int(tmp_partitions[partition]['minor']))+"\n"
					newgrubconf += "rootnoverify ("+grub_dev+","+str(int(tmp_partitions[partition]['minor'] -1))+")\n"
					newgrubconf += "makeactive\nchainloader +1\n\n"
		return newgrubconf

	def _configure_lilo(self):
		self.build_mode = self._install_profile.get_kernel_build_method()
		self._gather_lilo_drive_info()
		root = self._chroot_dir
		file_name3 = root + "/boot/kernel_name"
		root = self._chroot_dir
		exitstatus0 = GLIUtility.spawn("ls "+root+"/boot/kernel-* > "+file_name3)
		if (exitstatus0 != 0):
			raise GLIException("BootloaderError", 'fatal', '_configure_lilo', "Could not list kernels in /boot or no kernels found.")
		if self.build_mode == "genkernel" or self._install_profile.get_kernel_source_pkg() == "livecd-kernel":
			exitstatus1 = GLIUtility.spawn("ls "+root+"/boot/init* >> "+file_name3)
			if (exitstatus1 != 0):
				raise GLIException("BootloaderError", 'fatal', '_configure_lilo', "Could not list initrds in /boot")
		g = open(file_name3)
		kernel_name = g.readlines()
		g.close()
		if not kernel_name[0]:
			raise GLIException("BootloaderError", 'fatal', '_configure_lilo',"Error: We have no kernel in /boot to put in the grub.conf file!")
		kernel_name = map(string.strip, kernel_name)
		kernel_name[0] = kernel_name[0].split(root)[1]
		kernel_name[1] = kernel_name[1].split(root)[1]
		if self._install_profile.get_bootloader_kernel_args(): bootloader_kernel_args = self._install_profile.get_bootloader_kernel_args()
		else: bootloader_kernel_args = ""
		#-------------------------------------------------------------
		#time to build the lilo.conf
		newliloconf = ""
		if self._install_profile.get_boot_loader_mbr():
			newliloconf += "boot="+self.mbr_device+"   # Install LILO in the MBR \n"
		else:
			newliloconf += "boot="+self.boot_device+self.boot_minor+"   # Install LILO in the MBR \n"
		newliloconf += "prompt                    # Give the user the chance to select another section\n"
		newliloconf += "timeout=50                # Wait 5 (five) seconds before booting the default section\n"
		newliloconf += "default=gentoo            # When the timeout has passed, boot the \"gentoo\" section\n"
		newliloconf += "# Only if you use framebuffer. Otherwise remove the following line:\n"
		if not self._install_profile.get_kernel_bootsplash():
			newliloconf += "#"
		newliloconf += "vga=788                   # Framebuffer setting. Adjust to your own will\n"
		newliloconf += "image=/boot"+kernel_name[0][5:]+" \n"
		newliloconf += "  label=gentoo \n  read-only \n"
		if self.build_mode != "genkernel" and self._install_profile.get_kernel_source_pkg() != "livecd-kernel": 
			newliloconf += "  root="+self.root_device+self.root_minor+" \n"
			if bootloader_kernel_args:
				newliloconf += "  append=\""+bootloader_kernel_args+"\" \n"
		else:
			newliloconf += "  root=/dev/ram0 \n"
			newliloconf += "  append=\"init=/linuxrc ramdisk=8192 real_root="+self.root_device+self.root_minor + " " + bootloader_kernel_args + "\" \n"
			newliloconf += "  initrd=/boot"+kernel_name[1][5:] + "\n\n"
		newliloconf = self._lilo_add_windows(newliloconf)
		#now make the lilo.conf file
		file_name = root + "/etc/lilo.conf"	
		try:
			shutil.move(file_name, file_name + ".OLDdefault")
		except:
			pass
		f = open(file_name, 'w')
		f.writelines(newliloconf)
		f.close()
		self._logger.log("Lilo installed and configured.  Not run yet.")
		
	def _gather_lilo_drive_info(self):
		self.boot_device = ""
		self.boot_minor = ""
		self.root_device = ""
		self.root_minor = ""
		self.mbr_device = ""
		minornum = 0
		#Assign root to the root mount point to make lines more readable
		root = self._chroot_dir
		self.foundboot = False
		parts = self._install_profile.get_partition_tables()
		for device in parts:
			tmp_partitions = parts[device] #.get_install_profile_structure()
			for partition in tmp_partitions:
				mountpoint = tmp_partitions[partition]['mountpoint']
				if (mountpoint == "/boot"):
					self.foundboot = True
				if (( (mountpoint == "/") and (not self.foundboot) ) or (mountpoint == "/boot")):
					self.boot_minor = str(int(tmp_partitions[partition]['minor']))
					self.boot_device = device
					self.mbr_device = device
				if mountpoint == "/":
					self.root_minor = str(int(tmp_partitions[partition]['minor']))
					self.root_device = device
		#RESET the boot device if one is stored already
		if self._install_profile.get_boot_device():
			self.mbr_device = self._install_profile.get_boot_device()
			self._logger.log("Found a mbr device: " + self.mbr_device)			
		
	def _lilo_add_windows(self, newliloconf):
		parts = self._install_profile.get_partition_tables()
		for device in parts:
			tmp_partitions = parts[device] #.get_install_profile_structure()
			for partition in tmp_partitions:
				if (tmp_partitions[partition]['type'] == "fat32") or (tmp_partitions[partition]['type'] == "ntfs"):
					newliloconf += "other="+device+str(int(tmp_partitions[partition]['minor']))+"\n"
					newliloconf += "label=Windows_P"+str(int(tmp_partitions[partition]['minor']))+"\n\n"
		return newliloconf
		
	def _map_device_to_grub_device(self, device):
		file_name = self._chroot_dir + "/boot/grub/glidevice.map"
		#If we can't find it, make it.  If we STILL can't find it. die.
		if not GLIUtility.is_file(file_name):
			exitstatus1 = GLIUtility.spawn("echo quit | "+ self._chroot_dir+"/sbin/grub --batch --no-floppy --device-map="+file_name, logfile=self._compile_logfile, append_log=True)
		if not GLIUtility.is_file(file_name):
			raise GLIException("BootloaderError", 'fatal', '_configure_grub', "Error making the new device map.")
		"""
		read the device map.  sample looks like this:
		(fd0)   /dev/floppy/0
		(hd0)   /dev/sda
		(hd1)   /dev/hda
		(hd2)   /dev/hdb
		"""
		
		# Search for the key
		f = open(file_name)  #open the device map
		file = f.readlines()
		f.close()	
		for i in range(len(file)):
			if file[i][6:-1] == device:
				return file[i][1:4]
		raise GLIException("BootloaderError", 'fatal', '_map_device_to_grub_device', "ERROR, could not map"+device+" to anything in the device map")

	def setup_and_run_bootloader(self):
		bootloader_pkg = self._install_profile.get_boot_loader_pkg()
		if bootloader_pkg.lower() == "none":
			return
		elif "grub" in bootloader_pkg: # this catches 'grub-static' as well as '=sys-boot/grub-0.95*'
			self._setup_grub()
		elif "lilo" in bootloader_pkg:
			self._setup_lilo()
		# probably should add in some more bootloaders
		# dvhtool, raincoat, netboot, gnu-efi, cromwell, syslinux, psoload
		else:
			raise GLIException("BootLoaderError",'fatal','setup_and_run_bootloader',"Don't know how to configure this bootloader: "+bootloader_pkg)

	def _setup_grub(self):
		#-------------------------------------------------------------
		#OK, now that the file is built.  Install grub.
		#cp /proc/mounts /etc/mtab
		#grub-install --root-directory=/boot /dev/hda
		#shutil.copy("/proc/mounts",root +"/etc/mtab")
		self._gather_grub_drive_info()
		grubinstallstring = "echo -en 'root ("+self.grub_boot_drive + "," + self.grub_boot_minor + ")\n"
		if not self._install_profile.get_boot_loader_mbr():
			grubinstallstring +="setup ("+self.grub_boot_drive + "," + self.grub_boot_minor + ")\n"
		else:
			grubinstallstring +="setup ("+self.grub_mbr_drive+")\n"
		grubinstallstring += "quit\n' | "+self._chroot_dir+"/sbin/grub --batch --no-floppy"
		if self._debug: self._logger.log("DEBUG: _configure_grub(): Grub install string: " + grubinstallstring)
		exitstatus = GLIUtility.spawn(grubinstallstring, logfile=self._compile_logfile, append_log=True)
		if not GLIUtility.exitsuccess(exitstatus):
			raise GLIException("GrubInstallError", 'fatal', '_setup_grub', "Could not install grub!")
		self._logger.log("Bootloader: grub has been installed!")

	def _setup_lilo(self):
		#-------------------------------------------------------------
		#OK, now that the file is built.  Install lilo.
		exitstatus = GLIUtility.spawn("/sbin/lilo",chroot=self._chroot_dir, logfile=self._compile_logfile, append_log=True)
		if exitstatus != 0:
			raise GLIException("LiloInstallError", 'fatal', '_setup_lilo', "Running lilo failed!")
		self._logger.log("Bootloader: lilo has been run/installed!")
