# Copyright 1999-2006 Gentoo Foundation
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
	Other settings for an install.
	
	@author:    John N. Laliberte <allanonjl@gentoo.org>
	@license:   GPL
	"""
	# Attributes:
	#title="Other Settings"
	_helptext = """
<b><u>Other Settings</u></b>

Display Manager:
If you installed gnome, choose gdm. If you installed kde, choose kdm. If you
installed anything else specified in XSession, choose xdm.

Console Font:
You probably don't want to mess with this.

Extended Keymaps:
You probably don't want to mess with this.

Windowkeys:
If installing on x86 you are safe with Yes, otherwise you'll probably want to
say No.

Keymap:
This defaults to "us" if not set (recommended).  If you don't want an English
keymap, choose it from the list.

XSession:
Choose this only if you didn't choose gdm or kdm from the Display Manager list.

Clock:
If you chose a local timezone, you'll want to choose "local" for the clock
setting. Otherwise if you chose UTC in the Timezone screen, choose UTC here.

Default Editor:
Pick one.  Nano is the default and recommended.
"""
	
	# Operations
	def __init__(self, controller):
		GLIScreen.GLIScreen.__init__(self, controller)

		vert    = gtk.VBox(False, 10) # This box is content so it should fill space to force title to top
		horiz   = gtk.HBox(False, 0)
		horiz2   = gtk.HBox(False, 0)
		horiz3   = gtk.HBox(False, 0)

		addme_to_vert = []
		
		# this code could be reduced, but would it make things any clearer?
		
		# create the CLOCK object
		self.clock = self.Option("Clock")
		self.clock.HelpText = "Should CLOCK be set to UTC or local? Unless you set your timezone to UTC you will want to choose local."
		self.clock.Options = ["UTC","local"]
		self.clock.Type = self.Option.OptionType.COMBO
		clock_gtk = self.clock.Generate_GTK()
		addme_to_vert.append(clock_gtk)
		
		# create the Windowkeys object
		self.windowkeys = self.Option("Windowkeys")
		self.windowkeys.HelpText = "Should we first load the 'windowkeys' console keymap?"
		self.windowkeys.Options = ["Yes","No"]
		self.windowkeys.Type = self.Option.OptionType.COMBO
		clock_gtk = self.windowkeys.Generate_GTK()
		addme_to_vert.append(clock_gtk)
		
		# create the Display Manager object
		self.displaymanager = self.Option("Display Manager")
		self.displaymanager.HelpText = "Choose your display manager for Xorg-x11 (note you must make sure that package also gets installed for it to work)"
		self.displaymanager.Options = ["xdm","kdm","gdm"]
		self.displaymanager.Type = self.Option.OptionType.COMBO_ENTRY
		clock_gtk = self.displaymanager.Generate_GTK()
		addme_to_vert.append(clock_gtk)
		
		# create the Default Editor object
		self.editor = self.Option("Default Editor")
		self.editor.HelpText = "Choose your default editor"
		self.editor.Options = ["/bin/nano","/usr/bin/vim","/usr/bin/emacs"]
		self.editor.Type = self.Option.OptionType.COMBO
		editor_gtk = self.editor.Generate_GTK()
		addme_to_vert.append(editor_gtk)

		# create the Keymap object
		self.keymap = self.Option("Keymap")
		self.keymap.HelpText = "Choose your desired keymap"
		self.keymap.Options = [""] + GLIUtility.generate_keymap_list()
		self.keymap.Type = self.Option.OptionType.COMBO
		editor_gtk = self.keymap.Generate_GTK()
		addme_to_vert.append(editor_gtk)

		# create the Console Font object
		self.font = self.Option("Console Font")
		self.font.HelpText = "Choose your default console font"
		self.font.Options = [""] + GLIUtility.generate_consolefont_list()
		self.font.Type = self.Option.OptionType.COMBO
		editor_gtk = self.font.Generate_GTK()
		addme_to_vert.append(editor_gtk)
		
		# create a last bogus one to make it look pretty.
		bogus = self.Option("")
		bogus.HelpText = ""
		bogus.Type = self.Option.OptionType.NONE
		bogus = bogus.Generate_GTK()
		addme_to_vert.append(bogus)
		
		# create the XSession object
		self.xsession = self.Option("XSession")
		self.xsession.HelpText = "Choose what window manager you want to start default with X if run with xdm, startx, or xinit. (common options are Gnome or Xsession)"
		self.xsession.Options = ["Gnome","Xsession","fluxbox"]
		self.xsession.Type = self.Option.OptionType.COMBO_ENTRY
		editor_gtk = self.xsession.Generate_GTK()
		addme_to_vert.append(editor_gtk)
		
		# create the Extended Keymaps object
		self.extkeymap = self.Option("Extended Keymaps")
		self.extkeymap.HelpText = "This sets the maps to load for extended keyboards. Most users will leave this as is."
		self.extkeymap.Type = self.Option.OptionType.TEXT
		editor_gtk = self.extkeymap.Generate_GTK()
		addme_to_vert.append(editor_gtk)
		
		addme_to_vert.reverse()
		for i,item in enumerate(addme_to_vert):
			if i< 3:
				horiz.pack_start(item, expand=True, fill=True, padding=10)
			elif i<6:
				horiz2.pack_start(item, expand=True, fill=True, padding=10)
			else:
				horiz3.pack_start(item, expand=True, fill=True, padding=10)
		
		self.add_content(horiz)
		self.add_content(horiz2)
		self.add_content(horiz3)
	
	def create_etc_files(self, etc_files):
		if not "conf.d/keymaps" in etc_files: 
			etc_files['conf.d/keymaps'] = {}
#		if not "conf.d/consolefont" in etc_files: 
#			etc_files['conf.d/consolefont'] = {}
		if not "conf.d/clock" in etc_files: 
			etc_files['conf.d/clock'] = {}
		if not "rc.conf" in etc_files: 
			etc_files['rc.conf'] = {}
			
		return etc_files
			
	def activate(self):
		
		etc_files = self.controller.install_profile.get_etc_files()
		etc_files = self.create_etc_files(etc_files)
		
		if 'conf.d/keymaps' in etc_files:
			if 'KEYMAP' in etc_files['conf.d/keymaps']:
				self.keymap.SetValue(etc_files['conf.d/keymaps']['KEYMAP'])
			if 'SET_WINDOWSKEYS' in etc_files['conf.d/keymaps']:
				self.windowkeys.SetValue(etc_files['conf.d/keymaps']['SET_WINDOWSKEYS'])
			if 'EXTENDED_KEYMAPS' in etc_files['conf.d/keymaps']:
				self.extkeymap.SetValue(etc_files['conf.d/keymaps']['EXTENDED_KEYMAPS'])
				
		if 'conf.d/consolefont' in etc_files:
			if 'CONSOLEFONT' in etc_files['conf.d/consolefont']:
				self.font.SetValue(etc_files['conf.d/consolefont']['CONSOLEFONT'])
			
		if 'conf.d/clock' in etc_files:
			if 'CLOCK' in etc_files['conf.d/clock']:
				self.clock.SetValue(etc_files['conf.d/clock']['CLOCK'])
				
		if 'rc.conf' in etc_files:
			if 'EDITOR' in etc_files['rc.conf']:
				self.editor.SetValue(etc_files['rc.conf']['EDITOR'])
			if 'DISPLAYMANAGER' in etc_files['rc.conf']:
				self.displaymanager.SetValue(etc_files['rc.conf']['DISPLAYMANAGER'])
			if 'XSESSION' in etc_files['rc.conf']:
				self.xsession.SetValue(etc_files['rc.conf']['XSESSION'])
	
		
		self.controller.SHOW_BUTTON_EXIT    = True
		self.controller.SHOW_BUTTON_HELP    = True
		self.controller.SHOW_BUTTON_BACK    = True
		self.controller.SHOW_BUTTON_FORWARD = True
		self.controller.SHOW_BUTTON_FINISH  = False
		
	def deactivate(self):
		value = True
		
		etc_files = self.controller.install_profile.get_etc_files()
		etc_files = self.create_etc_files(etc_files)

		if self.keymap.GetValue():
			etc_files['conf.d/keymaps']['KEYMAP'] = self.keymap.GetValue()
		etc_files['conf.d/keymaps']['SET_WINDOWSKEYS'] = self.windowkeys.GetValue()
		if self.extkeymap.GetValue() != "":
			etc_files['conf.d/keymaps']['EXTENDED_KEYMAPS'] = self.extkeymap.GetValue()
		if self.font.GetValue():
			if not "conf.d/consolefont" in etc_files: 
				etc_files['conf.d/consolefont'] = {}
			etc_files['conf.d/consolefont']['CONSOLEFONT'] = self.font.GetValue()
		etc_files['conf.d/clock']['CLOCK'] = self.clock.GetValue()
		etc_files['rc.conf']['EDITOR'] = self.editor.GetValue()
		if self.displaymanager.GetValue() != "":
			etc_files['rc.conf']['DISPLAYMANAGER'] = self.displaymanager.GetValue()
		if self.xsession.GetValue() != "":
			etc_files['rc.conf']['XSESSION'] = self.xsession.GetValue()
			
		try:
			self.controller.install_profile.set_etc_files(etc_files)
		except:
			msgbox=Widgets().error_Box("Error","An internal error occurred!")
			msgbox.run()
			msgbox.destroy()
			
		return value

	class Option:

		class Property(object):
			class __metaclass__(type):
				def __init__(cls, name, bases, dct):
					for fname in ['get', 'set', 'delete']:
						if fname in dct:
							setattr(cls, fname, staticmethod(dct[fname]))
				def __get__(cls, obj, objtype=None):
					if obj is None:
						return cls
					fget = getattr(cls, 'get')
					return fget(obj)
				def __set__(cls, obj, value):
					fset = getattr(cls, 'set')
					fset(obj, value)
				def __delete__(cls, obj):
					fdel = getattr(cls, 'delete')
					fdel(obj)
					
		class OptionType:
			NONE = 0
			TEXT = 1
			COMBO = 2
			COMBO_ENTRY = 3
			
		def __init__(self, name):
			self.Name = name
			self.HelpText = ""
			# by default we make a combo
			self.Type = self.OptionType.COMBO
			self.Options = []
		
		class Name(Property):
			""" Name property """
			def get(self):
				return self._name
			def set(self):
				self._name = val
		
		class HelpText(Property):
			""" HelpText property """
			def get(self):
				return self._helptext
			def set(self):
				self._helptext = val
		
		class Type(Property):
			""" Name property """
			def get(self):
				return self._type
			def set(self):
				self._type = val
		
		class Options(Property):
			""" Options property """
			def get(self):
				return self._options
			def set(self):
				self._name = self._options

		class GtkElement(Property):
			""" GtkElement Property """
			def get(self):
				return self._gtkelement
			def set(self):
				self._gtkelement = val
				
		def GetValue(self):
			if self.Type == self.OptionType.TEXT:
				return self.GtkElement.get_text()
			elif self.Type == self.OptionType.COMBO:
				model = self.GtkElement.get_model()
				active = self.GtkElement.get_active()
				return model[active][0]
			elif self.Type == self.OptionType.COMBO_ENTRY:
				return self.GtkElement.get_child().get_text()
		
		def SetValue(self, text):
			if self.Type == self.OptionType.TEXT:
				self.GtkElement.set_text(text)
			elif self.Type == self.OptionType.COMBO:
				# iterate through all the elements,
				# get the number and set it.
				model = self.GtkElement.get_model()

				for i,item in enumerate(model):
					if item[0] == text:
						self.GtkElement.set_active(i)
			elif self.Type == self.OptionType.COMBO_ENTRY:
				self.GtkElement.get_child().set_text(text)
			
		def Generate_GTK(self):
			
			box = gtk.VBox(False, 0)
			
			# the name of the setting
			hbox = gtk.HBox(False,0)
			label = gtk.Label("")
			label.set_markup('<span weight="bold">'+self.Name+'</span>')

			label.set_size_request(150, -1)
			hbox.pack_start(label, expand=False, fill=False, padding=0)
			box.pack_start(hbox, expand=False, fill=False, padding=5)
			
			# the description of the option
			hbox = gtk.HBox(False,0)
			label = gtk.Label(self.HelpText)
			label.set_size_request(200, -1)
			label.set_line_wrap(True)
			label.set_justify(gtk.JUSTIFY_FILL)
			hbox.pack_start(label, expand=False, fill=False, padding=0)
			box.pack_start(hbox, expand=False, fill=False, padding=5)
			
			# switch here based on type of gui element.
			if self.Type == self.OptionType.TEXT:
				gui_element = gtk.Entry()
			elif self.Type == self.OptionType.NONE:
				gui_element = gtk.Label("")
				# but we want to HIDE the entry so its not visible
				gui_element.hide()
			elif self.Type == self.OptionType.COMBO:
				gui_element = gtk.combo_box_new_text()
				#gui_element.set_wrap_width(5)
			elif self.Type == self.OptionType.COMBO_ENTRY:
				gui_element = gtk.combo_box_entry_new_text()

			# store it for later :)
			self.GtkElement = gui_element
			
			for option_text in self.Options:
				gui_element.append_text(option_text)
			
			gui_element.set_name(self.Name)
			gui_element.set_size_request(150, -1)
			
			# what we do by default
			if self.Type == self.OptionType.TEXT or self.Type == self.OptionType.NONE:
				#gui_element.set_text(()
				pass
			elif self.Type == self.OptionType.COMBO:
				gui_element.set_active(0)
			
			hbox = gtk.HBox(False,0)
			hbox.pack_start(gui_element, expand=False, fill=False, padding=0)
			box.pack_start(hbox, expand=False, fill=False, padding=5)
			return box
		
