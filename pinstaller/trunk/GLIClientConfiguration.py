"""
# Copyright 1999-2005 Gentoo Foundation
# This source code is distributed under the terms of version 2 of the GNU
# General Public License as published by the Free Software Foundation, a copy
# of which can be found in the main directory of this project.
Gentoo Linux Installer

$Id: GLIClientConfiguration.py,v 1.44 2006/04/17 05:31:53 agaffney Exp $
Copyright 2004 Gentoo Technologies Inc.

The GLIClientConfiguration module contains the ClientConfiguration class
which is a singleton class that represents configuration data that is
used by the installer client during installation. Data that is part of
the actual install is contained in GLIInstallProfile.

Usage:
	from GLIClientConfiguration import ClientConfiguration

	PROCEDURE TO ADD NEW VARIABLES:  (PLEASE KEEP IN ALPHABETICAL ORDER)
	1. Add a handler to the list.  If the variable has children make sure you do it right.
	   Look at the existing structure to get an idea.
	2. Create a section for the two or three functions.
	3. Create the get_variable_name and set_variable_name functions.
	   Ensure the set function has correct error checking.
	4. If a simple value, add to the list in the general serialize() function.
	   If more complex add a serialize_variable_name to the list of special cases.
	   Then add the serialize_variable_name function to the section for the variable.
"""

import string, re, GLIUtility, SimpleXMLParser, os.path
import xml.dom.minidom
from GLIException import *

