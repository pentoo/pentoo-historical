# Copyright 1999-2005 Gentoo Foundation
# This source code is distributed under the terms of version 2 of the GNU
# General Public License as published by the Free Software Foundation, a copy
# of which can be found in the main directory of this project.

import commands, string, os, parted
from glob import glob
from GLIException import *
import GLIUtility

MEGABYTE = 1024 * 1024

# these are here so that we can change them easily in future
# the values were chosen to represent perfect floating point representations
FREE_MINOR_FRAC_PRI = 1.0/32.0
FREE_MINOR_FRAC_LOG = 1.0/8.0

supported_types = {
  'all':   ( 'ext2', 'ext3', 'linux-swap' ),
  'x86':   ( 'ntfs', 'fat16', 'fat32', 'xfs', 'jfs', 'reiserfs' ),
  'amd64': ( 'ntfs', 'fat16', 'fat32', 'xfs', 'jfs', 'reiserfs' ),
  'ppc':   ( 'reiserfs', 'apple-bootstrap', 'hfs', 'hfs+' )
}

labelinfo = {
  'msdos': { 'ignoredparts': None, 'extended': True },
  'mac':   { 'ignoredparts': (1,), 'extended': False },
  'sun':   { 'ignoredparts': (3,), 'extended': False }
}

archinfo = {
  'sparc': 'sun',
  'hppa': 'msdos',
  'x86': 'msdos',
  'amd64': 'msdos',
  'ppc': 'mac'
}

