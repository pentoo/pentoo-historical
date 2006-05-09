"""
# Copyright 1999-2005 Gentoo Foundation
# This source code is distributed under the terms of version 2 of the GNU
# General Public License as published by the Free Software Foundation, a copy
# of which can be found in the main directory of this project.
Gentoo Linux Installer

$Id: GLIInstallProfile.py,v 1.91 2006/04/16 02:25:29 agaffney Exp $

The GLI module contains all classes used in the Gentoo Linux Installer (or GLI).
The InstallProfile contains all information related to the new system to be
installed.

PROCEDURE TO ADD NEW VARIABLES:
	1. Add a handler to the list.  If the variable has children make sure you do it right.
	   Look at the existing structure to get an idea.
	2. Create a section for the two or three functions.
	3. Create the get_variable_name and set_variable_name functions.
	   Ensure the set function has correct error checking.
	4. If a simple value, add to the list in the general serialize() function.
	   If more complex add a serialize_variable_name to the list of special cases.
	   Then add the serialize_variable_name function to the section for the variable.
"""

import string
import xml.sax
import os
import GLIUtility
import SimpleXMLParser
import xml.dom.minidom
import GLIStorageDevice
from GLIException import *

##
# This class contains all the settings used during the install
class InstallProfile:
	"""
	An object representation of a profile.
	InstallProfile is an object representation of a parsed installation
	profile file.
	"""

	##
	# Initializes all variables to default values and adds handlers.
	def __init__(self):

		# Configuration information - profile data
		# All variables must be declared here with a default value to ensure
		# the XML will correctly serialize.
		self._cron_daemon_pkg = "vixie-cron"
		self._logging_daemon_pkg = "syslog-ng"
		self._boot_device = ""
		self._boot_loader_mbr = True
		self._boot_loader_pkg = ""
		self._kernel_modules = []
		self._kernel_config_uri = ""
		self._kernel_build_method = "genkernel"
		self._bootloader_kernel_args = ""
		self._kernel_initrd = True
		self._kernel_bootsplash = False
		self._kernel_source_pkg = "livecd-kernel"
		self._users = []
		self._root_pass_hash = ""
		self._time_zone = "UTC"
		self._stage_tarball_uri = ""
		self._install_stage = 3
		self._portage_tree_sync_type = "sync"
		self._portage_tree_snapshot_uri = ""
		self._domainname = "localdomain"
		self._hostname = "localhost"
		self._http_proxy = ""
		self._ftp_proxy = ""
		self._rsync_proxy = ""
		self._nisdomainname = ""
		self._partition_tables = {}
		self._network_mounts = []
		self._temp_partition_table = []
		self._network_interfaces = {}
		self._make_conf = {}
#		self._rc_conf = {}
		self._install_rp_pppoe = False
		self._install_pcmcia_cs = False
		self._dns_servers = ()
		self._default_gateway = ()
		self._install_packages = ()
		self._services = ()
		self._mta_pkg = ""
		self._grp_install = False
		self._post_install_script_uri = ""
		self._etc_files = {}
		self._temp_etc_file = {}
		self._dynamic_stage3 = False
		self._install_distcc = False
		self.xmldoc = ""

		# Parser handler calls.  For each XML attribute and children of that attribute, a handler is needed.
		self._parser = SimpleXMLParser.SimpleXMLParser()
		self._parser.addHandler('gli-profile/bootloader', self.set_boot_loader_pkg)
		self._parser.addHandler('gli-profile/boot-device', self.set_boot_device)
		self._parser.addHandler('gli-profile/bootloader-kernel-args', self.set_bootloader_kernel_args)
		self._parser.addHandler('gli-profile/bootloader-mbr', self.set_boot_loader_mbr)
		self._parser.addHandler('gli-profile/cron-daemon', self.set_cron_daemon_pkg)
		self._parser.addHandler('gli-profile/default-gateway', self.set_default_gateway)
		self._parser.addHandler('gli-profile/dns-servers', self.set_dns_servers)
		self._parser.addHandler('gli-profile/domainname', self.set_domainname)
		self._parser.addHandler('gli-profile/dynamic-stage3', self.set_dynamic_stage3)
		self._parser.addHandler('gli-profile/etc-files/file', self.add_etc_files_file, call_on_null=True)
		self._parser.addHandler('gli-profile/etc-files/file/entry', self.add_etc_files_file_entry, call_on_null=True)
		self._parser.addHandler('gli-profile/ftp-proxy', self.set_ftp_proxy)
		self._parser.addHandler('gli-profile/grp-install', self.set_grp_install)
		self._parser.addHandler('gli-profile/hostname', self.set_hostname)
		self._parser.addHandler('gli-profile/http-proxy', self.set_http_proxy)
		self._parser.addHandler('gli-profile/install-distcc', self.set_install_distcc)
		self._parser.addHandler('gli-profile/install-packages', self.set_install_packages)
		self._parser.addHandler('gli-profile/install-pcmcia-cs', self.set_install_pcmcia_cs)
		self._parser.addHandler('gli-profile/install-rp-pppoe', self.set_install_rp_pppoe)
		self._parser.addHandler('gli-profile/install-stage', self.set_install_stage)
		self._parser.addHandler('gli-profile/kernel-bootsplash', self.set_kernel_bootsplash)
		self._parser.addHandler('gli-profile/kernel-build-method', self.set_kernel_build_method)
		self._parser.addHandler('gli-profile/kernel-config', self.set_kernel_config_uri)
		self._parser.addHandler('gli-profile/kernel-initrd', self.set_kernel_initrd)
		self._parser.addHandler('gli-profile/kernel-modules', self.set_kernel_modules)
		self._parser.addHandler('gli-profile/kernel-source', self.set_kernel_source_pkg)
		self._parser.addHandler('gli-profile/logging-daemon', self.set_logging_daemon_pkg)
#		self._parser.addHandler('gli-profile/make-conf/variable', self.make_conf_add_var)
		self._parser.addHandler('gli-profile/mta', self.set_mta_pkg)
		self._parser.addHandler('gli-profile/network-interfaces/device', self.add_network_interface)
		self._parser.addHandler('gli-profile/network-mounts/netmount', self.add_netmount, call_on_null=True)
		self._parser.addHandler('gli-profile/nisdomainname', self.set_nisdomainname)
		self._parser.addHandler('gli-profile/partitions/device', self.add_partitions_device, call_on_null=True)
		self._parser.addHandler('gli-profile/partitions/device/partition', self.add_partitions_device_partition, call_on_null=True)
		self._parser.addHandler('gli-profile/portage-snapshot', self.set_portage_tree_snapshot_uri)
		self._parser.addHandler('gli-profile/portage-tree-sync', self.set_portage_tree_sync_type)
		self._parser.addHandler('gli-profile/post-install-script-uri', self.set_post_install_script_uri)
#		self._parser.addHandler('gli-profile/rc-conf/variable', self.rc_conf_add_var)
		self._parser.addHandler('gli-profile/root-pass-hash', self.set_root_pass_hash)
		self._parser.addHandler('gli-profile/rsync-proxy', self.set_rsync_proxy)
		self._parser.addHandler('gli-profile/services', self.set_services)
		self._parser.addHandler('gli-profile/stage-tarball', self.set_stage_tarball_uri)
		self._parser.addHandler('gli-profile/time-zone', self.set_time_zone)
		self._parser.addHandler('gli-profile/users/user', self.add_user)
		
	##
	# Parses the given filename populating the client_configuration.
	# @param filename Parameter description
	def parse(self, filename):
		self._parser.parse(filename)

	##
	# This method serializes the configuration data and output a nice XML document.
	# NOTE: this method currently does not serialize: _partition_tables or _kernel_modules
	def serialize(self):
		xmltab = { 'boot-device': self.get_boot_device,	
		      'bootloader':				self.get_boot_loader_pkg,
					'bootloader-mbr':			self.get_boot_loader_mbr,
					'bootloader-kernel-args':	self.get_bootloader_kernel_args,
					'cron-daemon':				self.get_cron_daemon_pkg,
					'domainname':				self.get_domainname,
					'dynamic-stage3':			self.get_dynamic_stage3,
					'ftp-proxy':				self.get_ftp_proxy,
					'grp-install':				self.get_grp_install,
					'hostname':					self.get_hostname,
					'http-proxy':				self.get_http_proxy,
					'install-distcc':			self.get_install_distcc,
					'install-pcmcia-cs':		self.get_install_pcmcia_cs,
					'install-rp-pppoe':			self.get_install_rp_pppoe,
					'install-stage':			self.get_install_stage,
					'kernel-bootsplash':		self.get_kernel_bootsplash,
					'kernel-build-method':			self.get_kernel_build_method,
					'kernel-config':			self.get_kernel_config_uri,
					'kernel-initrd':			self.get_kernel_initrd,
					'kernel-source':			self.get_kernel_source_pkg,
					'logging-daemon':			self.get_logging_daemon_pkg,
					'mta':						self.get_mta_pkg,
					'nisdomainname':			self.get_nisdomainname,
					'portage-snapshot':			self.get_portage_tree_snapshot_uri,
					'portage-tree-sync':		self.get_portage_tree_sync_type,
					'post-install-script-uri':	self.get_post_install_script_uri,
					'root-pass-hash':			self.get_root_pass_hash,
					'rsync-proxy':				self.get_rsync_proxy,
					'stage-tarball':			self.get_stage_tarball_uri,
					'time-zone':				self.get_time_zone,
		}
		self.xmldoc = "<?xml version=\"1.0\"?>"
		self.xmldoc += "<gli-profile>"

		# Normal cases
		for key in xmltab.keys():
			self.xmldoc += "<%s>%s</%s>" % (key, xmltab[key](), key)

		# Special cases
		self.serialize_default_gateway()
		self.serialize_dns_servers()
		self.serialize_install_packages()
		self.serialize_kernel_modules()
