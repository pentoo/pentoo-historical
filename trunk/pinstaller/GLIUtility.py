"""
# Copyright 1999-2005 Gentoo Foundation
# This source code is distributed under the terms of version 2 of the GNU
# General Public License as published by the Free Software Foundation, a copy
# of which can be found in the main directory of this project.
Gentoo Linux Installer

The GLIUtility module contians all utility functions used throughout GLI.
"""

import string, os, re, shutil, sys, random, commands, crypt, pty, select
from GLIException import *

##
# Check to see if a string is actually a string, and if it is not null. Returns bool.
# @param string_a    string to be checked.
def is_realstring(string):
	# Make sure it is a string
	if not isinstance(string, (str, unicode)):
		return False
		
	return True

##
# Checks to see if x is a numeral by doing a type conversion.
# @param x   value to be checked
def is_numeric(x):
	try:
		float(x)
	except ValueError:
		return False
	else:
		return True

##
# Check to see if a string is a valid ip. Returns bool.
# @param ip 	ip to be checked.
def is_ip(ip):
	# Make sure it is a string
	if not is_realstring(ip):
		return False

	# Compile the regular expression that validates an IP. It will also check for valid ranges.
	expr = re.compile('(([0-9]|[01]?[0-9]{2}|2([0-4][0-9]|5[0-5]))\.){3}([0-9]|[01]?[0-9]{2}|2([0-4][0-9]|5[0-5]))$')

	# Run the test.
	res = expr.match(ip)

	# Return True only if there are results.
	return(res != None)

##
# Check to see if mac is a valid MAC address. Make sure use format_mac
# before using this function. Returns bool.
# @param mac   mac address to be checked.
def is_mac(mac):
	expr = re.compile('([0-9A-F]{2}:){5}[0-9A-F]{2}')
	res = expr.match(mac)
	return(res != None)

##
# Format's a mac address properly. Returns the correctly formatted MAC. (a string)
# @param mac   mac address to be formatted
def format_mac(mac):
	mac = string.replace(mac, '-', ':')
	mac = string.upper(mac)

	mac = string.split(mac, ':')
	for i in range(0, len(mac)):
		if len(mac[i]) < 2:
			mac[i] = "0" + mac[i]
	return string.join(mac, ":")

##
# Removes leading zero's from an IP address. For example
# trim_ip('192.168.01.002') => '192.168.1.2'
# @param ip  IP address to be trimmed
def trim_ip(ip):
	# Remove leading zero's on the first octet
	ip = re.sub('^0{1,2}','',ip)

	# Remove leading zero's from the other octets
	res = re.sub('((?<=\.)(00|0)(?P<num>\d))','\g<num>',ip)

	return(res)

##
# Check to see if the string passed is a valid device. Returns bool.
# @param device    device to be checked
def is_device(device):
	# Make sure it is a string
	if not is_realstring(device):
		return False
			
	# Make sure the string starts with /dev/
	if device[0:5] != '/dev/':
		return False
			
	# Check to make sure the device exists
	return os.access(device, os.F_OK)
		
##
# Check to see if the string is a valid hostname. Returns bool.
# @param hostname   host to be checked
def is_hostname(hostname):
	# Make sure it is a string
	if not is_realstring(hostname):
		return False
			
	expr = re.compile('^([a-zA-Z0-9-_\.])+\.[a-zA-Z]{2,4}$')
	res = expr.match(hostname)

	return(res != None)
		
##
# Check to see if the string is a valid path. Returns bool.
# @param path 	Path to be checked.
def is_path(path):
	# Make sure it is a string
	if not is_realstring(path):
		return False

	# Create a regular expression that matches all words and the symbols '-_./' _ is included in the \w
	expr = re.compile('^[\w\.\-\/~]+$')

	# Run the match
	res = expr.match(path)

	# Return True only if there are results
	return(res != None)
		
##
# Check to see if the string is a valid file. Returns bool.
# @param file  file to be checked for validity.
def is_file(file):
	# Make sure it is a string
	if not is_realstring(file):
		return False
			
	# Check to make sure the device exists
	return os.access(file, os.F_OK)

