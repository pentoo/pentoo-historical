"""
# Copyright 1999-2005 Gentoo Foundation
# This source code is distributed under the terms of version 2 of the GNU
# General Public License as published by the Free Software Foundation, a copy
# of which can be found in the main directory of this project.
Gentoo Linux Installer

$Id: GLIPortage.py,v 1.52 2006/04/19 16:31:18 agaffney Exp $
"""

import re
import os
import sys
import GLIUtility
from GLIException import GLIException

class GLIPortage(object):

	def __init__(self, chroot_dir, grp_install, logger, debug, cc, compile_logfile):
		self._chroot_dir = chroot_dir
		self._grp_install = grp_install
		self._logger = logger
		self._debug = debug
		self._cc = cc
		self._compile_logfile = compile_logfile

	def get_deps(self, pkgs):
		pkglist = []
		if isinstance(pkgs, str):
			pkgs = pkgs.split()
		for pkg in pkgs:
			if not pkg: continue
			if self._debug: self._logger.log("get_deps(): pkg is " + pkg)
			if not self._grp_install or not self.get_best_version_vdb(pkg):
				if self._debug: self._logger.log("get_deps(): grabbing compile deps")
				tmppkglist = GLIUtility.spawn("emerge -p " + pkg + r" 2>/dev/null | grep -e '^\[[a-z]' | cut -d ']' -f2 | sed -e 's:^ ::' -e 's: .\+$::'", chroot=self._chroot_dir, return_output=True)[1].strip().split("\n")
			else:
				if self._debug: self._logger.log("get_deps(): grabbing binary deps")
				# The runtimedeps.py script generates a package install order that is *very* different from emerge itself
#				tmppkglist = GLIUtility.spawn("python ../../runtimedeps.py " + self._chroot_dir + " " + pkg, return_output=True)[1].strip().split("\n")
				tmppkglist = []
				for tmppkg in GLIUtility.spawn("emerge -p " + pkg + r" 2>/dev/null | grep -e '^\[[a-z]' | cut -d ']' -f2 | sed -e 's:^ ::' -e 's: .\+$::'", chroot=self._chroot_dir, return_output=True)[1].strip().split("\n"):
					if self._debug: self._logger.log("get_deps(): looking at " + tmppkg)
					if self.get_best_version_vdb("=" + tmppkg):
						if self._debug: self._logger.log("get_deps(): package " + tmppkg + " in host vdb...adding to tmppkglist")
						tmppkglist.append(tmppkg)
			if self._debug: self._logger.log("get_deps(): deplist for " + pkg + ": " + str(tmppkglist))
			for tmppkg in tmppkglist:
				if self._debug: self._logger.log("get_deps(): checking to see if " + tmppkg + " is already in pkglist")
				if not tmppkg in pkglist and not self.get_best_version_vdb_chroot("=" + tmppkg):
					if self._debug: self._logger.log("get_deps(): adding " + tmppkg + " to pkglist")
					pkglist.append(tmppkg)
		if self._debug: self._logger.log("get_deps(): pkglist is " + str(pkglist))
		return pkglist

	def parse_vdb_contents(self, file):
		entries = []
		try:
			vdbfile = open(file, "r")
		except:
			return entries
		for line in vdbfile.readlines():
			parts = line.strip().split(" ")
			if parts[0] == "obj":
				entries.append(parts[1])
