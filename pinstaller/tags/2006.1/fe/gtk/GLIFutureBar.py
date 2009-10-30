# $Id: GLIFutureBar.py,v 1.2 2005/11/06 16:41:08 agaffney Exp $
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#

import gtk

class GLIFutureBar(gtk.HBox):

	def __init__(self, titles):
		"""
		future bar
		"""
		gtk.HBox.__init__(
			self,
			False,
			0
		)
		self.set_border_width(2)

		# Widths
		self.arrow_width = 20
		self.text_width = 144

		# state
		self.pos = 0
		self.titles = titles
#		self.titles = [
#			"Welcome",
#			"Client Config",
#			"Partitioning",
#			"Network Mounts",
#			"Stage",
#			"Portage Tree",
#			"make.conf",
#			"Kernel",
#			"Bootloader",
#			"Timezone",
#			"Networking",
#			"Daemons",
#			"Extra Packages",
#			"rc.conf",
#			"Users",
#			"Review",
#		]

		# markup
		self.l2_color = "#ABA9A5"
		self.l2_size = "-2"
		self.l1_color = "#787674"
		self.l1_size = "-1"
		self.cur_color = "#000000"
		self.cur_size = "-0"
		self.arrowl = unichr(8672)
		self.arrowr = unichr(8674)

		# l2 (level 2 on the left)
		self.l2 = gtk.HBox(False, 0)
		self.l2.label = gtk.Label()
		self.l2.label.set_use_markup(True)
		self.l2.label.set_size_request(self.text_width, -1)
		self.l2.pack_start(self.l2.label, True, True, 0)
		self.l2.arrow = gtk.Label()
		self.l2.arrow.set_use_markup(True)
		self.l2.arrow.set_size_request(self.arrow_width, -1)
		self.l2.pack_start(self.l2.arrow, False, False, 0)
		self.pack_start(self.l2, True, True, 0)

		# l1 (level 1 on the left)
		self.l1 = gtk.HBox(False, 0)
		self.l1.label = gtk.Label()
		self.l1.label.set_use_markup(True)
		self.l1.label.set_size_request(self.text_width, -1)
		self.l1.pack_start(self.l1.label, True, True, 0)
		self.l1.arrow = gtk.Label()
		self.l1.arrow.set_use_markup(True)
		self.l1.arrow.set_size_request(self.arrow_width, -1)
		self.l1.pack_start(self.l1.arrow, False, False, 0)
		self.pack_start(self.l1, True, True, 0)

		# cur (current in the middle)
		self.cur = gtk.Label()
		self.cur.set_use_markup(True)
		self.cur.set_size_request(self.text_width, -1)
		self.pack_start(self.cur, True, True, 0)

		# r1 (level 1 on the right)
		self.r1 = gtk.HBox(False, 0)
		self.r1.arrow = gtk.Label()
		self.r1.arrow.set_use_markup(True)
		self.r1.arrow.set_size_request(self.arrow_width, -1)
		self.r1.pack_start(self.r1.arrow, False, False, 0)
		self.r1.label = gtk.Label()
		self.r1.label.set_use_markup(True)
		self.r1.label.set_size_request(self.text_width, -1)
		self.r1.pack_start(self.r1.label, True, True, 0)
		self.pack_start(self.r1, True, True, 0)

		# r2 (level 2 on the right)
		self.r2 = gtk.HBox(False, 0)
		self.r2.arrow = gtk.Label()
		self.r2.arrow.set_use_markup(True)
		self.r2.arrow.set_size_request(self.arrow_width, -1)
		self.r2.pack_start(self.r2.arrow, False, False, 0)
		self.r2.label = gtk.Label()
		self.r2.label.set_use_markup(True)
		self.r2.label.set_size_request(self.text_width, -1)
		self.r2.pack_start(self.r2.label, True, True, 0)
		self.pack_start(self.r2, True, True, 0)

		# init positions
		self.setpos(0)

	def getpos(self):
		return self.pos

	def setpos(self, pos):
		if pos >= 0 and pos < len(self.titles):
			# set position variable
			self.pos = pos
	
			# create a reference label
			label = gtk.Label("Hello")
	
			if (self.pos - 2) >= 0:
				self.l2.label.set_markup("<span size=\"" + str(((label.get_pango_context().get_font_description().get_size() / 1024) + int(self.l2_size)) * 1024) + "\" weight=\"bold\" foreground=\"" + self.l2_color + "\">" + self.titles[self.pos - 2] + "</span>")
				self.l2.arrow.set_markup("<span size=\"" + str(((label.get_pango_context().get_font_description().get_size() / 1024) + int(self.l2_size) + 7) * 1024) + "\" weight=\"bold\" foreground=\"" + self.l2_color + "\">" + self.arrowl + "</span>")
			else:
				self.l2.label.set_markup("")
				self.l2.arrow.set_markup("")
	
			if (self.pos - 1) >= 0:
				self.l1.label.set_markup("<span size=\"" + str(((label.get_pango_context().get_font_description().get_size() / 1024) + int(self.l1_size)) * 1024) + "\" weight=\"bold\" foreground=\"" + self.l1_color + "\">" + self.titles[self.pos - 1] + "</span>")
				self.l1.arrow.set_markup("<span size=\"" + str(((label.get_pango_context().get_font_description().get_size() / 1024) + int(self.l1_size) + 7) * 1024) + "\" weight=\"bold\" foreground=\"" + self.l1_color + "\">" + self.arrowl + "</span>")
			else:
				self.l1.label.set_markup("")
				self.l1.arrow.set_markup("")
	
			self.cur.set_markup("<span size=\"" + str(((label.get_pango_context().get_font_description().get_size() / 1024) + int(self.cur_size)) * 1024) + "\" weight=\"bold\" foreground=\"" + self.cur_color + "\">" + self.titles[self.pos] + "</span>")
	
			if (self.pos + 1) < len(self.titles):
				self.r1.label.set_markup("<span size=\"" + str(((label.get_pango_context().get_font_description().get_size() / 1024) + int(self.l1_size)) * 1024) + "\" weight=\"bold\" foreground=\"" + self.l1_color + "\">" + self.titles[self.pos + 1] + "</span>")
				self.r1.arrow.set_markup("<span size=\"" + str(((label.get_pango_context().get_font_description().get_size() / 1024) + int(self.l1_size) + 7) * 1024) + "\" weight=\"bold\" foreground=\"" + self.l1_color + "\">" + self.arrowr + "</span>")
			else:
				self.r1.label.set_markup("")
				self.r1.arrow.set_markup("")
	
			if (self.pos + 2) < len(self.titles):
				self.r2.label.set_markup("<span size=\"" + str(((label.get_pango_context().get_font_description().get_size() / 1024) + int(self.l2_size)) * 1024) + "\" weight=\"bold\" foreground=\"" + self.l2_color + "\">" + self.titles[self.pos + 2] + "</span>")
				self.r2.arrow.set_markup("<span size=\"" + str(((label.get_pango_context().get_font_description().get_size() / 1024) + int(self.l2_size) + 7) * 1024) + "\" weight=\"bold\" foreground=\"" + self.l2_color + "\">" + self.arrowr + "</span>")
			else:
				self.r2.label.set_markup("")
				self.r2.arrow.set_markup("")

			self.show_all()

			return True
		else:
			return False

	def prev(self):
		return self.setpos(self.pos - 1)

	def next(self):
		return self.setpos(self.pos + 1)