##
# Parse a URI. Returns a tuple (protocol, username, password, host, port, path)
# Returns None if URI is invalid.
# @param uri URI to be parsed
def parse_uri(uri):
	# Compile the regex
	expr = re.compile('(\w+)://(?:([^:@]+)(?::([^@]+))?@)?(?:([a-zA-Z0-9.-]+)(?::(\d+))?)?(/.*)')

	# Run it against the URI
	res = expr.match(uri)

	if not res:
		# URI doesn't match regex and therefore is invalid
		return None

	# Get tuple of matches
	# 0 - Protocol
	# 1 - Username
	# 2 - Password
	# 3 - Host
	# 4 - Port
	# 5 - Path
	uriparts = res.groups()
	return uriparts

##
# Check to see if the string is a valid URI. Returns bool.
# @param uri 				URI to be validated
# @param checklocal=True	Whether to look for a local uri.
def is_uri(uri, checklocal=True):
	# Make sure it is a string
	if not is_realstring(uri):
		return False
			
	# Set the valid uri types
	valid_uri_types = ('ftp', 'rsync', 'http', 'file', 'https', 'scp')
		
	# Parse the URI
	uriparts = parse_uri(uri)
	if not uriparts:
		# Invalid URI
		return False

	# Check for valid uri type
	if not uriparts[0] in valid_uri_types:
		return False
		
	# If checklocal and the URI is a local file, check to see if the file exists
	if uriparts[0] == "file" and checklocal:
		if not is_file(uriparts[5]):
			return False
		
	return True

##
# Converts a string to a boolean value. anything not "True" is deemed false.
# @param input  must be a string so it can be converted to boolean.
def strtobool(input):
	if type(input) != str:
		raise GLIException("GLIUtilityError", 'fatal','strtobool',"The input must be a string!")

	if string.lower(input) == 'true':
		return True
	else:
		return False

##
# Check to see if device is a valid ethernet device. Returns bool.
# @param device  device to be checked
def is_eth_device(device):
	# Make sure it is a string
	if not is_realstring(device):
		return False

	# Old way w/ reg ex here:
	# Create a regular expression to test the specified device.
	#expr = re.compile('^(eth|wlan|ppp)([0-9]{1,2})(:[0-9]{1,2})?$')
	# Run the match
	#res = expr.match(device)
	# Return True only if there are results
	#return(res != None)

	status, output = spawn("/sbin/ifconfig -a | grep -e '^[A-Za-z]'| cut -d ' ' -f 1 | grep '"+ device + "'", return_output=True)
	if output:
		return True
	return False

##
# Will return a list of devices found in ifconfig.
def get_eth_devices():
	status, output = spawn("/sbin/ifconfig -a | grep -e '^[A-Za-z]'| cut -d ' ' -f 1", return_output=True)
	return output.split()

##
# Checks to see if device is a valid NFS device
# @param device 	device to be checked
def is_nfs(device):
	if not is_realstring(device):
		return False

	colon_location = device.find(':')

	if colon_location == -1:
		return False

	host = device[:colon_location]
	path = device[colon_location+1:]

	return((is_ip(host) or is_hostname(host)) and is_path(path))

##
# Sets the network ip (used for the livecd environment)
# @param dev 		device to be configured
# @param ip 		ip address of device
# @param broadcast 	broadcast address of device
# @param netmask 	netmask address of device
def set_ip(dev, ip, broadcast, netmask):
	if not is_ip(ip) or not is_ip(netmask) or not is_ip(broadcast):
		raise GLIException("GLIUtilityError", 'fatal','set_ip', ip + ", " + netmask + "and, " + broadcast + "must be a valid IP's!")
	if not is_eth_device(dev):
		raise GLIException("GLIUtilityError", 'fatal','set_ip', dev + "is not a valid ethernet device!")

	options = "%s inet %s broadcast %s netmask %s" % (dev, ip, broadcast, netmask)

	status = spawn("ifconfig " + options)

	if not exitsuccess(status):
		return False

	return True

