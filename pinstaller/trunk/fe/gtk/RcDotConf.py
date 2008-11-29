# Copyright 1999-2005 Gentoo Foundation
# This source code is distributed under the terms of version 2 of the GNU
# General Public License as published by the Free Software Foundation, a copy
# of which can be found in the main directory of this project.

import gtk
import os
import GLIScreen
import GLIUtility
from Widgets import Widgets

class Panel(GLIScreen.GLIScreen):
	"""
	The make.conf section of the installer.
	
	@author:    John N. Laliberte <allanonl@bu.edu>
	@license:   GPL
	"""
	# Attributes:
	title="rc.conf Settings"
	
	# Operations
	def __init__(self, controller):
		GLIScreen.GLIScreen.__init__(self, controller)

		vert    = gtk.VBox(False, 10) # This box is content so it should fill space to force title to top
		horiz   = gtk.HBox(False, 10)

		content_str = """
This is where you setup rc.conf."""
		# pack the description
		vert.pack_start(gtk.Label(content_str), expand=False, fill=False, padding=10)
		
		# keymap
		hbox = gtk.HBox(False, 0)
		label = gtk.Label("KEYMAP:")
		label.set_size_request(150, -1)
		#label.set_justify(gtk.JUSTIFY_LEFT)
		hbox.pack_start(label, expand=False, fill=False, padding=25)
		self.keymap = gtk.combo_box_new_text()
		self.keymap.set_name("KEYMAP")
		self.keymap.set_size_request(150, -1)
		hbox.pack_start(self.keymap, expand=False, fill=False, padding=5)
		vert.pack_start(hbox,expand=False,fill=False,padding=0)
		
		# set_windowskeys
		hbox = gtk.HBox(False, 0)
		label = gtk.Label("SET_WINDOWKEYS:")
		label.set_size_request(150, -1)
		hbox.pack_start(label, expand=False, fill=False, padding=25)
		self.windowkeys = gtk.combo_box_new_text()
		self.windowkeys.set_name("SET_WINDOWKEYS")
		self.windowkeys.set_size_request(150, -1)
		hbox.pack_start(self.windowkeys, expand=False, fill=False, padding=5)
		vert.pack_start(hbox,expand=False,fill=False,padding=0)
		
		# extended_keymaps
		hbox = gtk.HBox(False, 0)
		label = gtk.Label("EXTENDED_KEYMAPS:")
		label.set_size_request(150, -1)
		hbox.pack_start(label, expand=False, fill=False, padding=25)
		self.extended_keymaps = gtk.Entry()
		self.extended_keymaps.set_name("EXTENDED_KEYMAPS")
		self.extended_keymaps.set_size_request(150, -1)
		hbox.pack_start(self.extended_keymaps, expand=False, fill=False, padding=5)
		vert.pack_start(hbox,expand=False,fill=False,padding=0)
		
		# consolefont
		hbox = gtk.HBox(False, 0)
		label = gtk.Label("CONSOLEFONT:")
		label.set_size_request(150, -1)
		hbox.pack_start(label, expand=False, fill=False, padding=25)
		self.consolefont = gtk.combo_box_new_text()
		self.consolefont.set_name("CONSOLEFONT")
		self.consolefont.set_size_request(150, -1)
		hbox.pack_start(self.consolefont, expand=False, fill=False, padding=5)
		vert.pack_start(hbox,expand=False,fill=False,padding=0)
		
		# consoletranslation
		hbox = gtk.HBox(False, 0)
		label = gtk.Label("CONSOLETRANSLATION:")
		label.set_size_request(150, -1)
		hbox.pack_start(label, expand=False, fill=False, padding=25)
		self.consoletranslation = gtk.combo_box_new_text()
		self.consoletranslation.set_name("CONSOLETRANSLATION")
		self.consoletranslation.set_size_request(150, -1)
		hbox.pack_start(self.consoletranslation, expand=False, fill=False, padding=5)
		vert.pack_start(hbox,expand=False,fill=False,padding=0)
		
		# clock
		hbox = gtk.HBox(False, 0)
		label = gtk.Label("CLOCK:")
		label.set_size_request(150, -1)
		hbox.pack_start(label, expand=False, fill=False, padding=25)
		self.clock = gtk.combo_box_new_text()
		self.clock.set_name("CLOCK")
		self.clock.set_size_request(150, -1)
		hbox.pack_start(self.clock, expand=False, fill=False, padding=5)
		vert.pack_start(hbox,expand=False,fill=False,padding=0)
		
		# editor
		hbox = gtk.HBox(False, 0)
		label = gtk.Label("EDITOR:")
		label.set_size_request(150, -1)
		hbox.pack_start(label, expand=False, fill=False, padding=25)
		self.editor = gtk.combo_box_entry_new_text()
		self.editor.set_name("EDITOR")
		self.editor.set_size_request(150, -1)
		hbox.pack_start(self.editor, expand=False, fill=False, padding=5)
		vert.pack_start(hbox,expand=False,fill=False,padding=0)
		
		# protocols
		hbox = gtk.HBox(False, 0)
		label = gtk.Label("PROTOCOLS:")
		label.set_size_request(150, -1)
		hbox.pack_start(label, expand=False, fill=False, padding=25)
		self.protocols = gtk.Entry()
		self.protocols.set_name("PROTOCOLS")
		self.protocols.set_size_request(150, -1)
		hbox.pack_start(self.protocols, expand=False, fill=False, padding=5)
		vert.pack_start(hbox,expand=False,fill=False,padding=0)
		
		# displaymanager
		hbox = gtk.HBox(False, 0)
		label = gtk.Label("DISPLAYMANAGER:")
		label.set_size_request(150, -1)
		hbox.pack_start(label, expand=False, fill=False, padding=25)
		self.displaymanager = gtk.combo_box_new_text()
		self.displaymanager.set_name("DISPLAYMANAGER")
		self.displaymanager.set_size_request(150, -1)
		hbox.pack_start(self.displaymanager, expand=False, fill=False, padding=5)
		vert.pack_start(hbox,expand=False,fill=False,padding=0)
		
		# xsession
		hbox = gtk.HBox(False, 0)
		label = gtk.Label("XSESSION:")
		label.set_size_request(150, -1)
		hbox.pack_start(label, expand=False, fill=False, padding=25)
		self.xsession = gtk.combo_box_entry_new_text()
		self.xsession.set_name("XSESSION")
		self.xsession.set_size_request(150, -1)
		hbox.pack_start(self.xsession, expand=False, fill=False, padding=5)
		vert.pack_start(hbox,expand=False,fill=False,padding=0)
		
		# populate the gui elements
		self.populate_keymap_combo()
		self.populate_windowkeys_combo()
		self.populate_consolefont_combo()
		self.populate_consoletranslation_combo()
		self.populate_clock_combo()
		self.populate_editor_combo()
		self.protocols.set_text("1 2")
		self.populate_displaymanager_combo()
		self.populate_xsession_combo()
		
		self.add_content(vert)
		
		# setup the types of gui elements for access later
		self.data = {self.keymap:"combo",
			     self.windowkeys:"combo",
			     self.extended_keymaps:"entry",
			     self.consolefont:"combo",
			     self.consoletranslation:"combo",
			     self.clock:"combo",
			     self.editor:"comboentry",
			     self.protocols:"entry",
			     self.displaymanager:"combo",
			     self.xsession:"comboentry"
			     }
		
	
	def populate_keymap_combo(self, default="us"):
		# Adds all the keymaps to the dropdown
		keymaps = GLIUtility.generate_keymap_list()
		
		for i in range(len(keymaps)):
			keymap = keymaps[i]
			self.keymap.append_text(keymap)
			
			# select the default
			if keymap == default:
				self.keymap.set_active(i)
	
	def populate_windowkeys_combo(self, default=1):
		self.windowkeys.append_text("No")
		self.windowkeys.append_text("Yes")
		self.windowkeys.set_active(default)
	
	def populate_consolefont_combo(self, default="default8x16"):
		# Adds all the consolefonts
		consolefonts = GLIUtility.generate_consolefont_list()
		for i in range(len(consolefonts)):
			consolefont = consolefonts[i]
			self.consolefont.append_text(consolefont)
			
			# select the default
			if consolefont == default:
				self.consolefont.set_active(i)
	
	def populate_consoletranslation_combo(self, default=0):
		self.consoletranslation.append_text("commented out")
		
		consoletranslations = GLIUtility.generate_consoletranslation_list()
		
		for i in range(len(consoletranslations)):
			consoletran = consoletranslations[i]
			self.consoletranslation.append_text(consoletran)
			
		self.consoletranslation.set_active(default)
				
	def populate_clock_combo(self, default=0):
		self.clock.append_text("UTC")
		self.clock.append_text("local")
		self.clock.set_active(default)
	
	def populate_editor_combo(self,default=0):
		self.editor.append_text("/bin/nano")
		self.editor.append_text("/usr/bin/vim")
		self.editor.append_text("/usr/bin/emacs")
		self.editor.set_active(default)
	
	def populate_displaymanager_combo(self,default=0):
		self.displaymanager.append_text("commented out")
		self.displaymanager.append_text("xdm")
		self.displaymanager.append_text("kdm")
		self.displaymanager.append_text("gdm")
		self.displaymanager.append_text("entrance")
		self.displaymanager.set_active(0)
	
	def populate_xsession_combo(self,default=-1):
		self.xsession.append_text("Gnome")
		self.xsession.append_text("fluxbox")
		self.xsession.append_text("Xsession")
		self.xsession.set_active(-1)
		
	def get_combo_current_text(self, widget):
		model = widget.get_model()
		active = widget.get_active()
		
		return model[active][0]
	
	def set_combo_current_text(self, widget , text):
		if text=="##commented##": text = "commented out"
		# need to find the element in the combo box
		# that they selected in the file, and activate it.
		#iter = widget.get_active_iter()
		model = widget.get_model()
		iter = model.get_iter_first()
		
		i=0 # keep track of what to set active.
		while iter != None:
			# retrieve the text and test.
			#print model.get_value(iter,0)
			# if the value in the combobox equals whats in the xmlfile,
			# select it!
			if model.get_value(iter,0) == text:
				widget.set_active(i)
				
			iter = model.iter_next(iter)
			i+=1
		
	def generate_rc_conf_dictionary(self):
		rc_conf = {}

		for item in self.data.keys():
			# depending on what kind of gui element it is,
			# we need to get the data out of it differently.
			# equivalent of a switch statement in python...
			result = {
				'combo': lambda item: self.get_combo_current_text(item),
				'entry': lambda item: item.get_text(),
				'comboentry': lambda item: item.get_child().get_text()
				}[self.data[item]](item)
			
			# put it into the dictionary to be returned
			# consoletransation / displaymanager can be commented out
			# if result is commented out, set it to the 'special' string
			# so _edit_config can know to comment it out.
			if result == "commented out":
				result = "##commented##"
			
			rc_conf[item.get_name()] = result
				
				
		return rc_conf
	
	def load_rc_conf_dictionary(self, rc_conf):
		for item in self.data.keys():
			# depending on what kind of gui element it is,
			# we need to get the data out of it differently.
			# equivalent of a switch statement in python...
			try:
				result = {
					'combo': lambda item: self.set_combo_current_text(item,rc_conf[item.get_name()]),
					'entry': lambda item: item.set_text(rc_conf[item.get_name()]),
					'comboentry': lambda item: item.get_child().set_text(rc_conf[item.get_name()])
					}[self.data[item]](item)
			except KeyError:
				# that value didn't exist in the stored profile
				# debugging only here
				#print "KeyError"
				pass
		
	def activate(self):
		# FIXME: <codeman> this is a temp hack fix for rc.conf as it will not work with new baselayout.
		self.etc_files = self.controller.install_profile.get_etc_files()
		if not "rc.conf" in self.etc_files:
			self.etc_files['rc.conf'] = {}
		rc_conf = self.etc_files['rc.conf']
		self.load_rc_conf_dictionary(rc_conf)
		#print "loaded: "+str(rc_conf)
		
		self.controller.SHOW_BUTTON_EXIT    = True
		self.controller.SHOW_BUTTON_HELP    = True
		self.controller.SHOW_BUTTON_BACK    = True
		self.controller.SHOW_BUTTON_FORWARD = True
		self.controller.SHOW_BUTTON_FINISH  = False
		
	def deactivate(self):
		value = True
		rc_conf = self.generate_rc_conf_dictionary()
		#print "saving:"+str(rc_conf)
		
		try:
			self.etc_files['rc.conf'] = rc_conf
			self.controller.install_profile.set_etc_files(self.etc_files)
		except:
			msgbox=Widgets().error_Box("Error","An internal error occurred!")
			msgbox.run()
			msgbox.destroy()
		return value
