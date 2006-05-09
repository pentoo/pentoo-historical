#!/usr/bin/python

# Copyright 1999-2005 Gentoo Foundation
# This source code is distributed under the terms of version 2 of the GNU
# General Public License as published by the Free Software Foundation, a copy
# of which can be found in the main directory of this project.

import sys
sys.path.append("../..")

import GLIInstallProfile
import GLIClientConfiguration
import GLIClientController
import GLIUtility
from GLIFutureBar import GLIFutureBar
from HelpDialog import HelpDialog
from SplashScreen import SplashScreen
import gtk
import gobject
import crypt
import random
from gettext import gettext as _

import RunInstall

class Installer:

	SHOW_BUTTON_FINISH = 1
	SHOW_BUTTON_FORWARD = 1
	SHOW_BUTTON_BACK = 1
	SHOW_BUTTON_HELP = 1
	SHOW_BUTTON_EXIT = 1
	install_profile_xml_file = ""
	install_window = None

	menuItems = [ { 'text': _('Welcome'), 'module': __import__("Welcome") },
                  { 'text': _('Pre-install Config'), 'module': __import__("ClientConfig") },
                  { 'text': _('Partitioning'), 'module': __import__("Partitioning") },
                  { 'text': _('Network Mounts'), 'module': __import__("NetworkMounts") },
                  { 'text': _('Stage'), 'module': __import__("Stage") },
                  { 'text': _('Portage tree'), 'module': __import__("PortageTree") },
                  { 'text': _('make.conf'), 'module': __import__("MakeDotConf") },
                  { 'text': _('Kernel'), 'module': __import__("Kernel") },
                  { 'text': _('Bootloader'), 'module': __import__("Bootloader") },
                  { 'text': _('Timezone'), 'module': __import__("Timezone") },
                  { 'text': _('Networking'), 'module': __import__("Networking") },
                  { 'text': _('Daemons'), 'module': __import__("Daemons") },
                  { 'text': _('Extra Packages'), 'module': __import__("ExtraPackages") },
                  { 'text': _('Startup Services'), 'module': __import__("StartupServices") },
                  { 'text': _('Other Settings'), 'module': __import__("OtherSettings") },
                  { 'text': _('Users'), 'module': __import__("Users") },
                  { 'text': _('Review'), 'module': __import__("InstallSummary") }
                ]

	def __init__(self):
		self.client_profile = GLIClientConfiguration.ClientConfiguration()
		self.install_profile = GLIInstallProfile.InstallProfile()
		self._pretend = False
		self._debug = False

		for arg in sys.argv:
			if arg == "-p" or arg == "--pretend":
				self._pretend = True
			elif arg == "-d" or arg == "--debug":
				self._debug = True

		self.cc = GLIClientController.GLIClientController(pretend=self._pretend)

		self.window = None
		self.panel = None
		self._cur_panel = 0
		self.__full_path = self.get_current_path()
		self.splash = SplashScreen(self.__full_path)
		self.splash.show()
		while gtk.events_pending():
			gtk.main_iteration()
		self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
		self.title = _("Gentoo Linux Installer")
		self.window.realize()
		self.window.connect("delete_event", self.delete_event)
		self.window.connect("destroy", self.destroy)
		self.window.set_border_width(0)
		self.window.set_default_size(800,600)
		self.window.set_geometry_hints(None, min_width=800, min_height=600, max_width=800, max_height=600)
		self.window.set_title(_("Gentoo Linux Installer"))
		self.globalbox = gtk.VBox(False, 0)
		self.window.add(self.globalbox)

		# Banner image
		self.headerbox = gtk.HBox(False, 0)
		headerimg = gtk.Image()
		headerimg.set_from_file(self.__full_path + '/installer-banner-800x64.png')
		self.headerbox.add(headerimg)
		self.globalbox.pack_start(self.headerbox, expand=False, fill=False, padding=0)

		# Future bar
		self.futurebar = GLIFutureBar([element['text'] for element in self.menuItems])
		self.globalbox.pack_start(self.futurebar, expand=False, fill=False, padding=5)
		self.globalbox.pack_start(gtk.HSeparator(), expand=False, fill=False, padding=0)

		# Top box
		self.topbox = gtk.HBox(False, 0)
		self.globalbox.pack_start(self.topbox, expand=True, fill=True, padding=5)

		# Bottom box
		self.bottombox = gtk.HBox(False, 0)
		self.globalbox.pack_end(self.bottombox, expand=False, fill=False, padding=5)
		self.globalbox.pack_end(gtk.HSeparator(), expand=False, fill=False, padding=0)
		self.rightframe = gtk.VBox(False, 0)
		self.topbox.pack_end(self.rightframe, expand=True, fill=True, padding=5)
		self.globalbox.show_all();

		# Right frame contents
		self.panels = []
		self.right_pane_box = gtk.Notebook()