##
# Sets the default route (used for the livecd environment)
# @param route  	ip addresss of gateway.
def set_default_route(route):
	if not is_ip(route):
		raise GLIException("GLIUtilityError", 'fatal', 'set_default_route', route + " is not an ip address!")
	status = spawn("route add default gw " + route)

	if not exitsuccess(status):
		return False

	return True

##
# Will run a command with various flags for the style of output and logging.
# 
# @param cmd 					The command to be run
# @param quiet=False 			Whether or not to filter output to /dev/null
# @param logfile=None 			if provied will log output to the given filename
# @param display_on_tty8=False 	will output to tty8 instead of the screen.
# @param chroot=None 			will run the command inside the new chroot env.
# @param append_log=False 		whether to start over on the logfile or append.
# @param return_output=False 	Returns the output along with the exit status
def spawn(cmd, quiet=False, logfile=None, display_on_tty8=False, chroot=None, append_log=False, return_output=False, linecount=0, match=None, cc=None, status_message=None):
	# This is a hack since spawn() can't access _logger...set to True for verbose output on console
	debug = False

	if chroot:
		wrapper = open(chroot+"/var/tmp/spawn.sh", "w")
		wrapper.write("#!/bin/bash -l\n" + cmd + "\nexit $?\n")
		wrapper.close()
		cmd = "chmod a+x " + chroot + "/var/tmp/spawn.sh && chroot " + chroot + " /var/tmp/spawn.sh 2>&1"
	else:
		cmd += " 2>&1 "
	if debug:
		print "Command: " + cmd

	output = ""

	if logfile:
		if append_log:
			fd_logfile = open(logfile,'a')
		else:
			fd_logfile = open(logfile,'w')

	if display_on_tty8:
		fd_tty = open('/dev/tty8','w')

	# Set initial sub-progress display
	if cc:
		cc.addNotification("progress", (0, status_message))

	# open a read only pipe
	ro_pipe = os.popen(cmd, 'r')

	# read a line from the pipe and loop until
	# pipe is empty
#	data = ro_pipe.readline()
	seenlines = 0
	last_percent = 0

	while 1:
#		data = ro_pipe.read(16384)
		data = os.read(ro_pipe.fileno(), 16384)
		if debug:
			print "DEBUG: read some data...length " + str(len(data))
		if not data:
			if linecount and cc:
				if debug:
					print "DEBUG: end of stream...progress is 1"
				cc.addNotification("progress", (1, status_message))
			break

#		print "DEBUG: spawn(): data is " + str(len(data)) + " bytes long"

		if logfile:
			fd_logfile.write(data)
#			fd_logfile.flush()

		if display_on_tty8:
			fd_tty.write(data)
			fd_tty.flush()

		if return_output:
			output += data

		if linecount and cc:
			lastpos = -1
			while 1:
				lastpos = data.find("\n", lastpos + 1)
				if lastpos == -1: break
#				if match:
#					if not re.match(match, uri):
#						continue
				seenlines += 1
				if debug:
					print "DEBUG: seenlines=" + str(seenlines)
			percent = float(seenlines) / linecount
			if debug:
				print "DEBUG: percent=" + str(percent)
#			print "DEBUG: spawn(): seenlines=" + str(seenlines) + ", linecount=" + str(linecount) + ", percent=" + str(percent)
			if int(percent * 100) >= (last_percent + 5):
				last_percent = int(percent * 100)
				if debug:
					print "DEBUG: setting next progress point...last_percent=" + str(last_percent)
				cc.addNotification("progress", (percent, status_message))
#				print "DEBUG: spawn(): send notification " + str((percent, status_message))

#		data = ro_pipe.readline()

	# close the file descriptors
	if logfile: fd_logfile.close()
	if display_on_tty8: fd_tty.close()

	# close the pipe and save return value
	ret = ro_pipe.close() or 0

	if return_output:
		return ret, output
	else:
		return ret

##
# Will check the status of a spawn result to see if it did indeed return successfully.
# @param status Parameter description
def exitsuccess(status):
	if os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0:
		return True
	return False

##
# Will produce a bash shell with a special prompt for the installer.
def spawn_bash():
	os.putenv("PROMPT_COMMAND","echo \"Type 'exit' to return to the installer.\"")
	status = spawn("bash")
	return status

