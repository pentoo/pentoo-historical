# Copyright 1999-2005 Gentoo Foundation
# This source code is distributed under the terms of version 2 of the GNU
# General Public License as published by the Free Software Foundation, a copy
# of which can be found in the main directory of this project.

import gtk
import GLIScreen
import GLIStorageDevice
from GLIException import *
import re
import PartitionButton
import PartProperties
from gettext import gettext as _

class Panel(GLIScreen.GLIScreen):

	title = _("Partitioning")
	part_buttons = {}
	drives = []
	devices = {}
	active_device = ""
	active_device_bytes_in_cylinder = 0
	active_device_bytes_in_sector = 0
	active_device_cylinders = 0
	active_part_min_size = 0
	active_part_max_size = 0
	active_part_cur_size = 0
	active_part_start_cyl = 0
	active_part_minor = 0
	colors = { 'ext2': '#0af2fe', 'ext3': '#0af2fe', 'unalloc': '#a2a2a2', 'unknown': '#ed03e0', 'free': '#ffffff', 'ntfs': '#f20600', 'fat16': '#3d07f9', 'fat32': '#3d07f9', 'reiserfs': '#f0ff00', 'linux-swap': '#12ff09', 'xfs': '#006600', 'jfs': '#ffb400', 'hfs': '#fdb0ff' }
	supported_filesystems = ["ext2", "ext3", "linux-swap", "xfs", "jfs", "reiserfs", "fat16", "fat32", "ntfs", "hfs"]
	_helptext = """
<b><u>Partitioning</u></b>

The choices you make on this screen are very important. There are 2 ways to do
your partitioning.

The first method is the Recommended Layout. If you really have no idea how you
should lay out your partitions, this is probably the best option. You will need
at least 4GB of concurrent disk space to use this option. If you have any
existing partitions, they will be kept intact. Three partitions will be created:
/boot (100MB), swap (calculated based on physical memory, up to 512MB), and
/ (remaining concurrent space). The mountpoints and default mount options will
be automatically set for you. If you would like to mount any of your previously
existing partitions, you will need to edit those manually.

The second method is the old fashioned one: doing it yourself. The partition
edit is fairly straightforward (although, not <i>that</i> straightforward as
this help would not need to exist).

The currently active disk is represented by the bar near the top of the screen.
If you have more than one disk present in your system, you can change the
active disk by choosing another disk from the drop down box labeled 'Devices'.
Along the bottom of the screen, there is a color key for the disk representation
above.

To edit an existing partition, you must first select it by clicking it in the
bar above. You will get a brief overview of the partition below the bar. To edit
the partition's properties, click the button labeled 'Properties'. To delete it,
click the 'Delete' button. You will be asked for confirmation before the
partition is removed.

When you edit a partition's properties, you'll get a popup dialog with a few
options. If the installer is able to resize the partition, you will be able to
slide the bar at the top or enter a new size in the fields below the slider.
You can choose whether or not you want the partition to be formatted. If you
to keep the data, you should leave this as No. You can also choose a mountpoint
and mount options for the partition. If you don't enter a mountpoint, the
partition will not be mounted during the install and will not be added to your
/etc/fstab. Click 'OK' to save the changes you have made or 'Cancel' to leave it
as it was.

To create a new partition, select some unallocated space in the bar at the top.
The popup dialog that appears is the same one used for editing an existing
partition. The difference is that you will be able to select a partition type
(primary or logical for x86/amd64) and a filesystem type. If you select logical
for the type, an extended partition will be created automatically and take up
all of the remaining unallocated space. All partitions created after this will
automatically be logical. For a partition for use by Linux, you will want to use
ext2, ext3, reiserfs, jfs, or xfs. Ext3 is the recommended type.

Keep in mind that none of the changes to your partition table and filesystems
will be committed until you click the 'Install' button on the last screen of the
installer. Also, if your existing partitions are out of disk order, the 
installer will reorder the partition numbers so that they match the physical
disk order.
"""

	def __init__(self, controller):
		GLIScreen.GLIScreen.__init__(self, controller, show_title=True)

		vert = gtk.VBox(False, 0)
		vert.set_border_width(10)

		content_str = _("""
		On this screen, you will be presented with a list of detected partitionable devices. Selecting
		a device will show you the current partitions on it (if any) and allow you to add, remove, and
		resize partitions.""")
 
		content_label = gtk.Label(content_str)
		vert.pack_start(content_label, expand=False, fill=False, padding=0) # This was removed for screen space
		container = gtk.HBox(False, 0)
		detected_dev_label = gtk.Label(_("Devices:"))
		container.pack_start(detected_dev_label, expand=False, fill=False, padding=0)
		self.detected_dev_combo = gtk.combo_box_new_text()
		self.detected_dev_combo.connect("changed", self.drive_changed)
		container.pack_start(self.detected_dev_combo, expand=False, fill=False, padding=10)
		self.part_button_recommended = gtk.Button(_(" Recommended layout "))
		self.part_button_recommended.connect("clicked", self.part_button_recommended_clicked)
		container.pack_end(self.part_button_recommended, expand=False, fill=False, padding=0)
		self.part_button_clear = gtk.Button(_(" Clear partitions "))
		self.part_button_clear.connect("clicked", self.part_button_clear_clicked)
		container.pack_end(self.part_button_clear, expand=False, fill=False, padding=10)
		self.part_button_dump_info = gtk.Button(_(" Dump to console (debug) "))
		self.part_button_dump_info.connect("clicked", self.dump_part_info_to_console)
		container.pack_end(self.part_button_dump_info, expand=False, fill=False, padding=0)

		vert.pack_start(container, expand=False, fill=False, padding=10)

		# This builds the container for the "whole disk" display at the top
		part_table_frame = gtk.Frame()
		part_table_frame.set_shadow_type(gtk.SHADOW_IN)
		self.part_table = gtk.Table(1, 1, False)
		self.part_table.set_size_request(-1, 40)
		part_table_frame.add(self.part_table)
		vert.pack_start(part_table_frame, expand=False, fill=False, padding=5)

		# This builds the partition info box
		self.part_info_box = gtk.HBox(False, 0)
		part_info_table = gtk.Table(6, 2, False)
		part_info_table.set_col_spacings(10)
		info_partition_label = gtk.Label(_("Partition:"))
		info_partition_label.set_alignment(0.0, 0.5)
		self.info_partition = gtk.Label()
		self.info_partition.set_alignment(0.0, 0.5)
		info_type_label = gtk.Label(_("Type:"))
		info_type_label.set_alignment(0.0, 0.5)
		self.info_type = gtk.Label()
		self.info_type.set_alignment(0.0, 0.5)
		info_filesystem_label = gtk.Label(_("Filesystem:"))
		info_filesystem_label.set_alignment(0.0, 0.5)
		self.info_filesystem = gtk.Label()
		self.info_filesystem.set_alignment(0.0, 0.5)
		info_mountpoint_label = gtk.Label(_("Mountpoint:"))
		info_mountpoint_label.set_alignment(0.0, 0.5)
		self.info_mountpoint = gtk.Label()
		self.info_mountpoint.set_alignment(0.0, 0.5)
		info_size_label = gtk.Label(_("Size:"))
		info_size_label.set_alignment(0.0, 0.5)
		self.info_size = gtk.Label()
		self.info_size.set_alignment(0.0, 0.5)
		part_info_table.attach(info_partition_label, 0, 1, 0, 1)
		part_info_table.attach(self.info_partition, 1, 2, 0, 1)
		part_info_table.attach(info_type_label, 0, 1, 1, 2)
		part_info_table.attach(self.info_type, 1, 2, 1, 2)
		part_info_table.attach(info_filesystem_label, 0, 1, 2, 3)
		part_info_table.attach(self.info_filesystem, 1, 2, 2, 3)
		part_info_table.attach(info_mountpoint_label, 0, 1, 3, 4)
		part_info_table.attach(self.info_mountpoint, 1, 2, 3, 4)

		part_info_table.attach(info_size_label, 0, 1, 5, 6)
		part_info_table.attach(self.info_size, 1, 2, 5, 6)
		self.part_info_box.pack_start(part_info_table, expand=False, fill=False)
		vert.pack_start(self.part_info_box, expand=False, fill=False, padding=10)

		# This builds the row of buttons
		self.part_button_box = gtk.HBox(False, 0)
		self.part_button_delete = gtk.Button(_(" Delete "))
		self.part_button_delete.connect("clicked", self.part_button_delete_clicked)
		self.part_button_box.pack_start(self.part_button_delete, expand=False, fill=False, padding=0)
