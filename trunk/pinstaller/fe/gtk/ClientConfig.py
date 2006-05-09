# Copyright 1999-2005 Gentoo Foundation
# This source code is distributed under the terms of version 2 of the GNU
# General Public License as published by the Free Software Foundation, a copy
# of which can be found in the main directory of this project.

import gtk
import GLIScreen
import GLIUtility
from gettext import gettext as _

class Panel(GLIScreen.GLIScreen):

	title = _("Pre-install Configuration")
	_helptext = """
<b><u>Pre-install Config - aka Client Configuration</u></b>

If your network is already set up and you can ping www.gentoo.org, then the
checkbox labeled "My network is already set up and running (or no network)"
will be checked. In that case you do not need to set up any pre-install
networking.  If it is not, you need to set up your networking. If you are not
connected to a network, you should check that box, so the installer does not try
to find a DHCP server.

Note: If you intend to use wireless to connect to the Internet from the Livecd,
you will need to set up your connection before starting the installer.  See the
Wireless Networking guide at
http://www.gentoo.org/doc/en/handbook/handbook-x86.xml?part=4&amp;chap=4

To connect to the Internet you will need to configure one network device,
usually eth0.  In most cases you can select DHCP unless you have a specific IP
address or network configuration where you need to give Static information.

In the rare case that you need to connect to the Internet through a proxy, there
are three proxy types to enter.

In the Misc. tab there are a few customizable items:

Chroot directory:  This is the directory the the installer mounts your /
partition to and then chroots to in order to do the installation.  It is best to
not change this unless you need to.

Logfile:  The path and filename of the installer logfile.  The default is
recommended.

SSH:  If you want to start sshd to allow remote access to your machine during
the installation, select Yes, otherwise No.  No is recommended since it is not
necessary for an installation.

Root password: This sets the root password for the <i>Livecd environment <b>only</b></i>.
If you chose Yes for SSH then you will need to enter a root password or you will
not be able to login remotely.

Kernel Modules:  If you have additional modules (ex. some rare networking module
that didn't autoload) you need to load that are not in the Loaded modules list
on the right, you can enter them here.  

Verbose logging:  This adds a lot of debugging information to the logfiles,
which is useful for reporting bugs.

Install mode:  You want "Normal".  the Chroot mode is still under development
and will not leave you with a bootable system.
"""

	def __init__(self, controller):
		GLIScreen.GLIScreen.__init__(self, controller)
		vert = gtk.VBox(False, 0)
		vert.set_border_width(10)

		content_str = _("""On this screen, you will set all your pre-install options such as networking,
		chroot directory, logfile location, architecture, etc.""")

		content_label = gtk.Label(content_str)
		vert.pack_start(content_label, expand=False, fill=False, padding=5)

		self.notebook = gtk.Notebook()

		basicbox = gtk.VBox(False, 0)
		basicbox.set_border_width(10)
		hbox = gtk.HBox(False, 0)
		tmplabel = gtk.Label()
		tmplabel.set_markup("<b><u>" + _("Network setup (for install only):") + "</u></b>")
		hbox.pack_start(tmplabel, expand=False, fill=False, padding=0)
		basicbox.pack_start(hbox, expand=False, fill=False, padding=0)
		hbox = gtk.HBox(False, 0)
		self.already_setup_check = gtk.CheckButton()
		self.already_setup_check.set_active(False)
		self.already_setup_check.connect("toggled", self.already_setup_toggled)
		hbox.pack_start(self.already_setup_check, expand=False, fill=False, padding=0)
		hbox.pack_start(gtk.Label("My network is already setup and running (or no network)"), expand=False, fill=False, padding=10)
		basicbox.pack_start(hbox, expand=False, fill=False, padding=3)
		hbox = gtk.HBox(False, 0)
		hbox.pack_start(gtk.Label(_("Interface:")), expand=False, fill=False, padding=0)
		self.interface_combo = gtk.combo_box_entry_new_text()
		self.interface_combo.get_child().set_width_chars(9)
		self.interface_combo.connect("changed", self.interface_changed)
		self.interfaces = GLIUtility.get_eth_devices()
		for device in self.interfaces:
			self.interface_combo.append_text(device)
		hbox.pack_start(self.interface_combo, expand=False, fill=False, padding=10)
		basicbox.pack_start(hbox, expand=False, fill=False, padding=7)
		hbox = gtk.HBox(False, 0)
		self.basic_dhcp_radio = gtk.RadioButton(label=_("DHCP"))
		self.basic_dhcp_radio.connect("toggled", self.dhcp_static_toggled, "dhcp")
		hbox.pack_start(self.basic_dhcp_radio, expand=False, fill=False, padding=0)
		basicbox.pack_start(hbox, expand=False, fill=False, padding=0)
		hbox = gtk.HBox(False, 0)
		tmptable = gtk.Table(rows=1, columns=3)
		tmptable.set_col_spacings(6)
		tmptable.set_row_spacings(5)
		tmptable.attach(gtk.Label("        "), 0, 1, 0, 1)
		tmplabel = gtk.Label(_("DHCP options:"))
		tmplabel.set_alignment(0.0, 0.5)
		tmptable.attach(tmplabel, 1, 2, 0, 1)
		self.dhcp_options_entry = gtk.Entry()
		self.dhcp_options_entry.set_width_chars(35)
		tmptable.attach(self.dhcp_options_entry, 2, 3, 0, 1)
		hbox.pack_start(tmptable, expand=False, fill=False, padding=0)
		basicbox.pack_start(hbox, expand=False, fill=False, padding=3)
		hbox = gtk.HBox(False, 0)
		self.basic_static_radio = gtk.RadioButton(group=self.basic_dhcp_radio, label=_("Static"))
		self.basic_static_radio.connect("toggled", self.dhcp_static_toggled, "static")
		hbox.pack_start(self.basic_static_radio, expand=False, fill=False, padding=0)
		basicbox.pack_start(hbox, expand=False, fill=False, padding=3)
		hbox = gtk.HBox(False, 0)
		tmptable = gtk.Table(rows=5, columns=1)
		tmptable.set_col_spacings(6)
		tmptable.set_row_spacings(5)
		tmptable.attach(gtk.Label("        "), 0, 1, 0, 1)
		tmplabel = gtk.Label(_("IP address:"))
		tmplabel.set_alignment(0.0, 0.5)
		tmptable.attach(tmplabel, 1, 2, 0, 1)
		self.ip_address_entry = gtk.Entry()
		self.ip_address_entry.set_width_chars(20)
		tmptable.attach(self.ip_address_entry, 2, 3, 0, 1)
		tmptable.attach(gtk.Label("        "), 3, 4, 0, 1)
		tmplabel = gtk.Label(_("Netmask:"))
		tmplabel.set_alignment(0.0, 0.5)
		tmptable.attach(tmplabel, 4, 5, 0, 1)
		self.netmask_entry = gtk.Entry()
		self.netmask_entry.set_width_chars(20)
		tmptable.attach(self.netmask_entry, 5, 6, 0, 1)
		tmplabel = gtk.Label(_("Broadcast:"))
		tmplabel.set_alignment(0.0, 0.5)
		tmptable.attach(tmplabel, 1, 2, 1, 2)
		self.broadcast_entry = gtk.Entry()
		self.broadcast_entry.set_width_chars(20)
		tmptable.attach(self.broadcast_entry, 2, 3, 1, 2)
		tmplabel = gtk.Label(_("Gateway:"))
		tmplabel.set_alignment(0.0, 0.5)
		tmptable.attach(tmplabel, 4, 5, 1, 2)
		self.gateway_entry = gtk.Entry()
		self.gateway_entry.set_width_chars(20)
		tmptable.attach(self.gateway_entry, 5, 6, 1, 2)
		tmplabel = gtk.Label(_("DNS servers:"))
		tmplabel.set_alignment(0.0, 0.5)
		tmptable.attach(tmplabel, 1, 2, 2, 3)
		self.dns_entry = gtk.Entry()
		self.dns_entry.set_width_chars(20)
		tmptable.attach(self.dns_entry, 2, 3, 2, 3)
		hbox.pack_start(tmptable, expand=False, fill=False, padding=0)
		basicbox.pack_start(hbox, expand=False, fill=False, padding=3)
		hbox = gtk.HBox(False, 0)
		tmptable = gtk.Table(rows=1, columns=5)
		tmptable.set_col_spacings(6)
		tmptable.set_row_spacings(5)
