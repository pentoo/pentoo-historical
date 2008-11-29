"""
# Copyright 1999-2005 Gentoo Foundation
# This source code is distributed under the terms of version 2 of the GNU
# General Public License as published by the Free Software Foundation, a copy
# of which can be found in the main directory of this project.
Gentoo Linux Installer

$Id: GLIException.py,v 1.9 2005/08/22 18:35:51 codeman Exp $
Copyright 2004 Gentoo Technologies Inc.

"""

from string import upper

class GLIException(Exception):
	error_levels = ['notice', 'warning', 'fatal']

	##
	# Brief description of function
	# @param self Parameter description
	# @param error_name Parameter description
	# @param error_level Parameter description
	# @param function_name Parameter description
	# @param error_msg Parameter description
	def __init__(self, error_name, error_level, function_name, error_msg):
		if error_level not in GLIException.error_levels:
			raise GLIException('NoSuchLevelError', 'fatal', '__init__', "No such error level: %s" % error_level)

		Exception.__init__(self, error_name, error_level, function_name, error_msg)

	##
	# Brief description of function
	# @param self Parameter description
	def get_function_name(self):
		return self.args[2]

	##
	# Brief description of function
	# @param self Parameter description
	def get_error_level(self):
		return self.args[1]

	##
	# Brief description of function
	# @param self Parameter description
	def get_error_msg(self):
		return self.args[3]

	##
	# Brief description of function
	# @param self Parameter description
	def get_error_name(self):
		return self.args[0]

	##
	# Brief description of function
	# @param self Parameter description
	def __str__(self):
		return "%s :%s: %s: %s" % (self.args[0], upper(self.args[1]), self.args[2], self.args[3])