#		self.serialize_make_conf()
		self.serialize_network_interfaces()
		self.serialize_network_mounts()
		self.serialize_partition_tables()
#		self.serialize_rc_conf()
		self.serialize_services()
		self.serialize_users()
		self.serialize_etc_files()

		self.xmldoc += "</gli-profile>"

		dom = xml.dom.minidom.parseString(self.xmldoc)
		return dom.toprettyxml()
	
	############################################################################
	############################################################################
	#### Boot Device Selection
	
	##
	# boot_device is a string to decide which device to install the bootloader to
	# @param xml_path Used internally by the XML parser. Should be None when calling directly
	# @param boot_loader_pkg   boot device with full /dev
	# @param xml_attr 		not used here
	
	def set_boot_device(self, xml_path, boot_device, xml_attr):
		#check data type
		if type(boot_device) != str:
			raise GLIException("BootDevice", 'fatal', 'set_boot_device',  "Input must be type 'string'!")
		self._boot_device = boot_device
	
	##
	# returns boot_device
	def get_boot_device(self):
		return self._boot_device
	
	############################################################################
	#### Bootloader Package Selection

	##
	# boot_loader_pkg is a string to decide which boot loader to install. (ie. 'grub')
	# @param xml_path Used internally by the XML parser. Should be None when calling directly
	# @param boot_loader_pkg   bootloader package name (like grub or lilo)
	# @param xml_attr 		not used here
	def set_boot_loader_pkg(self, xml_path, boot_loader_pkg, xml_attr):
		# Check data type
		if type(boot_loader_pkg) != str:
			raise GLIException("BootLoaderPKG", 'fatal', 'set_boot_loader_pkg',  "Input must be type 'string'!")
		self._boot_loader_pkg = boot_loader_pkg

	##
	# returns boot_loader_pkg
	def get_boot_loader_pkg(self):
		return self._boot_loader_pkg
	
	############################################################################
	#### Bootloader Kernel Arguments
	
	##
	# FIXME: agaffney, what error checking needs to be done here?
	# kernel_args are the arguments to pass the kernel at boot from the bootloader.
	# @param xml_path Used internally by the XML parser. Should be None when calling directly
	# @param bootloader_kernel_args   FIXME no idea.
	# @param xml_attr 		not used here.
	def set_bootloader_kernel_args(self, xml_path, bootloader_kernel_args, xml_attr):
		self._bootloader_kernel_args = bootloader_kernel_args

	##
	# Returns kernel arguments
	def get_bootloader_kernel_args(self):
		return self._bootloader_kernel_args
		
	############################################################################
	#### Bootloader Installation to MBR

	##
	# boot_loader_mbr is a bool. True installs boot loader to MBR.  
	# False installs boot loader to the boot or root partition.
	# @param xml_path Used internally by the XML parser. Should be None when calling directly
	# @param boot_loader_mbr  
	# @param xml_attr Parameter description
	def set_boot_loader_mbr(self, xml_path, boot_loader_mbr, xml_attr):
		# Check data type
		if type(boot_loader_mbr) != bool:
			if type(boot_loader_mbr) == str:
				boot_loader_mbr = GLIUtility.strtobool(boot_loader_mbr)
			else:
				raise GLIException("BootLoaderMBRError", 'fatal', 'set_boot_loader_mbr',  "Input must be type 'bool'!")
		self._boot_loader_mbr = boot_loader_mbr

	##
	# returns boot_loader_mbr
	def get_boot_loader_mbr(self):
		return self._boot_loader_mbr	

	############################################################################
	#### Cron Daemon Package

	##
	# cron_daemon_pkg is a string to determine which cron daemon to install and configure (ie. 'vixie-cron')
	# @param xml_path Used internally by the XML parser. Should be None when calling directly
	# @param cron_daemon_pkg package name
	# @param xml_attr Not used here.
	def set_cron_daemon_pkg(self, xml_path, cron_daemon_pkg, xml_attr):
		# Check data type
		if type(cron_daemon_pkg) != str:
			raise GLIException("CronDaemonPKGError", 'fatal', 'set_cron_daemon_pkg',  "Input must be type 'string'!")
		self._cron_daemon_pkg = cron_daemon_pkg

	##
	# Returns the cron daemon pkg name
	def get_cron_daemon_pkg(self):
		return self._cron_daemon_pkg

	############################################################################
	#### Network Gateway 

	##
	# Set the default gateway for the post-installed system.
	# The format of the input is: <default-gateway interface="interface name">ip of gateway</default-gateway>
	# It saves this information in the following format: (<interface>, <ip of gateway>)
	# @param xml_path Used internally by the XML parser. Should be None when calling directly
	# @param gateway  		gateway ip address
	# @param xml_attr Parameter description
	def set_default_gateway(self, xml_path, gateway, xml_attr):
		if not GLIUtility.is_realstring(gateway):
			raise GLIException('DefaultGatewayError', 'fatal', 'set_default_gateway', "The gateway must be a non-empty string!")
		if not 'interface' in xml_attr.keys():
			raise GLIException('DefaultGatewayError', 'fatal', 'set_default_gateway', 'No interface information specified!')

		interface = str(xml_attr['interface'])

		if not GLIUtility.is_eth_device(interface):
			raise GLIException('DefaultGatewayError', 'fatal', 'set_default_gateway', "Invalid device!")
		if not GLIUtility.is_ip(gateway):
			raise GLIException("DefaultGateway", 'fatal', 'set_default_gateway',  "The IP Provided is not valid!")
		self._default_gateway = (interface, gateway)

	##
	# Returns the default gateway
	def get_default_gateway(self):
		return self._default_gateway

	##
	# Serializes default_gateway
	def serialize_default_gateway(self):
		if self.get_default_gateway() != ():
			gw = self.get_default_gateway()
			self.xmldoc += "<default-gateway interface=\"%s\">%s</default-gateway>" % (gw[0], gw[1])


	############################################################################
	#### DNS Servers

	##
	# Set the DNS servers for the post-installed system.
	# @param xml_path Used internally by the XML parser. Should be None when calling directly
	# @param dns_servers 	a tuple or space-separated list of dns servers
	# @param xml_attr Parameter description
	def set_dns_servers(self, xml_path, dns_servers, xml_attr):
		if type(dns_servers) == tuple:
			dns_servers = dns_servers[0:3]
		elif type(dns_servers) == str:
			dns_servers = string.split(dns_servers)
		else:
			raise GLIException("DnsServersError", 'fatal', 'set_dns_servers',  "Invalid input!")

		for server in dns_servers:
			if not GLIUtility.is_ip(server):
				raise GLIException("DnsServersError", 'fatal', 'set_dns_servers',  server + " must be a valid IP address!")

		self._dns_servers = dns_servers

	##
	# This returns a tuple of the form: (<nameserver 1>, <nameserver 2>, <nameserver 3>)
	def get_dns_servers(self):
		return self._dns_servers
		
	##
	# Serializes DNS Servers
	def serialize_dns_servers(self):
		if self.get_dns_servers() != ():
			self.xmldoc += "<dns-servers>"
			self.xmldoc += string.join(self.get_dns_servers(), ' ')
			self.xmldoc += "</dns-servers>"

