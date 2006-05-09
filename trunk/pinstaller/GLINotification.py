"""
# Copyright 1999-2005 Gentoo Foundation
# This source code is distributed under the terms of version 2 of the GNU
# General Public License as published by the Free Software Foundation, a copy
# of which can be found in the main directory of this project.
Gentoo Linux Installer

$Id: GLINotification.py,v 1.5 2005/08/22 18:35:51 codeman Exp $
"""

##
# This class provides a wrapper for passing data from the backend to the frontend
class GLINotification:
	##
	# Initialization function for GLINotification
	# @param type String specifying the type of data contained in the next parameter
	# @param data Data to pass
	def __init__(self, type, data):
		self._type = type
		self._data = data

	##
	# Retrieves data
	def get_data(self):
		return self._data

	##
	# Retrieves data type
	def get_type(self):
		return self._type

	##
	# Sets data
	# @param data Data (duh)
	def set_data(self, data):
		self._data = data

	##
	# Sets data type
	# @param type Type (duh)
	def set_type(self, type):
		self._type = type