##
# This class provides a partitioning abstraction for the frontends
class Device:
	"Class representing a partitionable device."
	
	_device = None
	_partitions = None
	_geometry = None
	_total_bytes = 0
	_total_sectors = 0
	_cylinder_bytes = 0
	_sectors_in_cylinder = 0
	_parted_dev = None
	_parted_disk = None
	_sector_bytes = 0
	_total_mb = 0
	_arch = None
	_disklabel = None

	##
	# Initialization function for Device class
	# @param device Device node (e.g. /dev/hda) of device being represented
	# @param arch Architecture that we're partition for (defaults to 'x86' for now)
	def __init__(self, device, arch="x86", set_geometry=True, local_device=True):
		self._device = device
		self._partitions = []
		self._geometry = {'cylinders': 0, 'heads': 0, 'sectors': 0, 'sectorsize': 512}
		self._total_bytes = 0
		self._cylinder_bytes = 0
		self._arch = arch
		self._local_device = local_device
		if self._local_device:
			self._parted_dev = parted.PedDevice.get(self._device)
			try:
				self._parted_disk = parted.PedDisk.new(self._parted_dev)
			except:
				self._parted_disk = self._parted_dev.disk_new_fresh(parted.disk_type_get(archinfo[self._arch]))
			self._disklabel = self._parted_disk.type.name
		else:
			self._disklabel = archinfo[self._arch]
		self._labelinfo = labelinfo[self._disklabel]
		if set_geometry:
			self.set_disk_geometry_from_disk()

	def __getitem__(self, name):
		return self.get_partition(name)

	def __iter__(self):
		for part in self.get_ordered_partition_list():
			yield part

	##
	# Returns list of supported filesystems based on arch
	def get_supported_types(self):
		return supported_types['all'] + supported_types[self._arch]

	##
	# Sets disk geometry info from disk. This function is used internally by __init__()
	def set_disk_geometry_from_disk(self):
		self._total_bytes = self._parted_dev.length * self._parted_dev.sector_size
		self._geometry['heads'], self._geometry['sectors'], self._geometry['cylinders'] = self._parted_dev.heads, self._parted_dev.sectors, self._parted_dev.cylinders
		self._sector_bytes = self._parted_dev.sector_size
		self._cylinder_bytes = self._geometry['heads'] * self._geometry['sectors'] * self._sector_bytes
		self._total_sectors = self._parted_dev.length
		self._sectors_in_cylinder = self._geometry['heads'] * self._geometry['sectors']
		self._total_mb = long(self._total_bytes / MEGABYTE)

	##
	# Sets partition info from disk.
	def set_partitions_from_disk(self):
		parted_part = self._parted_disk.next_partition()
		while parted_part:
			part_mb = long((parted_part.geom.end - parted_part.geom.start + 1) * self._sector_bytes / MEGABYTE)
			# Ignore metadata "partitions"...this will need to be changed for non-x86
			if parted_part.num >= 1:
				fs_type = ""
				if parted_part.fs_type != None: fs_type = parted_part.fs_type.name
				if parted_part.type == 2: fs_type = "extended"
				part_name = ""
				if self._parted_disk.type.check_feature(parted.DISK_TYPE_PARTITION_NAME):
					part_name = parted_part.get_name()
				self._partitions.append(Partition(self, parted_part.num, part_mb, parted_part.geom.start, parted_part.geom.end, fs_type, format=False, existing=True, name=part_name))
			elif parted_part.type_name == "free":
				if self._disklabel == "mac":
					free_minor = int(GLIUtility.spawn("mac-fdisk -l %s | grep '@ %s' | cut -d ' ' -f 1" % (self._device, str(parted_part.geom.start)), return_output=True)[1].strip()[-1])
				elif self.get_extended_partition() and parted_part.geom.start >= self.get_partition(self.get_extended_partition()).get_start() and parted_part.geom.end <= self.get_partition(self.get_extended_partition()).get_end():
					if self._partitions[-1].get_minor() > 4:
						free_minor = self._partitions[-1].get_minor() + FREE_MINOR_FRAC_LOG
					else:
						free_minor = 4 + FREE_MINOR_FRAC_LOG
				else:
					try:
						free_minor = self._partitions[-1].get_minor() + FREE_MINOR_FRAC_PRI
					except IndexError:
						free_minor = FREE_MINOR_FRAC_PRI
				self._partitions.append(Partition(self, free_minor, part_mb, parted_part.geom.start, parted_part.geom.end, "free", format=False, existing=False))
			parted_part = self._parted_disk.next_partition(parted_part)
		# Juggle minor numbers so they match physical disk order. People may complain, but we're actually doing them a favor
		self.reorder_minors()

	##
	# Reorders partition minors so that they match physical disk order
	def reorder_minors(self):
		for i, part in enumerate(self._partitions):
			if not i:
				last_minor = 0
			else:
				last_minor = self._partitions[i-1].get_minor()
			if part.get_type() == "free":
				if self._disklabel == "mac":
					new_minor = last_minor + 1
				elif last_minor and part.is_logical():
					if self.get_partition(last_minor).is_extended():
						last_minor = 4
					new_minor = last_minor + FREE_MINOR_FRAC_LOG
				else:
					new_minor = last_minor + FREE_MINOR_FRAC_PRI
				part.set_minor(new_minor)
			else:
				if not last_minor:
					new_minor = 1
				else:
					new_minor = int(last_minor) + 1
				part.set_minor(new_minor)

	##
	# Imports partition info from the install profile partition structure
	# @param ips Parameter structure returned from install_profile.get_partition_tables()
	def set_partitions_from_install_profile_structure(self, ips):
		for tmppart in ips:
			existing = False
			if tmppart['origminor'] and not tmppart['format']:
				existing = True
			self._partitions.append(Partition(self, tmppart['minor'], tmppart['mb'], tmppart['start'], tmppart['end'], tmppart['type'], format=tmppart['format'], origminor=tmppart['origminor'], existing=existing, mountpoint=tmppart['mountpoint'], mountopts=tmppart['mountopts'], mkfsopts=tmppart['mkfsopts'], resized=(existing and tmppart['resized'])))

	##
	# Returns the partition object with the specified minor
	# @param minor Minor number of partition object to get
	def get_partition(self, minor):
		for part in self._partitions:
			if part.get_minor() == minor:
				return part
		return None

	def get_partition_position(self, minor):
		for i, part in enumerate(self._partitions):
			if part.get_minor() == minor:
				return i
		return -1

	##
	# Returns name of device (e.g. /dev/hda) being represented
	def get_device(self):
		return self._device

	##
	# Returns whether the device is local or not
	def is_local(self):
		return self._local_device

	##
	# Uses magic to apply the recommended partition layout
	def do_recommended(self):
		free_minor = 0
		recommended_parts = [ { 'type': "ext2", 'size': 100, 'mountpoint': "/boot" },
                              { 'type': "linux-swap", 'size': 512, 'mountpoint': "" },
                              { 'type': "ext3", 'size': "*", 'mountpoint': "/" } ]
		to_create = []
		physical_memory = int(GLIUtility.spawn(r"free -m | egrep '^Mem:' | sed -e 's/^Mem: \+//' -e 's/ \+.\+$//'", return_output=True)[1].strip())