##
# Will download or copy a file/uri to a location
# @param uri 	uri to be fetched.
# @param path 	destination for the file.
def get_uri(uri, path, cc=None):
	uri = uri.strip()
	status = 0

	if re.match('^(ftp|http(s)?)://',uri):
		if cc:
			status = spawn("wget --progress=dot " + uri + " -O " + path + r""" 2>&1 | sed -u -e 's:^.\+\([0-9]\+\)%.\+$:\1:' | while read line; do [ "$line" = "$tmp_lastline" ] || echo $line | grep -e '^[1-9]'; tmp_lastline=$line; done""", linecount=100, cc=cc, status_message="Fetching " + uri.split('/')[-1])
		else:
			status = spawn("wget --quiet " + uri + " -O " + path)
	elif re.match('^rsync://', uri):
		status = spawn("rsync --quiet " + uri + " " + path)
	elif uri.startswith("scp://"):
		# Get tuple of matches
		# 0 - Protocol
		# 1 - Username
		# 2 - Password
		# 3 - Host
		# 4 - Port
		# 5 - Path
		uriparts = parse_uri(uri)
		scpcmd = "scp "
		if uriparts[4]:
			scpcmd += "-P " + uriparts[4] + " "
		if uriparts[1]:
			scpcmd += uriparts[1] + "@"
		scpcmd += uriparts[3] + ":" + uriparts[5] + " " + path
		pid, child_fd = pty.fork()
		if not pid:
			os.execvp("scp", scpcmd.split())
		else:
			while 1:
				r, w, e = select.select([child_fd], [], [])
				if child_fd in r:
					try:
						data = os.read(child_fd, 1024)
					except:
						pid2, status = os.waitpid(pid, 0)
						break
					if data.endswith("assword: "):
						if uriparts[2]:
							os.write(child_fd, uriparts[2] + "\n")
						else:
							os.write(child_fd, "\n")
					elif data.endswith("Are you sure you want to continue connecting (yes/no)? "):
						os.write(child_fd, "yes\n")
				else:
					pid2, status = os.waitpid(pid, os.WNOHANG)
					if pid2:
						break

	elif re.match('^file://', uri):
		r_file = uri[7:]
		if os.path.isfile(r_file):
			shutil.copy(r_file, path)
			if not os.path.isfile(path):
				raise GLIException("GLIUtilityError", 'fatal', 'get_uri', "Cannot copy " + r_file + " to " + path)
	else:
		# Just in case a person forgets file://
		if os.path.isfile(uri):
			shutil.copy(uri, path)
			if not os.path.isfile(path):
				raise GLIException("GLIUtilityError", 'fatal', 'get_uri', "Cannot copy " + r_file + " to " + path)
		else:
			raise GLIException("GLIUtilityError", 'fatal', 'get_uri', "File does not exist or URI is invalid!")

	if exitsuccess(status) and is_file(path):
		return True
	
	return False

##
# Pings a host.  Used to test network connectivity.
# @param host 	host to be pinged.
def ping(host):
	host = str(host)
	if not (is_hostname(host) or is_ip(host)):
		return False    #invalid IP or hostname
	status = spawn("ping -n -c 2 " + host)
	if not exitsuccess(status):
		return False
	return True