############################################################################
	#### Domainname

	##
	# domainname is a string containing the domainname for the new system. (ie. 'mydomain.com'; NOT FQDN)
	# @param xml_path Used internally by the XML parser. Should be None when calling directly
	# @param domainname 	string of the domain name
	# @param xml_attr 		not used here
	def set_domainname(self, xml_path, domainname, xml_attr):
		# Check type
		if type(domainname) != str:
			raise GLIException("DomainnameError", 'fatal', 'set_domainname',  "Must be a string!")
		self._domainname = domainname

	##
	# Returns domainname
	def get_domainname(self):
		return self._domainname
		
	###################################################################
	##
	# Set whether or not to build the stage3 from the LiveCD
	# @param xml_path Used internally by the XML parser. Should be None when calling directly
	# @param dynamic_stage3	True/False 	
	# @param xml_attr 		not used here
	def set_dynamic_stage3(self, xml_path, dynamic_stage3, xml_attr):
		if type(dynamic_stage3) != bool:
			if type(dynamic_stage3) == str:
				self._dynamic_stage3 = GLIUtility.strtobool(dynamic_stage3)
			else:
				raise GLIException("DynamicStage3", 'fatal', 'set_dynamic_stage3',  "Input must be type 'bool'!")
		else:
			self._dynamic_stage3 = dynamic_stage3

	##
	# Returns whether or not to build the stage3 from the LiveCD
	def get_dynamic_stage3(self):
		return self._dynamic_stage3

	##
	# Used internally for XML parsing...adds an entry to a file
	# @param xml_path Used internally by the XML parser. Should be None when calling directly
	# @param value uhh...the value
	# @param attr used for XML parsing
	def add_etc_files_file_entry(self, xml_path, value, attr):
		if 'name' in attr.getNames():
			if not self._temp_etc_file:
				self._temp_etc_file = {}
			self._temp_etc_file[attr['name']] = value
		else:
			if not self._temp_etc_file:
				self._temp_etc_file = []
			self._temp_etc_file.append(value)

	##
	# Used internally for XML parsing...adds a file
	# @param xml_path Used internally by the XML parser. Should be None when calling directly
	# @param unused this should be obvious
	# @param attr used for XML parsing
	def add_etc_files_file(self, xml_path, unused, attr):
		self._etc_files[attr['name']] = self._temp_etc_file
		self._temp_etc_file = None

	##
	# Returns etc_files structure
	def get_etc_files(self):
		return self._etc_files

	##
	# Replaces etc_files structure with one passed in
	# @param etc_files new etc_files structure
	def set_etc_files(self, etc_files):
		self._etc_files = etc_files

	##
	# Serializes the etc_files structure
	def serialize_etc_files(self):
		self.xmldoc += "<etc-files>"
		for etc_file in self._etc_files:
			self.xmldoc += "<file name=\"%s\">" % etc_file
			for entry in self._etc_files[etc_file]:
				self.xmldoc += "<entry"
				if isinstance(self._etc_files[etc_file], dict):
					self.xmldoc += " name=\"%s\">%s" % (entry, self._etc_files[etc_file][entry])
				else:
					self.xmldoc += ">%s" % entry
				self.xmldoc += "</entry>"
			self.xmldoc += "</file>"
		self.xmldoc += "</etc-files>"

		
	############################################################################
	#### FTP Proxy

	##
	# FTP proxy is a uri containing a proxy if needed for ftp traffic. (ie. 'ftp://myhost.mydomain:myport')
	# @param xml_path Used internally by the XML parser. Should be None when calling directly
	# @param ftp_proxy 	ftp proxy address
	# @param xml_attr  not used here
	def set_ftp_proxy(self, xml_path, ftp_proxy, xml_attr):
		# Check type
		if ftp_proxy and not GLIUtility.is_uri(ftp_proxy):
			raise GLIException("FTPProxyError", 'fatal', 'set_ftp_proxy',  "Must be a uri!")
		self._ftp_proxy = ftp_proxy

	##
	# Returns FTP proxy
	def get_ftp_proxy(self):
		return self._ftp_proxy
	
	############################################################################
	#### GRP Install
	
	##
	# grp_install is a bool. True installs GRP.  False doesn't.
	# @param xml_path Used internally by the XML parser. Should be None when calling directly
	# @param grp_install  boolean
	# @param xml_attr Parameter description
	def set_grp_install(self, xml_path, grp_install, xml_attr):
		# Check data type
		if type(grp_install) != bool:
			if type(grp_install) == str:
				grp_install = GLIUtility.strtobool(grp_install)
			else:
				raise GLIException("GRPInstall", 'fatal', 'set_grp_install',  "Input must be type 'bool'!")
		self._grp_install = grp_install
		
	##
	# returns grp_install
	def get_grp_install(self):
		return self._grp_install

	############################################################################
	#### Hostname

	##
	# Hostname is a string containing the hostname for the new system. (ie. 'myhost'; NOT 'myhost.mydomain.com')
	# @param xml_path Used internally by the XML parser. Should be None when calling directly
	# @param hostname 		string of hostname
	# @param xml_attr 		not used here.
	def set_hostname(self, xml_path, hostname, xml_attr):
		# Check type
		if type(hostname) != str:
			raise GLIException("HostnameError", 'fatal', 'set_hostname',  "Must be a string!")
		self._hostname = hostname

	##
	# Returns hostname
	def get_hostname(self):
		return self._hostname

	############################################################################
	#### HTTP Proxy

	##
	# HTTP proxy is a URI containing a proxy if needed for http traffic. (ie. 'http://myhost.mydomain:myport')
	# @param xml_path Used internally by the XML parser. Should be None when calling directly
	# @param http_proxy 	http proxy address
	# @param xml_attr  not used here
	def set_http_proxy(self, xml_path, http_proxy, xml_attr):
		# Check type
		if http_proxy and not GLIUtility.is_uri(http_proxy):
			raise GLIException("HTTPProxyError", 'fatal', 'set_http_proxy',  "Must be a uri!")
		self._http_proxy = http_proxy

	##
	# Returns HTTP proxy
	def get_http_proxy(self):
		return self._http_proxy

	############################################################################
	#### Install Distcc
	
	##
	# This tells the installer whether or not to install the distcc package
	# @param xml_path Used internally by the XML parser. Should be None when calling directly
	# @param install_distcc 	boolean
	# @param xml_attr Parameter description
	def set_install_distcc(self, xml_path, install_distcc, xml_attr):
		if type(install_distcc) != bool:
			if type(install_distcc) == str:
				install_distcc = GLIUtility.strtobool(install_distcc)
			else:
				raise GLIException("InstallDistcc", 'fatal', 'set_install_distcc',  "Input must be type 'bool'!")

		self._install_distcc = install_distcc

	##
	# Returns the boolean _install_distcc
	def get_install_distcc(self):
		return self._install_distcc

	############################################################################
	#### Install Package List
	##
	# Returns the list of packages to include in the Extra Packages screens.
	def get_install_package_list(self):
		install_package_list = { 
			'Desktop': ("Popular Desktop Applications",
				{"bittorrent": "tool for distributing files via a distributed network of nodes",
				"evolution": "A GNOME groupware application, a Microsoft Outlook workalike",
				"gaim": "GTK Instant Messenger client",
				"gftp": "Gnome based FTP Client",
				"gimp": "GNU Image Manipulation Program",
				"inkscape": "A SVG based generic vector-drawing program",
				"koffice": "An integrated office suite for KDE, the K Desktop Environment",
				"mozilla": "The Mozilla Web Browser",
				"mozilla-firefox": "The Mozilla Firefox Web Browser",
				"mozilla-thunderbird": "Thunderbird Mail Client",
				"mplayer": "Media Player for Linux",
				"openoffice": "OpenOffice.org, a full office productivity suite.",
				"openoffice-bin": "Same as OpenOffice but a binary package (no compiling!)",
# Removed because fetch-restriction would cause install to fail
#				"realplayer": "Real Media Player",
				"rhythmbox": "Music management and playback software for GNOME",
				"vlc": "VLC media player - Video player and streamer",
				"xchat": "Graphical IRC Client",
				"xine-ui": "Xine movie player",
				"xmms": "X MultiMedia System"  }),
			'Servers': ("Applications often found on servers.",
				{"apache": "Apache Web Server",
				"cups": "The Common Unix Printing System",
				"exim": "A highly configurable, drop-in replacement for sendmail",
				"iptables": "Linux kernel (2.4+) firewall, NAT and packet mangling tools",
				"mod_php": "Apache module for PHP",
				"mysql": "A fast, multi-threaded, multi-user SQL database server",
				"postfix": "A fast and secure drop-in replacement for sendmail",
				"postgresql": "sophisticated Object-Relational DBMS",
				"proftpd": "ProFTP Server",
				"samba": "SAMBA client/server programs for UNIX",
				"sendmail": "Widely-used Mail Transport Agent (MTA)",
				"traceroute": "Utility to trace the route of IP packets"  }),
			'X11': ("Window managers and X selection.", 
				{"xorg-x11": "An X11 implementation maintained by the X.Org Foundation",
				"gnome": "The Gnome Desktop Environment",
				"kde": "The K Desktop Environment",
				"blackbox": "A small, fast, full-featured window manager for X",
				"enlightenment": "Enlightenment Window Manager",
				"fluxbox": "Fluxbox is an X11 window manager featuring tabs and an iconbar",
				"xfce4": "XFCE Desktop Environment"  }),
			'Misc': ("Miscellaneous Applications you may want.",
				{"emacs": "An incredibly powerful, extensible text editor",
				"ethereal": "A commercial-quality network protocol analyzer",
				"gkrellm": "Single process stack of various system monitors",
				"gvim": "GUI version of the Vim text editor",
				"keychain": "ssh-agent manager",
				"logrotate": "Rotates, compresses, and mails system logs",
				"ntp": "Network Time Protocol suite/programs",
				"rdesktop": "A Remote Desktop Protocol Client",
				"slocate": "Secure way to index and quickly search for files on your system",
				"ufed": "Gentoo Linux USE flags editor",
				"vim": "Vim, an improved vi-style text editor" }),
			'Recommended': ("Applications recommended by the GLI Team.",
				{"anjuta": "A versatile IDE for GNOME",
				"chkrootkit": "a tool to locally check for signs of a rootkit",
				"crack-attack": "Addictive OpenGL-based block game",
				"gnupg": "The GNU Privacy Guard, a GPL pgp replacement",
				"net-snmp": "Software for generating and retrieving SNMP data",
				"netcat": "the network swiss army knife",
				"nmap": "A utility for network exploration or security auditing",
				"screen": "full-screen window manager that multiplexes between several processes",
				"xpdf": "An X Viewer for PDF Files" })
		}
		return install_package_list

	############################################################################
	#### Install Packages

	##
	# Sets up the list of packages to be installed for the new system.
	# @param xml_path Used internally by the XML parser. Should be None when calling directly
	# @param install_packages The space-separated list of packages to install.
	# @param xml_attr Parameter description
	def set_install_packages(self, xml_path, install_packages, xml_attr):
		if type(install_packages) == str:
			install_packages = string.split(install_packages)
		else:
			raise GLIException("InstallPackagesError", 'fatal', 'set_install_packages',  "Invalid input!")

		for install_package in install_packages:
			if not GLIUtility.is_realstring(install_package):
				raise GLIException("InstallPackagesError", 'fatal', 'set_install_packages',  install_package + " must be a valid string!")
		self._install_packages = install_packages

	##
	# This returns a list of the packages
	def get_install_packages(self):
		return self._install_packages
		
	##
	# Serializes install_packages
	def serialize_install_packages(self):
		if self.get_install_packages() != ():
			self.xmldoc += "<install-packages>"
			self.xmldoc += string.join(self.get_install_packages(), ' ')
			self.xmldoc += "</install-packages>"

	############################################################################
	#### PCMCIA-CS 

	##
	# This tells the installer whether or not to install the pcmcia_cs package
	# @param xml_path Used internally by the XML parser. Should be None when calling directly
	# @param install_pcmcia 	boolean
	# @param xml_attr Parameter description
	def set_install_pcmcia_cs(self, xml_path, install_pcmcia, xml_attr):
		if type(install_pcmcia) != bool:
			if type(install_pcmcia) == str:
				install_pcmcia = GLIUtility.strtobool(install_pcmcia)
			else:
				raise GLIException("InstallPcmciaCS", 'fatal', 'set_install_pcmcia_cs',  "Input must be type 'bool'!")

		self._install_pcmcia_cs = install_pcmcia

	##
	# Returns the boolean _install_pcmcia_cs
	def get_install_pcmcia_cs(self):
		return self._install_pcmcia_cs

	############################################################################
	#### RP-PPPoE Installation

	##
	# Tell the installer whether or not to install the rp-pppoe package
	# @param xml_path Used internally by the XML parser. Should be None when calling directly
	# @param install_rp_pppoe		boolean
	# @param xml_attr Parameter description
	def set_install_rp_pppoe(self, xml_path, install_rp_pppoe, xml_attr):
		if type(install_rp_pppoe) != bool:
			if type(install_rp_pppoe) == str:
				install_rp_pppoe = GLIUtility.strtobool(install_rp_pppoe)
			else:
				raise GLIException("InstallRP_PPPOE", 'fatal', 'set_install_rp_pppoe',  "Invalid input!")

		self._install_rp_pppoe = install_rp_pppoe

	##
	# Return the boolean value of _install_rp_pppoe
	def get_install_rp_pppoe(self):
		return self._install_rp_pppoe

	############################################################################
	#### Install Stage

	##
	# install_stage is a integer to define which stage install to use.  Appropriate stages are 1-3.
	# @param xml_path Used internally by the XML parser. Should be None when calling directly
	# @param install_stage 		install stage number
	# @param xml_attr  not used here.
	def set_install_stage(self, xml_path, install_stage, xml_attr):
		# Check type
		if type(install_stage) != int:
			if type(install_stage) == str:
				install_stage = int(install_stage)
			else:
				raise GLIException("InstallStageError", 'fatal', 'set_install_stage',  "Must be an integer!")
		
		# Check for stage bounds
		if 0 < install_stage < 4:
			self._install_stage = install_stage
		else:
			raise GLIException("InstallStageError", 'fatal', 'set_install_stage',  "install_stage must be 1-3!")

	##
	# Returns install_stage
	def get_install_stage(self):
		return self._install_stage

	############################################################################
	#### Kernel Bootsplash Option
	
	##
	# kernel_bootsplash is a bool to determine whether or not to install bootsplash into the kernel.  
	# True builds in bootsplash support to the initrd.  
	# WARNING: kernel_source_pkg must contain a kernel with bootsplash support or the bootsplash will not appear.  
	# If you set this to true, it will build an initrd kernel even if you chose false for kernel_initrd!
	# @param xml_path Used internally by the XML parser. Should be None when calling directly
	# @param kernel_bootsplash 		boolean
	# @param xml_attr 		not used here.
	def set_kernel_bootsplash(self, xml_path, kernel_bootsplash, xml_attr):
		# Check type
		if type(kernel_bootsplash) != bool:
			if type(kernel_bootsplash) == str:
					kernel_bootsplash = GLIUtility.strtobool(kernel_bootsplash)
			else:
				raise GLIException("KernelBootsplashError", 'fatal', 'set_kernel_bootsplash',  "Must be a bool!")
		
		self._kernel_bootsplash = kernel_bootsplash

	##
	# Returns kernel_bootsplash
	def get_kernel_bootsplash(self):
		return self._kernel_bootsplash		
	
	############################################################################
	#### Kernel Build Method

	##
	# kernel_build_method is a string specifying what build method you wish to use for the kernel.
	# Can also be a http:// or ftp:// path.
	# @param xml_path Used internally by the XML parser. Should be None when calling directly
	# @param kernel_build_method   URI of kernel .config file
	# @param xml_attr  	not used here.
	def set_kernel_build_method(self, xml_path, kernel_build_method, xml_attr):
		# Check type
		if type(kernel_build_method) != str:
			raise GLIException("KernelBuildMethodError", 'fatal', 'set_kernel_build_method',  "Must be a string!")

		self._kernel_build_method = kernel_build_method

	##
	# Returns kernel_build_method
	def get_kernel_build_method(self):
		return self._kernel_build_method
		
	############################################################################
	#### Kernel Configuration URI

	##
	# kernel_config_uri is a string that is the path to the kernel config file you wish to use.  
	# Can also be a http:// or ftp:// path.
	# @param xml_path Used internally by the XML parser. Should be None when calling directly
	# @param kernel_config_uri   URI of kernel .config file
	# @param xml_attr  	not used here.
	def set_kernel_config_uri(self, xml_path, kernel_config_uri, xml_attr):
		# Check type
		if type(kernel_config_uri) != str:
			raise GLIException("KernelConfigURIError", 'fatal', 'set_kernel_config_uri',  "Must be a string!")

		# Check validity (now done in the FE)
		#if not (kernel_config_uri):
		#	raise GLIException("KernelConfigURIError", 'fatal', 'set_kernel_config_uri',  "Empty Kernel URI!")

		self._kernel_config_uri = kernel_config_uri

	##
	# Returns kernel_config_uri
	def get_kernel_config_uri(self):
		return self._kernel_config_uri

	############################################################################
	#### Kernel Initrd Option
	
	##
	# kernel_initrd is a bool to determine whether or not to build an initrd kernel.  False builds a non-initrd kernel. 
	# (overwritten by kernel_bootsplash; needs genkernel non-initrd support not yet present)
	# @param xml_path Used internally by the XML parser. Should be None when calling directly
	# @param kernel_initrd 		boolean
	# @param xml_attr 		not used here
	def set_kernel_initrd(self, xml_path, kernel_initrd, xml_attr):
		# Check type
		if type(kernel_initrd) != bool:
			if type(kernel_initrd) == str:
				kernel_initrd = GLIUtility.strtobool(kernel_initrd)
			else:
				raise GLIException("KernelInitRDError", 'fatal', 'set_kernel_initrd',  "Must be a bool!")
		
		self._kernel_initrd = kernel_initrd

	##
	# Returns kernel_initrd
	def get_kernel_initrd(self):
		return self._kernel_initrd

	############################################################################
	#### Kernel Modules

	##
	# "kernel_modules is a tuple of strings containing names of modules to automatically load at boot time. (ie. '( 'ide-scsi', )')"
	# @param kernel_modules Parameter description
	def set_kernel_modules(self, kernel_modules):
		# Check type
		if isinstance(kernel_modules, str):