#		parts = self.get_ordered_partition_list()
		# Search for concurrent unallocated space >=4GB
		for part in self._partitions:
			if part.get_type() == "free" and part.get_mb() >= 4096:
				free_minor = part.get_minor()
				break
		if not free_minor:
			raise GLIException("RecommendedPartitionLayoutError", "notice", "do_recommended", "You do not have atleast 4GB of concurrent unallocated space. Please remove some partitions and try again.")
		remaining_free = self.get_partition(free_minor).get_mb()
		for newpart in recommended_parts:
			# extended/logical partitions suck like a hoover
			if self._labelinfo['extended'] and free_minor == (3 + FREE_MINOR_FRAC_PRI) and not newpart == recommended_parts[-1]:
				if self.get_extended_partition():
					raise GLIException("RecommendedPartitionLayoutError", "notice", "do_recommended", "This code is not yet robust enough to handle automatic partitioning with your current layout.")
				to_create.append({ 'type': "extended", 'size': remaining_free, 'mountpoint': "", 'free_minor': free_minor })
				free_minor = 4 + FREE_MINOR_FRAC_LOG
			newpart['free_minor'] = free_minor
			# Small hack to calculate optimal swap partition size
			if newpart['type'] == "linux-swap" and physical_memory and physical_memory < 1024:
				newpart['size'] = physical_memory * 2
			to_create.append(newpart)
			free_minor = free_minor + 1
			if not newpart['size'] == "*":
				remaining_free = remaining_free - newpart['size']
		for newpart in to_create:
			if newpart['size'] == "*":
				# This doesn't seem quite right...it should probably be set to remaining_free
#				newpart['size'] = self.get_partition(newpart['free_minor']).get_mb()
				newpart['size'] = remaining_free
			self.add_partition(newpart['free_minor'], newpart['size'], 0, 0, newpart['type'], mountpoint=newpart['mountpoint'])

	def find_free_minor(self, min, max):
		good_minor = max
		for i in range(int(max) - 1, int(min) - 1, -1):
			if not self.get_partition(i):
				good_minor = i
#		print "min = %s, max = %s, good_minor = %s" % (str(min), str(max), str(good_minor))
		return good_minor

	##
	# Combines free space and closes gaps in minor numbers. This is used internally
	def tidy_partitions(self):
		newparts = []
		for i, part in enumerate(self._partitions):
			if part.get_type() == "free":
				if i and newparts[-1].get_type() == "free":
					newparts[-1].set_mb(newparts[-1].get_mb()+part.get_mb())
