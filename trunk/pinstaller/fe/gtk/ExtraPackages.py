# Copyright 1999-2005 Gentoo Foundation
# This source code is distributed under the terms of version 2 of the GNU
# General Public License as published by the Free Software Foundation, a copy
# of which can be found in the main directory of this project.

import gtk, gobject, copy
import GLIScreen
from Widgets import Widgets
import GLIUtility

class Panel(GLIScreen.GLIScreen):
	"""
	The extrapackages section of the installer.
	
	@author:    John N. Laliberte <allanonjl@gentoo.org>
	@license:   GPL
	"""
	# Attributes:
	title="Do you need any extra packages?"
	_helptext = """
<b><u>Extra Packages</u></b>

Packages available via GRP (pre-compiled binaries on the livecd that get copied
over) are labeled with (GRP), and include all of their dependencies.  For
instance gnome (GRP) includes all of gnome, including xorg-x11.  Fluxbox,
however, is not available in GRP and must be compiled.  The list of packages is
very limited, as Portage has a vast list of available packages.  If you have
packages you need to install in addition to the list, enter them in a space
separated list in the text field.  The installer is designed to get you a system
capable of booting into a graphical environment, not install every single
package you will ever use.  That would just massively increase the changes of a
failed package ruining your installation.

If you choose a graphical desktop such as gnome, kde, or fluxbox, be sure to
choose xdm from the startup services and to set your Display Manager (and/or
XSession for fluxbox) in the Other Settings screen.
"""
	
	# list of packages to emerge from the checked off items.
	checked_items = []
	
	def __init__(self, controller):
		GLIScreen.GLIScreen.__init__(self, controller)

		self.vert    = gtk.VBox(False, 10)
		self.vert2    = gtk.VBox(False, 10)
		
	def draw_screen(self):
		content_str = """
This is where you emerge extra packages that your system may need. Packages that
are fetch-restricted (e.g. sun-jdk) or require you to accept licenses (e.g. many
big games) will cause your install to fail. Add additional packages with
caution. These trouble packages can be installed manually after you reboot.
"""
		
		# pack the description
		self.vert.pack_start(gtk.Label(content_str), expand=False, fill=False, padding=5)
		
		scrolled_window = gtk.ScrolledWindow(hadjustment=None, vadjustment=None)
		scrolled_window.set_policy(gtk.POLICY_NEVER, gtk.POLICY_ALWAYS)
		
		# store the objects for later ( when loading )
		self.category_objects = {}
		self.package_objects = {}
		
		self.categories = self.controller.install_profile.get_install_package_list()
		self.group_packages = GLIUtility.get_grp_pkgs_from_cd()
		
		# first load the category
		for category in self.categories:
			categ = self.Category(category)
			self.category_objects[category] = categ
			hbox = categ.Generate_GTK()
			self.vert2.pack_start(hbox,expand=False,fill=False,padding=0)
			
			# then load the packages in that category
			packages = self.categories[category][1]
			for package in packages:
				# group_packages may be in the format category/package or just package
				if "/" in package:
					displayname = package[package.index("/")+1:]
				else:
					displayname = package
				
				# if its a grp install, append (GRP) to the name
				if self.controller.install_profile.get_grp_install():
					if package in self.group_packages:
						displayname = displayname + " (GRP)"
						
				pack = self.Package(self, package, packages[package], displayname)
				self.package_objects[package] = pack
				hbox = pack.Generate_GTK()
				self.vert2.pack_start(hbox,expand=False,fill=False,padding=0)
		
		# add the custom space-seperated list bar
		entry_description = gtk.Label("Enter a space seperated list of extra packages to install on the system ( in addition to those checked above ):")
		self.entry=gtk.Entry()

		scrolled_window.add_with_viewport(self.vert2)
		viewport = scrolled_window.get_children()[0]
		viewport.set_shadow_type (gtk.SHADOW_IN)
		viewport.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse ("white"))
		
		self.vert.pack_start(scrolled_window,expand=True,fill=True,padding=0)
		self.vert.pack_start(entry_description,expand=False,fill=False,padding=0)
		self.vert.pack_start(self.entry,expand=False,fill=False,padding=0)
		self.vert.show_all()
		self.add_content(self.vert)
	
	def activate(self):
		self.controller.SHOW_BUTTON_EXIT    = True
		self.controller.SHOW_BUTTON_HELP    = True
		self.controller.SHOW_BUTTON_BACK    = True
		self.controller.SHOW_BUTTON_FORWARD = True
		self.controller.SHOW_BUTTON_FINISH  = False
		
		# remove all checked items to start with
		self.checked_items = []
		
		# we are destroying and redrawing because we have to
		# dynamically change what the options looks like based
		# on another screen's values.
		self.vert.destroy()
		self.draw_screen()
		
		# load the custom packages from the profile
		unjoined = self.controller.install_profile.get_install_packages()		
		#print "loaded custom packages: " + str(unjoined)
		
		# generate a full list of packages offered by the fe
		package_list = []
		for item in self.categories:
			for pack in self.categories[item][1]:
				#package_list.update()
				package_list.append(pack)
				
		# now check to see if any match
		unjoined_reduced = copy.deepcopy(unjoined)
		for package in unjoined:
			#print "Trying to match: " + package
			if package in package_list:
				# check it off!
				#print "matched! " + package
				self.package_objects[package].ToggleOn()
				
				# and remove it from the list
				unjoined_reduced.remove(package)
				
		
		s=" ".join(unjoined_reduced)
		self.entry.set_text(s)
	
	def deactivate(self):
		return_value = False
		# save the space seperated list
		#print self.custom_box.get_text()
		try:
			packages_to_emerge = ""
			packages_to_emerge = self.entry.get_text() + " " + " ".join(self.checked_items)
			
			self.controller.install_profile.set_install_packages(None, packages_to_emerge, None)
			#print packages_to_emerge
			return_value = True
		except:
			box = Widgets().error_Box("Error saving packages","You need to fix your input! \n Theres a problem, are you sure didn't enter \n funny characters?")
			box.show()
			return_value = False
			
		return return_value
	
	class Category:
		
		def __init__(self, category_name):
			self.category_name = category_name
		
		def Name(self):
			return category_name
		
		def Generate_GTK(self):
			# Generate GTK needed.
			hbox=gtk.HBox(True,0)
			
			name=gtk.Label("")
			name.set_markup('<span size="x-large" weight="bold" foreground="white">'+self.category_name+'</span>')
			name.set_justify(gtk.JUSTIFY_LEFT)
			
			table = gtk.Table(1, 1, False)
			table.set_col_spacings(10)
			table.set_row_spacings(6)
			table.attach(name,0,1,0,1)
			
			eb=gtk.EventBox()
			eb.add(Widgets().hBoxIt2(False, 0, table))
			eb.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("#737db5"))
			hbox.pack_start(eb, expand=True, fill=True,padding=5)
			
			return hbox
		
		property(Name)
	
	class Package:

		def __init__(self, parent, portage_name, description, display_name):
			self.parent = parent
			self.portage_name = portage_name
			self.description = description
			self._display_name = display_name
		
		def Name(self):
			return self.portage_name
		
		def DisplayName(self):
			return self._display_name
		
		def Description(self):
			return self.description
		
		def isChecked(self):
			return True
		
		def ToggleOn(self):
			self.checkbox.set_active(True)
		
		def Generate_GTK(self):
			# Generate the pygtk code ncessary for this object.
			hbox=gtk.HBox(False,0)
			table = gtk.Table(2, 2, False)
			table.set_col_spacings(10)
			table.set_row_spacings(1)
			
			button = gtk.CheckButton()
			
			title=gtk.Label("")
			title.set_markup('<span weight="bold">' + self._display_name + '</span>'
					 + " - " + self.description)
			button.add(title)
			button.connect("toggled", self.checkbox_callback, self.portage_name)
			self.checkbox = button
			
			table.attach(Widgets().hBoxIt2(False,0,button),1,2,0,1)
			hbox.pack_start(table,expand=False,fill=False,padding=0)
			
			return hbox
		
		def checkbox_callback(self, widget, data=None):
			#print "%s was toggled %s" % (data, ("OFF", "ON")[widget.get_active()])
			if widget.get_active():
				self.parent.checked_items.append(data)
			else:
				self.parent.checked_items.remove(data)
			# debug
			#print self.parent.checked_items
		
		property(Name)
		property(Description)
		property(isChecked)