#		self.part_button_recommended = gtk.Button(_(" Recommended "))
#		self.part_button_recommended.connect("clicked", self.part_button_recommended_clicked)
#		self.part_button_box.pack_start(self.part_button_recommended, expand=False, fill=False, padding=10)
		self.part_button_properties = gtk.Button(_(" Properties "))
		self.part_button_properties.connect("clicked", self.part_button_properties_clicked)
		self.part_button_box.pack_start(self.part_button_properties, expand=False, fill=False, padding=10)
		vert.pack_start(self.part_button_box, expand=False, fill=False, padding=10)

		# This builds the color key at the bottom
		color_codes = [ { 'label': "Swap", 'color': '#12ff09' },
                                { 'label': "Ext2/3", 'color': '#0af2fe' },
                                { 'label': "Reiserfs", 'color': '#f0ff00' },
                                { 'label': "JFS", 'color': '#ffb400' },
                                { 'label': "XFS", 'color': '#006600' },
                                { 'label': "FAT", 'color': '#3d07f9' },
                                { 'label': "NTFS", 'color': '#f20600' },
                                { 'label': "HFS", 'color': '#fdb0ff' },
                                { 'label': _("Other"), 'color': '#ed03e0' },
#                                { 'label': "Free space", 'color': '#ffffff' },
                                { 'label': _("Unallocated"), 'color': '#a2a2a2' }
                              ]
		color_codes_box = gtk.HBox(False, 0)
		vert.pack_end(color_codes_box, expand=False, fill=False, padding=2)
		for color in color_codes:
			temp_xpm = [ "12 12 2 1",
                                     "B c #000000",
                                     "C c " + color['color'],
                                     "BBBBBBBBBBBB",
                                     "BCCCCCCCCCCB",
                                     "BCCCCCCCCCCB",
                                     "BCCCCCCCCCCB",
                                     "BCCCCCCCCCCB",
                                     "BCCCCCCCCCCB",
                                     "BCCCCCCCCCCB",
                                     "BCCCCCCCCCCB",
                                     "BCCCCCCCCCCB",
                                     "BCCCCCCCCCCB",
                                     "BCCCCCCCCCCB",
                                     "BBBBBBBBBBBB"
                                   ]
			pixmap, mask = gtk.gdk.pixmap_create_from_xpm_d(self.controller.window.window, None, temp_xpm)
			tmp_image = gtk.Image()
			tmp_image.set_from_pixmap(pixmap, mask)
			tmpbox = gtk.HBox(False, 0)
			tmpbox.pack_start(tmp_image, expand=False, fill=False, padding=3)
			tmpbox.pack_start(gtk.Label(color['label']), expand=False, fill=False, padding=3)
			color_codes_box.pack_start(tmpbox, expand=False, fill=False, padding=6)

		self.add_content(vert)