##
# Pass in the eth device's number (0, 1, 2, etc).
# Returns network information in a tuple.
# Order is hw_addr, ip_addr, mask, bcast, route, and
# whether it's up (True or False).
# @param device 	device to gather info from.
def get_eth_info(device):
	"""Pass in the eth device's number (0, 1, 2, etc).
	Returns network information in a tuple.
	Order is hw_addr, ip_addr, mask, bcast, route, and
	whether it's up (True or False).
	"""
	
	hw_addr = 'None'
	ip_addr = 'None'
	mask    = 'None'
	bcast	= 'None'
	gw      = 'None'
	up      =  False
	
	if len(str(device)) == 1:
		device = "eth" + str(device)

	if not is_eth_device(device):
		raise GLIException("GLIUtilityError", 'fatal', "get_eth_info", device + " is not a valid ethernet device!")
		
	status, device_info = spawn("/sbin/ifconfig " + device, return_output=True)
	if exitsuccess(status):
		for line in device_info.splitlines():
			line = line.strip()
			if 'HWaddr' in line: 
				hw_addr = line.split('HWaddr',1)[1].strip()
			if 'inet addr' in line:
				ip_addr = line.split('  ')[0].split(':')[1]
			if 'Bcast' in line:
				bcast = line.split('  ')[1].split(':')[1]
			if 'Mask' in line:
				mask = line.split('  ')[2].split(':')[1]
			if line.startswith('UP'):
				up = True
	else:
		raise GLIException("GLIUtilityError", 'fatal', "get_eth_info", device_info)
	gw = spawn(r"/sbin/route -n | grep -e '^0\.0\.0\.0' | sed -e 's:^0\.0\.0\.0 \+::' -e 's: \+.\+$::'", return_output=True)[1].strip()
	
	return (hw_addr, ip_addr, mask, bcast, gw, up)
	
##
# Will take a uri and get and unpack a tarball into the destination.
# @param tarball_uri 			URI of tarball
# @param target_directory 		destination
# @param temp_directory="/tmp" 	a temporary location (used for dealing with the 
#								ramdisk size limitations of the livecd env.
# @param keep_permissions=False Whether or not to keep permissions (-p)
def fetch_and_unpack_tarball(tarball_uri, target_directory, temp_directory="/tmp", keep_permissions=False, cc=None):
	"Fetches a tarball from tarball_uri and extracts it into target_directory"

	# Get tarball info
	tarball_filename = tarball_uri.split("/")[-1]

	# Get the tarball
	if not get_uri(tarball_uri, temp_directory + "/" + tarball_filename, cc):
		raise GLIException("GLIUtilityError", 'fatal', 'fetch_and_unpack_tarball',"Could not fetch " + tarball_uri)

	# Reset tar options
	tar_options = "xv"

	# If the tarball is bzip'd
	if tarball_filename.split(".")[-1] == "tbz" or  tarball_filename.split(".")[-1] == "bz2":
		format_option = "j"

	# If the tarball is gzip'd
	elif tarball_filename.split(".")[-1] == "tgz" or  tarball_filename.split(".")[-1] == "gz":
		format_option = "z"

	tar_options += format_option

	# If we want to keep permissions
	if keep_permissions:
		tar_options = tar_options + "p"

	# Get number of files in tarball
	tarfiles = 0
	if cc:
		cc.addNotification("progress", (0, "Determining the number of files in " + tarball_filename))
		tarfiles = int(spawn("tar -t" + format_option + "f " + temp_directory + "/" + tarball_filename + " 2>/dev/null | wc -l", return_output=True)[1].strip())

	# Unpack the tarball
	exitstatus = spawn("tar -" + tar_options + " -f " + temp_directory + "/" + tarball_filename + " -C " + target_directory, display_on_tty8=True, logfile="/tmp/compile_output.log", append_log=True, linecount=tarfiles, cc=cc, status_message="Unpacking " + tarball_filename) # change this to the logfile variable

	if not exitsuccess(exitstatus):
		raise GLIException("GLIUtilityError", 'fatal', 'fetch_and_unpack_tarball',"Could not unpack " + tarball_uri + " to " + target_directory)

##
# OLD Will generate a random password.  Used when the livecd didn't auto-scramble the root password.
# can probably be removed but is good to keep around.
def generate_random_password():
	s = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890$%^&*[]{}-=+_,|'\"<>:/"
	s = list(s)

	for i in range(0,len(s)/2):
		x = random.randint(0,len(s)-1)
		y = random.randint(0,len(s)-1)
		tmp = s[x]
		s[x] = s[y]
		s[y] = tmp

	passwd = ""
	for i in range(0,random.randint(8,12)):
		passwd += s[i]

	return passwd

##
# Will grab a value from a specified file after sourcing it
# @param filename 		file to get the value from
# @param value			value to look for
def get_value_from_config(filename, value):
	#OLD WAY: return string.strip(commands.getoutput("source " + filename + " && echo $" + value))
	status, output = spawn("source " + filename + " && echo $" + value, return_output=True)
	return string.strip(output)


