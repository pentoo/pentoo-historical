# Copyright 1999-2005 Gentoo Foundation
# This source code is distributed under the terms of version 2 of the GNU
# General Public License as published by the Free Software Foundation, a copy
# of which can be found in the main directory of this project.

import gtk
import GLIScreen
import commands
import gobject
import GLIUtility

class Panel(GLIScreen.GLIScreen):

	title = "make.conf"
	make_conf_values = {}
	use_flags = []
	use_desc = {}
	columns = []
	arch_procs = { 'x86': ("i386", "i486", "i586", "pentium", "pentium-mmx", "i686", "pentiumpro", "pentium2", "pentium3", "pentium3m", "pentium-m", "pentium4", "pentium4m", "prescott", "nocona", "k6", "k6-2", "k6-3", "athlon", "athlon-tbird", "athlon-4", "athlon-xp", "athlon-mp", "k8", "opteron", "athlon64", "athlon-fx", "winchip-c6", "winchip2", "c3", "c3-2") }
	optimizations = ["-O0", "-O1", "-O2", "-Os", "-O3"]
	_helptext = """
<b><u>Make.conf</u></b>

One of the unique (and best) features of Gentoo is the ability to define flags
(called USE flags) that determine what components are compiled into
applications.  For example, you can enable the "alsa" flag and programs that
have alsa capability will compile in support for alsa.  Otherwise they will
leave it out, resulting in smaller, faster applications.  The result is a
finely-tuned OS with no unnecessary components to slow you down.

There are two types of USE flags, local (for only one application), and global
(for all apps).  The local use flags will tell you which package they refer to
in the Description.  Note that the names of the USE flags can sometimes be
misleading since they often refer to only one package.

CFLAGS:

The CFLAGS variable defines the optimization flags for the gcc C and C++
compilers. Although we define those generally here, you will only have maximum
performance if you optimize these flags for each program separately. The reason
for this is because every program is different. 

A first setting is the processor, which specifies the name of the target
architecture.  Select your Proc from the list.

A second one is the -O flag (that is a capital O, not a zero), which specifies
the gcc optimization class flag. Possible classes are s (for size-optimized),
0 (zero - for no optimizations), 1, 2 or 3 for more speed-optimization flags
(every class has the same flags as the one before, plus some extras).  2 is a
safe level of optimization.

You can add additional custom CFLAGS with the textbox.

Another popular optimization flag is -pipe (use pipes rather than temporary
files for communication between the various stages of compilation).

Mind you that using -fomit-frame-pointer (which doesn't keep the frame pointer
in a register for functions that don't need one) might have serious
repercussions on the debugging of applications! 

Other:

Select Use unstable only if you are an expert Gentoo user or want to use
bleeding edge unstable applications.  This is highly NOT recommended because it
will often result in failed installations due to compilation errors in unstable
applications.

Select Build binary packages if you plan on using the compiled packages
elsewhere (very rarely needed).

DistCC functionality has not yet been implemented with the GTK+ frontend.  If
you need this, use gli-dialog, the command-line frontend to GLI.

Select ccache to enable ccache support via CC.

The CHOST variable declares the target build host for your system. This variable
should already be set to the correct value. Do not edit it as that might break
your system. If the CHOST variable does not look correct to you, you might be
using the wrong stage3 tarball.

With MAKEOPTS you define how many parallel compilations should occur when you
install a package. A good choice is the number of CPUs in your system plus one,
but this guideline isn't always perfect. The syntax for the MAKEOPTS varaible is
"-jN" where N is the number of parallel compilations (for example: -j2).
"""

	def __init__(self, controller):
		GLIScreen.GLIScreen.__init__(self, controller)

		self.system_use_flags = commands.getoutput("portageq envvar USE").strip()
		self.system_cflags = commands.getoutput("portageq envvar CFLAGS").strip()
		self.system_chost = commands.getoutput("portageq envvar CHOST").strip()
		self.system_makeopts = commands.getoutput("portageq envvar MAKEOPTS").strip()
		self.system_features = commands.getoutput("portageq envvar FEATURES").strip()
		self.system_accept_keywords = commands.getoutput("portageq envvar ACCEPT_KEYWORDS").strip()

		vert = gtk.VBox(False, 0)
		vert.set_border_width(10)

		content_str = """On this screen, you'll define all of your /etc/make.conf settings.
"""

		content_label = gtk.Label(content_str)
		vert.pack_start(content_label, expand=False, fill=False, padding=0)

		f = open("/usr/portage/profiles/use.desc", "r")
		for line in f:
			line = line.strip()
			if not line or line.startswith("#"): continue
			dash_pos = line.find(" - ")
			if dash_pos == -1: continue
			flagname = line[:dash_pos] or line[dash_pos-1]
			desc = line[dash_pos+3:]
			self.use_desc[flagname] = desc
		f.close()

		f = open("/usr/portage/profiles/use.local.desc", "r")
		for line in f:
			line = line.strip()
			if not line or line.startswith("#"): continue
			dash_pos = line.find(" - ")
			if dash_pos == -1: continue
			colon_pos = line.find(":", 0, dash_pos)
			pkg = line[:colon_pos]
			flagname = line[colon_pos+1:dash_pos] or line[colon_pos+1]
			desc = "(" + pkg + ") " + line[dash_pos+3:]
			self.use_desc[flagname] = desc
		f.close()

		hbox = gtk.HBox(False, 0)
		label = gtk.Label()
		label.set_markup("<b>USE flags:</b>")
		hbox.pack_start(label, expand=False, fill=False, padding=0)
		vert.pack_start(hbox, expand=False, fill=False, padding=5)

		sorted_use = self.use_desc.keys()
		sorted_use.sort()
		self.treedata = gtk.ListStore(gobject.TYPE_BOOLEAN, gobject.TYPE_STRING, gobject.TYPE_STRING)
		for flag in sorted_use:
			self.treedata.append([(flag in self.use_flags and self.use_flags[flag] == 1), flag, self.use_desc[flag]])
		self.treeview = gtk.TreeView(self.treedata)
		self.toggle_renderer = gtk.CellRendererToggle()
		self.toggle_renderer.set_property("activatable", True)
		self.toggle_renderer.connect("toggled", self.flag_toggled)
		self.columns.append(gtk.TreeViewColumn("Active", self.toggle_renderer, active=0))
		self.columns.append(gtk.TreeViewColumn("Flag", gtk.CellRendererText(), text=1))
		self.columns.append(gtk.TreeViewColumn("Description", gtk.CellRendererText(), text=2))
		for column in self.columns:
			column.set_resizable(True)
			self.treeview.append_column(column)
		self.treewindow = gtk.ScrolledWindow()
		self.treewindow.set_size_request(-1, 180)
		self.treewindow.set_shadow_type(gtk.SHADOW_IN)
		self.treewindow.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
		self.treewindow.add(self.treeview)
		vert.pack_start(self.treewindow, expand=False, fill=False, padding=10)

		hbox = gtk.HBox(False, 0)
		label = gtk.Label()
		label.set_markup("<b>CFLAGS:</b>")
		hbox.pack_start(label, expand=False, fill=False, padding=0)
		vert.pack_start(hbox, expand=False, fill=False, padding=5)

		hbox = gtk.HBox(False, 0)
		hbox.pack_start(gtk.Label("Proc:"), expand=False, fill=False, padding=0)
		self.proc_combo = gtk.combo_box_new_text()
		for proc in self.arch_procs['x86']:
			self.proc_combo.append_text(proc)
		self.proc_combo.set_active(0)
		hbox.pack_start(self.proc_combo, expand=False, fill=False, padding=10)
		hbox.pack_start(gtk.Label("Optimizations:"), expand=False, fill=False, padding=0)
		self.optimizations_combo = gtk.combo_box_new_text()
		for opt in self.optimizations:
			self.optimizations_combo.append_text(opt)
		self.optimizations_combo.set_active(0)
		hbox.pack_start(self.optimizations_combo, expand=False, fill=False, padding=10)
		hbox.pack_start(gtk.Label("Custom:"), expand=False, fill=False, padding=0)
		self.custom_cflags_entry = gtk.Entry()
		self.custom_cflags_entry.set_width_chars(25)
		self.custom_cflags_entry.set_text("-pipe")
		hbox.pack_start(self.custom_cflags_entry, expand=False, fill=False, padding=10)
		vert.pack_start(hbox, expand=False, fill=False, padding=5)

		hbox = gtk.HBox(False, 0)
		label = gtk.Label()
		label.set_markup("<b>Other:</b>")
		hbox.pack_start(label, expand=False, fill=False, padding=0)
		vert.pack_start(hbox, expand=False, fill=False, padding=5)

		hbox = gtk.HBox(False, 0)
		self.unstable_packages_check = gtk.CheckButton("Use unstable (~arch)")
		hbox.pack_start(self.unstable_packages_check, expand=False, fill=False, padding=0)
		self.build_binary_check = gtk.CheckButton("Build binary packages")
		hbox.pack_start(self.build_binary_check, expand=False, fill=False, padding=20)
		self.use_distcc_check = gtk.CheckButton("DistCC")
		hbox.pack_start(self.use_distcc_check, expand=False, fill=False, padding=0)
		self.use_ccache_check = gtk.CheckButton("ccache")
		hbox.pack_start(self.use_ccache_check, expand=False, fill=False, padding=20)
		vert.pack_start(hbox, expand=False, fill=False, padding=5)

		hbox = gtk.HBox(False, 0)
		hbox.pack_start(gtk.Label("CHOST:"), expand=False, fill=False, padding=0)
		self.chost_combo = gtk.combo_box_new_text()