#		self.detected_dev_combo.set_active(0)

	def drive_changed(self, combobox, data=None):
		self.active_device = self.drives[self.detected_dev_combo.get_active()]
		self.draw_part_box()
		self.active_device_cylinders = self.devices[self.active_device].get_num_cylinders()
		self.active_device_bytes_in_cylinder = self.devices[self.active_device].get_cylinder_size()
		self.active_device_bytes_in_sector = self.devices[self.active_device].get_sector_size()
		self.info_partition.set_text("")
		self.info_type.set_text("")
		self.info_filesystem.set_text("")
		self.info_mountpoint.set_text("")
#		self.info_end.set_text("")
		self.info_size.set_text("")
		self.part_info_box.hide_all()
#		self.resize_box.hide_all()
		self.part_button_box.hide_all()
#		self.part_mount_info_box.hide_all()

	def part_selected(self, button, dev=None, minor=None):
		minor = int(minor)
		tmppart = self.devices[dev].get_partition(minor)
		self.info_partition.set_text(tmppart['devnode'])
		if self.devices[dev]._labelinfo['extended'] and minor > 4:
			self.info_type.set_text(_("Logical"))
		elif tmppart.get_type() == "extended":
			self.info_type.set_text(_("Extended"))
		else:
			self.info_type.set_text(_("Primary"))
		fstype = tmppart.get_type()
		if fstype == "extended":
			self.info_filesystem.set_text(_("N/A"))
		else:
			self.info_filesystem.set_text(fstype)
		self.info_mountpoint.set_text(tmppart.get_mountpoint() or "none")
		start = tmppart.get_start()
		end = tmppart.get_end()