#			elif parts[0] == "dir":
#				entries.append(parts[1] + "/")
			elif parts[0] == "sym":
				entries.append(" ".join(parts[1:4]))
		entries.sort()
		return entries

	def copy_pkg_to_chroot(self, package, use_root=False, ignore_missing=False):
		symlinks = { '/bin': '/mnt/livecd/bin/', '/boot': '/mnt/livecd/boot/', '/lib': '/mnt/livecd/lib/', 
		             '/opt': '/mnt/livecd/opt/', '/sbin': '/mnt/livecd/sbin/', '/usr': '/mnt/livecd/usr/',
		             '/etc/gconf': '/usr/livecd/gconf/' }

		tmpdir = "/var/tmp/portage"
		image_dir = tmpdir + "/" + package.split("/")[1] + "/image"
		root_cmd = ""
		tmp_chroot_dir = self._chroot_dir
		portage_tmpdir = "/var/tmp/portage"
		vdb_dir = "/var/db/pkg/"
		if use_root:
			root_cmd = "ROOT=" + self._chroot_dir
			tmp_chroot_dir = ""
			portage_tmpdir = self._chroot_dir + "/var/tmp/portage"
			vdb_dir = self._chroot_dir + "/var/db/pkg/"

		# Create /tmp, /var/tmp, and /var/lib/portage with proper permissions
		oldumask = os.umask(0)
		if not os.path.exists(self._chroot_dir + "/tmp"):
			if self._debug: self._logger.log("DEBUG: copy_pkg_to_chroot(): /tmp doesn't exist in chroot...creating with proper permissions")
			try:
				os.mkdir(self._chroot_dir + "/tmp", 01777)
			except:
				raise GLIException("CopyPackageToChrootError", 'fatal', 'copy_pkg_to_chroot', "Failed to create /tmp in chroot")
		if not os.path.exists(self._chroot_dir + "/var/tmp"):
			if self._debug: self._logger.log("DEBUG: copy_pkg_to_chroot(): /var/tmp doesn't exist in chroot...creating with proper permissions")
			try:
				os.mkdir(self._chroot_dir + "/var", 0755)
			except:
				pass
			try:
				os.mkdir(self._chroot_dir + "/var/tmp", 01777)
			except:
				raise GLIException("CopyPackageToChrootError", 'fatal', 'copy_pkg_to_chroot', "Failed to create /var/tmp in chroot")
		if not os.path.exists(self._chroot_dir + "/var/lib/portage"):
			if self._debug: self._logger.log("DEBUG: copy_pkg_to_chroot(): /var/lib/portage doesn't exist in chroot...creating with proper permissions")
			try:
				os.mkdir(self._chroot_dir + "/var/lib", 0755)
			except:
				pass
			try:
				os.mkdir(self._chroot_dir + "/var/lib/portage", 02750)
			except:
				raise GLIException("CopyPackageToChrootError", 'fatal', 'copy_pkg_to_chroot', "Failed to create /var/lib/portage in chroot")
		os.umask(oldumask)

		# Check to see if package is actually in vdb
		if not GLIUtility.is_file("/var/db/pkg/" + package):
			if ignore_missing:
				if self._debug:
					self._logger.log("DEBUG: copy_pkg_to_chroot(): package " + package + " does not have a vdb entry but ignore_missing=True...ignoring error")
				return
			else:
				raise GLIException("CopyPackageToChrootError", 'fatal', 'copy_pkg_to_chroot', "There is no vdb entry for " + package)

		# Copy the vdb entry for the package from the LiveCD to the chroot
		if self._debug: self._logger.log("DEBUG: copy_pkg_to_chroot(): copying vdb entry for " + package)
		if not GLIUtility.exitsuccess(GLIUtility.spawn("mkdir -p " + self._chroot_dir + "/var/db/pkg/" + package + " && cp -a /var/db/pkg/" + package + "/* " + self._chroot_dir + "/var/db/pkg/" + package, logfile=self._compile_logfile, append_log=True)):
			raise GLIException("CopyPackageToChrootError", 'fatal', 'copy_pkg_to_chroot', "Could not copy vdb entry for " + package)

		# Create the image dir in the chroot
		if self._debug: self._logger.log("DEBUG: copy_pkg_to_chroot(): running 'mkdir -p " + self._chroot_dir + image_dir + "'")
		if not GLIUtility.exitsuccess(GLIUtility.spawn("mkdir -p " + self._chroot_dir + image_dir, logfile=self._compile_logfile, append_log=True)):
			raise GLIException("CopyPackageToChrootError", 'fatal', 'copy_pkg_to_chroot', "Could not create image dir for " + package)

		# Create list of files for tar to work with from CONTENTS file in vdb entry
		entries = self.parse_vdb_contents("/var/db/pkg/" + package + "/CONTENTS")
		if not entries:
			if self._debug: self._logger.log("DEBUG: copy_pkg_to_chroot(): no files for " + package + "...skipping tar and symlink fixup")
		else:
