# Copyright 1999-2005 Gentoo Foundation
# This source code is distributed under the terms of version 2 of the GNU
# General Public License as published by the Free Software Foundation, a copy
# of which can be found in the main directory of this project.

import gtk, gobject
import GLIScreen
import GLIUtility
import Widgets
import commands, string
import copy

class Panel(GLIScreen.GLIScreen):

	title = "Network Mounts"
	columns = []
	netmounts = []
	active_entry = -1
	mount_types = ["NFS"]
	_helptext = """
<b><u>Network Mounts</u></b>

Here, you can specify network shares to mount during (and after) the install.
They will be mounted along with the local partitions you specified on the
previous screen when the install starts. This is useful for using a NFS mounted
/usr/portage.

To start, click the button labeled 'New'. Then, select a mount type. Currently,
the only supported type is NFS. If you get this choice wrong, you shall be
shunned. Next, enter a hostname or IP address. Then, you can either enter the
name of the share/export or click the button next to the field to have it
auto-populated with the available shares on the host you entered in the box
above. Enter a local mountpoint and mount options. Click the button labeled
'Update' to save the new network mount.

To edit an existing mount, select it in the list above. Edit any fields below
and then click the 'Update' button. You can remove it from the list by clicking
the 'Delete' button.
"""

	def __init__(self, controller):
		GLIScreen.GLIScreen.__init__(self, controller)
		vert = gtk.VBox(False, 0)
		vert.set_border_width(10)

		content_str = """Here, you will be able to define any network mounts that you want to use during
and after the installation. For example, you can mount /usr/portage from another box
on your network so you don't have to 'emerge sync' and store the tree locally. Currently, 
only NFS is supported.
		"""

		content_label = gtk.Label(content_str)
		vert.pack_start(content_label, expand=False, fill=False, padding=0)

		self.treedata = gtk.ListStore(gobject.TYPE_INT, gobject.TYPE_STRING, gobject.TYPE_STRING, gobject.TYPE_STRING, gobject.TYPE_STRING, gobject.TYPE_STRING)
		for i in range(0, len(self.netmounts)):
			self.treedata.append([i, self.netmounts[i]['host'], self.netmounts[i]['export'], self.netmounts[i]['type'], self.netmounts[i]['mountpoint'], self.netmounts[i]['mountopts']])
		self.treedatasort = gtk.TreeModelSort(self.treedata)
		self.treeview = gtk.TreeView(self.treedatasort)
		self.treeview.connect("cursor-changed", self.selection_changed)
		self.columns.append(gtk.TreeViewColumn("Host/IP", gtk.CellRendererText(), text=1))
		self.columns.append(gtk.TreeViewColumn("Export/Share", gtk.CellRendererText(), text=2))
		self.columns.append(gtk.TreeViewColumn("Type", gtk.CellRendererText(), text=3))
		self.columns.append(gtk.TreeViewColumn("Mount Point", gtk.CellRendererText(), text=4))
		self.columns.append(gtk.TreeViewColumn("Mount Options", gtk.CellRendererText(), text=5))
		col_num = 0
		for column in self.columns:
			column.set_resizable(True)
			column.set_sort_column_id(col_num)
			self.treeview.append_column(column)
			col_num += 1
		self.treewindow = gtk.ScrolledWindow()
		self.treewindow.set_size_request(-1, 130)
		self.treewindow.set_shadow_type(gtk.SHADOW_IN)
		self.treewindow.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
		self.treewindow.add(self.treeview)
		vert.pack_start(self.treewindow, expand=False, fill=False, padding=0)

		self.mount_info_box = gtk.HBox(False, 0)
		mount_info_table = gtk.Table(5, 3, False)
		mount_info_table.set_col_spacings(10)
		mount_info_table.set_row_spacings(6)
		mount_info_type_label = gtk.Label("Type:")
		mount_info_type_label.set_alignment(0.0, 0.5)
		mount_info_table.attach(mount_info_type_label, 0, 1, 0, 1)
		self.mount_info_type = gtk.combo_box_new_text()
		for mount_type in self.mount_types:
			self.mount_info_type.append_text(mount_type)
		self.mount_info_type.set_active(0)
		mount_info_table.attach(self.mount_info_type, 1, 2, 0, 1)
		mount_info_host_label = gtk.Label("Host/IP:")
		mount_info_host_label.set_alignment(0.0, 0.5)
		mount_info_table.attach(mount_info_host_label, 0, 1, 1, 2)
		self.mount_info_host = gtk.Entry()
		self.mount_info_host.set_width_chars(25)
		mount_info_table.attach(self.mount_info_host, 1, 2, 1, 2)
		mount_info_export_label = gtk.Label("Export/Share:")
		mount_info_export_label.set_alignment(0.0, 0.5)
		mount_info_table.attach(mount_info_export_label, 0, 1, 2, 3)
		self.mount_info_export = gtk.ComboBoxEntry(gtk.ListStore(gobject.TYPE_STRING))
		if not self.mount_info_export.get_text_column() == 0:
			self.mount_info_export.set_text_column(0)
		mount_info_table.attach(self.mount_info_export, 1, 2, 2, 3)
		self.mount_info_export_refresh = gtk.Button()
		mount_info_export_refresh_img = gtk.Image()
		mount_info_export_refresh_img.set_from_file(self.full_path + '/button_images/stock_refresh.png')
		self.mount_info_export_refresh.add(mount_info_export_refresh_img)
		self.mount_info_export_refresh.connect("clicked", self.populate_exports)
		mount_info_table.attach(self.mount_info_export_refresh, 2, 3, 2, 3)
		mount_info_mountpoint_label = gtk.Label("Mount point:")
		mount_info_mountpoint_label.set_alignment(0.0, 0.5)
		mount_info_table.attach(mount_info_mountpoint_label, 0, 1, 3, 4)
		self.mount_info_mountpoint = gtk.Entry()
		self.mount_info_mountpoint.set_width_chars(30)
		mount_info_table.attach(self.mount_info_mountpoint, 1, 2, 3, 4)
		mount_info_mountopts_label = gtk.Label("Mount options:")
		mount_info_mountopts_label.set_alignment(0.0, 0.5)
		mount_info_table.attach(mount_info_mountopts_label, 0, 1, 4, 5)
		self.mount_info_mountopts = gtk.Entry()
		self.mount_info_mountopts.set_width_chars(30)
		mount_info_table.attach(self.mount_info_mountopts, 1, 2, 4, 5)
		self.mount_info_box.pack_start(mount_info_table, expand=False, fill=False)
		vert.pack_start(self.mount_info_box, expand=False, fill=False, padding=10)

		mount_button_box = gtk.HBox(False, 0)
		mount_button_new = gtk.Button(" _New ")
		mount_button_new.connect("clicked", self.new_mount)
		mount_button_box.pack_start(mount_button_new, expand=False, fill=False, padding=10)
		self.mount_button_update = gtk.Button(" _Update ")
		self.mount_button_update.connect("clicked", self.update_mount)
		self.mount_button_update.set_sensitive(False)
		mount_button_box.pack_start(self.mount_button_update, expand=False, fill=False, padding=10)
		self.mount_button_delete = gtk.Button(" _Delete ")
		self.mount_button_delete.connect("clicked", self.delete_mount)
		self.mount_button_delete.set_sensitive(False)
		mount_button_box.pack_start(self.mount_button_delete, expand=False, fill=False, padding=10)
		self.mount_button_populate = gtk.Button(" _Populate Exports ")
		self.mount_button_populate.connect("clicked", self.populate_exports)
		self.mount_button_populate.set_sensitive(False)
		mount_button_box.pack_start(self.mount_button_populate, expand=False, fill=False, padding=10)
		vert.pack_start(mount_button_box, expand=False, fill=False, padding=10)

		self.add_content(vert)

	def disable_all_fields(self):
		self.mount_info_host.set_text("")
		self.mount_info_export.get_child().set_text("")
		self.mount_info_export.set_model(gtk.ListStore(gobject.TYPE_STRING))
		self.mount_info_mountpoint.set_text("")
		self.mount_info_mountopts.set_text("")
		self.mount_info_host.set_sensitive(False)
		self.mount_info_export.set_sensitive(False)
		self.mount_info_export_refresh.set_sensitive(False)
		self.mount_info_type.set_sensitive(False)
		self.mount_info_mountpoint.set_sensitive(False)
		self.mount_info_mountopts.set_sensitive(False)

	def enable_all_fields(self):
		self.mount_info_host.set_text("")
		self.mount_info_export.get_child().set_text("")
		self.mount_info_export.set_model(gtk.ListStore(gobject.TYPE_STRING))
		self.mount_info_mountpoint.set_text("")
		self.mount_info_mountopts.set_text("")
		self.mount_info_host.set_sensitive(True)
		self.mount_info_export.set_sensitive(True)
		self.mount_info_export_refresh.set_sensitive(True)
		self.mount_info_type.set_sensitive(True)
		self.mount_info_mountpoint.set_sensitive(True)
		self.mount_info_mountopts.set_sensitive(True)

	def refresh_list_at_top(self):
		self.treedata = gtk.ListStore(gobject.TYPE_INT, gobject.TYPE_STRING, gobject.TYPE_STRING, gobject.TYPE_STRING, gobject.TYPE_STRING, gobject.TYPE_STRING)
		for i in range(0, len(self.netmounts)):
			self.treedata.append([i, self.netmounts[i]['host'], self.netmounts[i]['export'], self.netmounts[i]['type'], self.netmounts[i]['mountpoint'], self.netmounts[i]['mountopts']])
		self.treedatasort = gtk.TreeModelSort(self.treedata)
		self.treeview.set_model(self.treedatasort)
		self.treeview.show_all()

	def selection_changed(self, treeview, data=None):
		treeselection = treeview.get_selection()
		treemodel, treeiter = treeselection.get_selected()
		row = treemodel.get(treeiter, 0)
		self.active_entry = row[0]
		mount = self.netmounts[self.active_entry]
		self.enable_all_fields()
		self.mount_info_host.set_text(mount['host'])
		self.mount_info_export.set_model(gtk.ListStore(gobject.TYPE_STRING))
		self.mount_info_export.get_child().set_text(mount['export'])
		i = 0
		for mounttype in self.mount_types:
			if mounttype == mount['type']:
				self.mount_info_type.set_active(i)
			else:
				i = i + 1
		self.mount_info_mountpoint.set_text(mount['mountpoint'])
		self.mount_info_mountopts.set_text(mount['mountopts'])
		self.mount_button_update.set_sensitive(True)
		self.mount_button_delete.set_sensitive(True)
		self.mount_button_populate.set_sensitive(True)

	def new_mount(self, button, data=None):
		self.active_entry = -1
		self.mount_button_update.set_sensitive(True)
		self.mount_button_delete.set_sensitive(False)
		self.mount_button_populate.set_sensitive(True)
		self.enable_all_fields()
		self.mount_info_host.grab_focus()

	def update_mount(self, button, data=None):
		if not GLIUtility.is_ip(self.mount_info_host.get_text()) and not GLIUtility.is_hostname(self.mount_info_host.get_text()):
			msgdialog = Widgets.Widgets().error_Box("Invalid Host or IP", "You must specify a valid hostname or IP address")
			result = msgdialog.run()
			if result == gtk.RESPONSE_ACCEPT:
				msgdialog.destroy()
			return
		if self.mount_info_export.get_child().get_text() == "":
			msgdialog = Widgets.Widgets().error_Box("Invalid Entry", "You must enter a value for the export field")
			result = msgdialog.run()
			if result == gtk.RESPONSE_ACCEPT:
				msgdialog.destroy()
			return
		if self.mount_info_mountpoint.get_text() == "":
			msgdialog = Widgets.Widgets().error_Box("Invalid Entry", "You must enter a mountpoint")
			result = msgdialog.run()
			if result == gtk.RESPONSE_ACCEPT:
				msgdialog.destroy()
			return
		if self.active_entry == -1:
			self.netmounts.append({ 'host': self.mount_info_host.get_text(), 'export': self.mount_info_export.get_child().get_text(), 'type': self.mount_types[self.mount_info_type.get_active()], 'mountpoint': self.mount_info_mountpoint.get_text(), 'mountopts': self.mount_info_mountopts.get_text() })
			self.active_entry = -1
			self.mount_button_update.set_sensitive(False)
			self.mount_button_delete.set_sensitive(False)
			self.mount_button_populate.set_sensitive(False)
		else:
			self.netmounts[self.active_entry]['host'] = self.mount_info_host.get_text()
			self.netmounts[self.active_entry]['export'] = self.mount_info_export.get_child().get_text()
			self.netmounts[self.active_entry]['type'] = self.mount_info_type.get_text()
			self.netmounts[self.active_entry]['mountpoint'] = self.mount_info_mountpoint.get_text()
			self.netmounts[self.active_entry]['mountopts'] = self.mount_info_mountopts.get_text()
		self.refresh_list_at_top()
		self.disable_all_fields()

	def delete_mount(self, button, data=None):
		self.netmounts.pop(self.active_entry)
		self.active_entry = -1
		self.mount_button_update.set_sensitive(False)
		self.mount_button_delete.set_sensitive(False)
		self.mount_button_populate.set_sensitive(False)
		self.refresh_list_at_top()
		self.disable_all_fields()

	def populate_exports(self, button, data=None):
		host = self.mount_info_host.get_text()
		oldtext = self.mount_info_export.get_child().get_text()
		if GLIUtility.is_ip(host) or GLIUtility.is_hostname(host):
			remotemounts = commands.getoutput("/usr/sbin/showmount -e " + host + " 2>&1 | egrep '^/' | cut -d ' ' -f 1 && echo")
			mountlist = gtk.ListStore(gobject.TYPE_STRING)
			self.mount_info_export.set_model(mountlist)
			while remotemounts.find("\n") != -1:
				index = remotemounts.find("\n") + 1
				remotemount = remotemounts[:index]
				remotemounts = remotemounts[index:]
				remotemount = string.strip(remotemount)
				mountlist.append([remotemount])
			self.mount_info_export.get_child().set_text(oldtext)
		else:
			msgdialog = Widgets.Widgets().error_Box("Invalid Host or IP", "You must specify a valid hostname or IP address to scan for exports")
			result = msgdialog.run()
			if result == gtk.RESPONSE_ACCEPT:
				msgdialog.destroy()

	def activate(self):
		self.controller.SHOW_BUTTON_EXIT    = True
		self.controller.SHOW_BUTTON_HELP    = True
		self.controller.SHOW_BUTTON_BACK    = True
		self.controller.SHOW_BUTTON_FORWARD = True
		self.controller.SHOW_BUTTON_FINISH  = False
		self.netmounts = copy.deepcopy(self.controller.install_profile.get_network_mounts())
		self.refresh_list_at_top()
		self.disable_all_fields()
		self.mount_button_update.set_sensitive(False)
		self.mount_button_delete.set_sensitive(False)
		self.mount_button_populate.set_sensitive(False)

	def deactivate(self):
		self.controller.install_profile.set_network_mounts(self.netmounts)
		return True