##
# Will take a password and return it hashed in md5 format
# @param password 		the password to be hashed
def hash_password(password):
	salt = "$1$"
	chars = "./abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
	for i in range(0, 8):
		salt += chars[random.randint(0, len(chars)-1)]
	salt += "$"
	passwd_hash = crypt.crypt(password, salt)

	return passwd_hash

##
# Returns the real name (manufacturer and model) of a network interface
# @param interface Name of interface (like in ifconfig)
def get_interface_realname(interface):
	# TODO: rewrite with 2.4 support
	if is_file("/sys/class/net/" + interface + "/device"):
		return spawn("lspci | grep $(basename $(readlink /sys/class/net/" + interface + r"/device)) | sed -e 's|^.\+ Ethernet controller: ||'", return_output=True)[1].strip()
	else:
		return "No Information Found"

def list_stage_tarballs_from_mirror(mirror, arch, subarch):
	return spawn("wget -O - " + mirror + "/releases/" + arch + "/current/stages/" + subarch + r"/ 2> /dev/null | grep 'bz2\"' | sed -e 's:^.\+href=\"\(.\+\)\".\+$:\1:i'", return_output=True)[1].strip().split("\n")

def list_subarch_from_mirror(mirror, arch):
	return spawn("wget -O - " + mirror + "/releases/" + arch + r"/current/stages/ 2> /dev/null | grep folder.gif | sed -e 's:^.\+href=\"\(.\+\)\".\+$:\1:i'", return_output=True)[1].strip().split("\n")

def list_mirrors(http=True, ftp=True, rsync=True):
	mirrors = []
	mirrortypes = ""
	if http:
		mirrortypes += "http"
	if ftp:
		if mirrortypes:
			mirrortypes += '\|'
		mirrortypes += "ftp"
	if rsync:
		if mirrortypes:
			mirrortypes += '\|'
		mirrortypes += "rsync"
	mirrorlist = spawn(r"wget -O - 'http://www.gentoo.org/main/en/mirrors.xml?passthru=1' 2>/dev/null | /bin/sed -ne '/^[[:space:]]\+<uri link=\"\(" + mirrortypes + r"\):\/\/[^\"]\+\">/{s/^[[:space:]]\+<uri link=\"\([^\"]\+\)\">\(.*\)<\/uri>.*$/\1|\2/;p}'", return_output=True)[1].strip().split("\n")
	for mirror in mirrorlist:
		mirror = mirror.strip()
		mirrors.append(mirror.split("|"))
	return mirrors
	
def generate_keymap_list():
	keymap_list = []
	path = "/usr/share/keymaps"
	
	# find /usr/share/keymaps -iname *.map.gz -printf "%f \n"
	put, get = os.popen4("find "+path+" -iname *.map.gz -printf \"%f \n\"")
	for keymap in get.readlines():
		# strip the last 9 chars ( .map.gz\n )
		keymap.strip()
		keymap = keymap[:-9]
		keymap_list.append(keymap)
	
	# sort the keymap list
	keymap_list.sort()
	
	return keymap_list

def generate_consolefont_list():
	consolefont_list=[]
	path = "/usr/share/consolefonts"
	
	# find /usr/share/consolefonts -iname *.gz -printf "%f \n"
	put, get = os.popen4("find "+path+" -iname *.gz -printf \"%f \n\"")
	for consolefont in get.readlines():
		# strip the last 5 chars ( .gz\n )
		consolefont.strip()
		consolefont = consolefont[:-5]
		
		# test if its psfu or psf or fnt
		# and remove it if necessary
		if consolefont[-4:]== "psfu":
			consolefont = consolefont[:-5]
		if consolefont[-3:]== "psf":
			consolefont = consolefont[:-4]
		if consolefont[-3:]=="fnt":
			consolefont = consolefont[:-4]
			
		consolefont_list.append(consolefont)
			
	# sort the keymap list
	consolefont_list.sort()
	
	return consolefont_list

