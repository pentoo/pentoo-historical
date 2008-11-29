"""
# Copyright 1999-2005 Gentoo Foundation
# This source code is distributed under the terms of version 2 of the GNU
# General Public License as published by the Free Software Foundation, a copy
# of which can be found in the main directory of this project.
Gentoo Linux Installer

$Id: GLILocalization.py,v 1.6 2005/08/22 18:35:51 codeman Exp $

This module is used for reading and returning localized errors and informative
messages.

"""

import codecs
import os

class Localization:

	messages = None
	lang = None

	##
	# Brief description of function
	# @param self Parameter description
	# @param filename Parameter description
	# @param lang=None Parameter description
	def __init__(self, filename, lang=None):
		self.messages = {}
		self.lang = lang or os.getenv("LANG") # maybe LC_ALL
		message_file = codecs.open(filename, "r", "utf-8")
		for line in message_file.readlines():
			line = line.strip()
			parts = line.split('\t')
			if not parts[0] in self.messages: self.messages[parts[0]] = {}
			self.messages[parts[0]][parts[1]] = parts[2]

	##
	# Brief description of function
	# @param self Parameter description
	# @param message Parameter description
	def get_localized_message(self, message):
		if message in self.messages and self.lang in self.messages[message]:
			return self.messages[message][self.lang]
		else:
			return None