#		self.info_start.set_text(str(start))
#		self.info_end.set_text(str(end))
#		part_size = int(round(float(self.devices[dev].get_sector_size()) * (end - start + 1) / 1024 / 1024))
		part_size = int(tmppart.get_mb())
		self.info_size.set_text(str(part_size) + _(" MB"))
		self.active_part_minor = int(tmppart.get_minor())
		self.part_button_delete.set_sensitive(True)
		self.part_info_box.show_all()
		self.part_button_box.show_all()

	def unalloc_selected(self, button, dev=None, extended=False, mb=0, minor=0):
		props = PartProperties.PartProperties(self, self.active_device, minor, 0, 0, mb, "free", self.active_device_bytes_in_sector)
		props.run()

	def part_button_delete_clicked(self, button, data=None):
		msgdlg = gtk.MessageDialog(parent=self.controller.window, type=gtk.MESSAGE_QUESTION, buttons=gtk.BUTTONS_YES_NO, message_format=_("Are you sure you want to delete ") + self.devices[self.active_device][self.active_part_minor]['devnode'])
		resp = msgdlg.run()
		msgdlg.destroy()
		if resp == gtk.RESPONSE_YES:
			self.devices[self.active_device].remove_partition(self.active_part_minor)
			if self.devices[self.active_device]._labelinfo['extended'] and self.active_part_minor > 4:
				ext_part = self.devices[self.active_device].get_extended_partition()
				if not len(self.devices[self.active_device].get_partition(ext_part).get_logicals()):
					self.devices[self.active_device].remove_partition(ext_part)
			self.drive_changed(None)

	def part_button_recommended_clicked(self, button):
		try:
			self.devices[self.active_device].do_recommended()
		except GLIException, error:
			msgdlg = gtk.MessageDialog(parent=self.controller.window, type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK, message_format=error.get_error_msg())
			msgdlg.run()
			msgdlg.destroy()
		self.draw_part_box()

	def part_button_clear_clicked(self, button):
		msgdlg = gtk.MessageDialog(parent=self.controller.window, type=gtk.MESSAGE_QUESTION, buttons=gtk.BUTTONS_YES_NO, message_format=_("Are you sure you wish to clear the partition table for " + self.active_device + "?"))
		resp = msgdlg.run()
		msgdlg.destroy()
		if resp == gtk.RESPONSE_YES:
			self.devices[self.active_device].clear_partitions()
			self.drive_changed(self.detected_dev_combo)

	def draw_part_box(self):