#					self._partitions.pop(i)
					continue
				else:
					if self._disklabel == "mac":
						part.set_minor(self.find_free_minor(newparts[-1].get_minor() + 1, part.get_minor()))
					elif self._labelinfo['extended'] and part.get_minor() > 4:
						last_minor = newparts[-1].get_minor()
						if last_minor <= 4: last_minor = 4
						part.set_minor(last_minor + FREE_MINOR_FRAC_LOG)
					else:
						if i:
							free_minor = newparts[-1].get_minor() + FREE_MINOR_FRAC_PRI
						else:
							free_minor = FREE_MINOR_FRAC_PRI
						part.set_minor(free_minor)
			else:
				if self._labelinfo['extended'] and part.get_minor() > 4:
					part.set_minor(self.find_free_minor(5, part.get_minor()))
				else:
					part.set_minor(self.find_free_minor(1, part.get_minor()))
			newparts.append(part)
		self._partitions = newparts

	##
	# Adds a new partition to the partition info
	# @param free_minor minor of unallocated space partition is being created in
	# @param mb size of partition in MB
	# @param start Start sector (only used for existing partitions)
	# @param end End sector (only used for existing partitions)
	# @param type Partition type (ext2, ext3, fat32, linux-swap, free, extended, etc.)
	# @param mountpoint='' Partition mountpoint
	# @param mountopts='' Partition mount options
	# @param mkfsopts='' Additional mkfs options
	def add_partition(self, free_minor, mb, start, end, type, mountpoint='', mountopts='',mkfsopts=''):
		# Automatically pick the first unused minor if not a local device
		if not self._local_device or free_minor == -1:
			tmpminor = self._partitions[-1].get_minor()
			if self._disklabel == "mac":
				free_minor = tmpminor + 1
			elif self._labelinfo['extended'] and tmpminor > 4:
				free_minor = tmpminor + FREE_MINOR_FRAC_LOG
			else:
				free_minor = tmpminor + FREE_MINOR_FRAC_PRI
			self._partitions.append(Partition(self, free_minor, mb, 0, 0, "free"))
		if self._disklabel == "mac":
			new_minor = free_minor
		else:
			new_minor = int(free_minor) + 1
		free_minor_pos = self.get_partition_position(free_minor)
		if self._local_device:
			# Check to see if the new minor we picked already exists. If it does, scoot all partitions from
			# that one on down a minor
			if self.get_partition(new_minor):
				for i, part in enumerate(self._partitions):
					if i <= free_minor_pos or new_minor > part.get_minor(): continue
					part.set_minor(part.get_minor() + 1)
			# If the size specified for the new partition is less than the size of the unallocated space that it
			# is getting placed into, a new partition to represent the remaining unallocated space needs to be
			# created.
			if mb != self.get_partition(free_minor).get_mb():
				old_free_mb = self.get_partition(free_minor).get_mb()
				self._partitions.pop(free_minor_pos)
				if self._disklabel == "mac":
					free_minor = new_minor + 1
					if self.get_partition(free_minor):
						for i, part in enumerate(self._partitions):
							if i < self.get_partition_position(new_minor+1) or free_minor > part.get_minor(): continue
							part.set_minor(part.get_minor() + 1)
				if self._labelinfo['extended'] and new_minor > 4:
					free_minor = new_minor + FREE_MINOR_FRAC_LOG
				else:
					free_minor = new_minor + FREE_MINOR_FRAC_PRI
				self._partitions.insert(free_minor_pos, Partition(self, free_minor, old_free_mb-mb, 0, 0, "free"))
			else:
				self._partitions.pop(free_minor_pos)
		self._partitions.insert(free_minor_pos, Partition(self, new_minor, mb, start, end, type, mountpoint=mountpoint, mountopts=mountopts,mkfsopts=mkfsopts))
		# When we create an extended partition, we have to create the partition to represent the unallocated
		# space inside of the extended partition
		if type == "extended":
			self._partitions.insert(self.get_partition_position(self.get_extended_partition()) + 1, Partition(self, (4 + FREE_MINOR_FRAC_LOG), mb, 0, 0, "free"))
		new_minor_pos = self.get_partition_position(new_minor)
		self.tidy_partitions()
		return self._partitions[new_minor_pos].get_minor()

	##
	# Removes partition from partition info
	# @param minor Minor of partition to remove
	def remove_partition(self, minor):
		part = self.get_partition(minor)
		part_pos = self.get_partition_position(minor)
		free_minor = 0
		if self._disklabel == "mac":
			free_minor = minor
		elif part.is_logical():
			free_minor = int(minor-1)+FREE_MINOR_FRAC_LOG
		else:
			free_minor = int(minor-1)+FREE_MINOR_FRAC_PRI
		if part.get_type() == "extended":
			# Remove free partition inside extended
			self._partitions.pop(part_pos+1)
		self._partitions[part_pos] = Partition(self, free_minor, part.get_mb(), 0, 0, "free", format=False, existing=False)
		self.tidy_partitions()

	##
	# This function clears the partition table
	def clear_partitions(self):
		self._partitions = [ Partition(self, (0 + FREE_MINOR_FRAC_PRI), self.get_total_mb(), 0, 0, "free", format=False, existing=False) ]
		self._disklabel = archinfo[self._arch]

	##
	# Returns an ordered list (disk order) of partition minors
	def get_ordered_partition_list(self):
		partlist = []
		for part in self._partitions:
			partlist.append(part.get_minor())
		return partlist

	##
	# Returns partition info in a format suitable for passing to install_profile.set_partition_tables()
	def get_install_profile_structure(self):
		devlist = []
		for tmppart in self._partitions:
#			tmppart = self._partitions[part]
			devlist.append({ 'mb': tmppart.get_mb(), 'minor': float(tmppart.get_minor()), 'origminor': tmppart.get_orig_minor(), 'type': tmppart.get_type(), 'mountpoint': tmppart.get_mountpoint(), 'mountopts': tmppart.get_mountopts(), 'format': tmppart.get_format(), 'mkfsopts': tmppart.get_mkfsopts(), 'start': tmppart._start, 'end': tmppart._end, 'resized': tmppart.get_resized() })
		return devlist

	##
	# Returns the minor of the extended partition, if any
	def get_extended_partition(self):
		for part in self._partitions:
			if part.is_extended():
				return part.get_minor()
		return 0

	##
	# Returns the drive model
	def get_model(self):
		if self._local_device:
			return self._parted_dev.model
		else:
			return "Generic disk"

	##
	# Sets the disklabel type
	def set_disklabel(self, disklabel):
		self._disklabel = disklabel

	##
	# Returns the disklabel type
	def get_disklabel(self):
		return self._disklabel

	##
	# Returns the number of sectors on the device
	def get_num_sectors(self):
		return long(self._total_sectors)

	##
	# Returns the size of a cylinder in bytes
	def get_cylinder_size(self):
		return long(self._cylinder_bytes)

	##
	# Returns the size of a sector in bytes
	def get_sector_size(self):
		return long(self._sector_bytes)

	##
	# Returns the number of cylinders
	def get_num_cylinders(self):
		return long(self._geometry['cylinders'])

	##
	# Returns the total number of bytes on the device
	def get_drive_bytes(self):
		return long(self._total_bytes)

	##
	# Returns the total number of MB on the device
	def get_total_mb(self):
		if self._local_device:
			return self._total_mb
		else:
			total_mb = 0
			for tmppart in self._partitions:
				total_mb += tmppart.get_mb()
			return total_mb

	##
	# Returns partition info dictionary
	def get_partitions(self):
		return self._partitions

