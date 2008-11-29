"""
# Copyright 1999-2005 Gentoo Foundation
# This source code is distributed under the terms of version 2 of the GNU
# General Public License as published by the Free Software Foundation, a copy
# of which can be found in the main directory of this project.
Gentoo Linux Installer

$Id: GLILogger.py,v 1.9 2005/08/22 18:35:51 codeman Exp $

Logger is a singleton style generic logger object.
"""

import time

class Logger(object):

	_LOG_FILE_PATH = "install.log"
	_SHARED_LOGGER = None

	##
	# Creates a shared logger like in GLIClientConfiguration
	# @param cls It's just done like that.
	def shared_logger(cls):
		if Logger._SHARED_LOGGER == None:
			Logger._SHARED_LOGGER = Logger()

		return Logger._SHARED_LOGGER

	##
	# Basic Initialization function.  Appends to the given logfile
	# @param logfile=None file to log stuff to.
	def __init__(self,logfile=None):
		if logfile == None:
			self._file = file(Logger._LOG_FILE_PATH, 'a')
		else:
			self._file = file(logfile,'a')

	##
	# Logs the given message to the logfile
	# @param message Parameter description
	def log(self, message):
		self._file.write("GLI: " + time.strftime("%B %d %Y %H:%M:%S") + " - " + message + "\n")
		self._file.flush()
		
	##
	# Inserts a mark into the logfile.
	def mark(self):
		self.log(" -- MARK -- ")

	shared_logger = classmethod(shared_logger)