class ClientConfiguration:

	##
	# Initializes the ClientConfiguration.
	def __init__(self):
		self._architecture_template = "x86"
		self._profile_uri = ""
	
		# This is the full path to the logfile
		self._log_file = "/var/log/installer.log"
		
		# This is the root mount point
		self._root_mount_point = "/mnt/gentoo"

		# Initialize some variables so we never reference a variable that never exists.
		self._dns_servers = ()
		self._network_type = None
		self._network_interface = ""
		self._network_ip = ""
		self._network_broadcast = ""
		self._network_dhcp_options = ""
		self._network_netmask = ""
		self._network_gateway = ""
		self._enable_ssh = False
		self._root_passwd = ""
		self._interactive = True
		self._kernel_modules = ()
		self._ftp_proxy = ""
		self._http_proxy = ""
		self._rsync_proxy = ""
		self._verbose = False
		self._install_mode = "normal"
		self.data = ""  # used for serialization

		self._parser = SimpleXMLParser.SimpleXMLParser()

		self._parser.addHandler('client-configuration/architecture-template', self.set_architecture_template)
		self._parser.addHandler('client-configuration/dns-servers', self.set_dns_servers)
		self._parser.addHandler('client-configuration/enable-ssh', self.set_enable_ssh)
		self._parser.addHandler('client-configuration/ftp-proxy', self.set_ftp_proxy)
		self._parser.addHandler('client-configuration/http-proxy', self.set_http_proxy)
		self._parser.addHandler('client-configuration/install-mode', self.set_install_mode)
		self._parser.addHandler('client-configuration/interactive', self.set_interactive)
		self._parser.addHandler('client-configuration/kernel-modules', self.set_kernel_modules)
		self._parser.addHandler('client-configuration/log-file', self.set_log_file)
		self._parser.addHandler('client-configuration/network-interface', self.set_network_interface)
		self._parser.addHandler('client-configuration/network-ip', self.set_network_ip)
		self._parser.addHandler('client-configuration/network-broadcast', self.set_network_broadcast)
		self._parser.addHandler('client_configuration/network-dhcp-options', self.set_network_dhcp_options)
		self._parser.addHandler('client-configuration/network-netmask', self.set_network_netmask)
		self._parser.addHandler('client-configuration/network-gateway', self.set_network_gateway)
		self._parser.addHandler('client-configuration/network-type', self.set_network_type)
		self._parser.addHandler('client-configuration/profile-uri', self.set_profile_uri)
		self._parser.addHandler('client-configuration/root-mount-point', self.set_root_mount_point)
		self._parser.addHandler('client-configuration/root-passwd', self.set_root_passwd)
		self._parser.addHandler('client-configuration/rsync-proxy', self.set_rsync_proxy)
		self._parser.addHandler('client-configuration/verbose', self.set_verbose)
	##
	# Parses the given filename populating the client_configuration.
	# @param filename the file to be parsed.  This should be a URI actually.
	def parse(self, filename):
		self._parser.parse(filename)

	##
	# Serializes the Client Configuration into an XML format that is returned.
	def serialize(self):
		fntable ={	'architecture-template': self.get_architecture_template,
					'enable-ssh': self.get_enable_ssh,
					'ftp-proxy': self.get_ftp_proxy,
					'http-proxy': self.get_http_proxy,
					'install-mode': self.get_install_mode,
					'interactive': self.get_interactive,
					'log-file': self.get_log_file,
					'network-broadcast': self.get_network_broadcast,
					'network-dhcp-options': self.get_network_dhcp_options,
					'network-gateway': self.get_network_gateway,
					'network-interface': self.get_network_interface,
					'network-ip': self.get_network_ip,
					'network-netmask': self.get_network_netmask,
					'network-type':	self.get_network_type,
					'profile-uri': self.get_profile_uri,
					'root-mount-point': self.get_root_mount_point,
					'root-passwd': self.get_root_passwd,
					'rsync-proxy': self.get_rsync_proxy,
					'verbose': self.get_verbose,
				}
		self.data = "<client-configuration>"

		for key in fntable.keys():
			self.data += "<%s>%s</%s>" % (key, fntable[key](), key)

		# Serialize the special cases.
		self.serialize_dns_servers()
		self.serialize_kernel_modules()

		# Add closing tag
		self.data += "</client-configuration>"
		
		#Finish by putting it all in nice XML.
		dom = xml.dom.minidom.parseString(self.data)
		return dom.toprettyxml()
		
	############################################################################
	#### Architecture Template
	
	##
	# Sets the architecture to be used for the install.
	# @param xml_path not used here.
	# @param architecture_template the architecture to be installed
	# @param xml_attr not used here.
	def set_architecture_template(self, xml_path, architecture_template, xml_attr):
		if not architecture_template in ["x86", "amd64", "ppc", "sparc", "hppa", "alpha"]:
			raise GLIException("UnsupportedArchitectureTemplateError", 'fatal','set_architecture_template', 'Architecture Template specified is not supported!')
		self._architecture_template = architecture_template
	##
	# Returns the architecture_template
	def get_architecture_template(self):
		return self._architecture_template
	
	# This variable has a simple serialize function.
	
	############################################################################
	#### DNS Servers List

	##
	# Sets the dns servers
	# @param xml_path not used here.
	# @param nameservers space-separated list of nameservers
	# @param xml_attr not used here.
	def set_dns_servers(self, xml_path, nameservers, xml_attr):
		if type(nameservers) == str:
			nameservers = nameservers.split(" ")
			dns = []
			for server in nameservers:
				dns.append(server)
		self._dns_servers = tuple(dns)

	##
	# Returns the list of dns servers
	# @param self Parameter description
	def get_dns_servers(self):
		return self._dns_servers

	##
	# Serialization for the DNS servers
	def serialize_dns_servers(self):
		# Special Case the kernel modules
		self.data += "<dns-servers>%s</dns-servers>" % " ".join(self.get_dns_servers())

	# This variable has a simple serialize function.
	
	############################################################################
	#### Enable SSH Decision for livecd environment

	##
	# Choose whether or not to enable SSH.
	# @param xml_path not used here.
	# @param enable_ssh a True/False bool value here or a string
	# @param xml_attr not used here.
	def set_enable_ssh(self, xml_path, enable_ssh, xml_attr):
		if type(enable_ssh) == str:
			enable_ssh = GLIUtility.strtobool(enable_ssh)
		self._enable_ssh = enable_ssh

	##
	# Returns the choice of whether or not to enable SSH (True/False)
	# @param self Parameter description
	def get_enable_ssh(self):
		return self._enable_ssh

	# This variable has a simple serialize function.
	
	############################################################################
	#### FTP Proxy Address Information for livecd environment

	##
	# Sets the FTP proxy URI
	# @param xml_path not used here.
	# @param proxy a URI
	# @param xml_attr not used here.
	def set_ftp_proxy(self, xml_path, proxy, xml_attr):
		self._ftp_proxy = proxy

	##
	# Returns the FTP proxy.
	# @param self Parameter description
	def get_ftp_proxy(self):
		return self._ftp_proxy

	# This variable has a simple serialize function.
	
	############################################################################
	#### HTTP Proxy Address Information for livecd environment

	##
	# Sets the HTTP proxy URI
	# @param xml_path not used here.
	# @param proxy a URI
	# @param xml_attr not used here.
	def set_http_proxy(self, xml_path, proxy, xml_attr):
		self._http_proxy = proxy

	##
	# Returns the HTTP proxy
	def get_http_proxy(self):
		return self._http_proxy

	# This variable has a simple serialize function.
	
	############################################################################
	#### Install Mode

	##
	# Sets the install mode. (currently "normal", "stage4", or "chroot")
	# @param xml_path not used here.
	# @param install_mode Install mode
	# @param xml_attr not used here.
	def set_install_mode(self, xml_path, install_mode, xml_attr):
		self._install_mode = install_mode

	##
	# Returns install mode
	# @param self Parameter description
	def get_install_mode(self):
		return self._install_mode

	# This variable has a simple serialize function.
	
	############################################################################
	#### Interactive Install

	##
	# Sets whether or not to be an interactive install. (boolean)
	# @param xml_path not used here.
	# @param interactive True/False bool value or a string.
	# @param xml_attr not used here.
	def set_interactive(self, xml_path, interactive, xml_attr):
		if type(interactive) != bool:
			interactive = GLIUtility.strtobool(interactive)
		self._interactive = interactive

	##
	# Returns bool value on interactive install choice.
	# @param self Parameter description
	def get_interactive(self):
		return self._interactive

	# This variable has a simple serialize function.
	
	############################################################################
	#### Set Kernel Modules to be loaded for the livecd environment

	##
	# Sets a list of modules to load on the livecd environment.
	# @param xml_path not used here.
	# @param modules string of modules
	# @param xml_attr not used here.
	def set_kernel_modules(self, xml_path, modules, xml_attr):
		self._kernel_modules = tuple(string.split(modules))

	##
	# Returns the list of kernel modules to load on the livecd environment.
	def get_kernel_modules(self):
		return self._kernel_modules

	##
	# Serialization for the kernel module list.  joins together the modules.
	def serialize_kernel_modules(self):
		# Special Case the kernel modules
		self.data += "<kernel-modules>%s</kernel-modules>" % " ".join(self.get_kernel_modules())
	
	############################################################################
	#### Log File Location

	##
	# Sets the log filename.
	# @param xml_path not used here.
	# @param log_file the name of the logfile for the CC to use.
	# @param xml_attr not used here.
	def set_log_file(self, xml_path, log_file, xml_attr):
		self._log_file = log_file

	##
	# Returns the log filename
	def get_log_file(self):
		return self._log_file
	
	# This variable has a simple serialize function.
	
	############################################################################
	#### Network Broadcast Address for livecd environment

	##
	# Sets the network broadcast address for the livecd environment
	# @param xml_path not used here.
	# @param broadcast the network broadcast address
	# @param xml_attr= None
	def set_network_broadcast(self, xml_path, broadcast, xml_attr=None):
		if not GLIUtility.is_ip(broadcast):
			raise GLIException("IPAddressError", 'fatal','set_network_broadcast', 'The specified broadcast is not a valid IP Address!')
		self._network_broadcast = broadcast
	
	##
	# Returns the network broadcast address
	def get_network_broadcast(self):
		return self._network_broadcast

	# This variable has a simple serialize function.
	
	############################################################################
	#### Network DHCP Options for livecd environment

	##
	# Sets the network dhcp options for the livecd environment
	# @param xml_path not used here.
	# @param broadcast the dhcp options
	# @param xml_attr= None
	def set_network_dhcp_options(self, xml_path, options, xml_attr=None):
		if not GLIUtility.is_realstring(options):
			raise GLIException("BadDHCPOptionsError", 'fatal','set_network_dhcp_options', 'The specified dhcp_optioons is not a valid string!')
		self._network_dhcp_options = options
	
	##
	# Returns the network dhcp options
	def get_network_dhcp_options(self):
		return self._network_dhcp_options

	# This variable has a simple serialize function.
	
	############################################################################
	#### Network Gateway Address for livecd environment
	
	##
	# Sets the network gateway for the livecd environment
	# @param xml_path not used here.
	# @param gateway the network gateway
	# @param xml_attr= None
	def set_network_gateway(self, xml_path, gateway, xml_attr=None):
		if not GLIUtility.is_ip(gateway):
			raise GLIException("IPAddressError", 'fatal', 'set_network_gateway', "The gateway IP provided is not a valid gateway!!")
		self._network_gateway = gateway
	
	##
	# Returns the network gateway
	def get_network_gateway(self):
		return self._network_gateway
		
	# This variable has a simple serialize function.
		
	############################################################################
	#### Network Interface Information for livecd environment

	##
	# Sets the network interface configuration info for the livecd environment
	# @param xml_path not used here.
	# @param interface the interface to talk over
	# @param xml_attr= None
	def set_network_interface(self, xml_path, interface, xml_attr=None):
		if not GLIUtility.is_eth_device(interface):
			raise GLIException("InterfaceError", 'fatal', 'set_network_interface', "Interface " + interface + " must be a valid device!")
		self._network_interface = interface
	
	##
	# Returns the network interface
	def get_network_interface(self):
		return self._network_interface

	# This variable has a simple serialize function.
	
	############################################################################
	#### Network IP Address for livecd environment

	##
	# Sets the network ip address for the livecd environment
	# @param xml_path not used here.
	# @param ip the ip address
	# @param xml_attr= None
	def set_network_ip(self, xml_path, ip, xml_attr=None):
		if not GLIUtility.is_ip(ip):
			raise GLIException("IPAddressError", 'fatal', 'set_network_ip', 'The specified IP ' + ip + ' is not a valid IP Address!')
		self._network_ip = ip
	
	##
	# Returns the network ip address
	def get_network_ip(self):
		return self._network_ip
		
	# This variable has a simple serialize function.
	
	############################################################################
	#### Network Netmask Address for livecd environment

	##
	# Sets the network netmask for the livecd environment
	# @param xml_path not used here.
	# @param netmask the network netmask
	# @param xml_attr= None
	def set_network_netmask(self, xml_path, netmask, xml_attr=None):
		if not GLIUtility.is_ip(netmask):
			raise GLIException("IPAddressError", 'fatal','set_network_netmask', 'The specified netmask is not a valid IP Address!')
		else:
			# Need to guess the netmask... just in case (probably need the gateway..)
			pass
			
		self._network_netmask = netmask
	
	##
	# Returns the network netmask
	def get_network_netmask(self):
		return self._network_netmask
		
	# This variable has a simple serialize function.
	
	
	############################################################################
	#### Network Type Information for livecd environment (static or dhcp)

	##
	# Sets the network configuration info for the livecd environment
	# @param xml_path not used here.
	# @param network_type the network type, either static or dhcp
	# @param xml_attr=None
	def set_network_type(self, xml_path, network_type, xml_attr):
		if not network_type in ('static', 'dhcp', 'null', 'none'):
			raise GLIException("NoSuchTypeError", 'fatal','set_network_type',"You can only have a static or dhcp network!")

		self._network_type = network_type

	##
	# Returns the network type
	def get_network_type(self):
		return self._network_type

	# This variable has a simple serialize function.
	
	############################################################################
	#### Install Profile URI
	
	##
	# Sets the profile_uri for use in non-interactive installs
	# @param xml_path not used here.
	# @param profile_uri location of the profile
	# @param xml_attr not used here.
	def set_profile_uri(self, xml_path, profile_uri, xml_attr):
		if profile_uri != None and not GLIUtility.is_uri(profile_uri):
			raise GLIException("URIError", 'fatal', 'set_profile_uri',"The URI specified is not valid!")
		self._profile_uri = profile_uri
	
	##
	# Returns the profile_uri
	def get_profile_uri(self):
		return self._profile_uri

	# This variable has a simple serialize function.

	############################################################################
	#### Root Mount Point For New System

	##
	# Sets the root_mount_point for the new system to be installed to
	# @param xml_path not used here.
	# @param root_mount_point new location for the root mount point
	# @param xml_attr not used here.
	def set_root_mount_point(self, xml_path, root_mount_point, xml_attr):
		self._root_mount_point = root_mount_point

	##
	# Returns the root_mount_point
	def get_root_mount_point(self):
		return self._root_mount_point

	# This variable has a simple serialize function.

	############################################################################
	#### Root Password Selection for livecd environment

	##
	# Sets the root password on the livecd.  This is supposed to be given a hash.
	# @param xml_path not used here.
	# @param passwd a hashed password to be set on the livecd environment.
	# @param xml_attr not used here.
	def set_root_passwd(self, xml_path, passwd, xml_attr):
		self._root_passwd = passwd

	##
	# Returns the hash of the root password for the livecd environment
	def get_root_passwd(self):
		return self._root_passwd

	# This variable has a simple serialize function.
	
	############################################################################
	#### RSYNC Proxy Address Information for livecd environment

	##
	# Sets the RSYNC proxy URI
	# @param xml_path not used here.
	# @param proxy a URI
	# @param xml_attr not used here.
	def set_rsync_proxy(self, xml_path, proxy, xml_attr):
		self._rsync_proxy = proxy

	##
	# Returns the RSYNC proxy
	def get_rsync_proxy(self):
		return self._rsync_proxy

	##
	# Sets the Verbose mode (DEBUG mode)
	# @param xml_path not used here.
	# @param verbose flag. boolean.
	# @param xml_attr not used here.
	def set_verbose(self, xml_path, verbose, xml_attr):
		if type(verbose) == str:
			verbose = GLIUtility.strtobool(verbose)
		self._verbose = verbose

	##
	# Returns the verbose (DEBUG) flag
	def get_verbose(self):
		return self._verbose
