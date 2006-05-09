# Copyright 1999-2005 Gentoo Foundation
# This source code is distributed under the terms of version 2 of the GNU
# General Public License as published by the Free Software Foundation, a copy
# of which can be found in the main directory of this project.

import gtk
import PartitionButton
from gettext import gettext as _

# keep these in sync with GLIStorageDevice!
# these are here so that we can change them easily in future
# the values were chosen to represent perfect floating point representations
FREE_MINOR_FRAC_PRI = 1.0/32.0
FREE_MINOR_FRAC_LOG = 1.0/8.0

class PartProperties(gtk.Window):

	def __init__(self, controller, device, minor, cur_size, min_size, max_size, fstype, bytes_in_sector=512, format=True):
		gtk.Window.__init__(self, gtk.WINDOW_TOPLEVEL)

		self.controller = controller
		self.device = device
		self.minor = minor
		self.min_size = min_size
		self.max_size = max_size
		self.cur_size = cur_size
		self.fstype = fstype
		self.bytes_in_sector = bytes_in_sector
		self.format = format
		if self.min_size == -1 or self.max_size == -1:
			self.min_size = self.cur_size
			self.max_size = self.cur_size
		self.sync_slider_to_text = True

		self.connect("delete_event", self.delete_event)
		self.connect("destroy", self.destroy_event)
		self.set_default_size(400,300)
		if self.fstype == "free":
			self.set_title(_("New partition on ") + device)
		else:
			self.set_title(_("Properties for ") + self.controller.devices[self.device][minor]['devnode'])

		self.globalbox = gtk.VBox(False, 0)
		self.globalbox.set_border_width(10)

		self.resize_box = gtk.VBox(False, 0)
		self.resize_hpaned = gtk.HPaned()
