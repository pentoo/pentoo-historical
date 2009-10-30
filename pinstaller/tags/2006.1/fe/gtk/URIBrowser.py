# Copyright 1999-2005 Gentoo Foundation
# This source code is distributed under the terms of version 2 of the GNU
# General Public License as published by the Free Software Foundation, a copy
# of which can be found in the main directory of this project.

import gtk, gobject
import GLIUtility
from gettext import gettext as _

class URIBrowser(gtk.Window):

	uritypes = ("file", "http", "ftp", "scp")

	def __init__(self, controller, entry):
		gtk.Window.__init__(self, gtk.WINDOW_TOPLEVEL)

		self.controller = controller
		self.entry = entry
		self.uri = None
		self.old_uri = None
		self.uriparts = None
		self.mirrors = None

		self.set_title(_("URI Browser"))
		self.connect("delete_event", self.delete_event)
		self.connect("destroy", self.destroy_event)

		self.globalbox = gtk.VBox(False, 0)
		self.globalbox.set_border_width(10)

		self.table = gtk.Table(5, 3, False)
		self.table.set_col_spacings(5)
		self.table.set_row_spacings(3)

		tmplabel = gtk.Label("URI type:")
		tmplabel.set_alignment(0.0, 0.5)
		self.table.attach(tmplabel, 0, 1, 0, 1)
		self.uritype = gtk.combo_box_new_text()
		self.uritype.connect("changed", self.uritype_changed)
		for tmpuritype in self.uritypes:
			self.uritype.append_text(tmpuritype)
		self.table.attach(self.uritype, 1, 3, 0, 1)

		tmplabel = gtk.Label("Host:")
		tmplabel.set_alignment(0.0, 0.5)
		self.table.attach(tmplabel, 0, 1, 1, 2)
		self.host_entry = gtk.Entry()
		self.table.attach(self.host_entry, 1, 2, 1, 2)
		self.host_browse = gtk.Button(" ... ")
		self.host_browse.connect("clicked", self.host_browse_clicked)
		self.table.attach(self.host_browse, 2, 3, 1, 2)

		tmplabel = gtk.Label("Username:")
		tmplabel.set_alignment(0.0, 0.5)
		self.table.attach(tmplabel, 0, 1, 2, 3)
		self.username_entry = gtk.Entry()
		self.table.attach(self.username_entry, 1, 3, 2, 3)

		tmplabel = gtk.Label("Password:")
		tmplabel.set_alignment(0.0, 0.5)
		self.table.attach(tmplabel, 0, 1, 3, 4)
		self.password_entry = gtk.Entry()
		self.table.attach(self.password_entry, 1, 3, 3, 4)

		tmplabel = gtk.Label("Port:")
		tmplabel.set_alignment(0.0, 0.5)
		self.table.attach(tmplabel, 0, 1, 4, 5)
		self.port_entry = gtk.Entry()
		self.table.attach(self.port_entry, 1, 3, 4, 5)

		tmplabel = gtk.Label("Path:")
		tmplabel.set_alignment(0.0, 0.5)
		self.table.attach(tmplabel, 0, 1, 5, 6)
		self.path_entry = gtk.Entry()
		self.table.attach(self.path_entry, 1, 3, 5, 6)

		self.treedata = gtk.TreeStore(gobject.TYPE_STRING, gobject.TYPE_STRING)
		self.treeview = gtk.TreeView(self.treedata)
		self.treeview.connect("row-activated", self.row_activated)
		column = gtk.TreeViewColumn()
		cell_renderer = gtk.CellRendererPixbuf()
		column.pack_start(cell_renderer, False)
		column.set_attributes(cell_renderer, stock_id=0)
		cell_renderer = gtk.CellRendererText()
		column.pack_start(cell_renderer, True)
		column.set_attributes(cell_renderer, text=1)
		self.treeview.append_column(column)
		self.treeview.set_headers_visible(False)
		self.treewindow = gtk.ScrolledWindow()
		self.treewindow.set_size_request(-1, 130)
		self.treewindow.set_shadow_type(gtk.SHADOW_IN)
		self.treewindow.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
		self.treewindow.add(self.treeview)
		self.treewindow.set_size_request(300, 200)
		self.table.attach(self.treewindow, 0, 3, 6, 7)

		hbox = gtk.HBox(True)
		self.ok_button = gtk.Button("OK")
		self.ok_button.connect("clicked", self.ok_clicked)
		hbox.pack_start(self.ok_button, expand=False, fill=True, padding=10)
		self.cancel_button = gtk.Button("Cancel")
		self.cancel_button.connect("clicked", self.cancel_clicked)
		hbox.pack_start(self.cancel_button, expand=False, fill=True, padding=10)
		self.refresh_button = gtk.Button("Refresh")
		self.refresh_button.connect("clicked", self.refresh_clicked)
		hbox.pack_start(self.refresh_button, expand=False, fill=True, padding=10)
		self.table.attach(hbox, 0, 3, 7, 8)

		self.globalbox.pack_start(self.table, expand=False, fill=False)
		self.add(self.globalbox)
		self.set_modal(True)
		self.set_transient_for(self.controller.controller.window)
		self.uritype.set_active(0)

	def update_from_uri(self):
		if self.uri:
			self.uriparts = GLIUtility.parse_uri(self.uri)
			if not self.uriparts:
				msgdlg = gtk.MessageDialog(parent=self, type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK, message_format=_("The URI you had previously entered was malformed and couldn't be parsed."))
				msgdlg.run()
				msgdlg.destroy()
				self.uri = "file:///"
				self.uriparts = GLIUtility.parse_uri(self.uri)
			else:
				for i, tmpuritype in enumerate(self.uritypes):
					if self.uriparts[0] == tmpuritype:
						self.uritype.set_active(i)
				if self.uriparts[3]: self.host_entry.set_text(self.uriparts[3])
				if self.uriparts[1]: self.username_entry.set_text(self.uriparts[1])
				if self.uriparts[2]: self.password_entry.set_text(self.uriparts[2])
				if self.uriparts[4]: self.port_entry.set_text(self.uriparts[4])
		else:
			self.uri = "file:///"
			self.uriparts = GLIUtility.parse_uri(self.uri)
		self.refresh_file_list()

	def run(self, uri=None):
		self.uri = uri
		self.update_from_uri()
		self.make_visible()

	def make_visible(self):
		self.show_all()
		self.present()

	def make_invisible(self):
		self.hide_all()

	def refresh_file_list(self):
		if not self.uri.endswith("/"):
			self.uri = self.uri[:self.uri.rfind("/")+1]
		try:
			filelist = GLIUtility.get_directory_listing_from_uri(self.uri)
		except GLIException, e:
			if e.get_error_name() == "IncorrectPassword":
				msgdlg = gtk.MessageDialog(parent=self, type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK, message_format=_("Your password is incorrect."))
				msgdlg.run()
				msgdlg.destroy()
			return
		if not filelist:
			msgdlg = gtk.MessageDialog(parent=self, type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK, message_format=_("The information you entered is invalid."))
			msgdlg.run()
			msgdlg.destroy()
			self.uri = self.old_uri
			filelist = GLIUtility.get_directory_listing_from_uri(self.uri)
		self.uriparts = GLIUtility.parse_uri(self.uri)
		self.treedata.clear()
		for file in filelist:
