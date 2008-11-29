# Copyright 1999-2005 Gentoo Foundation
# This source code is distributed under the terms of version 2 of the GNU
# General Public License as published by the Free Software Foundation, a copy
# of which can be found in the main directory of this project.

import gtk, pango
from gettext import gettext as _
import TextBufferMarkup

class HelpDialog(gtk.Window):

	def __init__(self, parent, helptext):
		gtk.Window.__init__(self, gtk.WINDOW_TOPLEVEL)

		self.connect("delete_event", self.delete_event)
		self.connect("destroy", self.destroy_event)
		self.set_default_size(500,400)
#		self.set_resizable(True)
		self.set_title("Gentoo Installer Help")

		self.globalbox = gtk.VBox(False, 0)

		self.textbuff = TextBufferMarkup.PangoBuffer()

		# Here is where we chop up the text a bit
#		helptext = " ".join(helptext.split("\n"))
#		helptext = "\n".join(helptext.split('<br>'))

		self.textbuff.set_text(helptext)
		self.textview = gtk.TextView(self.textbuff)
		self.textview.set_editable(False)
		self.textview.set_wrap_mode(gtk.WRAP_CHAR)
		self.textview.modify_base(gtk.STATE_NORMAL, gtk.gdk.color_parse('#f4ffa9'))
		self.textviewscroll = gtk.ScrolledWindow()
		self.textviewscroll.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
		self.textviewscroll.add(self.textview)
		self.globalbox.pack_start(self.textviewscroll, expand=True, fill=True)

		self.add(self.globalbox)
		self.set_modal(True)
#		self.set_transient_for(parent)

	def run(self):
		self.show_all()

	def delete_event(self, widget, event, data=None):
		return False

	def destroy_event(self, widget, data=None):
		return True