#		tmptable.attach(gtk.Label("   "), 0, 2, 0, 1)
		tmplabel = gtk.Label()
		tmplabel.set_markup("<b><u>" + _("Proxies:") + "</u></b>")
		tmplabel.set_alignment(0.0, 0.5)
		tmptable.attach(tmplabel, 0, 5, 0, 1)

		tmpbox = gtk.HBox(False, 5)
		tmplabel = gtk.Label(_("HTTP:"))
		tmplabel.set_alignment(0, 0.5)
#		tmptable.attach(tmplabel, 0, 1, 2, 3)
		tmpbox.pack_start(tmplabel, expand=False, fill=False)
		self.http_proxy_entry = gtk.Entry()
		tmpbox.pack_start(self.http_proxy_entry, expand=False, fill=False)
#		tmptable.attach(self.http_proxy_entry, 1, 2, 2, 3)
		tmptable.attach(tmpbox, 0, 1, 1, 2)
		tmptable.attach(gtk.Label("    "), 1, 2, 1, 2)

		tmpbox = gtk.HBox(False, 5)
		tmplabel = gtk.Label(_("FTP:"))
		tmplabel.set_alignment(0, 0.5)
#		tmptable.attach(tmplabel, 0, 1, 3, 4)
		tmpbox.pack_start(tmplabel, expand=False, fill=False)
		self.ftp_proxy_entry = gtk.Entry()
		tmpbox.pack_start(self.ftp_proxy_entry, expand=False, fill=False)