#			if self._debug: self._logger.log("DEBUG: copy_pkg_to_chroot: files for " + package + ": " + str(entries))
			try:
				tarfiles = open("/tmp/tarfilelist", "w")
				for entry in entries:
					parts = entry.split(" ")
#					# Hack for symlink crappiness
#					for symlink in symlinks:
#						if parts[0].startswith(symlink):
#							parts[0] = symlinks[symlink] + parts[0][len(symlink):]
					tarfiles.write(parts[0] + "\n")
				tarfiles.close()
			except:
				raise GLIException("CopyPackageToChrootError", 'fatal', 'copy_pkg_to_chroot', "Could not create filelist for " + package)

			# Use tar to transfer files into IMAGE directory
			if self._debug: self._logger.log("DEBUG: copy_pkg_to_chroot(): running 'tar -cp --files-from=/tmp/tarfilelist --no-recursion 2>/dev/null | tar -C " + self._chroot_dir + image_dir + " -xp'")
			if not GLIUtility.exitsuccess(GLIUtility.spawn("tar -cp --files-from=/tmp/tarfilelist --no-recursion 2>/dev/null | tar -C " + self._chroot_dir + image_dir + " -xp", logfile=self._compile_logfile, append_log=True)):
				raise GLIException("CopyPackageToChrootError", 'fatal', 'copy_pkg_to_chroot', "Could not execute tar for " + package)

			# Fix mode, uid, and gid of directories
#			if self._debug: self._logger.log("DEBUG: copy_pkg_to_chroot(): running find " + self._chroot_dir + image_dir + " -type d 2>/dev/null | sed -e 's:^" + self._chroot_dir + image_dir + "::' | grep -v '^$'")
#			dirlist = GLIUtility.spawn("find " + self._chroot_dir + image_dir + " -type d 2>/dev/null | sed -e 's:^" + self._chroot_dir + image_dir + "::' | grep -v '^$'", return_output=True)[1].strip().split("\n")
#			if self._debug: self._logger.log("DEBUG: copy_pkg_to_chroot(): found the following directories: " + str(dirlist))
#			if not dirlist or dirlist[0] == "":
#				raise GLIException("CopyPackageToChrootError", 'fatal', 'copy_pkg_to_chroot', "directory list entry for " + package + "...this shouldn't happen!")
#			for dir in dirlist:
#				dirstat = os.stat(dir)
#				if self._debug: self._logger.log("DEBUG: copy_pkg_to_chroot(): setting mode " + str(dirstat[0]) + " and uid/gid " + str(dirstat[4]) + "/" + str(dirstat[5]) + " for directory " + self._chroot_dir + image_dir + dir)
#				os.chown(self._chroot_dir + image_dir + dir, dirstat[4], dirstat[5])
#				os.chmod(self._chroot_dir + image_dir + dir, dirstat[0])