#		for item in self.menuItems:
#			if item['module'] == None: break
#			if self._debug:
#				print "Instantiating " + item['text'] + " screen...",
#			panel = item['module'].Panel(self)
#			if self._debug:
#				print "done"
#			self.panels.append(panel)
#			self.right_pane_box.append_page(panel)
		self.right_pane_box.set_show_tabs(False)
		self.right_pane_box.set_show_border(False)
		self.rightframe.add(self.right_pane_box)

		buttons_info = [ ('exit', _(" _Exit "), '/button_images/stock_exit.png', self.exit_button, 'start'),
                                 ('help', _(" _Help "), '/button_images/stock_help.png', self.help, 'start'),
                                 ('load', _(" _Load "), '/button_images/stock_open.png', self.load_button, 'start'),
                                 ('save', _(" _Save "), '/button_images/stock_save.png', self.save_button, 'start'),
                                 ('finish', _(" _Install "), '/button_images/stock_exec.png', self.finish, 'end'),
                                 ('forward', _(" _Forward "), '/button_images/stock_right.png', self.forward, 'end'),
                                 ('back', _(" _Back "), '/button_images/stock_left.png', self.back, 'end')
                               ]
		self.buttons = {}

		for button in buttons_info:
			self.buttons[button[0]] = gtk.Button()
			tmpbuttonbox = gtk.HBox(False, 0)
			tmpbuttonimg = gtk.Image()
			tmpbuttonimg.set_from_file(self.__full_path + button[2])
			tmpbuttonbox.pack_start(tmpbuttonimg)
			tmpbuttonlabel = gtk.Label(button[1])
			tmpbuttonlabel.set_use_underline(True)
			tmpbuttonbox.pack_start(tmpbuttonlabel)
			self.buttons[button[0]].add(tmpbuttonbox)
			self.buttons[button[0]].connect("clicked", button[3], None)
			if button[4] == "start":
				self.bottombox.pack_start(self.buttons[button[0]], expand=False, fill=False, padding=5)
			else:
				self.bottombox.pack_end(self.buttons[button[0]], expand=False, fill=False, padding=5)

		gobject.idle_add(self.init_screens)

	def redraw_left_pane(self, firstrun=False):
		if not firstrun: self.leftframe.remove(self.navlinks)
		self.navlinks = gtk.VBox(False, 5)
		self.navlinks.set_size_request(140, -1)
		navlinkslabel = gtk.Label(_("    Installation Steps    "))
		self.navlinks.pack_start( navlinkslabel, expand=False, fill=False, padding=10)
		self.num_times = 0
		for item_ in self.menuItems:
			item = str(self.num_times+1) + ". " + item_['text']
			self.box = gtk.HBox(False,5)
			box_string = item
			box_label=gtk.Label(box_string)
			box_label.set_alignment(0,0)
			self.box.pack_start( box_label, expand=False, fill=False, padding=5)
			self.navlinks.pack_start( self.box, expand=False, fill=False, padding=3)
			box_label.set_sensitive(True)

			if self._cur_panel == self.num_times:
				box_label.set_markup('<b>'+box_string+'</b>')

			self.num_times = self.num_times + 1
		self.leftframe.add(self.navlinks)
		self.leftframe.show_all()

	def redraw_buttons(self):
		self.bottombox.hide_all()
		self.buttons['finish'].set_sensitive(self.SHOW_BUTTON_FINISH)
		self.buttons['forward'].set_sensitive(self.SHOW_BUTTON_FORWARD)
		self.buttons['back'].set_sensitive(self.SHOW_BUTTON_BACK)
		self.buttons['help'].set_sensitive(self.SHOW_BUTTON_HELP)
		self.buttons['exit'].set_sensitive(self.SHOW_BUTTON_EXIT)
		if self.SHOW_BUTTON_FORWARD:
			self.buttons['forward'].set_flags(gtk.CAN_DEFAULT)
			self.buttons['forward'].grab_default()
		elif self.SHOW_BUTTON_FINISH:
			self.buttons['finish'].set_flags(gtk.CAN_DEFAULT)
			self.buttons['finish'].grab_default()
