# Copyright 1999-2005 Gentoo Foundation
# This source code is distributed under the terms of version 2 of the GNU
# General Public License as published by the Free Software Foundation, a copy
# of which can be found in the main directory of this project.

import gtk
import gobject
import GLIScreen
from gettext import gettext as _

class Panel(GLIScreen.GLIScreen):

	title = _("Startup Services")
	_helptext = """
<b><u>Startup Services</u></b>

If you installed gnome, kde, or another graphical desktop, be sure to select xdm
if you want to startup into your graphical environment.  

sshd is also a recommended service already installed in the base system.
"""

	def __init__(self, controller):
		GLIScreen.GLIScreen.__init__(self, controller)
		vert = gtk.VBox(False, 0)
		vert.set_border_width(10)

		self.services = None
		self.choice_list = [("alsasound", _(u"Loads ALSA modules and restores mixer levels")),
		("apache", _(u"Common web server (version 1.x)")),
		("apache2", _(u"Common web server (version 2.x)")),
		("distccd", _(u"Allows your system to help other systems compile")),
		("hdparm", _(u"Makes it easy to set drive parameters automatically at boot")),
		("portmap", _(u"Necessary for mounting NFS shares")),
		("proftpd", _(u"Common FTP server")),
		("sshd", _(u"OpenSSH server (allows remote logins)")),
		("xfs", _(u"X Font Server (available if xorg-x11 compiled with USE=font-server)")),
		("xdm", _(u"Gives you a graphical login which then starts X"))]

		content = """
On this screen, you can select services that you would like to startup at boot.
Common choices are sshd (remote access) and xdm (graphical login...choose this
for kdm, gdm, and entrance, as well). Adding a service here does not
automatically emerge the corresponding package. You will need to add it on the
Extra Packages screen yourself.
"""
		content_label = gtk.Label(content)
		vert.pack_start(content_label, expand=False, fill=False, padding=0)

		self.treedata = gtk.ListStore(gobject.TYPE_BOOLEAN, gobject.TYPE_STRING, gobject.TYPE_STRING)
		self.treeview = gtk.TreeView(self.treedata)
		self.toggle_renderer = gtk.CellRendererToggle()
		self.toggle_renderer.set_property("activatable", True)
		self.toggle_renderer.connect("toggled", self.flag_toggled)
		self.columns = []
		self.columns.append(gtk.TreeViewColumn("", self.toggle_renderer, active=0))
		self.columns.append(gtk.TreeViewColumn("Service", gtk.CellRendererText(), text=1))
		self.columns.append(gtk.TreeViewColumn("Description", gtk.CellRendererText(), text=2))
		for column in self.columns:
#			column.set_resizable(True)
			self.treeview.append_column(column)
		self.treewindow = gtk.ScrolledWindow()
		self.treewindow.set_size_request(-1, 180)
		self.treewindow.set_shadow_type(gtk.SHADOW_IN)
		self.treewindow.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
		self.treewindow.add(self.treeview)
		vert.pack_start(self.treewindow, expand=False, fill=False, padding=10)

		self.add_content(vert)

	def flag_toggled(self, cell, path):
		model = self.treeview.get_model()
		model[path][0] = not model[path][0]
		service = model[path][1]
		if model[path][0]:
			if not service in self.services:
				self.services.append(service)
		else:
			if service in self.services:
				self.services.pop(self.services.index(service))

	def deactivate(self):
		self.controller.install_profile.set_services(None, ",".join(self.services), None)
		return True

	def activate(self):
		self.controller.SHOW_BUTTON_EXIT    = True
		self.controller.SHOW_BUTTON_HELP    = True
		self.controller.SHOW_BUTTON_BACK    = True
		self.controller.SHOW_BUTTON_FORWARD = True
		self.controller.SHOW_BUTTON_FINISH  = False

		self.services = self.controller.install_profile.get_services()
		if self.services:
			if isinstance(self.services, str):
				self.services = self.services.split(',')
			else:
				self.services = list(self.services)
		else:
			self.services = []
		self.treedata.clear()
		for choice in self.choice_list:
			self.treedata.append([(choice[0] in self.services), choice[0], choice[1]])