#			# More symlink crappiness hacks
#			for symlink in symlinks:
##				if GLIUtility.is_file(self._chroot_dir + image_dir + symlinks[symlink]):
#				if os.path.islink(self._chroot_dir + image_dir + symlink):
#					if self._debug: self._logger.log("DEBUG: copy_pkg_to_chroot(): fixing " + symlink + " symlink ickiness stuff in " + image_dir + " for " + package)
#					GLIUtility.spawn("rm " + self._chroot_dir + image_dir + symlink)
#					if not GLIUtility.exitsuccess(GLIUtility.spawn("mv " + self._chroot_dir + image_dir + symlinks[symlink] + " " + self._chroot_dir + image_dir + symlink)):
#						raise GLIException("CopyPackageToChrootError", 'fatal', 'copy_pkg_to_chroot', "Could not fix " + symlink + " symlink ickiness for " + package)

		# Run pkg_setup
		if self._debug: self._logger.log("DEBUG: copy_pkg_to_chroot(): running pkg_setup for " + package)
		if not GLIUtility.exitsuccess(GLIUtility.spawn("env " + root_cmd + " PORTAGE_TMPDIR=" + portage_tmpdir + " ebuild " + vdb_dir + package + "/*.ebuild setup", chroot=tmp_chroot_dir, logfile=self._compile_logfile, append_log=True)):
			raise GLIException("CopyPackageToChrootError", 'fatal', 'copy_pkg_to_chroot', "Could not execute pkg_setup for " + package)

		# Run pkg_preinst
		if self._debug: self._logger.log("DEBUG: copy_pkg_to_chroot(): running preinst for " + package)
		if not GLIUtility.exitsuccess(GLIUtility.spawn("env " + root_cmd + " PORTAGE_TMPDIR=" + portage_tmpdir + " ebuild " + vdb_dir + package + "/*.ebuild preinst", chroot=tmp_chroot_dir, logfile=self._compile_logfile, append_log=True)):
			raise GLIException("CopyPackageToChrootError", 'fatal', 'copy_pkg_to_chroot', "Could not execute preinst for " + package)

		# Copy files from image_dir to chroot
		if not entries:
			if self._debug: self._logger.log("DEBUG: copy_pkg_to_chroot(): no files for " + package + "...skipping copy from image dir to /")
		else:
			if self._debug: self._logger.log("DEBUG: copy_pkg_to_chroot(): copying files from " + image_dir + " to / for " + package)
#			if not GLIUtility.exitsuccess(GLIUtility.spawn("cp -a " + self._chroot_dir + image_dir + "/* " + self._chroot_dir)):
			if not GLIUtility.exitsuccess(GLIUtility.spawn("tar -C " + self._chroot_dir + image_dir + "/ -cp . | tar -C " + self._chroot_dir + "/ -xp", logfile=self._compile_logfile, append_log=True)):
				raise GLIException("CopyPackageToChrootError", 'fatal', 'copy_pkg_to_chroot', "Could not copy files from " + image_dir + " to / for " + package)

		# Run pkg_postinst
		if self._debug: self._logger.log("DEBUG: copy_pkg_to_chroot(): running postinst for " + package)
		if not GLIUtility.exitsuccess(GLIUtility.spawn("env " + root_cmd + " PORTAGE_TMPDIR=" + portage_tmpdir + " ebuild " + vdb_dir + package + "/*.ebuild postinst", chroot=tmp_chroot_dir, logfile=self._compile_logfile, append_log=True)):
			raise GLIException("CopyPackageToChrootError", 'fatal', 'copy_pkg_to_chroot', "Could not execute postinst for " + package)

		# Remove image_dir
		if self._debug: self._logger.log("DEBUG: copy_pkg_to_chroot(): removing " + image_dir + " for " + package)
		if not GLIUtility.exitsuccess(GLIUtility.spawn("rm -rf " + self._chroot_dir + image_dir, logfile=self._compile_logfile, append_log=True)):
			raise GLIException("CopyPackageToChrootError", 'fatal', 'copy_pkg_to_chroot', "Could not remove + " + image_dir + " for " + package)

		# Run env-update
		if not use_root:
			if self._debug: self._logger.log("DEBUG: copy_pkg_to_chroot(): running env-update inside chroot")
			if not GLIUtility.exitsuccess(GLIUtility.spawn("env-update", chroot=self._chroot_dir, logfile=self._compile_logfile, append_log=True)):
				raise GLIException("CopyPackageToChrootError", 'fatal', 'copy_pkg_to_chroot', "Could not run env-update for " + package)

	def add_pkg_to_world(self, package):
		if package.find("/") == -1:
			package = self.get_best_version_vdb_chroot(package)
		if not package: return False
		expr = re.compile('^=?(.+?/.+?)(-\d.+)?$')
		res = expr.match(package)
		if res:
			GLIUtility.spawn("echo " + res.group(1) + " >> " + self._chroot_dir + "/var/lib/portage/world")

	def get_best_version_vdb(self, package):
		if package.startswith('='):
			package = package[1:]
			if GLIUtility.is_file("/var/db/pkg/" + package):
				return package
			else:
				return ""
		else:
			return GLIUtility.spawn("portageq best_version / " + package, return_output=True)[1].strip()

	def get_best_version_vdb_chroot(self, package):
		if package.startswith('='):
			package = package[1:]
			if GLIUtility.is_file(self._chroot_dir + "/var/db/pkg/" + package):
				return package
			else:
				return ""
		else:
			return GLIUtility.spawn("portageq best_version / " + package, chroot=self._chroot_dir, return_output=True)[1].strip()