#		if self.install_profile_xml_file != "":
#			self.finishbutton.set_sensitive(True)
		self.bottombox.show_all()

	def refresh_right_panel(self):
		self.rightframe.show_all()

	def make_visible(self):
		self.window.show_all()
		self.window.present()

	def make_invisible(self):
		self.window.hide_all()

	def get_current_path(self):
		# this will return the absolute path to the
		# directory containing this file
		# it will only work if this file is imported somewhere,
		# not if it is run directly (__file__ will be undefined)
		import os.path
		return os.path.abspath(os.path.dirname(__file__))

	def add_content(self, content):
		self.right_pane_box.pack_end(content, True, True, 0)

	def get_commands(self):
		pass

	def set_active(self):
		self.active=1

	def loadPanel(self, panel=0):
		if not self.panels[self._cur_panel].deactivate():
			return
		self._cur_panel = panel
		self.right_pane_box.set_current_page(panel)
		self.panels[panel].activate()
		self.futurebar.setpos(panel)
		self.redraw_buttons()

	def init_screens(self):
#		self.splash.show()
		for item in self.menuItems:
			if item['module'] == None: break
			if self._debug:
				print "Instantiating " + item['text'] + " screen...",
			panel = item['module'].Panel(self)
			if self._debug:
				print "done"
			self.panels.append(panel)
			self.right_pane_box.append_page(panel)
		self.splash.destroy()
		self.make_visible()
		self.loadPanel()
		return False

	def run(self):
		gtk.threads_init()
		gtk.main()

	def back(self, widget, data=None):
		if self._cur_panel > 0:
			self.loadPanel(self._cur_panel - 1)

	def forward(self, widget, data=None):
		if self._cur_panel < (len(self.menuItems) - 1):
			self.loadPanel(self._cur_panel + 1)

	def help(self, widget, data=None):
#		GLIUtility.spawn("firefox http://www.gentoo.org/doc/en/handbook/index.xml &>/dev/null &")
		try:
			helptext = self.panels[self._cur_panel]._helptext
		except:
			helptext = "There is no help available for this screen"
		helpdlg = HelpDialog(self.window, helptext)
		helpdlg.run()

	def exit_button(self, widget, data=None):
		msgdlg = gtk.MessageDialog(parent=self.window, type=gtk.MESSAGE_QUESTION, buttons=gtk.BUTTONS_YES_NO, message_format="Are you sure you want to exit?")
		resp = msgdlg.run()
		msgdlg.destroy()
		if resp == gtk.RESPONSE_YES:
			self.exit()

	def finish(self, widget, data=None):
		# Remove screens
		while len(self.panels):
			self.right_pane_box.remove_page(-1)
			del self.panels[-1]
		self.make_invisible()
		self.install_window = RunInstall.RunInstall(self)

	def load_button(self, widget, data=None):
		filesel = gtk.FileSelection(_("Select the install profile to load"))
		if self.install_profile_xml_file == "":
			filesel.set_filename("installprofile.xml")
		else:
			filesel.set_filename(self.install_profile_xml_file)
		resp = filesel.run()
		filename = filesel.get_filename()
		filesel.destroy()
		if resp == gtk.RESPONSE_OK:
			self.install_profile_xml_file = filename
			try:
				tmp_install_profile = GLIInstallProfile.InstallProfile()
				tmp_install_profile.parse(self.install_profile_xml_file)
				self.install_profile = tmp_install_profile
				msgdlg = gtk.MessageDialog(parent=self.window, type=gtk.MESSAGE_INFO, buttons=gtk.BUTTONS_OK, message_format=_("Install profile loaded successfully!"))
				msgdlg.run()
				msgdlg.destroy()
			except:
				errdlg = gtk.MessageDialog(parent=self.window, type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK, message_format=_("An error occured loading the install profile"))
				errdlg.run()
				errdlg.destroy()

	def save_button(self, widget, data=None):
		filesel = gtk.FileSelection(_("Select the location to save the install profile"))
		if self.install_profile_xml_file == "":
			filesel.set_filename("installprofile.xml")
		else:
			filesel.set_filename(self.install_profile_xml_file)
		resp = filesel.run()
		filename = filesel.get_filename()
		filesel.destroy()
		if resp == gtk.RESPONSE_OK:
			self.install_profile_xml_file = filename
			try:
				configuration = open(filename, "w")
				configuration.write(self.install_profile.serialize())
				configuration.close()
				msgdlg = gtk.MessageDialog(parent=self.window, type=gtk.MESSAGE_INFO, buttons=gtk.BUTTONS_OK, message_format=_("Install profile saved successfully!"))
				msgdlg.run()
				msgdlg.destroy()
			except:
				errdlg = gtk.MessageDialog(parent=self.window, type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK, message_format=_("An error occured saving the install profile"))
				errdlg.run()
				errdlg.destroy()

	def delete_event(self, widget, event, data=None):
		return False

	def destroy(self, widget, data=None):
		gtk.main_quit()
		return True
	
	def exit(self):
		gtk.main_quit()
		sys.exit(0)

if __name__ == "__main__":
	install = Installer()
	install.run()