#		partlist = self.devices[self.active_device].get_ordered_partition_list()
		cylinders = self.devices[self.active_device].get_num_cylinders()
		sectors = self.devices[self.active_device].get_num_sectors()
		total_mb = self.devices[self.active_device].get_total_mb()
		for button in self.part_buttons.keys():
			self.part_table.remove(self.part_buttons[button])
		self.part_table.resize(1, 100)
		self.part_buttons = {}
		last_percent = 0
		last_log_percent = 0
		extended_part = 0
		extended_table = None
		for part in self.devices[self.active_device]: #.get_partitions():
			tmppart = self.devices[self.active_device][part]
			if tmppart.get_type() == "free":
				partsize = tmppart.get_mb()
				percent = (float(partsize) / float(total_mb)) * 100
				if percent < 1: percent = 1
				percent = int(percent)
#				print "minor: " + str(part) + ", mb: " + str(partsize) + ", percent: " + str(percent) + ", last_percent: " + str(last_percent)
				if tmppart.is_logical():
					tmpbutton = PartitionButton.Partition(color1=self.colors['unalloc'], color2=self.colors['unalloc'], label="", division=0)
					tmpbutton.connect("clicked", self.unalloc_selected, self.active_device, False, partsize, tmppart.get_minor())
					extended_table.attach(tmpbutton, last_log_percent, (last_log_percent + percent), 0, 1)
					last_log_percent = last_log_percent + percent
				else:
					self.part_buttons['free_' + str(tmppart.get_minor())] = PartitionButton.Partition(color1=self.colors['unalloc'], color2=self.colors['unalloc'], label="", division=0)
					if self.devices[self.active_device]._labelinfo['extended'] and self.devices[self.active_device].get_partition(1) and self.devices[self.active_device].get_partition(2) and self.devices[self.active_device].get_partition(3) and self.devices[self.active_device].get_partition(4):
						self.part_buttons['free_' + str(tmppart.get_minor())].connect("clicked", self.show_no_more_primary_message)
					else:
						self.part_buttons['free_' + str(tmppart.get_minor())].connect("clicked", self.unalloc_selected, self.active_device, False, partsize, tmppart.get_minor())
					self.part_table.attach(self.part_buttons['free_' + str(tmppart.get_minor())], last_percent, (last_percent + percent), 0, 1)
					last_percent = last_percent + percent
			else:
				partsize = tmppart.get_mb()
				percent = (float(partsize) / float(total_mb)) * 100
				if percent < 1: percent = 1
				percent = int(percent)
				tmpminor = int(tmppart.get_minor())
				tmpdevice = self.active_device