##
# This class represents a partition within a GLIStorageDevice object
class Partition:
	"Class representing a single partition within a Device object"

	_device = None
	_minor = 0
	_orig_minor = 0
	_start = 0
	_end = 0
	_type = None
	_mountpoint = None
	_mountopts = None
	_format = None
	_resizeable = None
	_min_mb_for_resize = 0
	_mb = ""
	_mkfsopts = None
	_resized = False
	_name = None
	
	##
	# Initialization function for the Partition class
	# @param device Parent GLIStorageDevice object
	# @param minor Minor of partition
	# @param mb Parameter Size of partition in MB
	# @param start Parameter Start sector of partition
	# @param end Parameter Start sector of partition
	# @param type Parameter Type of partition (ext2, ext3, fat32, linux-swap, free, extended, etc.)
	# @param mountpoint='' Mountpoint of partition
	# @param mountopts='' Mount options of partition
	# @param mkfsopts='' Additional mkfs options
	# @param format=True Format partition
	# @param existing=False This partition exists on disk
	def __init__(self, device, minor, mb, start, end, type, mountpoint='', mountopts='', format=True, existing=False, origminor=0, mkfsopts='', resized=False, name=""):
		self._device = device
		self._minor = float(minor)
		self._start = long(start)
		self._end = long(end)
		self._type = type or "unknown"
		self._mountpoint = mountpoint
		self._mountopts = mountopts
		self._format = format
		self._mb = mb
		self._orig_minor = origminor
		self._mkfsopts = mkfsopts
		self._resizeable = False
		self._resized = resized
		self._name = name
		self._flags = []
		if type != "free":
			if existing and not origminor:
				self._orig_minor = self._minor
			self._minor = int(self._minor)
			self._orig_minor = int(self._orig_minor)
		if existing:
			try:
				parted_part = device._parted_disk.get_partition(self._orig_minor)
				label_type = device._parted_disk.type.name
				if label_type == "loop":
					dev_node = device._device
				else:
					dev_node = device._device + str(self._orig_minor)
				# The 10 is completely arbitrary. If flags seem to be missed, this number should be increased
				for flag in range(0, 10):
					if parted_part.is_flag_available(flag) and parted_part.get_flag(flag):
						self._flags.append(flag)
				if type == "ext2" or type == "ext3":
					block_size = long(string.strip(commands.getoutput("dumpe2fs -h " + dev_node + r" 2>&1 | grep -e '^Block size:' | sed -e 's/^Block size:\s\+//'")))
					free_blocks = long(string.strip(commands.getoutput("dumpe2fs -h " + dev_node + r" 2>&1 | grep -e '^Free blocks:' | sed -e 's/^Free blocks:\s\+//'")))
					free_bytes = long(block_size * free_blocks)
					# can't hurt to pad (the +50) it a bit since this is really just a guess
					self._min_mb_for_resize = self._mb - long(free_bytes / MEGABYTE) + 50
					self._resizeable = True
				elif type == "ntfs":
					min_bytes = long(commands.getoutput("ntfsresize -f --info " + dev_node + " | grep -e '^You might resize' | sed -e 's/You might resize at //' -e 's/ bytes or .\+//'"))
					self._min_mb_for_resize = long(min_bytes / MEGABYTE) + 50
					self._resizeable = True
				else:
					parted_part = self._device._parted_disk.get_partition(int(self._orig_minor))
					parted_fs = parted_part.geom.file_system_open()
					resize_constraint = parted_fs.get_resize_constraint()
					min_bytes = resize_constraint.min_size * self._device._sector_bytes
					self._min_mb_for_resize = long(min_bytes / MEGABYTE) + 1
					self._resizeable = True
			except:
				self._resizeable = False

	def __getitem__(self, name):
		tmpdict = { 'start': self.get_start,
                    'end': self.get_end,
                    'format': self.get_format,
                    'type': self.get_type,
                    'resized': self.get_resized,
                    'minor': self.get_minor,
                    'mb': self.get_mb,
                    'origminor': self.get_orig_minor,
                    'mountpoint': self.get_mountpoint,
                    'mountopts': self.get_mountopts,
                    'mkfsopts': self.get_mkfsopts,
                    'flags': self.get_flags,
		            'devnode': self.get_devnode,
		            'name': self.get_name
                  }
		if name in tmpdict:
			return tmpdict[name]()
		else:
			raise ValueError(name + " is not a valid attribute!")

	def __setitem__(self, name, value):
		tmpdict = { 'start': self.set_start,
                    'end': self.set_end,
                    'format': self.set_format,
                    'type': self.set_type,
#                    'resized': self.set_resized,
                    'minor': self.set_minor,
                    'mb': self.set_mb,
                    'origminor': self.set_orig_minor,
                    'mountpoint': self.set_mountpoint,
                    'mountopts': self.set_mountopts,
                    'mkfsopts': self.set_mkfsopts,
                    'flags': self.set_flags,
		            'name': self.set_name
                  }
		if name in tmpdict:
			tmpdict[name](value)
		else:
			raise ValueError(name + " is not a valid attribute!")

	##
	# Returns the dev node that this partition will have
	def get_devnode(self):
		device = self._device.get_device()
		if device[-1] in "0123456789":
			return device + "p" + str(self.get_minor())
		else:
			return device + str(self.get_minor())

	##
	# Returns whether or not the partition is extended
	def is_extended(self):
		if self._type == "extended":
			return True
		else:
			return False

	##
	# Returns whether or not the partition is logical
	def is_logical(self):
		if self._type == "free":
			if int(self._minor) + FREE_MINOR_FRAC_LOG == self._minor:
				return True
			else:
				return False
		elif self._device._labelinfo['extended'] and self._minor > 4:
			return True
		else:
			return False

	##
	# Returns a list of logical partitions if this is an extended partition
	def get_logicals(self):
		if not self.is_extended():
			return None
		logicals = []
		for part in self._device._partitions:
			if part.get_minor() > 4 and not part.get_type() == "free":
				logicals.append(part.get_minor())
		return logicals

	##
	# Returns the extened parent partition if this is a logical partition (no longer used)
	def get_extended_parent(self):
		if not self.is_logical():
			return None
		else:
			return self._device.get_partition_at(self._start, ignore_extended=0)

	##
	# Sets the options passed to mkfs
	# @param mkfsopts Options passed to mkfs
	def set_mkfsopts(self, mkfsopts):
		self._mkfsopts = mkfsopts

	##
	# Returns the options passes to mkfs
	def get_mkfsopts(self):
		return self._mkfsopts

	##
	# Sets the start sector for the partition
	# @param start Start sector
	def set_start(self, start):
		self._start = long(start)

	##
	# Returns the start sector for the partition
	def get_start(self):
		return long(self._start)

	##
	# Sets the end sector of the partition
	# @param end End sector
	def set_end(self, end):
		self._end = long(end)

	##
	# Returns end sector for the partition
	def get_end(self):
		return long(self._end)

	##
	# Returns size of partition in MB
	def get_mb(self):
		return self._mb

	##
	# Sets size of partition in MB
	# @param mb Parameter description
	def set_mb(self, mb):
		self._mb = mb

	##
	# Sets type of partition
	# @param type Parameter description
	def set_type(self, type):
		self._type = type

	##
	# Returns type of partition
	def get_type(self):
		return self._type

	##
	# Returns parent GLIStorageDevice object
	def get_device(self):
		return self._device

	##
	# Sets minor of partition
	# @param minor New minor
	def set_minor(self, minor):
		self._minor = float(minor)

	##
	# Returns minor of partition
	def get_minor(self):
		if int(self._minor) == self._minor:
			return int(self._minor)
		else:
			return float(self._minor)

	##
	# Sets the original minor of the partition
	# @param orig_minor Parameter description
	def set_orig_minor(self, orig_minor):
		self._orig_minor = int(orig_minor)

	##
	# Returns the original minor of the partition
	def get_orig_minor(self):
		return self._orig_minor

	##
	# Sets the mountpoint for the partition
	# @param mountpoint Mountpoint
	def set_mountpoint(self, mountpoint):
		self._mountpoint = mountpoint

	##
	# Returns the mountpoint for the partition
	def get_mountpoint(self):
		return self._mountpoint

	##
	# Sets the mount options for the partition
	# @param mountopts Mount options
	def set_mountopts(self, mountopts):
		self._mountopts = mountopts

	##
	# Returns the mount options for the partition
	def get_mountopts(self):
		return self._mountopts

	##
	# Set whether to format the partition
	# @param format Format this partition (True/False)
	def set_format(self, format):
		self._format = format

	##
	# Returns whether to format the partition
	def get_format(self):
		return self._format

	##
	# Returns whether to partition is resized
	def get_resized(self):
		return self._resized

	##
	# Returns whether the partition is resizeable
	def is_resizeable(self):
		return self._resizeable

	##
	# Sets partition flags
	def set_flags(self, flags):
		self._flags = flags

	##
	# Returns partition flags
	def get_flags(self):
		return self._flags

	##
	# Sets partition name
	def set_name(self, name):
		self._name = name

	##
	# Returns partition name
	def get_name(self):
		return self._name

	##
	# Returns minimum MB for resize
	def get_min_mb_for_resize(self):