#			raise GLIException("KernelModulesError", 'fatal', 'set_kernel_modules',  "Must be a tuple!")
			kernel_modules = kernel_modules.split(" ")
		self._kernel_modules = kernel_modules

	##
	# Returns kernel_modules
	def get_kernel_modules(self):
		return self._kernel_modules
		
	##
	# Serializes kernel modules
	def serialize_kernel_modules(self):
		if self.get_kernel_modules() != []:
			kernel_modules = self.get_kernel_modules()
			self.xmldoc += "<kernel-modules>%s</kernel-modules>" % " ".join(kernel_modules)

	############################################################################
	#### Kernel Sources
	
	##
	# kernel_source_pkg is a string to define which kernel source to use.  (ie. 'gentoo-sources')
	# @param xml_path Used internally by the XML parser. Should be None when calling directly
	# @param kernel_source_pkg   package name of the kernel sources to be emerged
	# @param xml_attr 	not used here.
	def set_kernel_source_pkg(self, xml_path, kernel_source_pkg, xml_attr):
		# Check type
		if type(kernel_source_pkg) != str:
			raise GLIException("KernelSourcePKGError", 'fatal', 'set_kernel_source_pkg',  "Must be a string!")
		self._kernel_source_pkg = kernel_source_pkg

	##
	# Returns kernel_source_pkg
	def get_kernel_source_pkg(self):
		return self._kernel_source_pkg
		
	############################################################################
	#### Logging Daemon Package
	
	##
	# logging_daemon_pkg is a string to determine which logging daemon to install and configure (ie. 'sysklogd')
	# @param xml_path Used internally by the XML parser. Should be None when calling directly
	# @param logging_daemon_pkg package name of logging daemon to be emerged
	# @param xml_attr Parameter description
	def set_logging_daemon_pkg(self, xml_path, logging_daemon_pkg, xml_attr):
		# Check data type
		if type(logging_daemon_pkg) != str:
			raise GLIException("LoggingDaemonPKGError", 'fatal', 'set_logging_daemon_pkg',  "Input must be type 'string'!")
		self._logging_daemon_pkg = logging_daemon_pkg
	
	##
	# Returns logging daemon pkg name
	def get_logging_daemon_pkg(self):
		return self._logging_daemon_pkg

	############################################################################
	#### /etc/make.conf Configuration

	##
	# Adds a variable to the new system make.conf
	# @param xml_path Used internally by the XML parser. Should be None when calling directly
	# @param data 		a string that is the value of the variable name.
	# @param attr 		an xml attribute that contains the name of the variable
	# 		OR attr is a variable name, like 'USE'. This makes it easier for front-end designers.
	def make_conf_add_var(self, xml_path, data, attr):
		if 'name' not in attr.keys():
			raise GLIException("MakeConfError", 'fatal', 'make_conf_add_var',  "Every value needs to have a variable name!")

		varName = attr['name']
		if not "make.conf" in self._etc_files:
			self._etc_files['make.conf'] = {}
		self._make_conf[str(varName)] = str(data)

	##
	# make_conf is a dictionary that will be set to _make_conf
	# There is no checking that needs to be done, so please sure sure that the make_conf dictionary
	# that is passed in is valid.
	# @param make_conf 		a dictionary that will be set to _make_conf
	def set_make_conf(self, make_conf):
		self._etc_files['make.conf'] = make_conf

	##
	# Return a dictionary of the make.conf
	def get_make_conf(self):
		if "make.conf" in self._etc_files:
			return self._etc_files['make.conf']
		else:
			return {}
		
	##
	# Serializes make.conf (no longer used)
	def serialize_make_conf(self):
		if self.get_make_conf() != {}:
			self.xmldoc += "<make-conf>"

			# keys should always be in the same order!
			make_conf = self.get_make_conf()
			make_conf_keys = make_conf.keys()
			make_conf_keys.sort()

			for var in make_conf_keys:
				self.xmldoc += "<variable name=\"%s\">%s</variable>" % (var, make_conf[var])

			self.xmldoc += "</make-conf>"

	############################################################################
	#### MTA Selection

	##
	# Sets the intended MTA package
	# @param xml_path Used internally by the XML parser. Should be None when calling directly
	# @param mta 	package name of mta
	# @param xml_attr Parameter description
	def set_mta_pkg(self, xml_path, mta_pkg, xml_attr):
		if type(mta_pkg) != str:
			raise GLIException("MTAError", 'fatal', 'set_mta_pkg',  "The MTA must be a string!")
		self._mta_pkg = mta_pkg

	##
	# returns the MTA
	def get_mta_pkg(self):
		return self._mta_pkg
	
	############################################################################
	#### Network Interface Selection

	##
	# This adds an ethernet device to the _network_interfaces dictionary.
	#	The format of this dictionary is:
	#	{ <eth_device> : (options tuple), ... }
	#
	#	eth_device can be a valid ethernet device eth0, eth1, wlan*... OR 
	#	it can be a valid MAC address.
	#
	#	The format of the options tuple is for a static IP:
	#	( <ip address>, <broadcast>, <netmask> )
	#
	#	For DHCP, the format of the options tuple is:
	#	( 'dhcp', <dhcp options>, None )
	#
	#	We keep the None as a placeholder, to not break anything that uses this
	#	in other parts of the installer.
	#	
	#	Aliases are no longer needed in the tuple because they can be treated like
	#	an individual interface. GLIUtility.is_eth_device will recognize
	# @param xml_path Used internally by the XML parser. Should be None when calling directly
	# @param device  	the type and name of the device
	# @param attr 		should be dhcp or a tuple of the ip addresses.
	def add_network_interface(self, xml_path, device, attr):
		options = None
		ip = broadcast = netmask = dhcp_options = None
		dhcp = True

		if type(device) != str:
			raise GLIException("NetworkInterfacesError", 'fatal', 'add_network_interface',  "Invalid or unimplimented device type (" + device + ")!")
	
		if not GLIUtility.is_eth_device(device):
			device = GLIUtility.format_mac(device)
			if not GLIUtility.is_mac(device):
				raise GLIException("NetworkInterfacesError", 'fatal', 'add_network_interface',  "Invalid or unimplimented device type (" + device + ")!")

		if type(attr) == tuple:
			ip = attr[0]
			dhcp_options = broadcast = attr[1]
			netmask = attr[2]
			if ip != 'dhcp':
				dhcp = False
		else:
			for attrName in attr.keys():
				if attrName == 'ip':
					ip = str(attr[attrName])
				elif attrName == 'broadcast':
					broadcast = str(attr[attrName])
				elif attrName == 'netmask':
					netmask = str(attr[attrName])
				elif attrName == 'options':
					dhcp_options = str(attr[attrName])

			if ip != 'dhcp' and ip != None:
				dhcp = False

		if not dhcp:
			if not GLIUtility.is_ip(ip):
				raise GLIException("NetworkInterfacesError", 'fatal', 'add_network_interface',  "The ip address you specified for " + device + " is not valid!")
			if not GLIUtility.is_ip(broadcast):
				raise GLIException("NetworkInterfacesError", 'fatal', 'add_network_interface',  "The broadcast address you specified for " + device + " is not valid!")
			if not GLIUtility.is_ip(netmask):
				raise GLIException("NetworkInterfacesError", 'fatal', 'add_network_interface',  "The netmask address you specified for " + device + " is not valid!")
			options = (ip, broadcast, netmask)
		else:
			options = ('dhcp', dhcp_options, None)

		self._network_interfaces[device] = options

	##
	# This method sets the network interfaces diction to network_interfaces.
	# This method uses the function add_network_interfaces to do all of the real work.
	# @param network_interfaces   a dict with all the networking info.  see add_ for specification.
	def set_network_interfaces(self, network_interfaces):
		# Check type
		if type(network_interfaces) != dict:
			raise GLIException("NetworkInterfacesError", 'fatal', 'set_network_interfaces',  "Must be a dictionary!")

		self._network_interfaces = {}
		for device in network_interfaces:
			self.add_network_interface(None, device, network_interfaces[device])

	##
	# Returns network_interfaces
	def get_network_interfaces(self):
		return self._network_interfaces
		
	##
	# Serialize Network Interfaces
	def serialize_network_interfaces(self):
		if self.get_network_interfaces() != {}:
			self.xmldoc += "<network-interfaces>"
			interfaces = self.get_network_interfaces()
			for iface in interfaces:
				if interfaces[iface][0] == 'dhcp':
					attrs = "ip=\"dhcp\""
					if interfaces[iface][1] != None:
						dhcp_options = "options=\"%s\"" % interfaces[iface][1]
						attrs = attrs + " " + dhcp_options
					self.xmldoc += "<device %s>%s</device>" % (attrs, iface)
				else:
					self.xmldoc += "<device ip=\"%s\" broadcast=\"%s\" netmask=\"%s\">%s</device>" % (interfaces[iface][0], interfaces[iface][1], interfaces[iface][2], iface)
			self.xmldoc += "</network-interfaces>"

	############################################################################
	#### Network Mounts

	##
	# FIXME: agaffney: Brief description of function
	# @param xml_path Used internally by the XML parser. Should be None when calling directly
	# @param unused Parameter description
	# @param attr Parameter description
	def add_netmount(self, xml_path, unused, attr):
		netmount_entry = {'export': '', 'host': '', 'mountopts': '', 'mountpoint': '', 'type': ''}
		if type(attr) == tuple:
			netmount_entry['export'] = attr[0]
			netmount_entry['host'] = attr[1]
			netmount_entry['mountopts'] = attr[2]
			netmount_entry['mountpoint'] = attr[3]
			netmount_entry['type'] = attr[4]
		else:
			if "export" in attr.getNames():
				for attrName in attr.getNames():
					netmount_entry[attrName] = str(attr.getValue(attrName))
		self._network_mounts.append(netmount_entry)

	##
	# Sets Network Mounts given a netmounts found probably in the config file.  Not sure if used.
	# @param netmounts Parameter description
	def set_network_mounts(self, netmounts):
		self._network_mounts = netmounts

	##
	# Returns the network mounts.
	def get_network_mounts(self):
		return self._network_mounts
		
	##
	# Serializes network mounts
	def serialize_network_mounts(self):
		if self.get_network_mounts() != {}:
			netmounts = self.get_network_mounts()
			self.xmldoc += "<network-mounts>"
			for mount in netmounts:
				self.xmldoc += "<netmount host=\"%s\" export=\"%s\" type=\"%s\" mountpoint=\"%s\" mountopts=\"%s\" />" % (mount['host'], mount['export'], mount['type'], mount['mountpoint'], mount['mountopts'])
			self.xmldoc += "</network-mounts>"
		
	############################################################################
	#### NIS Domain Name

	##
	# nisdomainname is a string containing the NIS domainname for the new system.
	# @param xml_path Used internally by the XML parser. Should be None when calling directly
	# @param nisdomainname  the name. is a string.
	# @param xml_attr not used here
	def set_nisdomainname(self, xml_path, nisdomainname, xml_attr):
		# Check type
		if type(nisdomainname) != str:
			raise GLIException("NISDomainnameError", 'fatal', 'set_nisdomainname',  "Must be a string!")
			
		self._nisdomainname = nisdomainname
	
	##
	# Returns nisdomainname
	def get_nisdomainname(self):
		return self._nisdomainname

	############################################################################
	#### Partitioning

	##
	# FIXME: agaffney
	# @param xml_path Used internally by the XML parser. Should be None when calling directly
	# @param unused Parameter description
	# @param attr Parameter description
	def add_partitions_device(self, xml_path, unused, attr):
		devnode = None
		if type(attr) == tuple:
			devnode = attr[0]
			disklabel = attr[1]
		else:
			if "devnode" in attr.getNames():
				devnode = str(attr.getValue("devnode"))
				if "disklabel" in attr.getNames():
					disklabel = str(attr.getValue("disklabel"))
				else:
					disklabel = ""
		self._partition_current_device = devnode
		self._partition_tables[devnode] = GLIStorageDevice.Device(devnode)
		self._partition_tables[devnode].set_disklabel(disklabel)
		self._partition_tables[devnode].set_partitions_from_install_profile_structure(self._temp_partition_table)
		self._temp_partition_table = []

	##
	# FIXME: agaffney
	# @param xml_path Used internally by the XML parser. Should be None when calling directly
	# @param unused Parameter description
	# @param attr Parameter description
	def add_partitions_device_partition(self, xml_path, unused, attr):
		part_entry = {'end': 0, 'format': None, 'mb': 0, 'minor': 0, 'mountopts': '', 'mountpoint': '', 'origminor': '', 'start': 0, 'type': ''}