#		tmptable.attach(self.ftp_proxy_entry, 1, 2, 3, 4)
		tmptable.attach(tmpbox, 2, 3, 1, 2)
		tmptable.attach(gtk.Label("    "), 3, 4, 1, 2)

		tmpbox = gtk.HBox(False, 5)
		tmplabel = gtk.Label(_("Rsync:"))
		tmplabel.set_alignment(0, 0.5)
#		tmptable.attach(tmplabel, 0, 1, 4, 5)
		tmpbox.pack_start(tmplabel, expand=False, fill=False)
		self.rsync_proxy_entry = gtk.Entry()
		tmpbox.pack_start(self.rsync_proxy_entry, expand=False, fill=False)
#		tmptable.attach(self.rsync_proxy_entry, 1, 2, 4, 5)
		tmptable.attach(tmpbox, 4, 5, 1, 2)

		hbox.pack_start(tmptable, expand=False, fill=False, padding=0)
		basicbox.pack_start(hbox, expand=False, fill=False, padding=3)
		self.notebook.append_page(basicbox, gtk.Label(_("Networking")))

		advbox = gtk.VBox(False, 0)
		advbox.set_border_width(10)
		hbox = gtk.HBox(False, 0)
		tmptable = gtk.Table(rows=5, columns=1)
		tmptable.set_col_spacings(6)
		tmptable.set_row_spacings(5)
		tmplabel = gtk.Label()
		tmplabel.set_markup("<b><u>" + _("Directories and logfiles:") + "</u></b>")
		tmplabel.set_alignment(0.0, 0.5)
		tmptable.attach(tmplabel, 0, 2, 0, 1)
		tmplabel = gtk.Label(_("Chroot directory:"))
		tmplabel.set_alignment(0.0, 0.5)
		tmptable.attach(tmplabel, 0, 1, 1, 2)
		self.chroot_dir_entry = gtk.Entry()
		self.chroot_dir_entry.set_width_chars(25)
		tmptable.attach(self.chroot_dir_entry, 1, 2, 1, 2)
		tmplabel = gtk.Label(_("Logfile:"))
		tmplabel.set_alignment(0.0, 0.5)
		tmptable.attach(tmplabel, 0, 1, 2, 3)
		self.logfile_entry = gtk.Entry()
		self.logfile_entry.set_width_chars(25)
		tmptable.attach(self.logfile_entry, 1, 2, 2, 3)
		tmplabel = gtk.Label("   ")
		tmptable.attach(tmplabel, 0, 1, 3, 4)
		tmplabel = gtk.Label()
		tmplabel.set_markup("<b><u>" + _("SSH:") + "</u></b>")
		tmplabel.set_alignment(0.0, 0.5)
		tmptable.attach(tmplabel, 0, 2, 4, 5)
		tmplabel = gtk.Label(_("Start SSHd:"))
		tmplabel.set_alignment(0.0, 0.5)
		tmptable.attach(tmplabel, 0, 1, 5, 6)
		tmphbox = gtk.HBox(False, 0)
		self.sshd_yes_radio = gtk.RadioButton(label=_("Yes"))
		tmphbox.pack_start(self.sshd_yes_radio, expand=False, fill=False, padding=0)
		self.sshd_no_radio = gtk.RadioButton(group=self.sshd_yes_radio, label=_("No"))
		tmphbox.pack_start(self.sshd_no_radio, expand=False, fill=False, padding=15)
		tmptable.attach(tmphbox, 1, 2, 5, 6)
		tmplabel = gtk.Label(_("Root password:"))
		tmplabel.set_alignment(0.0, 0.5)
		tmptable.attach(tmplabel, 0, 1, 6, 7)
		self.root_password_entry = gtk.Entry()
		self.root_password_entry.set_width_chars(25)
		self.root_password_entry.set_visibility(False)
		tmptable.attach(self.root_password_entry, 1, 2, 6, 7, xoptions=0)
		tmplabel = gtk.Label(_("Verify root password:"))
		tmplabel.set_alignment(0.0, 0.5)
		tmptable.attach(tmplabel, 0, 1, 7, 8)
		self.verify_root_password_entry = gtk.Entry()
		self.verify_root_password_entry.set_width_chars(25)
		self.verify_root_password_entry.set_visibility(False)
		tmptable.attach(self.verify_root_password_entry, 1, 2, 7, 8, xoptions=0)
		tmplabel = gtk.Label("   ")
		tmptable.attach(tmplabel, 0, 1, 8, 9)
		tmplabel = gtk.Label()