#		if self.is_extended():
#			min_size = self._start
#			for part in self._device._partitions:
#				if part < 5: continue
#				if part.get_end > min_size: min_size = part.get_end()
#			return min_size
#		else:
		if self._resizeable:
			return self._min_mb_for_resize
		else:
			return -1

	##
	# Returns maximum MB for resize
	def get_max_mb_for_resize(self):
		if self._resizeable:
			minor_pos = self._device.get_partition_position(self._minor)
			try:
				free_minor = self._device._partitions[minor_pos+1].get_minor()
			except:
				free_minor = 0
			if not free_minor or not self._device.get_partition(free_minor).get_type() == "free": return self._mb
			if self._device.get_partition(free_minor).is_logical():
				if self.is_logical():
					return self._mb + self._device.get_partition(free_minor).get_mb()
				else:
					return self._mb
			else:
				return self._mb + self._device.get_partition(free_minor).get_mb()
		else:
			return -1

	##
	# Resizes the partition
	# @param mb New size in MB
	def resize(self, mb):
		minor_pos = self._device.get_partition_position(self._minor)
		try:
			free_minor = self._device._partitions[minor_pos+1].get_minor()
		except:
			free_minor = 0
		if mb < self._mb:
			# Shrinking
			if not free_minor or not self._device.get_partition(free_minor).get_type() == "free":
				if self._device._disklabel == "mac":
					free_minor = self._minor + 1
				elif self.is_logical():
					free_minor = self._minor + FREE_MINOR_FRAC_LOG
				else:
					free_minor = self._minor + FREE_MINOR_FRAC_PRI
				if self._device.get_partition(free_minor):
					for i, part in enumerate(self._device._partitions):
						if i <= minor_pos or free_minor > part.get_minor(): continue
						part.set_minor(part.get_minor() + 1)
				self._device._partitions.insert(minor_pos+1, Partition(self._device, free_minor, self._mb - mb, 0, 0, "free", format=False, existing=False))
			else:
				self._device.get_partition(free_minor).set_mb(self._device.get_partition(free_minor).get_mb() + (self._mb - mb))
			self._mb = mb
		else:
			if mb == self._mb + self._device.get_partition(free_minor).get_mb():
				# Using all available unallocated space
				self._device._partitions.pop(self._device.get_partition_position(free_minor))
				self._mb = mb
			else:
				# Growing
				self._device.get_partition(free_minor).set_mb(self._device.get_partition(free_minor).get_mb() - (mb - self._mb))
				self._mb = mb
		self._resized = True
		self._device.tidy_partitions()