#	def get_best_version_tree(self, package):
#		return portage.best(tree.match(package))

	def emerge(self, packages, add_to_world=True):
		if isinstance(packages, str):
			packages = packages.split()
		self._cc.addNotification("progress", (0, "Calculating dependencies for " + " ".join(packages)))
		pkglist = self.get_deps(packages)
		if self._debug: self._logger.log("install_packages(): pkglist is " + str(pkglist))
		for i, pkg in enumerate(pkglist):
			if not pkg: continue
			if self._debug: self._logger.log("install_packages(): processing package " + pkg)
			self._cc.addNotification("progress", (float(i) / len(pkglist), "Emerging " + pkg + " (" + str(i+1) + "/" + str(len(pkglist)) + ")"))
			if not self._grp_install or not self.get_best_version_vdb("=" + pkg):
				status = GLIUtility.spawn("emerge -1 =" + pkg, display_on_tty8=True, chroot=self._chroot_dir, logfile=self._compile_logfile, append_log=True)
#				status = self._emerge("=" + pkg)
				if not GLIUtility.exitsuccess(status):
					raise GLIException("EmergePackageError", "fatal", "emerge", "Could not emerge " + pkg + "!")
			else:
#				try:
				self.copy_pkg_to_chroot(pkg)
#				except:
#					raise GLIException("EmergePackageError", "fatal", "emerge", "Could not emerge " + pkg + "!")
			self._cc.addNotification("progress", (float(i+1) / len(pkglist), "Done emerging " + pkg + " (" + str(i+1) + "/" + str(len(pkglist)) + ")"))
		if add_to_world:
			for package in packages:
				self.add_pkg_to_world(package)


def usage(progname):
	print """
Usage: %s [-c|--chroot-dir <chroot directory>] [-g|--grp] [-s|--stage3] [-h|--help]

Options:

  -c|--chroot-dir   Specifies the directory where your chroot is. This is
                    "/mnt/gentoo" by default.

  -g|--grp          Install specified packages and dependencies into chroot
                    by using files from the LiveCD.

  -s|--stage3       Create a stage3 equivelant in the chroot directory by using
                    files from the LiveCD.

  -h|--help         Display this help
""" % (progname)