#		tmplabel.set_markup("<b><u>" + _("Kernel modules:") + "</u></b>")
		tmplabel.set_markup("<b><u>" + _("Other:") + "</u></b>")
		tmplabel.set_alignment(0.0, 0.5)
		tmptable.attach(tmplabel, 0, 2, 9, 10)
		tmplabel = gtk.Label(_("Kernel modules:"))
		tmplabel.set_alignment(0.0, 0.5)
		tmptable.attach(tmplabel, 0, 1, 10, 11)
		self.modules_entry = gtk.Entry()
		self.modules_entry.set_width_chars(25)
		tmptable.attach(self.modules_entry, 1, 2, 10, 11)
#		tmplabel = gtk.Label("   ")
#		tmptable.attach(tmplabel, 0, 1, 11, 12)
#		tmplabel = gtk.Label()
#		tmplabel.set_markup("<b><u>" + _("Debug:") + "</u></b>")
#		tmplabel.set_alignment(0.0, 0.5)
#		tmptable.attach(tmplabel, 0, 2, 12, 13)
		tmplabel = gtk.Label(_("Verbose logging:"))
		tmplabel.set_alignment(0.0, 0.5)
		tmptable.attach(tmplabel, 0, 1, 11, 12)
		tmphbox = gtk.HBox(False, 0)
		self.verbose_no_radio = gtk.RadioButton(label=_("No"))
		tmphbox.pack_start(self.verbose_no_radio, expand=False, fill=False, padding=0)
		self.verbose_yes_radio = gtk.RadioButton(group=self.verbose_no_radio, label=_("Yes"))
		tmphbox.pack_start(self.verbose_yes_radio, expand=False, fill=False, padding=15)
		tmptable.attach(tmphbox, 1, 2, 11, 12)
		tmplabel = gtk.Label(_("Install mode:"))
		tmplabel.set_alignment(0.0, 0.5)
		tmptable.attach(tmplabel, 0, 1, 12, 13)
		self.install_mode_combo = gtk.combo_box_new_text()
		self._install_modes = ( "Normal", "Chroot" )
		for install_mode in self._install_modes:
			self.install_mode_combo.append_text(install_mode)
		self.install_mode_combo.set_active(0)
		tmptable.attach(self.install_mode_combo, 1, 2, 12, 13)

		hbox.pack_start(tmptable, expand=False, fill=False, padding=0)

		# Currently loaded modules
		loaded_mod_frame = gtk.Frame(label="Loaded modules")
		loaded_mod_frame.set_size_request(200, -1)
		module_list_box = gtk.VBox(False, 3)
		module_list_box.set_border_width(7)
		module_scroll = gtk.ScrolledWindow()
		module_scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
		module_scroll.set_shadow_type(gtk.SHADOW_NONE)
		module_viewport = gtk.Viewport()
		module_viewport.set_shadow_type(gtk.SHADOW_NONE)
		module_viewport.add(module_list_box)
		module_scroll.add(module_viewport)
		loaded_mod_frame.add(module_scroll)
		loaded_modules = GLIUtility.spawn(r"lsmod | grep -v ^Module | cut -d ' ' -f 1", return_output=True)[1].strip().split("\n")
		for module in loaded_modules:
			tmplabel = gtk.Label(module)
			tmplabel.set_alignment(0.0, 0.5)
			module_list_box.pack_start(tmplabel, expand=False, fill=False, padding=0)
		hbox.pack_end(loaded_mod_frame, expand=False, fill=False, padding=5)

		advbox.pack_start(hbox, expand=False, fill=False, padding=0)
		self.notebook.append_page(advbox, gtk.Label(_("Misc.")))

		vert.pack_start(self.notebook, expand=True, fill=True, padding=0)

		self.add_content(vert)

	def interface_changed(self, combobox):
		hw_addr, ip_addr, mask, bcast, gw, up = ("", "", "", "", "", "")
		interface = combobox.child.get_text()
		try:
			if interface.startswith("eth"):
				hw_addr, ip_addr, mask, bcast, gw, up = GLIUtility.get_eth_info(interface[-1:])
		except:
			pass
		self.ip_address_entry.set_text(ip_addr)
		self.netmask_entry.set_text(mask)
		self.broadcast_entry.set_text(bcast)