#		self.resize_hpaned.set_size_request(400, -1)
		self.resize_hpaned.connect("size-allocate", self.part_resized)
		self.resize_part_space_frame = gtk.Frame()
		self.resize_part_space_frame.set_shadow_type(gtk.SHADOW_IN)
		self.resize_part_space = PartitionButton.Partition(color1=self.controller.colors['linux-swap'], color2=self.controller.colors['free'], division=0, label="")
		self.resize_part_space.set_sensitive(False)
		self.resize_part_space_frame.add(self.resize_part_space)
		if self.type == "free" or self.min_size <= 1:
			self.resize_hpaned.pack1(self.resize_part_space_frame, resize=True, shrink=True)
		else:
			self.resize_hpaned.pack1(self.resize_part_space_frame, resize=True, shrink=False)
		self.resize_unalloc_space_frame = gtk.Frame()
		self.resize_unalloc_space_frame.set_shadow_type(gtk.SHADOW_IN)
		self.resize_unalloc_space = PartitionButton.Partition(color1=self.controller.colors['unalloc'], color2=self.controller.colors['unalloc'], label="")
		self.resize_unalloc_space.set_sensitive(False)
		self.resize_unalloc_space_frame.add(self.resize_unalloc_space)
		self.resize_hpaned.add2(self.resize_unalloc_space_frame)
		self.resize_hpaned.set_position(0)
		self.resize_box.pack_start(self.resize_hpaned, expand=False, fill=False, padding=0)
		self.resize_box.pack_start(gtk.Label(_("You can slide above or enter values below")), expand=False, padding=2)
		resize_text_box = gtk.HBox(False, 0)
		resize_text_box.pack_start(gtk.Label(_("New size:")), expand=False, fill=False, padding=0)
		self.resize_info_part_size = gtk.Entry(max=9)
		self.resize_info_part_size.set_width_chars(7)
		self.resize_info_part_size.connect("insert-text", self.validate_keypress)
		self.resize_info_part_size.connect("focus-out-event", self.update_slider_and_entries, "part-size")
		resize_text_box.pack_start(self.resize_info_part_size, expand=False, fill=False, padding=6)
		resize_text_box.pack_start(gtk.Label(_("MB")), expand=False, fill=False, padding=0)
		resize_text_box.pack_start(gtk.Label("  "), expand=False, fill=False, padding=20)
		resize_text_box.pack_start(gtk.Label(_("Unalloc. size:")), expand=False, fill=False, padding=6)
		self.resize_info_unalloc_size = gtk.Entry(max=9)
		self.resize_info_unalloc_size.set_width_chars(7)
		self.resize_info_unalloc_size.connect("insert-text", self.validate_keypress)
		self.resize_info_unalloc_size.connect("focus-out-event", self.update_slider_and_entries, "unalloc-size")
		resize_text_box.pack_start(self.resize_info_unalloc_size, expand=False, fill=False, padding=0)
		resize_text_box.pack_start(gtk.Label("MB"), expand=False, fill=False, padding=3)
		self.resize_box.pack_start(resize_text_box, expand=False, fill=False, padding=10)
		self.globalbox.pack_start(self.resize_box, expand=False, fill=False, padding=0)

		self.part_info_box = gtk.HBox(False, 0)
		part_info_table = gtk.Table(6, 2, False)
		part_info_table.set_col_spacings(10)
		part_info_table.set_row_spacings(5)
		info_partition_label = gtk.Label(_("Partition:"))
		info_partition_label.set_alignment(0.0, 0.5)
		part_info_table.attach(info_partition_label, 0, 1, 0, 1)
		self.info_partition = gtk.Label()
		self.info_partition.set_alignment(0.0, 0.5)
		part_info_table.attach(self.info_partition, 1, 2, 0, 1)

		info_partition_format = gtk.Label(_("Format:"))
		info_partition_format.set_alignment(0.0, 0.5)
		part_info_table.attach(info_partition_format, 0, 1, 1, 2)
		resize_info_part_format_box = gtk.HBox(False, 0)
		self.resize_info_part_format_yes = gtk.RadioButton(label=_("Yes"))
		self.resize_info_part_format_no = gtk.RadioButton(label=_("No"), group=self.resize_info_part_format_yes)
		if self.fstype == "free":
			self.resize_info_part_format_yes.set_sensitive(False)
			self.resize_info_part_format_no.set_sensitive(False)
		else:
			if self.format:
				self.resize_info_part_format_yes.set_active(True)
			else:
				self.resize_info_part_format_no.set_active(True)
		resize_info_part_format_box.pack_start(self.resize_info_part_format_yes, expand=False, fill=False)
		resize_info_part_format_box.pack_start(self.resize_info_part_format_no, expand=False, fill=False, padding=10)
		part_info_table.attach(resize_info_part_format_box, 1, 2, 1, 2)

		info_partition_type = gtk.Label(_("Type:"))
		info_partition_type.set_alignment(0.0, 0.5)
		part_info_table.attach(info_partition_type, 0, 1, 2, 3)
		self.resize_info_part_type = gtk.combo_box_new_text()
		self.resize_info_part_type.append_text(_("Primary"))
		self.resize_info_part_type.append_text(_("Logical"))
		self.resize_info_part_type.set_active(0)
		part_info_table.attach(self.resize_info_part_type, 1, 2, 2, 3)

		info_partition_fs = gtk.Label(_("Filesystem:"))
		info_partition_fs.set_alignment(0.0, 0.5)
		part_info_table.attach(info_partition_fs, 0, 1, 3, 4)
		self.resize_info_part_filesystem = gtk.combo_box_new_text()
		for fs in self.controller.supported_filesystems:
			self.resize_info_part_filesystem.append_text(fs)
		self.resize_info_part_filesystem.set_active(0)
		self.resize_info_part_filesystem.connect("changed", self.filesystem_changed)
		part_info_table.attach(self.resize_info_part_filesystem, 1, 2, 3, 4)

		info_partition_mountpoint = gtk.Label(_("Mount point:"))
		info_partition_mountpoint.set_alignment(0.0, 0.5)
		part_info_table.attach(info_partition_mountpoint, 0, 1, 4, 5)
		self.part_mount_point_entry = gtk.Entry()
		part_info_table.attach(self.part_mount_point_entry, 1, 2, 4, 5)

		info_partition_mountopts = gtk.Label(_("Mount options:"))
		info_partition_mountopts.set_alignment(0.0, 0.5)
		part_info_table.attach(info_partition_mountopts, 0, 1, 5, 6)
		self.part_mount_opts_entry = gtk.Entry()
		part_info_table.attach(self.part_mount_opts_entry, 1, 2, 5, 6)

		self.part_info_box.pack_start(part_info_table, expand=False, fill=False, padding=0)
		self.globalbox.pack_start(self.part_info_box, expand=False, fill=False, padding=10)

		bottom_box = gtk.HBox(True, 0)
		ok_button = gtk.Button(_(" OK "))
		ok_button.set_flags(gtk.CAN_DEFAULT)
		ok_button.set_size_request(60, -1)
		ok_button.connect("clicked", self.ok_clicked)
		bottom_box.pack_start(ok_button, expand=False, fill=False, padding=0)
		cancel_button = gtk.Button(_(" Cancel "))
		cancel_button.set_size_request(60, -1)
		cancel_button.connect("clicked", self.cancel_clicked)
		bottom_box.pack_start(cancel_button, expand=False, fill=False, padding=0)
		self.globalbox.pack_end(bottom_box, expand=False, fill=False, padding=0)

		self.add(self.globalbox)
		ok_button.grab_default()
		self.set_modal(True)
		self.set_transient_for(self.controller.controller.window)
		self.make_visible()

	def run(self):
		hpaned_width = self.resize_hpaned.get_allocation().width - self.resize_hpaned.style_get_property("handle-size")
		if self.fstype == "free":
			hpaned_pos = hpaned_width
			self.resize_hpaned.set_position(hpaned_pos)