#			print "adding " + file + " to self.treedata"
			if file.endswith('/'):
				self.treedata.append(None, ("gtk-directory", file[:-1]))
			else:
				self.treedata.append(None, ("", file))
		self.treewindow.get_vadjustment().set_value(0)
		self.path_entry.set_text(self.uriparts[5])

	def row_activated(self, treeview, path, view_column):
		treeselection = treeview.get_selection()
		treemodel, treeiter = treeselection.get_selected()
		row = treemodel.get(treeiter, 0, 1)
#		print str(row)
		stock_icon, name = row[0], row[1]
		self.old_uri = self.uri
		if stock_icon == "gtk-directory":
			if name == "..":
				self.uri = self.uri[:self.uri[:-1].rfind("/")+1]
			else:
				self.uri += name + "/"
		else:
			self.entry.set_text(self.uri + name)
			self.destroy()
#		print "New URI is '%s'" % self.uri
		self.refresh_file_list()

	def uritype_changed(self, combobox):
		if self.uritype.get_active() == 0:
			self.host_entry.set_sensitive(False)
			self.host_browse.set_sensitive(False)
			self.port_entry.set_sensitive(False)
			self.username_entry.set_sensitive(False)
			self.password_entry.set_sensitive(False)
		else:
			self.host_entry.set_sensitive(True)
			self.host_browse.set_sensitive(True)
			self.port_entry.set_sensitive(True)
			self.username_entry.set_sensitive(True)
			self.password_entry.set_sensitive(True)

	def refresh_clicked(self, button):
		if self.uritype.get_active() == 0:
			self.uri = "file://"
		else:
			self.host_entry.set_sensitive(True)
			self.port_entry.set_sensitive(True)
			self.username_entry.set_sensitive(True)
			self.password_entry.set_sensitive(True)
			self.uri = self.uritypes[self.uritype.get_active()] + "://"
			if self.username_entry.get_text():
				self.uri += self.username_entry.get_text()
				if self.password_entry.get_text():
					self.uri += ":" + self.password_entry.get_text()
				self.uri += "@"
			self.uri += self.host_entry.get_text()
			if self.port_entry.get_text():
				self.uri += ":" + self.port_entry.get_text()
		self.uri += (self.path_entry.get_text() or "/")
		self.uriparts = GLIUtility.parse_uri(self.uri)
		self.refresh_file_list()

	def host_browse_clicked(self, button):
		hostdlg = gtk.Dialog("Browse mirror list", self, gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT, (gtk.STOCK_OK, gtk.RESPONSE_ACCEPT, gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT))
		hbox = gtk.HBox(False)
		hbox.set_border_width(10)
		hbox.pack_start(gtk.Label("Mirror:"), expand=False, fill=False, padding=0)
		host_combo = gtk.combo_box_new_text()
		if self.uritypes[self.uritype.get_active()] == "http":
			mirrors = GLIUtility.list_mirrors(http=True, ftp=False, rsync=False)
		elif self.uritypes[self.uritype.get_active()] == "ftp":
			mirrors = GLIUtility.list_mirrors(http=False, ftp=True, rsync=False)
		else:
			msgdlg = gtk.MessageDialog(parent=self, type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK, message_format=_("There are no known mirrors for this URI type."))
			msgdlg.run()
			msgdlg.destroy()
			return
		for mirror in mirrors:
			host_combo.append_text(mirror[1])
			host_combo.set_active(0)
		hbox.pack_start(host_combo, expand=False, fill=True, padding=15)
		hbox.show_all()
		hostdlg.vbox.pack_start(hbox)
		resp = hostdlg.run()
		if resp == gtk.RESPONSE_ACCEPT:
			mirror = mirrors[host_combo.get_active()][0]
			if not mirror.endswith("/"):
				mirror += "/"
			self.uri = mirror
			self.update_from_uri()
		hostdlg.destroy()

	def ok_clicked(self, button):
		treeselection = self.treeview.get_selection()
		treemodel, treeiter = treeselection.get_selected()
		row = treemodel.get(treeiter, 0, 1)
		stock_icon, name = row[0], row[1]
		self.old_uri = self.uri
		if stock_icon == "gtk-directory":
			if name == "..":
				self.uri = self.uri[:self.uri[:-1].rfind("/")+1]
			else:
				self.uri += name + "/"
		else:
			self.entry.set_text(self.uri + name)
			self.destroy()

	def cancel_clicked(self, button):
		self.destroy()

	def delete_event(self, widget, event, data=None):
		return False

	def destroy_event(self, widget, data=None):
		return True
