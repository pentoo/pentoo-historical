#!/usr/bin/python
# Copyright 1999-2005 Gentoo Foundation
# This source code is distributed under the terms of version 2 of the GNU
# General Public License as published by the Free Software Foundation, a copy
# of which can be found in the main directory of this project.
import sys
import GLIUtility
import GLIArchitectureTemplate
import GLIInstallProfile
import GLIClientConfiguration

def usage():
	print "Usage: " + sys.argv[0] + " <installprofile.xml> [command [command ...]]\n"
	print "command is one of:\n"
	print "\tpartition              add, remove, and resize partitions"
	print "\tmount                  mount all partitions"
	print "\tmount_net              mount network shares"
	print "\tunpack                 unpack stage tarball"
	print "\tprep_make_conf         prepare the make.conf"
	print "\tportage_tree           portage tree magic"
	print "\tprep_chroot            prepare the chroot"
	print "\tbootstrap              duh :P"
	print "\temerge_system          duh :P"
	print "\ttimezone               set timezone"
	print "\temerge_kernel          install the kernel sources"
	print "\tbuild_kernel           build the kernel"
	print "\tlogger                 install logger"
	print "\tcrond                  install cron daemon"
	print "\tfstools                install filesystem tools"
	print "\tnetwork                configure network"
	print "\tbootloader             install and configure bootloader"
	print "\tconfig_files           update config files"
	print "\tupdate_rc_conf         update rc.conf"
	print "\tset_users              set up the users"
	print "\tetc_portage            set up the files in /etc/portage"
	print "\tinstall_packages       install required packages"
	print "\tunmount                unmount all filesystems"

def not_working():
	print "This is a placeholder. This function does nothing right now."

if len(sys.argv) < 3:
	usage()
	sys.exit(1)

progname = sys.argv.pop(0)
xmlfile = sys.argv.pop(0)

if not GLIUtility.is_file(xmlfile):
	print "The XML file '" + xmlfile + "' cannot be accessed.\n"
	usage()
	sys.exit(1)

client_profile = GLIClientConfiguration.ClientConfiguration()
client_profile.set_root_mount_point(None, "/mnt/gentoo", None)
install_profile = GLIInstallProfile.InstallProfile()
install_profile.parse(xmlfile)

template =  __import__('templates' + '/' + 'x86ArchitectureTemplate')
archtemplate = getattr(template, 'x86ArchitectureTemplate')(client_profile, install_profile, False)

#archtemplate = GLIArchitectureTemplate.ArchitectureTemplate(install_profile=install_profile)

operations = {
              'partition': archtemplate.partition,
              'mount': archtemplate.mount_local_partitions,
              'mount_net': archtemplate.mount_network_shares,
              'unpack': archtemplate.unpack_stage_tarball,
              'prep_make_conf': archtemplate.configure_make_conf,
              'portage_tree': archtemplate.install_portage_tree,
              'prep_chroot': archtemplate.prepare_chroot,
              'bootstrap': archtemplate.stage1,
              'emerge_system': archtemplate.stage2,
              'timezone': archtemplate.set_timezone,
              'emerge_kernel': archtemplate.emerge_kernel_sources,
              'build_kernel': archtemplate.build_kernel,
              'logger': archtemplate.install_logging_daemon,
              'crond': archtemplate.install_cron_daemon,
              'fstools': archtemplate.install_filesystem_tools,
              'network': archtemplate.setup_network_post,
              'bootloader': archtemplate.install_bootloader,
              'config_files': archtemplate.update_config_files,
              'update_rc_conf': archtemplate.configure_rc_conf,
			  'set_users': archtemplate.set_users,
			  'etc_portage': archtemplate.set_etc_portage,
			  'install_packages': archtemplate.install_packages,
			  'unmount': not_working
			}

for action in sys.argv:
	if operations.has_key(action):
		operations[action]()
	else:
		print "Operation '" + action + "' is not valid"