#			print "min_size = %s, max_size = %s, hpaned_width = %s, hpaned_pos = %s" % (str(self.min_size), str(self.max_size), str(hpaned_width), str(hpaned_pos))
			self.info_partition.set_text(self.device + _(" (unallocated)"))
			self.resize_part_space.set_division(0)
			self.resize_part_space.set_colors(self.controller.colors['ext3'], self.controller.colors['ext3'])
			if self.controller.devices[self.device].get_extended_partition():
				if self.controller.devices[self.device].get_partition(self.minor).is_logical():
					self.resize_info_part_type.set_active(1)
				else:
					self.resize_info_part_type.set_active(0)
				self.resize_info_part_type.set_sensitive(False)
			else:
				self.resize_info_part_type.set_active(0)
				self.resize_info_part_type.set_sensitive(True)
			self.resize_info_part_filesystem.set_active(0)
			self.resize_info_part_filesystem.set_sensitive(True)
		else:
			tmppart = self.controller.devices[self.device].get_partition(self.minor)
			self.info_partition.set_text(tmppart['devnode'])
			if self.minor < 5:
				self.resize_info_part_type.set_active(0)
			else:
				self.resize_info_part_type.set_active(1)
			self.resize_info_part_type.set_sensitive(False)
			self.resize_info_part_filesystem.set_sensitive(False)
			for i, fs in enumerate(self.controller.supported_filesystems):
				if fs == self.fstype:
					self.resize_info_part_filesystem.set_active(i)
					break
			hpaned_pos = int(hpaned_width * (float(self.cur_size) / self.max_size))
			self.resize_hpaned.set_position(hpaned_pos)
#			print "min_size = %s, max_size = %s, hpaned_width = %s, hpaned_pos = %s" % (str(self.min_size), str(self.max_size), str(hpaned_width), str(hpaned_pos))
			if self.max_size == self.cur_size and self.min_size == self.cur_size:
				# Non-resizeable
				self.resize_part_space.set_division(0)
				self.resize_part_space.set_colors(self.controller.colors[self.fstype], self.controller.colors[self.fstype])
				self.resize_hpaned.set_sensitive(False)
			else:
				# Resizeable
				division = int(hpaned_pos * (float(self.min_size) / self.cur_size)) - 13
				self.resize_part_space.set_division(division)
				if self.min_size <= 1:
					self.resize_part_space.set_colors(self.controller.colors[self.fstype], self.controller.colors[self.fstype])
				else:
					self.resize_part_space.set_colors(self.controller.colors[self.fstype], self.controller.colors["free"])
				self.resize_hpaned.set_sensitive(True)
			self.part_mount_point_entry.set_text(tmppart.get_mountpoint())
			self.part_mount_opts_entry.set_text(tmppart.get_mountopts())

	def make_visible(self):
		self.show_all()
		self.present()

	def make_invisible(self):
		self.hide_all()

	def ok_clicked(self, button):
		if not int(self.resize_info_part_size.get_text()):
			msgdlg = gtk.MessageDialog(parent=self.controller.controller.window, type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK, message_format="You cannot define a 0MB partition.")
			resp = msgdlg.run()
			msgdlg.destroy()
			return
		if self.controller.supported_filesystems[self.resize_info_part_filesystem.get_active()] == "linux-swap":
			self.part_mount_point_entry.set_text("")
			self.part_mount_opts_entry.set_text("")
		else:
			if self.part_mount_point_entry.get_text() and not self.part_mount_opts_entry.get_text():
				# Mount point but no mount options
				self.part_mount_opts_entry.set_text("defaults")
		if self.fstype == "free":
			hpaned_width = self.resize_hpaned.get_allocation().width - self.resize_hpaned.style_get_property("handle-size")
			hpaned_pos = self.resize_hpaned.get_position()
			part_space = float(hpaned_width - (hpaned_width - hpaned_pos)) / hpaned_width