def generate_consoletranslation_list():
	consoletranslation_list=[]
	path = "/usr/share/consoletrans"
	
	# find /usr/share/keymaps -iname *.trans -printf "%f \n"
	put, get = os.popen4("find "+path+" -iname *.trans -printf \"%f \n\"")
	for consoletran in get.readlines():
		# strip the last 8 chars ( .trans\n )
		consoletran.strip()
		consoletran = consoletran[:-8]
		consoletranslation_list.append(consoletran)
		
	consoletranslation_list.sort()
	
	return consoletranslation_list

def get_global_use_flags():
	use_desc = {}
	f = open("/usr/portage/profiles/use.desc", "r")
	for line in f:
		line = line.strip()
		if line == "# The following flags are NOT to be set or unset by users":
			break
		if not line or line.startswith("#"): continue
		dash_pos = line.find(" - ")
		if dash_pos == -1: continue
		flagname = line[:dash_pos] or line[dash_pos-1]
		desc = line[dash_pos+3:]
		use_desc[flagname] = desc
	f.close()
	return use_desc
	
def get_local_use_flags():
	use_local_desc = {}
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
		use_local_desc[flagname] = desc
	f.close()
	return use_local_desc
	
def get_cd_snapshot_uri():
	snapshot_loc = spawn("ls /mnt/{cdrom,livecd}/snapshots/portage-* 2>/dev/null | head -n 1", return_output=True)[1].strip()
	if snapshot_loc:
		snapshot_loc = "file://" + snapshot_loc
	return snapshot_loc

def validate_uri(uri):
	# Get tuple of matches
	# 0 - Protocol
	# 1 - Username
	# 2 - Password
	# 3 - Host
	# 4 - Port
	# 5 - Path
	uriparts = parse_uri(uri)
	if not uriparts:
		return False
	if uriparts[0] in ('http', 'https', 'ftp'):
		ret = spawn("wget --spider " + uri)
		return exitsuccess(ret)
	elif uriparts[0] == "file":
		return is_file(uriparts[5])
	return True

def get_directory_listing_from_uri(uri):
	uriparts = parse_uri(uri)
	if not uriparts:
		return []
	if uriparts[0] == "file":
		dirlist = os.listdir(uriparts[5])
		dirlist.sort()
		dirs = []
		files = []
		for entry in dirlist:
			if os.path.isdir(uriparts[5] + entry):
				dirs.append(entry + "/")
			else:
				files.append(entry)
		if not uriparts[5] == "/":
			dirlist = ["../"]
		else:
			dirlist = []
		dirlist += dirs + files
	elif uriparts[0] == "http":
		dirlist = spawn("wget -O - http://" + uriparts[3] + uriparts[5] + r" 2> /dev/null | grep -i href | grep -v 'http://' | grep -v 'ftp://' | sed -e 's:^.\+href=\"\(.\+\)\".\+$:\1:i'", return_output=True)[1].strip().split("\n")
		dirs = []
		files = []
		for entry in dirlist:
			if not entry.startswith("/") and entry.find("?") == -1:
				if entry.endswith("/"):
					dirs.append(entry)
				else:
					files.append(entry)
		dirs.sort()
		files.sort()
		if not uriparts[5] == "/":
			dirlist = ["../"]
		else:
			dirlist = []
		dirlist += dirs + files
	elif uriparts[0] == "ftp":
		dirlist = spawn("wget -O - ftp://" + uriparts[3] + uriparts[5] + r" 2> /dev/null | grep -i href | sed -e 's:^.\+href=\"\(.\+\)\".\+$:\1:i' -e 's|^ftp://[^/]\+/|/|'", return_output=True)[1].strip().split("\n")
		dirs = []
		files = []
		for entry in dirlist:
			if entry.startswith(uriparts[5]):
				entry = entry[len(uriparts[5]):]
				if entry.endswith("/"):
					dirs.append(entry)
				else:
					files.append(entry)
		dirs.sort()
		files.sort()
		if not uriparts[5] == "/":
			dirlist = ["../"]
		else:
			dirlist = []
		dirlist += dirs + files
	elif uriparts[0] == "scp":
		tmpdirlist = ""
		dirlist = []
		sshcmd = ["ssh"]
		if uriparts[4]:
			sshcmd.append("-p")
			sshcmd.append(uriparts[4])
		if uriparts[1]:
			sshcmd.append(uriparts[1] + "@" + uriparts[3])
		else:
			sshcmd.append(uriparts[3])
		sshcmd.append("ls --color=no -1F " + uriparts[5] + r" 2>/dev/null | sed -e 's:\*$::'")
