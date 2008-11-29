"""
# Copyright 1999-2005 Gentoo Foundation
# This source code is distributed under the terms of version 2 of the GNU
# General Public License as published by the Free Software Foundation, a copy
# of which can be found in the main directory of this project.
Gentoo Linux Installer

$Id: GLIClientController.py,v 1.83 2006/04/03 03:23:24 agaffney Exp $
Copyright 2004 Gentoo Technologies Inc.

Steps (based on the ClientConfiguration):
	1. Load any modules?  (this may have to be done manually, using a shell - not implemented)
	2. Set the root password (may need to generate one. GLIUtility.generate_random_password())
	3. Add users? (not implemented yet)
	4. Start ssh
	5. Network setup
	6. Start the ArchTemplate doing it's thing. - maybe.. this might get called from elsewhere

"""

import os, GLIClientConfiguration, GLIInstallProfile, GLIUtility, GLILogger, sys, signal, Queue, GLIArchitectureTemplate, GLINotification, traceback
from GLIException import *
from threading import Thread, Event

# Global constants for notifications
NEXT_STEP_READY = 1
INSTALL_DONE = 2

TEMPLATE_DIR = 'templates'

##
# This class provides an interface between the backend and frontend
class GLIClientController(Thread):

	##
	# Initialization function for the GLIClientController class
	# @param configuration=None GLIClientConfiguration object
	# @param install_profile=None GLIInstallProfile object
	# @param pretend=False Pretend mode. If pretending, no steps will actually be performed
	def __init__(self,configuration=None,install_profile=None,pretend=False):
		Thread.__init__(self)

		if configuration == None and os.path.isfile('/etc/gli.conf'):
			self.output("Using /etc/gli.conf...")
			configuration = GLIClientConfiguration.ClientConfiguration()
			configuration.parse('/etc/gli.conf')

		self.set_install_profile(install_profile)
		self.set_configuration(configuration)
		self._install_event = Event()
		self._notification_queue = Queue.Queue(50)
		self._install_mode = None
		self._install_step = -1
		self._install_steps = None
		self._pretend = pretend
		self._thread_pid = 0
		self.setDaemon(True)

	##
	# Sets the GLIInstallProfile object
	# @param install_profile GLIInstallProfile object
	def set_install_profile(self, install_profile):
		self._install_profile = install_profile

	##
	# Returns the GLIInstallProfile object
	def get_install_profile(self):
		return self._install_profile

	##
	# Sets the GLIClientConfiguration object
	# @param configuration GLIClientConfiguration object
	def set_configuration(self, configuration):
		self._configuration = configuration
		if self._configuration != None:
			self._logger = GLILogger.Logger(self._configuration.get_log_file())

	##
	# Returns the GLIClientConfiguration object
	def get_configuration(self):
		return self._configuration

	##
	# This function runs as a second thread to do the actual installation (only used internally)
	def run(self):
		self._thread_pid = os.getpid()
		if self._configuration.get_verbose(): self._logger.log("DEBUG: secondary thread PID is " + str(self._thread_pid))

		interactive = self._configuration.get_interactive()

		if self._configuration == None and not interactive and not self._pretend:
			print "You can not do a non-interactive install without a ClientConfiguration!"
			sys.exit(1)
			
		# Write client configuration profile to disk for debugging purposes
		configuration = open("/tmp/clientconfiguration.xml", "w")
		configuration.write(self._configuration.serialize())
		configuration.close()

		steps = [self.load_kernel_modules, self.set_proxys, self.set_root_passwd, self.configure_networking, self.enable_ssh, self.start_portmap]
		# Do Pre-install client-specific things here.
		while len(steps) > 0:
			try:
				step = steps.pop(0)
				if not self._pretend:
					step()
			except GLIException, error:
				etype, value, tb = sys.exc_info()
				s = traceback.format_exception(etype, value, tb)
				self._logger.log("Exception received during pre-install function '" + repr(step) + "': " + str(error))
				for line in s:
					line = line.strip()
					self._logger.log(line)
				self.addNotification("exception", error)
				self._install_event.clear()
				break
			except Exception, error:
				# Something very bad happened
				etype, value, tb = sys.exc_info()
				s = traceback.format_exception(etype, value, tb)
				self._logger.log("This is a bad thing. An exception occured outside of the normal install errors. The error was: '" + str(error) + "'")
				for line in s:
					line = line.strip()
					self._logger.log(line)
				self.addNotification("exception", error)
				self._install_event.clear()
				break