#		self.gateway_entry.set_text(gw)

	def dhcp_static_toggled(self, radiobutton, data=None):
		if radiobutton.get_active():
			# This one was just toggled ON
			if data == "dhcp":
				self.ip_address_entry.set_sensitive(False)
				self.netmask_entry.set_sensitive(False)
				self.broadcast_entry.set_sensitive(False)
				self.gateway_entry.set_sensitive(False)
				self.dns_entry.set_sensitive(False)
				self.dhcp_options_entry.set_sensitive(True)
			else:
				self.ip_address_entry.set_sensitive(True)
				self.netmask_entry.set_sensitive(True)
				self.broadcast_entry.set_sensitive(True)
				self.gateway_entry.set_sensitive(True)
				self.dns_entry.set_sensitive(True)
				self.dhcp_options_entry.set_sensitive(False)

	def already_setup_toggled(self, widget):
		if self.already_setup_check.get_active():
			self.interface_combo.set_sensitive(False)
			self.basic_dhcp_radio.set_sensitive(False)
			self.basic_static_radio.set_sensitive(False)
			self.ip_address_entry.set_sensitive(False)
			self.netmask_entry.set_sensitive(False)
			self.broadcast_entry.set_sensitive(False)
			self.gateway_entry.set_sensitive(False)
			self.dns_entry.set_sensitive(False)
			self.dhcp_options_entry.set_sensitive(False)
		else:
			self.interface_combo.set_sensitive(True)
			self.basic_dhcp_radio.set_sensitive(True)
			self.basic_static_radio.set_sensitive(True)
			if self.basic_static_radio.get_active():
				self.ip_address_entry.set_sensitive(True)
				self.netmask_entry.set_sensitive(True)
				self.broadcast_entry.set_sensitive(True)
				self.gateway_entry.set_sensitive(True)
				self.dns_entry.set_sensitive(True)
			else:
				self.dhcp_options_entry.set_sensitive(True)

	def activate(self):
		self.controller.SHOW_BUTTON_EXIT    = True
		self.controller.SHOW_BUTTON_HELP    = True
		self.controller.SHOW_BUTTON_BACK    = False
		self.controller.SHOW_BUTTON_FORWARD = True
		self.controller.SHOW_BUTTON_FINISH  = False

		interface = self.controller.client_profile.get_network_interface()
		ip = self.controller.client_profile.get_network_ip()
		if not interface:
			self.interface_combo.set_active(0)
		else:
			self.interface_combo.child.set_text(interface)
			for i, dev in enumerate(self.interfaces):
				if dev == interface:
					self.interface_combo.set_active(i)
		if ip == "dhcp" or not ip:
			self.basic_dhcp_radio.set_active(True)
			self.dhcp_static_toggled(self.basic_dhcp_radio, "dhcp")
			self.dhcp_options_entry.set_text(self.controller.client_profile.get_network_dhcp_options())
		else:
			self.basic_static_radio.set_active(True)
		self.chroot_dir_entry.set_text(self.controller.client_profile.get_root_mount_point())
		self.logfile_entry.set_text(self.controller.client_profile.get_log_file())
		if self.controller.client_profile.get_enable_ssh():
			self.sshd_yes_radio.set_active(True)
		else:
			self.sshd_no_radio.set_active(True)
		dns_servers = GLIUtility.spawn(r"grep -e '^nameserver' /etc/resolv.conf | sed -e 's:^nameserver ::'", return_output=True)[1].strip().split('\n')
		dns_servers = " ".join(dns_servers)
		self.dns_entry.set_text(dns_servers)
		self.gateway_entry.set_text(GLIUtility.spawn(r"/sbin/route -n | grep -e '^0\.0\.0\.0' | sed -e 's:^0\.0\.0\.0 \+::' -e 's: \+.\+$::'", return_output=True)[1].strip())
		self.modules_entry.set_text(" ".join(self.controller.client_profile.get_kernel_modules()))
		if self.controller.client_profile.get_verbose():
			self.verbose_yes_radio.set_active(True)
		else:
			self.verbose_no_radio.set_active(True)
		if GLIUtility.ping("www.gentoo.org"):
			self.already_setup_check.set_active(True)

	def deactivate(self):
		self.controller.client_profile.set_network_interface(None, self.interface_combo.get_child().get_text(), None)
		if self.already_setup_check.get_active():
			self.controller.client_profile.set_network_type(None, "none", None)
		else:
			if self.basic_dhcp_radio.get_active():
				self.controller.client_profile.set_network_type(None, "dhcp", None)
				self.controller.client_profile.set_network_dhcp_options(None, self.dhcp_options_entry.get_text(), None)
			else:
				self.controller.client_profile.set_network_type(None, "static", None)
				self.controller.client_profile.set_network_ip(None, self.ip_address_entry.get_text(), None)
				self.controller.client_profile.set_network_netmask(None, self.netmask_entry.get_text(), None)
				self.controller.client_profile.set_network_broadcast(None, self.broadcast_entry.get_text(), None)
				self.controller.client_profile.set_network_gateway(None, self.gateway_entry.get_text(), None)
				self.controller.client_profile.set_dns_servers(None, self.dns_entry.get_text(), None)
		self.controller.client_profile.set_http_proxy(None, self.http_proxy_entry.get_text(), None)
		self.controller.client_profile.set_ftp_proxy(None, self.ftp_proxy_entry.get_text(), None)
		self.controller.client_profile.set_rsync_proxy(None, self.rsync_proxy_entry.get_text(), None)
		self.controller.client_profile.set_root_mount_point(None, self.chroot_dir_entry.get_text(), None)
		self.controller.client_profile.set_log_file(None, self.logfile_entry.get_text(), None)
		self.controller.client_profile.set_enable_ssh(None, self.sshd_yes_radio.get_active(), None)
		if self.root_password_entry.get_text() == self.verify_root_password_entry.get_text():
			self.controller.client_profile.set_root_passwd(None, GLIUtility.hash_password(self.root_password_entry.get_text()), None)
		self.controller.client_profile.set_kernel_modules(None, self.modules_entry.get_text(), None)
		self.controller.client_profile.set_verbose(None, self.verbose_yes_radio.get_active(), None)
		arch = GLIUtility.spawn(r"uname -m | sed -e 's:i[3-6]86:x86:' -e 's:x86_64:amd64:' -e 's:parisc:hppa:'", return_output=True)[1].strip()
		self.controller.client_profile.set_architecture_template(None, arch, None)
		self.controller.client_profile.set_install_mode(None, self._install_modes[self.install_mode_combo.get_active()].lower(), None)

		self.controller.cc.set_configuration(self.controller.client_profile)
		self.controller.cc.start_pre_install()
				
		return True