##
# Returns a list of detected partitionable devices
def detect_devices():
	devices = []
	
	# Make sure sysfs exists
	# TODO: rewrite for 2.4 support
	if not os.path.exists("/sys/bus"):
		raise GLIException("GLIStorageDeviceError", 'fatal', 'detect_devices', "no sysfs found (you MUST use a kernel >2.6)")
	# Make sure /proc/partitions exists
	if not os.path.exists("/proc/partitions"):
		raise GLIException("GLIStorageDeviceError", 'fatal', 'detect_devices', "/proc/partitions does not exist! Please make sure procfs is in your kernel and mounted!")
	
	# Load /proc/partitions into the variable 'partitions'
	partitions = []
	for line in open("/proc/partitions"):
		tmpparts = line.split()
		if len(tmpparts) < 4 or not tmpparts[0].isdigit() or not tmpparts[1].isdigit():
			continue
		
		# Get the major, minor and device name
		major = int(tmpparts[0])
		minor = int(tmpparts[1])
		device = "/dev/" + tmpparts[3]
		
		# If there is no /dev/'device_name', then scan
		# all the devices in /dev to try and find a
		# devices with the same major and minor		
		if not os.path.exists(device):
			device = None
			for path, dirs, files in os.walk("/dev"):
				for d_file in files:
					full_file = os.path.join(path, d_file)
					if not os.path.exists(full_file):
						continue
					statres = os.stat(full_file)
					fmaj = os.major(statres.st_rdev)
					fmin = os.minor(statres.st_rdev)
					if fmaj == major and fmin == minor:
						device = full_file
						break
			if not device:
				continue
			
		partitions.append(( major, minor, device ))
	
	# Scan sysfs for the devices of type 'x'
	# 'x' being a member of the list below:
	# Compaq cards.../sys/block/{cciss,ida}!cXdX/dev
	for dev_glob in ("/sys/bus/ide/devices/*/block*/dev", "/sys/bus/scsi/devices/*/block*/dev", "/sys/block/cciss*/dev", "/sys/block/ida*/dev"):
		sysfs_devices = glob(dev_glob)
		if not sysfs_devices: continue
		for sysfs_device in sysfs_devices:
			# Get the major and minor info
			try:
				major, minor = open(sysfs_device).read().split(":")
				major = int(major)
				minor = int(minor)
			except:
				raise GLIException("GLIStorageDeviceError", 'fatal', 'detect_devices', "invalid major/minor in " + sysfs_device)
			
			# Find a device listed in /proc/partitions
			# that has the same minor and major as our
			# current block device.
			for record in partitions:
				if major == record[0] and minor == record[1]:
					devices.append(record[2])

	# For testing the partitioning code
	if GLIUtility.is_file("/tmp/disk.img"):
		devices.append("/tmp/disk.img")

	# We have assembled the list of devices, so return it
	return devices