#			except GLIException, error:
#					self.output("Non-fatal error... continuing...")
#				if error.get_error_level() != 'fatal':
#					self._logger.log("Error: "+ error.get_function_name() + ": " + error.get_error_msg())
#				else:
#					self._logger.log("Pre-install step error: "+ error.get_function_name() + ": " + error.get_error_msg())
#					raise error
		else:
			self._logger.log("Completed pre_install steps")

		# Wait for the self._install_event to be set before starting the installation.
		# start_install() is called to pass here
		self._install_event.wait()
		self._install_event.clear()

		if self._install_profile == None and not interactive:	
			print "You can not do a non-interactive install without an InstallProfile!"
			sys.exit(1)

		#self.output("Starting install now...")

		templates = {	'x86':		'x86ArchitectureTemplate',
				'sparc':	'sparcArchitectureTemplate',
				'amd64':	'amd64ArchitectureTemplate',
				'mips':		'mipsArchitectureTemplate',
				'hppa':		'hppaArchitectureTemplate',
				'alpha':	'alphaArchitectureTemplate',
				'ppc':		'ppcArchitectureTemplate',
				'ppc64':	'ppc64ArchitectureTemplate'
			}

		if self._configuration.get_architecture_template() not in templates.keys():
			self.addNotification("exception", GLIException("UnsupportedArchitectureError", "fatal", "run", self._configuration.get_architecture_template() + ' is not supported by the Gentoo Linux Installer!'))

		try:
			template = __import__(TEMPLATE_DIR + '/' + templates[self._configuration.get_architecture_template()])
			self._arch_template = getattr(template, templates[self._configuration.get_architecture_template()])(self._configuration, self._install_profile, self)
		except ImportError:
			self.addNotification("exception", GLIException("UnsupportedArchitectureError", 'fatal', 'run', 'The Gentoo Linux Installer could not import the install template for this architecture!'))
		except AttributeError:
			self.addNotification("exception", GLIException("UnsupportedArchitectureError", 'fatal', 'run', 'This architecture template was not defined properly!'))

		self._install_mode = self._configuration.get_install_mode()
		tmp_install_steps = self._arch_template.get_install_steps()
		self._install_steps = [step for step in tmp_install_steps if self._install_mode in step['modes']]

		if self._configuration.get_verbose(): self._logger.log("DEBUG: install_steps: " + str(self._install_steps))

		self.addNotification("int", NEXT_STEP_READY)
#		self._install_event.wait()

		# Write install profile to disk for debugging purposes
		configuration = open("/tmp/installprofile.xml", "w")
		configuration.write(self._install_profile.serialize())
		configuration.close()

		while 1:
			if self._install_step >= len(self._install_steps): break
			if self._configuration.get_verbose(): self._logger.log("DEBUG: waiting at top of 'while' loop in CC in secondary thread...waiting to start step " + str(self._install_step+1) + ", " + self._install_steps[(self._install_step+1)]['name'])
			self._install_event.wait()
			if self._configuration.get_verbose(): self._logger.log("DEBUG: Event() cleared at top of 'while' loop in CC in secondary thread...starting step " + str(self._install_step) + ", " + self._install_steps[(self._install_step)]['name'])
#			if self._install_step <= (len(self._install_steps) - 1):
			try:
				if not self._pretend:
					self._install_steps[self._install_step]['function']()
				self._install_event.clear()
				if self.has_more_steps():
					self.addNotification("int", NEXT_STEP_READY)
				else:
					self.addNotification("int", INSTALL_DONE)
			except GLIException, error:
				etype, value, tb = sys.exc_info()
				s = traceback.format_exception(etype, value, tb)
				self._logger.log("Exception received during '" + self._install_steps[self._install_step]['name'] + "': " + str(error))
				for line in s:
					line = line.strip()
					self._logger.log(line)
				self.addNotification("exception", error)
				self._install_event.clear()
			except Exception, error:
				# Something very bad happened
				etype, value, tb = sys.exc_info()
				s = traceback.format_exception(etype, value, tb)
				self._logger.log("This is a bad thing. An exception occured outside of the normal install errors. The error was: '" + str(error) + "'")
				for line in s:
					line = line.strip()
					self._logger.log(line)
				self.addNotification("exception", error)
				self._install_event.clear()
