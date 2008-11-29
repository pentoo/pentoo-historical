# Copyright 1999-2005 Gentoo Foundation
# This source code is distributed under the terms of version 2 of the GNU
# General Public License as published by the Free Software Foundation, a copy
# of which can be found in the main directory of this project.

import gtk
import GLIScreen

class Panel(GLIScreen.GLIScreen):

	title = "Kernel Sources"
	active_selection = None
	kernel_sources = {}
	sources = [("gentoo-sources", "These are the vanilla sources patched with the Gentoo patchset. These are generally considered stable."),
	           ("vanilla-sources", "These are the kernel sources straight from kernel.org without patches (except where necessary)"),
	           ("hardened-sources", "These are the vanilla sources patched with the hardened patchset. This results in a more secure system. Do not use these unless you have read the hardened guide first."),
#	           ("grsec-sources", "These are the vanilla sources patched with the grsecurity patchset. Do not use these unless you wear a tinfoil hat and think the government is out to get you."),
	           ("livecd-kernel", "This will install the LiveCD's kernel/initrd into your new system. Use this option to get your system up and running quickly. You should not tell the installer to emerge any packages that require kernel sources as they won't be present.")]
	_helptext = """
<b><u>Choosing a Kernel</u></b>

The core around which all distributions are built is the Linux kernel. It is the
layer between the user programs and your system hardware. Gentoo provides its
users several possible kernel sources. A full listing with description is
available at the Gentoo Kernel Guide at
http://www.gentoo.org/doc/en/gentoo-kernel.xml.

For x86-based systems we have, amongst other kernels, vanilla-sources (the
default kernel source as developed by the linux-kernel developers), 
gentoo-sources (kernel source patched with performance-enhancing features) (less
stable), 
 
livecd-kernel:  This will copy the currently running kernel over to the new
system, just as if genkernel had created your kernel.  This is generally
recommended since it is much faster than genkernel and just as good, except that
once your system is installed you will eventually need to recreate a kernel
again.

If you're not concerned about time, select vanilla-sources or gentoo-sources if
you're feeling lucky.

For non-livecd-kernel sources, selecting Enable Bootsplash gives you a colorful
background image in a frame buffer.
"""

	def __init__(self, controller):
		GLIScreen.GLIScreen.__init__(self, controller)
		vert = gtk.VBox(False, 0)
		vert.set_border_width(10)

		content_str = """Here, you will select which kernel sources package you would like to use. Each option has
a brief description beside it.
"""
		content_label = gtk.Label(content_str)
		vert.pack_start(content_label, expand=False, fill=False, padding=0)

		for source in self.sources:
			parent = None
			name, descr = source
			if name != self.sources[0][0]:
				parent = self.kernel_sources[self.sources[0][0]]
			self.kernel_sources[name] = gtk.RadioButton(parent, name)
			self.kernel_sources[name].set_name(name)
			self.kernel_sources[name].connect("toggled", self.kernel_selected, name)
			self.kernel_sources[name].set_size_request(150, -1)
			hbox = gtk.HBox(False, 0)
			hbox.pack_start(self.kernel_sources[name], expand=False, fill=False, padding=0)
			tmplabel = gtk.Label(descr)
			tmplabel.set_line_wrap(True)
			hbox.pack_start(tmplabel, expand=False, fill=False, padding=20)
			vert.pack_start(hbox, expand=False, fill=False, padding=10)

		hbox = gtk.HBox(False, 0)
		self.bootsplash_check = gtk.CheckButton("Enable bootsplash")
		self.bootsplash_check.set_size_request(150, -1)
		hbox.pack_start(self.bootsplash_check, expand=False, fill=False, padding=0)
		tmplabel = gtk.Label("This enables a colorful background image during system boot.")
		tmplabel.set_line_wrap(True)
		hbox.pack_start(tmplabel, expand=False, fill=False, padding=20)
		vert.pack_start(hbox, expand=False, fill=False, padding=10)

		self.add_content(vert)

	def kernel_selected(self, widget, data=None):
		self.active_selection = data

	def activate(self):
		self.controller.SHOW_BUTTON_EXIT    = True
		self.controller.SHOW_BUTTON_HELP    = True
		self.controller.SHOW_BUTTON_BACK    = True
		self.controller.SHOW_BUTTON_FORWARD = True
		self.controller.SHOW_BUTTON_FINISH  = False
		self.active_selection = self.controller.install_profile.get_kernel_source_pkg() or "gentoo-sources"
		self.kernel_sources[self.active_selection].set_active(True)
		self.bootsplash_check.set_active(self.controller.install_profile.get_kernel_bootsplash())

	def deactivate(self):
		self.controller.install_profile.set_kernel_source_pkg(None, self.active_selection, None)
		# For now
		self.controller.install_profile.set_kernel_build_method(None, "genkernel", None)
		self.controller.install_profile.set_kernel_bootsplash(None, self.bootsplash_check.get_active(), None)
		if self.bootsplash_check.get_active() and not self.controller.install_profile.get_bootloader_kernel_args():
			proc_cmdline = open("/proc/cmdline", "r")
			cmdline = proc_cmdline.readline().strip()
			proc_cmdline.close()
			vga = None
			splash = None
			for x in cmdline.split(" "):
				parts = x.split("=")
				if len(parts) < 2: continue
				if parts[0] == "vga":
					vga = parts[1]
				elif parts[0] == "splash":
					splash = parts[1]
			self.controller.install_profile.set_bootloader_kernel_args(None, "vga=%s splash=%s CONSOLE=/dev/tty1 quiet" % (vga, splash), None)
		return True
