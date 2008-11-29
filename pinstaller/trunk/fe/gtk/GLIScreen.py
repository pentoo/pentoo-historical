# Copyright 1999-2005 Gentoo Foundation
# This source code is distributed under the terms of version 2 of the GNU
# General Public License as published by the Free Software Foundation, a copy
# of which can be found in the main directory of this project.

import gtk
import os.path

class GLIScreen(gtk.VBox):

	full_path = ""

	def __init__(self, controller, show_title=True):
		self.controller = controller
		self.full_path = os.path.abspath(os.path.dirname(__file__))

		gtk.VBox.__init__(self, False, 0)

#		if show_title:
#			right_title_label = gtk.Label()
#			right_title_label.set_markup('<span><b>'+self.title+'</b></span>')
#			right_title_label.set_use_markup(True)
#			self.pack_start(right_title_label, expand=False, fill=False, padding=10)

	def add_content(self, content):
		self.pack_end(content, True, True, 0)

	def activate(self):
		print "Bad boy! You should really impliment this function in your subclass."

	def deactivate(self):
		return True