#			part_size = round(self.max_size * part_space)
			part_size = int(self.resize_info_part_size.get_text())
			if self.resize_info_part_type.get_active() == 1 and self.controller.devices[self.device].get_extended_partition() == 0: # Logical and no extended partition
				self.controller.devices[self.device].add_partition(self.minor, self.max_size, 0, 0, "extended")
				self.minor = 4 + FREE_MINOR_FRAC_LOG
			fstype = self.controller.supported_filesystems[self.resize_info_part_filesystem.get_active()]
			new_minor = self.controller.devices[self.device].add_partition(self.minor, part_size, 0, 0, fstype, mountpoint=self.part_mount_point_entry.get_text(), mountopts=self.part_mount_opts_entry.get_text())
			self.controller.draw_part_box()
			self.controller.part_selected(None, self.device, new_minor)
		else:
			tmppart = self.controller.devices[self.device].get_partition(self.minor)
			tmppart.set_mountpoint(self.part_mount_point_entry.get_text())
			tmppart.set_mountopts(self.part_mount_opts_entry.get_text())
			tmppart.set_format(self.resize_info_part_format_yes.get_active())
			new_size = int(self.resize_info_part_size.get_text())
			if new_size != self.cur_size:
				tmppart.resize(new_size)
			self.controller.draw_part_box()
			self.controller.part_selected(None, self.device, int(self.minor))

		self.destroy()

	def cancel_clicked(self, button):
		self.destroy()

	def part_resized(self, widget, allocation):
		if not self.sync_slider_to_text:
			self.sync_slider_to_text = True
			return
		hpaned_width = self.resize_hpaned.get_allocation().width - self.resize_hpaned.style_get_property("handle-size")
		hpaned_pos = self.resize_hpaned.get_position()
		part_space = float(hpaned_width - (hpaned_width - hpaned_pos)) / hpaned_width
		part_size_mb = int(round(part_space * self.max_size))
		self.resize_info_part_size.set_text(str(part_size_mb))
		part_unalloc_mb = int(self.max_size - part_size_mb)
		self.resize_info_unalloc_size.set_text(str(part_unalloc_mb))

	def validate_keypress(self, editable, new_text, new_text_length, position):
		if new_text == ".": return
		try:
			float(new_text)
		except:
			editable.stop_emission("insert-text")

	def update_slider_and_entries(self, widget, event, which_one):
		hpaned_width = self.resize_hpaned.get_allocation().width - self.resize_hpaned.style_get_property("handle-size")
		hpaned_pos = self.resize_hpaned.get_position()
		if which_one == "part-size":
			part_size_mb = int(round(long(self.resize_info_part_size.get_text())))
			if part_size_mb > self.max_size:
				part_size_mb = self.max_size
			elif part_size_mb < self.min_size:
				part_size_mb = self.min_size
			self.resize_info_part_size.set_text(str(part_size_mb))
			part_unalloc_mb = int(self.max_size - part_size_mb)
			self.resize_info_unalloc_size.set_text(str(part_unalloc_mb))
			if part_size_mb >= self.min_size and part_size_mb <= self.max_size:
				hpaned_pos = round((float(part_size_mb) / self.max_size) * hpaned_width)
		else:
			part_unalloc_mb = int(round(long(self.resize_info_unalloc_size.get_text())))
			if part_unalloc_mb > (self.max_size - self.min_size):
				part_unalloc_mb = self.max_size = self.min_size
				self.resize_info_unalloc_size.set_text(str(part_unalloc_mb))
			part_size_mb = int(round(self.max_size - part_unalloc_mb))
			self.resize_info_part_size.set_text(str(part_size_mb))
			if (self.max_size - part_unalloc_mb) >= self.min_size:
				hpaned_pos = hpaned_width - round((float(part_unalloc_mb) / self.max_size) * hpaned_width)
		self.sync_slider_to_text = False
		if hpaned_pos <= hpaned_width:
			self.resize_hpaned.set_position(int(hpaned_pos))
		else:
			self.resize_hpaned.set_position(self.resize_hpaned.get_position())

	def filesystem_changed(self, widget, data=None):
		fs = self.controller.supported_filesystems[self.resize_info_part_filesystem.get_active()]
		self.resize_part_space.set_colors(self.controller.colors[fs], self.controller.colors[fs])
		if self.fstype == "free": self.resize_part_space.get_child().expose_event(None, None)
		if fs == "linux-swap":
			self.part_mount_point_entry.set_sensitive(False)
			self.part_mount_opts_entry.set_sensitive(False)
		else:
			self.part_mount_point_entry.set_sensitive(True)
			self.part_mount_opts_entry.set_sensitive(True)

	def delete_event(self, widget, event, data=None):
		return False

	def destroy_event(self, widget, data=None):
		return True