#			else:
#				break

		# This keeps the thread running until the FE exits
		self._install_event.clear()
		self._install_event.wait()

	##
	# Returns the number of steps in the install process
	def get_num_steps(self):
		return len(self._install_steps)

	##
	# Returns information about the next install step
	def get_next_step_info(self):
		return self._install_steps[(self._install_step + 1)]['name']

	##
	# Performs the next install step
	def next_step(self):
		self._install_step = self._install_step + 1
		if self._configuration.get_verbose(): self._logger.log("DEBUG: next_step(): setting Event() flag...starting step " + str(self._install_step) + ", " + self._install_steps[(self._install_step)]['name'])
		self._install_event.set()

	##
	# Retries the current install step
	def retry_step(self):
		self._install_event.set()

	##
	# Returns True if there are more install steps remaining
	def has_more_steps(self):
		return (self._install_step < (len(self._install_steps) - 1))

	##
	# Sets proxy information from the environment
	def set_proxys(self):
		if self._configuration.get_verbose(): self._logger.log("DEBUG: beginning of set_proxys()")
		if self._configuration.get_ftp_proxy() != "":
			os.environ['ftp_proxy'] = self._configuration.get_ftp_proxy()

		if self._configuration.get_http_proxy() != "":
			os.environ['http_proxy'] = self._configuration.get_http_proxy()

		if self._configuration.get_rsync_proxy() != "":
			os.environ['RSYNC_PROXY'] = self._configuration.get_rsync_proxy()
		if self._configuration.get_verbose(): self._logger.log("DEBUG: end of set_proxys()")

	##
	# Loads kernel modules specified in the GLIClientConfiguration object
	def load_kernel_modules(self):
		if self._configuration.get_verbose(): self._logger.log("DEBUG: beginning of load_kernel_modules()")
		modules = self._configuration.get_kernel_modules()
		if self._configuration.get_verbose(): self._logger.log("DEBUG: load_kernel_modules(): modules are " + str(modules))
		for module in modules:
			try:
				if self._configuration.get_verbose(): self._logger.log("DEBUG: load_kernel_modules(): trying to load module " + module)
				ret = GLIUtility.spawn('modprobe ' + module)
				if not GLIUtility.exitsuccess(ret):
					self._logger.log("ERROR! : Could not load module: "+module)
				#	raise GLIException("KernelModuleError", 'warning', 'load_kernel_modules', 'Could not load module: ' + module)
				else:
					self._logger.log('kernel module: ' + module + ' loaded.')
			except KernelModuleError, error:
				self.output(error)
				self._logger.log(error.get_error_level() + '! ' + error.get_error_msg())

	##
	# Sets the root password specified in the GLIClientConfiguration object
	def set_root_passwd(self):
		self._logger.log("Setting root password.")
		if self._configuration.get_root_passwd() != "":
			# The password specified in the configuration is encrypted.
			status = GLIUtility.spawn("echo 'root:" + self._configuration.get_root_passwd() + "' | chpasswd -e")
	
			if not GLIUtility.exitsuccess(status):
				self._logger.log("ERROR! : Could not set the root password on the livecd environment!")
			#	raise GLIException("PasswordError", 'warning', 'set_root_passwd', "Could not set the root password!")
			else:
				self._logger.log("Livecd root password set.")

	##
	# Starts portmap if specified in the GLIClientConfiguration object
	def start_portmap(self):
		if self._configuration.get_verbose(): self._logger.log("DEBUG: beginning of start_portmap()")
		status = GLIUtility.spawn('/etc/init.d/portmap start') #, display_on_tty8=True)
		if not GLIUtility.exitsuccess(status):
			self._logger.log("ERROR! : Could not start the portmap service!")
		#	raise GLIException("PortmapError", 'warning', 'start_portmap', "Could not start the portmap service!")
		else:
			self._logger.log("Portmap started.")

	##
	# Configures networking as specified in the GLIClientConfiguration object
	def configure_networking(self):
		if self._configuration.get_verbose(): self._logger.log("DEBUG: beginning of configure_networking()")
		# Do networking setup right here.
		if self._configuration.get_network_type() != None:
			type = self._configuration.get_network_type()
			if type == "null" or type == "none":
				# don't do anything, it's not our problem if the user specifies this.
				return
			elif type == "dhcp":
				if self._configuration.get_verbose(): self._logger.log("DEBUG: configure_networking(): DHCP selected")
				# Run dhcpcd.
				try:
					interface = self._configuration.get_network_interface()
					dhcp_options = self._configuration.get_network_dhcp_options()
				except:
					self._logger.log("No interface found.. defaulting to eth0.")
					interface = "eth0"
					dhcp_options = ""

				if interface and not dhcp_options:
					if self._configuration.get_verbose(): self._logger.log("DEBUG: configure_networking(): running '/sbin/dhcpcd -n " + interface + "'")
					status = GLIUtility.spawn("/sbin/dhcpcd -t 15 -n " + interface)
				elif interface and dhcp_options:
					if self._configuration.get_verbose(): self._logger.log("DEBUG: configure_networking(): running '/sbin/dhcpcd " + dhcp_options + " " + interface + "'")
					status = GLIUtility.spawn("/sbin/dhcpcd -t 15 " + dhcp_options + " " + interface)
				else:
					if self._configuration.get_verbose(): self._logger.log("DEBUG: configure_networking(): running '/sbin/dhcpcd -n'")
					status = GLIUtility.spawn("/sbin/dhcpcd -t 15 -n")
				if self._configuration.get_verbose(): self._logger.log("DEBUG: configure_networking(): call to /sbin/dhcpcd complete")

				if not GLIUtility.exitsuccess(status):
					raise GLIException("DHCPError", 'fatal', 'configure_networking', "Failed to get a dhcp address for " + interface + ".")

			elif type == "manual" and self._configuration.get_interactive():
				# Drop to bash shell and let them configure it themselves
				print "Please configure & test your network device."
				GLIUtility.spawn_bash()
			elif type == "manual" and not self._interactive.get_interactive():
				print "You cannot manually configure the network in non-interactive mode!"
				print "Please fix either the network settings or the interactive mode!"
				sys.exit(1)
			elif type == "static":
				if self._configuration.get_verbose(): self._logger.log("DEBUG: configure_networking(): setting static IP")
				# Configure the network from the settings they gave.
				net_interface = self._configuration.get_network_interface()
				net_ip        = self._configuration.get_network_ip()
				net_broadcast = self._configuration.get_network_broadcast()
				net_netmask   = self._configuration.get_network_netmask()
				if not GLIUtility.set_ip(net_interface, net_ip, net_broadcast, net_netmask):
					raise GLIException("SetIPError", 'fatal', 'configure_networking', "Could not set the IP address!")

				route = self._configuration.get_network_gateway()
				if not GLIUtility.set_default_route(route):
					raise GLIException("DefaultRouteError", 'fatal','configure_networking', "Could not set the default route!")

				dns_servers = self._configuration.get_dns_servers()
				if dns_servers:
					try:
						resolv_conf = open("/etc/resolv.conf", "w")
						for dns_server in dns_servers:
							resolv_conf.write("nameserver " + dns_server + "\n")
						resolv_conf.close()
					except:
						raise GLIException("DNSServerError", 'fatal','configure_networking', "Could not set the DNS servers!")

				if self._configuration.get_verbose(): self._logger.log("DEBUG: configure_networking(): done setting static IP")

	##
	# Enables SSH if specified in the GLIClientConfiguration object
	def enable_ssh(self):
		if self._configuration.get_verbose(): self._logger.log("DEBUG: beginning of enable_ssh()")
		if self._configuration.get_enable_ssh():
			status = GLIUtility.spawn("/etc/init.d/sshd start")
			if not GLIUtility.exitsuccess(status):
				self._logger.log("ERROR! : Could not start the SSH daemon!")
			#	raise GLIException("SSHError", 'warning','enable_ssh',"Could not start SSH daemon!")
			else:
				self._logger.log("SSH Started.")

	##
	# Loads the install profile
	def load_install_profile(self):
		install_profile=None
		if self._install_profile == None:
			if self._configuration != None:
				success = GLIUtility.get_uri(self._configuration.get_profile_uri(),'/tmp/install_profile.xml')
				if success:
					self._logger.log("Profile downloaded succesfully, loading it now.")
					self.output("Profile downloaded... loading it now...")
					install_profile = GLIInstallProfile.InstallProfile()
					install_profile.parse('/tmp/install_profile.xml')
				else:
					raise GLIException("InstallProfileError", 'fatal', 'get_install_profile', 'Could not download/copy the install profile from: ' + self._configuration.get_profile_uri())

		self._install_profile = install_profile

	##
	# Starts the install
	def start_install(self):
		self._install_event.set()

	##
	# Starts the secondary thread running. The thread will wait to continue until start_install() is called
	def start_pre_install(self):
		self.start()

	##
	# Cleans up after a failed install
	def start_failure_cleanup(self):
		self._arch_template.install_failed_cleanup()

	##
	# Displays specified output
	# @param str String to display
	def output(self, str):
		print str

	##
	# Returns a notification object from the queue
	def getNotification(self):
		notification = None
		try:
			notification = self._notification_queue.get_nowait()
		except:
			pass
		return notification

	##
	# Adds a notification object to the queue
	# @param type Notification type
	# @param data Notification contents
	def addNotification(self, type, data):
		notification = GLINotification.GLINotification(type, data)
		try:
			self._notification_queue.put_nowait(notification)
		except:
			# This should only ever happen if the frontend is not checking for notifications
			pass