#		print str(sshcmd)
		pid, child_fd = pty.fork()
		if not pid:
			os.execvp("ssh", sshcmd)
		else:
			got_password_prompt = False
			while 1:
				r, w, e = select.select([child_fd], [], [])
				if child_fd in r:
					try:
						data = os.read(child_fd, 1024)
					except:
						pid2, status = os.waitpid(pid, 0)
						break
					if data.endswith("assword: "):
						if uriparts[2]:
							os.write(child_fd, uriparts[2] + "\n")
						else:
							os.write(child_fd, "\n")
						got_password_prompt = True
					elif data.endswith("Are you sure you want to continue connecting (yes/no)? "):
						os.write(child_fd, "yes\n")
					else:
						if got_password_prompt:
							if not tmpdirlist and data.endswith("assword: "):
								raise GLIException("IncorrectPassword", "notice", "get_directory_listing_from_uri", "Your SSH password was incorrect")
							tmpdirlist += data
				else:
					pid2, status = os.waitpid(pid, os.WNOHANG)
					if pid2:
						break
		for tmpentry in tmpdirlist.strip().split("\n"):
			dirlist.append(tmpentry.strip())
		dirs = []
		files = []
		for entry in dirlist:
			if entry.endswith("/"):
				dirs.append(entry)
			else:
				files.append(entry)
		dirs.sort()
		files.sort()
		if not uriparts[5] == "/":
			dirlist = ["../"]
		else:
			dirlist = []
		dirlist += dirs + files
	else:
		dirlist = ["this/", "type/", "isn't/", "supported", "yet"]
	return dirlist

def cdata(text):
	if text.startswith("<![CDATA["):
		return text
	else:
		return "<![CDATA[\n" + text + "\n]]>"

def uncdata(text):
	if text.startswith("<![CDATA["):
		return text[9:-5]
	else:
		return text
		
def get_grp_pkgs_from_cd():
	if not is_file("/usr/livecd/grppkgs.txt"):
		return ""
		#raise GLIException("GLIUtilityError", "fatal", "get_grp_pkgs_from_cd", "Required file /usr/livecd/grppkgs.txt does not exist")
	status,output = spawn('cat /usr/livecd/grppkgs.txt',return_output=True)
	output = output.split()
	#remove the first part before a / for comparision
	results = []
	for pkg in output:
		results.append(pkg[(pkg.find('/')+1):])
	return results

def get_keymaps(self):
	return GLIUtility.spawn(r"find /usr/share/keymaps -iname *.map.gz | sed -e 's:^.\+/::' -e 's:\..\+$::' | sort", return_output=True)[1].strip().split("\n")

def get_chosts(arch):
	chosts = []
	if arch == "x86":
		chosts = ["i386-pc-linux-gnu", "i486-pc-linux-gnu", "i586-pc-linux-gnu", "i686-pc-linux-gnu"]
	if arch == "amd64":
		chosts = ["x86_64-pc-linux-gnu"]
	if arch == "alpha":
		chosts = ["alpha-unknown-linux-gnu"]
	if arch == "ppc":
		chosts = ["powerpc-unknown-linux-gnu"]
	if arch == "ppc64":
		chosts = ["powerpc64-unknown-linux-gnu"]
	if arch in ["sparc", "sparc64"]:
		chosts = ["sparc-unknown-linux-gnu"]
	if arch == "hppa":
		chosts = ["hppa-unknown-linux-gnu", "hppa1.1-unknown-linux-gnu", "hppa2.0-unknown-linux-gnu"]
	if arch == "mips":
		chosts = ["mips-unknown-linux-gnu"]
	return chosts
