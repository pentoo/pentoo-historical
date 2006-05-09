#!/usr/bin/python

# Copyright 1999-2005 Gentoo Foundation
# This source code is distributed under the terms of version 2 of the GNU
# General Public License as published by the Free Software Foundation, a copy
# of which can be found in the main directory of this project.

import gtk, pango

class Partition(gtk.Button):
	def __init__(self, *params_tuple, **params):
		if not "color1" in params: params["color1"] = "green"
		if not "color2" in params: params["color2"] = "gray"
		if not "division" in params: params["division"] = 30
		if not "label" in params: params["label"] = "label not set"
		color1, color2 = (params.pop("color1"), params.pop("color2"))
		division = params.pop("division")
		label = params.pop("label") # we use the same name for our param
		params["label"] = None
		super(Partition, self).__init__(*params_tuple, **params)
		self.relief = gtk.RELIEF_NONE
		self.add(Partition.DrawingArea(color1 = color1, color2 = color2, label = label, division = division))
	def set_division(self, width): self.get_child().set_division(width)
	def set_colors(self, color1, color2): self.get_child().set_colors(color1, color2)
	def set_label(self, label): self.get_child().set_label(label)

	class DrawingArea(gtk.DrawingArea):
		height = 24
		def __init__(self, **params):
			if not "color1" in params: params["color1"] = "green"
			if not "color2" in params: params["color2"] = "gray"
			if not "division" in params: params["division"] = 30
			if not "label" in params: params["label"] = "label not set"
			color1, color2 = (params.pop("color1"), params.pop("color2"))
			label = params.pop("label")
			division = params.pop("division")
			super(Partition.DrawingArea, self).__init__(**params)
			self.layout = self.create_pango_layout("")
			self.layout.set_alignment(pango.ALIGN_CENTER)
			self.set_colors(color1, color2)
			self.set_division(division)
			self.set_label(label)
			self.gc = None
			self.connect("expose-event", self.expose_event)
			self.connect("style-set", self.context_changed)
			self.connect("direction-changed", self.context_changed)
			self.connect("size-allocate", self.size_allocate)
		def set_colors(self, color1, color2):
			self._color1 = color1
			if isinstance(self._color1, gtk.gdk.Color): pass
			elif isinstance(self._color1, (str, unicode)): self._color1 = gtk.gdk.color_parse(self._color1)
			elif isinstance(self._color1, (tuple, list)): self._color1 = gtk.gdk.Color(*tuple(self._color1))
			elif isinstance(self._color1, dict): self._color1 = gtk.gdk.Color(**self._color1)
			self._color2 = color2
			if isinstance(self._color2, gtk.gdk.Color): pass
			elif isinstance(self._color2, (str, unicode)): self._color2 = gtk.gdk.color_parse(self._color2)
			elif isinstance(self._color2, (tuple, list)): self._color2 = gtk.gdk.Color(*tuple(self._color2))
			elif isinstance(self._color2, dict): self._color2 = gtk.gdk.Color(**self._color2)
		def set_division(self, width):
			self._division = width
			self.set_size_request(self._division, self.layout.get_pixel_size()[1])
		def set_label(self, label):
			self.layout.set_text(str(label))
			self.set_size_request(self._division, self.layout.get_pixel_size()[1])
		def size_allocate(self, widget, allocation): self._width, self._height = (allocation.width, allocation.height)
		def expose_event(self, area, event):
			if self.gc is None: self.gc = self.get_style().fg_gc[gtk.STATE_NORMAL]
#			old_fg_color = self.gc.foreground
			old_fg_color = gtk.gdk.color_parse("black")
			self.gc.set_rgb_fg_color(self._color1)
			self.window.draw_rectangle(gc = self.gc, filled = True, x = 0, y = 0, width = self._division, height = self._height)
			self.gc.set_rgb_fg_color(self._color2)
			self.window.draw_rectangle(gc = self.gc, filled = True, x = self._division, y = 0, width = self._width - self._division, height = self._height)
			w, h = self.layout.get_pixel_size()
			self.window.draw_layout(gc = self.gc, x = (self._width - w) / 2, y = (self._height - h) / 2, foreground = gtk.gdk.color_parse("black"), layout = self.layout)
			self.gc.set_rgb_fg_color(old_fg_color)
		def context_changed(self, *ignored1, **ignored2): self.layout.context_changed()

if __name__ == "__main__":
	window = gtk.Window()
	window.add(Partition(label = 4))
	window.connect("delete-event", lambda *ignored: gtk.main_quit())
	window.show_all()
	gtk.mainloop()