#		for chost in GLIUtility.get_chosts(self.controller.client_profile.get_architecture_template()):
#			self.chost_combo.append_text(chost)
#		self.chost_combo.set_active(0)
		hbox.pack_start(self.chost_combo, expand=False, fill=False, padding=10)
		hbox.pack_start(gtk.Label(" "), expand=False, fill=False, padding=15)
		hbox.pack_start(gtk.Label("MAKEOPTS:"), expand=False, fill=False, padding=0)
		self.makeopts_entry = gtk.Entry()
		self.makeopts_entry.set_width_chars(7)
		hbox.pack_start(self.makeopts_entry, expand=False, fill=False, padding=10)
		vert.pack_start(hbox, expand=False, fill=False, padding=5)

		self.add_content(vert)

	def flag_toggled(self, cell, path):
		model = self.treeview.get_model()
		model[path][0] = not model[path][0]
		flag = model[path][1]
		if model[path][0]:
			self.use_flags[flag] = 1
		else:
			if flag in self.use_flags:
				self.use_flags[flag] = 0
		return

	def activate(self):
		self.controller.SHOW_BUTTON_EXIT    = True
		self.controller.SHOW_BUTTON_HELP    = True
		self.controller.SHOW_BUTTON_BACK    = True
		self.controller.SHOW_BUTTON_FORWARD = True
		self.controller.SHOW_BUTTON_FINISH  = False
		self.etc_files = self.controller.install_profile.get_etc_files()
		if not "make.conf" in self.etc_files:
			self.etc_files['make.conf'] = {}	
		self.make_conf_values = self.etc_files['make.conf']
		# Parsing USE
		self.use_flags = {}
		if not self.make_conf_values.has_key('USE') or not self.make_conf_values['USE']:
			self.make_conf_values['USE'] = self.system_use_flags
		for flag in self.make_conf_values['USE'].split(" "):
			if flag.startswith("-"):
				flag = flag[1:]
				self.use_flags[flag] = 0
			else:
				self.use_flags[flag] = 1
		sorted_use = self.use_desc.keys()
		sorted_use.sort()
		self.treedata = gtk.ListStore(gobject.TYPE_BOOLEAN, gobject.TYPE_STRING, gobject.TYPE_STRING)
		for flag in sorted_use:
			if flag in self.use_flags and self.use_flags[flag] == 1:
				self.treedata.append([True, flag, self.use_desc[flag]])
			else:
				self.treedata.append([False, flag, self.use_desc[flag]])
		self.treeview.set_model(self.treedata)
		if self.controller.install_profile.get_grp_install():
			self.treeview.set_sensitive(False)
			self.unstable_packages_check.set_sensitive(False)
			self.unstable_packages_check.set_active(False)
		else:
			self.treeview.set_sensitive(True)
			self.unstable_packages_check.set_sensitive(True)
		# Parsing CFLAGS
		if not self.make_conf_values.has_key('CFLAGS') or not self.make_conf_values['CFLAGS']:
			self.make_conf_values['CFLAGS'] = self.system_cflags
		custom_cflags = ""
		for flag in self.make_conf_values['CFLAGS'].split(" "):
			flag = flag.strip()
			if flag.startswith("-march="):
				equal_pos = flag.find("=")
				arch = flag[equal_pos+1:]
				i = 0
				for proc in self.arch_procs['x86']:
					if proc == arch:
						self.proc_combo.set_active(i)
						break
					i += 1
			elif flag.startswith("-O"):
				i = 0
				for opt in self.optimizations:
					if flag == opt:
						self.optimizations_combo.set_active(i)
						break
					i += 1
			else:
				custom_cflags = custom_cflags + " " + flag
		self.custom_cflags_entry.set_text(custom_cflags.strip())
		# Parsing ACCEPT_KEYWORDS
		if not self.make_conf_values.has_key('ACCEPT_KEYWORDS') or not self.make_conf_values['ACCEPT_KEYWORDS']:
			self.make_conf_values['ACCEPT_KEYWORDS'] = self.system_accept_keywords
		if self.make_conf_values['ACCEPT_KEYWORDS'].find("~x86") != -1:
			self.unstable_packages_check.set_active(True)
		else:
			self.unstable_packages_check.set_active(False)
		# Parsing FEATURES
		if not self.make_conf_values.has_key('FEATURES') or not self.make_conf_values['FEATURES']:
			self.make_conf_values['FEATURES'] = self.system_features
		self.use_distcc_check.set_active(False)
		self.use_ccache_check.set_active(False)
		self.build_binary_check.set_active(False)
		for feature in self.make_conf_values['FEATURES'].split(" "):
			feature = feature.strip()
			if feature == "distcc":
				self.use_distcc_check.set_active(True)
			elif feature == "ccache":
				self.use_ccache_check.set_active(True)
			elif feature == "buildpkg":
				self.build_binary_check.set_active(True)
		# Parsing CHOST
		if not self.make_conf_values.has_key('CHOST') or not self.make_conf_values['CHOST']:
			self.make_conf_values['CHOST'] = self.system_chost
		self.chost_combo.get_model().clear()
		for i, chost in enumerate(GLIUtility.get_chosts(self.controller.client_profile.get_architecture_template())):
			self.chost_combo.append_text(chost)
			if chost == self.make_conf_values['CHOST'] or i == 0:
				self.chost_combo.set_active(i)
		if self.controller.install_profile.get_install_stage() > 1:
			self.chost_combo.set_sensitive(False)
		else:
			self.chost_combo.set_sensitive(True)
		# Parsing MAKEOPTS
		if not self.make_conf_values.has_key('MAKEOPTS') or not self.make_conf_values['MAKEOPTS']:
			self.make_conf_values['MAKEOPTS'] = self.system_makeopts
		self.makeopts_entry.set_text(self.make_conf_values['MAKEOPTS'])

	def deactivate(self):
		temp_use = ""
		sorted_use = self.use_flags.keys()
		sorted_use.sort()
		for flag in sorted_use:
			if self.use_flags[flag]:
				temp_use += " " + flag
			else:
				temp_use += " -" + flag
		self.make_conf_values['USE'] = temp_use
		self.make_conf_values['CFLAGS'] = "-march=" + self.arch_procs['x86'][self.proc_combo.get_active()] + " " + self.optimizations[self.optimizations_combo.get_active()] + " " + self.custom_cflags_entry.get_text()
		if self.unstable_packages_check.get_active():
			self.make_conf_values['ACCEPT_KEYWORDS'] = "~x86"
		else:
			self.make_conf_values['ACCEPT_KEYWORDS'] = ""
		temp_features = ""
		if self.build_binary_check.get_active():
			temp_features += "buildpkg "
		if self.use_distcc_check.get_active():
			temp_features += "distcc "
		if self.use_ccache_check.get_active():
			temp_features += "ccache "
		self.make_conf_values['FEATURES'] = temp_features.strip()
		if self.controller.install_profile.get_install_stage() > 1:
			if 'CHOST' in self.make_conf_values:
				del self.make_conf_values['CHOST']
		else:
			self.make_conf_values['CHOST'] = GLIUtility.get_chosts(self.controller.client_profile.get_architecture_template())[self.chost_combo.get_active()]
		self.make_conf_values['MAKEOPTS'] = self.makeopts_entry.get_text()
		self.etc_files['make.conf'] = self.make_conf_values
		self.controller.install_profile.set_etc_files(self.etc_files)
		return True