#		if type(attr) == tuple:
#			part_entry['end'] = attr[0]
#			part_entry['format'] = attr[1]
#			part_entry['mb'] = attr[2]
#			part_entry['minor'] = attr[3]
#			part_entry['mountopts'] = attr[4]
#			part_entry['mountpoint'] = attr[5]
#			part_entry['origminor'] = attr[6]
#			part_entry['start'] = attr[7]
#			part_entry['type'] = attr[8]
#		else:
		if "minor" in attr.getNames():
			for attrName in attr.getNames():
				part_entry[attrName] = str(attr.getValue(attrName))
		if type(part_entry['format']) == str: part_entry['format'] = GLIUtility.strtobool(part_entry['format'])
		if type(part_entry['resized']) == str: part_entry['resized'] = GLIUtility.strtobool(part_entry['resized'])
#		if GLIUtility.is_numeric(part_entry['end']): part_entry['end'] = long(part_entry['end'])
#		if GLIUtility.is_numeric(part_entry['start']): part_entry['start'] = long(part_entry['start'])
		if GLIUtility.is_numeric(part_entry['mb']): part_entry['mb'] = long(part_entry['mb'])
		if GLIUtility.is_numeric(part_entry['minor']):
#			if part_entry['type'] == "free":
			part_entry['minor'] = float(part_entry['minor'])
			if int(part_entry['minor']) == part_entry['minor']:
				part_entry['minor'] = int(part_entry['minor'])
		if GLIUtility.is_numeric(part_entry['origminor']): part_entry['origminor'] = int(part_entry['origminor'])
		self._temp_partition_table.append(part_entry)

	############################################################################
	#### Partition Tables
	
	##
	# Sets the partition Tables
	# @param partition_tables   multilevel dictionary described below.
	def set_partition_tables(self, partition_tables):
		"""
		Sets the partition tables.  A partition is a multi level dictionary in the following format:
		{ <device (local)>: <partition table>, <device (nfs)>: <mount point> }
		
		<device (local)> is a string containing the path to the local file. (ie. '/dev/hda')
		<device (nfs)> is a string containing the ip address of the nfs mount. (ie. '192.168.1.2')
		
		<partition table> is a dictionary in the following format:
			{ <minor>: { 'mb': <size in mb>, 'type': <type>, 'mountpoint': <mount point>, 'start': <start cylinder>,
			             'end': <end cylinder>, 'mountopts': <mount options>, 'format': <format> } }
		
		ie. partition_tables['/dev/hda'][1] would return { 'mb': 0, 'type': 'ext3', 'mountpoint': '/boot', 'start': 12345,
								   'end': 34567, 'mountopts': 'auto', format: 'False' }

		Types are as follows:
		string: <device>, <mount point>, <mount options>, <type>
		integer: <minor>, <size in mb>, <start cylinder>, <end cylinder>
		boolean: <format>
		
		Current <type> options include:
		ext2, ext3, reiserfs, xfs, jfs, linux-swap, extended, others?
		
		There will be a method in the partitioning code to make sure that the current parition_tables can actually be implemented.
		Should we call that function to test the culpability of our potential partitioning scheme?
		Should we create a method in the Controller to take raw variables and put them in the proper structure?
		Are all filesystems supported by all arches?
		"""
		
		# All the sanity checks are being commented out until I can fix them for the GLIStorageDevice stuff
		"""
		if type(partition_tables) != dict:
			raise GLIException("PartitionTableError", 'fatal', 'set_partition_tables',  "Invalid data type! partition_tables is a dict...")
		
		for device in partition_tables:
		
			# If the device is a valid local device...
			if GLIUtility.is_device(device):
			
				# We should check to make sure device is in /proc/partitions
				# If it is in /proc/partitions, it is a partitionable device
			
				# ... then loop through each minor to check data
				for minor in partition_tables[device]:

					# Make sure that the <minor> is an integer or can be converted to one
					try:
						int(minor)
					except:
						raise GLIException("ParitionTableError", 'fatal', 'set_partition_tables',  "The minor you specified (" + minor + ") is not an integer!")
					
					# Make sure that a minor number is valid
					if minor < 1:
						raise GLIException("ParitionTableError", 'fatal', 'set_partition_tables',  "The minor you specified (" + minor + ") is not a valid minor!")
				
					# Make sure that <size>, <type> and <mount point> are all set
					#if len(partition_tables[device][minor]) != 3:
					#	raise GLIException("ParitionTableError", 'fatal', 'set_partition_tables',  "The number of attributes for minor " + minor + " is incorrect!")
					#
					# Make sure that the <size> is an integer or can be converted to one
					#try:
					#	int(partition_tables[device][minor][0])
					#except:
					#	raise GLIException("ParitionTableError", 'fatal', 'set_partition_tables',  "The size you specified (" + partition_tables[device][minor][0] + ") is not an integer!")

			# Else, if the device is a valid remote device (hostname or ip)
			elif GLIUtility.is_ip(device) or GLIUtility.is_hostname(device):
			
				pass
				# Make sure that only the mount point is set
			#	if type(partition_tables[device]) != str:
			#		raise GLIException("ParitionTableError", 'fatal', 'set_partition_tables',  "Invalid mount point for nfs mount (device: " + device + ")!")

			# If the device is not a local or remote device, then it is invalid
			else:
				raise GLIException("PartitionTableError", 'fatal', 'set_partition_tables',  "The device you specified (" + device + ") is not valid!")
		"""

		# If all the tests clear, then set the variable
		self._partition_tables = partition_tables

	##
	# Returns partition_tables
	def get_partition_tables(self):
		return self._partition_tables
	
	##
	# Serializes partition tables
	def serialize_partition_tables(self):
		if self.get_partition_tables() != {}:
			partitions = self.get_partition_tables()
			self.xmldoc += "<partitions>";
			for device in partitions.keys():
				self.xmldoc += "<device devnode=\"%s\" disklabel=\"%s\">" % (device, partitions[device].get_disklabel())
				ips = partitions[device].get_install_profile_structure()
				for part in ips:
#					part = ips[minor]
					self.xmldoc += "<partition minor=\"%s\" origminor=\"%s\" mb=\"%s\" type=\"%s\" mountpoint=\"%s\" mountopts=\"%s\" format=\"%s\" mkfsopts=\"%s\" resized=\"%s\" />" % (str(part['minor']), str(part['origminor']), str(part['mb']), str(part['type']), str(part['mountpoint']), str(part['mountopts']), str(part['format']), str(part['mkfsopts']), str(part['resized']))
				self.xmldoc += "</device>"
			self.xmldoc += "</partitions>"

	############################################################################
	#### Portage Snapshot URI

	##
	# portage_tree_snapshot_uri is a string defining the path to a portage tree 
	# snapshot. (ie. 'file:///mnt/cdrom/snapshots/portage-*.tar.bz2')
	# @param xml_path Used internally by the XML parser. Should be None when calling directly
	# @param portage_tree_snapshot_uri  URI of the portage tree shapshot location
	# @param xml_attr 		not used here
	def set_portage_tree_snapshot_uri(self, xml_path, portage_tree_snapshot_uri, xml_attr):
		# Check type
		if type(portage_tree_snapshot_uri) != str:
			raise GLIException("PortageTreeSnapshotURIError", 'fatal', 'set_portage_tree_snapshot_uri',  "Must be a string!")

		self._portage_tree_snapshot_uri = portage_tree_snapshot_uri

	##
	# Returns portage_tree_snapshot_uri
	def get_portage_tree_snapshot_uri(self):
		return self._portage_tree_snapshot_uri
		
	############################################################################
	#### Portage Tree Sync Type

	##
	# Sets the sync type to be used by portage
	# @param xml_path Used internally by the XML parser. Should be None when calling directly
	# @param portage_tree_sync  string with sync type
	# @param xml_attr 		not used here
	def set_portage_tree_sync_type(self, xml_path, portage_tree_sync, xml_attr):
		# Check type
		if type(portage_tree_sync) != str:
			raise GLIException("PortageTreeSyncError", 'fatal', 'set_portage_tree_sync_type',  "Must be a string!")

		if string.lower(portage_tree_sync) not in ('sync', 'webrsync', 'custom', 'snapshot', 'none'):
			raise GLIException("PortageTreeSyncError", 'fatal', 'set_portage_tree_sync_type',  "Invalid Input!")

		self._portage_tree_sync_type = string.lower(portage_tree_sync)

	##
	# Returns portage_tree_sync
	def get_portage_tree_sync_type(self):
		return self._portage_tree_sync_type	

	############################################################################
	#### Post-Install Script URI
	
	##
	# Sets the URI for the post install script
	# @param xml_path Used internally by the XML parser. Should be None when calling directly
	# @param post_install_script_uri the URI
	# @param xml_attr Parameter description
	def set_post_install_script_uri(self, xml_path, post_install_script_uri, xml_attr):
		self._post_install_script_uri = post_install_script_uri
	
	##
	# Returns the URI for the post install script
	def get_post_install_script_uri(self):
		return self._post_install_script_uri

	############################################################################
	#### /etc/rc.conf Configuration

	##
	# Adds a variable set for the new system rc.conf
	# @param xml_path Used internally by the XML parser. Should be None when calling directly
	# @param data 		a string that is the value of the variable name.
	# @param attr 		an xml attribute that contains the name of the variable
	def rc_conf_add_var(self, xml_path, data, attr):
		if 'name' not in attr.keys():
			raise GLIException("RCConfError", 'fatal', 'rc_conf_add_var',  "Every value needs to have a variable name!")

		varName = attr['name']
		if not "rc.conf" in self._etc_files:
			self._etc_files['rc.conf'] = {}
		self._etc_files[str(varName)] = str(data)

	##
	# rc_conf is a dictionary that will be set to _rc_conf
	# There is no checking that needs to be done, so please sure sure that the rc_conf dictionary
	# that is passed in is valid.Brief description of function
	# @param rc_conf 	dictionary in the format specified above.
	def set_rc_conf(self, rc_conf):
		self._etc_files['rc.conf'] = rc_conf

	##
	# Return a dictionary of the make.conf
	def get_rc_conf(self):
		if "rc.conf" in self._etc_files:
			return self._etc_files['rc.conf']
		else:
			return {}
		
	##
	# Serializes rc.conf (no longer used)
	def serialize_rc_conf(self):
		if self.get_rc_conf() != {}:
			self.xmldoc += "<rc-conf>"

			rc_conf = self.get_rc_conf()
			for var in rc_conf:
				self.xmldoc += "<variable name=\"%s\">%s</variable>" % (var, rc_conf[var])

			self.xmldoc += "</rc-conf>"

	############################################################################
	#### Root Password Hash

	##
	# root_pass_hash is a string containing an md5 password hash to be assinged as the password for the root user.
	# @param xml_path Used internally by the XML parser. Should be None when calling directly
	# @param root_pass_hash Parameter description
	# @param xml_attr Parameter description
	def set_root_pass_hash(self, xml_path, root_pass_hash, xml_attr):
		# Check type
		if type(root_pass_hash) != str:
			raise GLIException("RootPassHashError", 'fatal', 'set_root_pass_hash',  "Must be a string!")
		self._root_pass_hash = root_pass_hash

	##
	# Returns root_pass_hash
	def get_root_pass_hash(self):
		return self._root_pass_hash

	############################################################################
	#### RSYNC Proxy

	##
	# RSYNC proxy is a uri containing a proxy if needed for rsync traffic. (ie. 'rsync://myhost.mydomain:myport')
	# @param xml_path Used internally by the XML parser. Should be None when calling directly
	# @param rsync_proxy 	the proxy address
	# @param xml_attr not used here
	def set_rsync_proxy(self, xml_path, rsync_proxy, xml_attr):
		# Check type
		if rsync_proxy and not GLIUtility.is_uri(rsync_proxy):
			raise GLIException("RSYNCProxyError", 'fatal', 'set_rsync_proxy',  "Must be a uri!")
		self._rsync_proxy = rsync_proxy

	##
	# Returns RSYNC proxy
	def get_rsync_proxy(self):
		return self._rsync_proxy

	############################################################################
	#### Services
	
	##
	# Set the services to be started on bootup. Services should be
	# seperated by ','. WARNING: This used to be ' ' instead!
	# @param xml_path Used internally by the XML parser. Should be None when calling directly
	# @param services 		comma-separated list of services
	# @param xml_attr Parameter description
	def set_services(self, xml_path, services, xml_attr):
		if type(services) == str:
			services = services.split(',')
		else:
			raise GLIException("ServicesError", 'fatal', 'set_services',  "Invalid input!")

		for service in services:
			if not GLIUtility.is_realstring(service):
				raise GLIException("ServicesError", 'fatal', 'set_services',  service + " must be a valid string!")
		self._services = services

	##
	# This returns a list of the packages:
	def get_services(self):
		return self._services
		
	##
	# Serializes services
	def serialize_services(self):
		if self.get_services() != ():
			self.xmldoc += "<services>"
			self.xmldoc += string.join(self.get_services(), ',')
			self.xmldoc += "</services>"

	############################################################################
	#### Stage Tarball URI

	##
	# stage_tarball_uri is a string that is the full path to the tarball you 
	# wish to use. (ie. 'file:///path/to/mytarball.tar.bz2')
	# @param xml_path Used internally by the XML parser. Should be None when calling directly
	# @param stage_tarball_uri   string of URI for stage tarball location.
	# @param xml_attr   not used here.
	def set_stage_tarball_uri(self, xml_path, stage_tarball_uri, xml_attr):
		# Check type
		if type(stage_tarball_uri) != str:
			raise GLIException("StageTarballURIError", 'fatal', 'set_stage_tarball_uri',  "Must be a string!")

		# Check validity (now done in the FE)
		#if not stage_tarball_uri:
		#	raise GLIException("CustomStage3TarballURIError", 'fatal', 'set_stage_tarball_uri',  "Empty URI!")
		
		self._stage_tarball_uri = stage_tarball_uri

	##
	# Returns stage_tarball_uri
	def get_stage_tarball_uri(self):
		return self._stage_tarball_uri

	############################################################################
	#### Timezone

	##
	# time_zone is a string defining the time zone to use.  
	# Time zones are found in /usr/share/zoneinfo/.  Syntax is 'UTC' or 'US/Eastern'.
	# @param xml_path Used internally by the XML parser. Should be None when calling directly
	# @param time_zone 		string of the intended timezone
	# @param xml_attr 		not used here.
	def set_time_zone(self, xml_path, time_zone, xml_attr):
		# Check type
		if type(time_zone) != str:
			raise GLIException("TimeZoneError", 'fatal', 'set_time_zone',  "Must be a string!")
		self._time_zone = time_zone

	##
	# Returns time_zone
	def get_time_zone(self):
		return self._time_zone

	############################################################################
	#### Users
	
	##
	# Adds a user to the list of users
	# @param xml_path Used internally by the XML parser. Should be None when calling directly
	# @param username  		name of user to be added
	# @param attr=None  	parameters for the user.
	def add_user(self, xml_path, username, attr=None):
		"""
		This will take a username (that is a string) and a set of attributes and it will verify everything is valid
		and convert it into a 7-tuple set. Then it adds this tuple into the users list.
		username and hash are manditory. All other attributes are optional. Or this method will
		take a 7-tuple set, verify it's correctness and then append it to the _users list.
		All items are strings except <uid>, which is an integer, and groups, which is a tuple. 

		The finished tuples look like this:
		( <user name>, <password hash>, (<tuple of groups>), <shell>, <home directory>, <user id>, <user comment> )

		"""
		hash = ''
		shell = None
		groups = None
		shell = None
		homedir = None
		uid = None
		comment = None

		if type(username) == tuple:
			if len(username) != 7:
				raise GLIException("UserError", 'fatal', 'add_user',  "Wrong format for user tuple!")

			username_tmp = username[0]
			hash = username[1]
			groups = username[2]
			shell = username[3]
			homedir = username[4]
			uid = username[5]
			comment = username[6]
			username = username_tmp

			if type(groups) != tuple:
				if groups != None:
					groups = tuple(groups.split(','))
		else:
			for attrName in attr.keys():
				if attrName == 'groups':
					groups = tuple(str(attr[attrName]).split(','))
				elif attrName == 'shell':
					shell = str(attr[attrName])
				elif attrName == 'hash':
					hash = str(attr[attrName])
				elif attrName == 'homedir':
					homedir = str(attr[attrName])
				elif attrName == 'uid':
					if attr[attrName]:
						uid = int(attr[attrName])
				elif attrName == 'comment':
					comment = str(attr[attrName])

		allowable_nonalphnum_characters = '_-'

		if not GLIUtility.is_realstring(username):
			raise GLIException("UserError", 'fatal', 'add_user',  "username must be a non-empty string")

		if username[0] not in (string.lowercase + string.uppercase):
			raise GLIException("UsersError", 'fatal', 'add_user',  "A username must start with a letter!")

		for x in username:
			if x not in (string.lowercase + string.uppercase + string.digits + allowable_nonalphnum_characters):
				raise GLIException("UsersError", 'fatal', 'add_user', "A username must contain only letters, numbers, or these symbols: " + allowable_nonalphnum_characters)

		for user in self._users:
			if username == user[0]:
				raise GLIException("UserError", 'fatal', 'add_user',  "This username already exists!")

		if (hash == None) or (hash == ''):
			raise GLIException("UserError", 'fatal', 'add_user',  "A password hash must be given for every user!")

		self._users.append((username,hash,groups,shell,homedir,uid,comment))

	##
	# Remove "username" from the _users list.
	# @param username    name of user to be removed
	def remove_user(self, username):
		for user in self._users:
			if username == user[0]:
				self._users.remove(user)
				break

	##
	# users is a tuple(user) of tuple's. This sets _users to this set of tuples.
	# @param users   a tuple(user) of tuple's.
	def set_users(self, users):
		self._users = []
		if users != None:
			for user in users:
				self._users.append(user)

	##
	# Returns users
	def get_users(self):
		return self._users
		
	##
	# Serializes users
	def serialize_users(self):
		if self.get_users() != []:
			self.xmldoc += "<users>"
			users = self.get_users()
			for user in users:
				attrstr = ""
				username = user[0]

				if user[1] != None:
					attrstr += "hash=\"%s\" " % user[1]
				if user[2] != None:
					attrstr += "groups=\"%s\" " % string.join(user[2],',')
				if user[3] != None:
					attrstr += "shell=\"%s\" " % user[3]
				if user[4] != None:
					attrstr += "homedir=\"%s\" " % user[4]
				if user[5] != None:
					attrstr += "uid=\"%s\" " % user[5]
				if user[6] != None:
					attrstr += "comment=\"%s\" " % user[6]

				self.xmldoc += "<user %s>%s</user>" % (string.strip(attrstr), username)
			self.xmldoc += "</users>"