if __name__ == "__main__":
	chroot_dir = "/mnt/gentoo"
	mode = None
	grp_packages = []
	progname = sys.argv.pop(0)
	while len(sys.argv):
		arg = sys.argv.pop(0)
		if arg == "-c" or arg == "--chroot-dir":
			chroot_dir = sys.argv.pop(0)
		elif arg == "-g" or arg == "--grp":
			mode = "grp"
		elif arg == "-s" or arg == "--stage3":
			mode = "stage3"
		elif arg == "-h" or arg == "--help":
			usage(progname)
			sys.exit(0)
		elif arg[0] == "-":
			usage(progname)
			sys.exit(1)
		else:
			grp_packages.append(arg)

	gliportage = GLIPortage(chroot_dir, True, None, False, None, None)
	if mode == "stage3":
		if not GLIUtility.is_file("/usr/livecd/systempkgs.txt"):
			print "Required file /usr/livecd/systempkgs.txt does not exist!"
			sys.exit(1)
		try:
			syspkgs = open("/usr/livecd/systempkgs.txt", "r")
			systempkgs = syspkgs.readlines()
			syspkgs.close()
		except:
			print "Could not open /usr/livecd/systempkgs.txt!"
			sys.exit(1)

		# Pre-create /lib (and possible /lib32 and /lib64)
		if os.path.islink("/lib") and os.readlink("/lib") == "lib64":
			if not GLIUtility.exitsuccess(GLIUtility.spawn("mkdir " + chroot_dir + "/lib64 && ln -s lib64 " + chroot_dir + "/lib")):
				print "Could not precreate /lib64 dir and /lib -> /lib64 symlink"
				sys.exit(1)

		syspkglen = len(systempkgs)
		for i, pkg in enumerate(systempkgs):
			pkg = pkg.strip()
			print "Copying " + pkg + " (" + str(i+1) + "/" + str(syspkglen) + ")"
			gliportage.copy_pkg_to_chroot(pkg, True, ignore_missing=True)
		GLIUtility.spawn("cp /etc/make.conf " + chroot_dir + "/etc/make.conf")
		GLIUtility.spawn("ln -s `readlink /etc/make.profile` " + chroot_dir + "/etc/make.profile")
		GLIUtility.spawn("cp -f /etc/inittab.old " + chroot_dir + "/etc/inittab")

		# Nasty, nasty, nasty hack because vapier is a tool
		for tmpfile in ("/etc/passwd", "/etc/group", "/etc/shadow"):
			GLIUtility.spawn("grep -ve '^gentoo' " + tmpfile + " > " + chroot_dir + tmpfile)

		chrootscript = r"""
		#!/bin/bash

		source /etc/make.conf
		export LDPATH="/usr/lib/gcc-lib/${CHOST}/$(cd /usr/lib/gcc-lib/${CHOST} && ls -1 | head -n 1)"

		ldconfig $LDPATH
		gcc-config 1
		env-update
		source /etc/profile
		modules-update
		[ -f /usr/bin/binutils-config ] && binutils-config 1
		source /etc/profile
		#mount -t proc none /proc
		#cd /dev
		#/sbin/MAKEDEV generic-i386
		#umount /proc
		[ -f /lib/udev-state/devices.tar.bz2 ] && tar -C /dev -xjf /lib/udev-state/devices.tar.bz2
		"""
		script = open(chroot_dir + "/tmp/extrastuff.sh", "w")
		script.write(chrootscript)
		script.close()
		GLIUtility.spawn("chmod 755 /tmp/extrastuff.sh && /tmp/extrastuff.sh", chroot=chroot_dir)
		GLIUtility.spawn("rm -rf /var/tmp/portage/* /usr/portage /tmp/*", chroot=chroot_dir)
		print "Stage3 equivelant generation complete!"
	elif mode == "grp":
		for pkg in grp_packages:
			if not gliportage.get_best_version_vdb(pkg):
				print "Package " + pkg + " is not available for install from the LiveCD"
				continue
			pkglist = gliportage.get_deps(pkg)
			for i, tmppkg in enumerate(pkglist):
				print "Copying " + tmppkg + " (" + str(i+1) + "/" + str(len(pkglist)) + ")"
				gliportage.copy_pkg_to_chroot(tmppkg)
			gliportage.add_pkg_to_world(pkg)
		print "GRP install complete!"
	else:
		print "You must specify an operating mode (-g or -s)!"
		usage(progname)
		sys.exit(1)