#				print "minor: " + str(tmpminor) + ", mb: " + str(partsize) + ", percent: " + str(percent) + ", last_percent: " + str(last_percent)
				if tmppart.is_extended():
					extended_table = gtk.Table(1, percent)
					extended_table.set_border_width(3)
					extended_part = tmpminor
					self.part_buttons[tmpminor] = extended_table
					self.part_table.attach(self.part_buttons[tmpminor], last_percent, (last_percent + percent), 0, 1)
					last_percent = last_percent + percent
				elif tmppart.is_logical():
					tmpbutton = PartitionButton.Partition(color1=self.colors[tmppart.get_type()], color2=self.colors[tmppart.get_type()], label="", division=0)
					if percent >= 15:
						tmpbutton.set_label(tmppart['devnode'])
					extended_table.attach(tmpbutton, last_log_percent, (last_log_percent + percent), 0, 1)
					last_log_percent = last_log_percent + percent
					tmpbutton.connect("clicked", self.part_selected, tmpdevice, tmpminor)
				else:
					self.part_buttons[tmpminor] = PartitionButton.Partition(color1=self.colors[tmppart.get_type()], color2=self.colors[tmppart.get_type()], label="", division=0)
					if percent >= 15:
						self.part_buttons[tmpminor].set_label(tmppart['devnode'])
					self.part_buttons[tmpminor].connect("clicked", self.part_selected, tmpdevice, tmpminor)
					self.part_table.attach(self.part_buttons[tmpminor], last_percent, (last_percent + percent), 0, 1)
					last_percent = last_percent + percent
		self.part_table.show_all()

	def show_no_more_primary_message(self, button, data=None):
		msgdlg = gtk.MessageDialog(parent=self.controller.window, type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK, message_format=_("You cannot create more than 4 primary partitions. If you need more partitions, delete one or more and create logical partitions."))
		msgdlg.run()
		msgdlg.destroy()

	def dump_part_info_to_console(self, button, data=None):
		import pprint
		pp = pprint.PrettyPrinter(indent=4)
		pp.pprint(self.devices[self.active_device].get_install_profile_structure())

	def part_button_properties_clicked(self, widget, data=None):
		tmppart = self.devices[self.active_device].get_partition(self.active_part_minor)
		props = PartProperties.PartProperties(self, self.active_device, self.active_part_minor, tmppart.get_mb(), tmppart.get_min_mb_for_resize(), tmppart.get_max_mb_for_resize(), tmppart.get_type(), self.active_device_bytes_in_sector, format=tmppart.get_format())
		props.run()

	def activate(self):
		self.controller.SHOW_BUTTON_EXIT    = True
		self.controller.SHOW_BUTTON_HELP    = True
		self.controller.SHOW_BUTTON_BACK    = False
		self.controller.SHOW_BUTTON_FORWARD = True
		self.controller.SHOW_BUTTON_FINISH  = False

		self.devices = self.controller.install_profile.get_partition_tables()
		if not self.devices:
			part_load_error = 0
			tmp_drives = GLIStorageDevice.detect_devices()
			tmp_drives.sort()
			for drive in tmp_drives:
				try:
					self.devices[drive] = GLIStorageDevice.Device(drive, arch=self.controller.client_profile.get_architecture_template())
					self.devices[drive].set_partitions_from_disk()
					self.detected_dev_combo.append_text(drive)
					self.drives.append(drive)
				except:
					print _("Exception received while loading partitions")
					if self.devices.has_key(drive): del self.devices[drive]
					part_load_error = 1
			if part_load_error:
				msgdlg = gtk.MessageDialog(parent=self.controller.window, type=gtk.MESSAGE_WARNING, buttons=gtk.BUTTONS_OK, message_format="There was an error loading one or more drives' partition table. Possible causes are running as a normal user or partitions being out of disk order.")
				msgdlg.run()
				msgdlg.destroy()
				return

		if not self.drives:
			tmp_drives = self.devices.keys()
			tmp_drives.sort()
			self.drives = tmp_drives
			for drive in self.drives:
				self.detected_dev_combo.append_text(drive)
					
		if self.devices:
			self.active_device = self.drives[0]
			self.detected_dev_combo.set_active(0)
			self.drive_changed(None)

		for device in self.devices:
			for tmppart in self.devices[device].get_partitions():
				if tmppart.get_type() == "unknown":
					msgdlg = gtk.MessageDialog(parent=self.controller.window, type=gtk.MESSAGE_WARNING, buttons=gtk.BUTTONS_OK, message_format="One of your disks contains a partition of a type that the installer cannot currently handle. If you continue, you risk damaging your partition table. You have been warned!")
					msgdlg.run()
					msgdlg.destroy()
					return

	def deactivate(self):
		parts_tmp = {}
		for device in self.devices.keys():
			parts_tmp[device] = self.devices[device].get_install_profile_structure()
		for device in parts_tmp:
			for part in parts_tmp[device]:
				if part['mountpoint'] == "/":
					self.controller.install_profile.set_partition_tables(self.devices)
					return True
		msgdlg = gtk.MessageDialog(parent=self.controller.window, type=gtk.MESSAGE_QUESTION, buttons=gtk.BUTTONS_YES_NO, message_format=_("You have not specified a partition to mount as /. Do you want to continue?"))
		resp = msgdlg.run()
		msgdlg.destroy()
		if resp == gtk.RESPONSE_YES:
			self.controller.install_profile.set_partition_tables(self.devices)
			return True
		else:
			return False
