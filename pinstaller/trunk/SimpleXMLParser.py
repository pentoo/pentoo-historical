"""
# Copyright 1999-2005 Gentoo Foundation
# This source code is distributed under the terms of version 2 of the GNU
# General Public License as published by the Free Software Foundation, a copy
# of which can be found in the main directory of this project.
Gentoo Linux Installer

$Id: SimpleXMLParser.py,v 1.13 2006/01/22 23:42:29 agaffney Exp $

"""

import xml.sax, string

class SimpleXMLParser(xml.sax.ContentHandler):

	##
	# Brief description of function
	# @param self Parameter description
	# @param file=None Parameter description
	def __init__(self, file=None):
		self._xml_elements = []
		self._xml_attrs = []
		self._xml_current_data = ""
		self._fntable = {}
		self._path = file
		self._prepass = False

	##
	# Brief description of function
	# @param self Parameter description
	# @param path Parameter description
	# @param fn Parameter description
	# @param call_on_null=False Parameter description
	def addHandler(self, path, fn, call_on_null=False):
		try:
			self._fntable[path].append((fn,call_on_null))
		except KeyError:
			self._fntable[path] = [(fn, call_on_null)]

	##
	# Brief description of function
	# @param self Parameter description
	# @param path Parameter description
	# @param fn Parameter description
	def delHandler(self, path, fn):
		try:
			for function in self._fntable[path]:
				if function[0] == fn:
					self._fntable[path].remove(function)
					return True
			return False
		except KeyError:
			return False

	def startElement(self, name, attr): 
		"""
		XML SAX start element handler

		Called when the SAX parser encounters an XML openning element.
		"""

		self._xml_elements.append(name)
		self._xml_attrs.append(attr)
		self._xml_current_data = ""

	##
	# Brief description of function
	# @param self Parameter description
	# @param name Parameter description
	def endElement(self, name):
		path = self._xml_element_path()
		if self._prepass:
			if self._xml_elements[-2] == "include":
				if self._xml_elements[-1] == "file":
					pass
				elif self._xml_elements[-1] == "command":
					pass
		if path in self._fntable.keys():
			for fn in self._fntable[path]:
				if self._xml_current_data != "" or fn[1]:
					# This is being disabled since this should only apply to certain values
#					if self._xml_current_data == "True":
#						self._xml_current_data = True
#					if self._xml_current_data == "False":
#						self._xml_current_data = False
#					if self._xml_current_data == "None":
#						self._xml_current_data = None
					if self._xml_current_data.startswith("<![CDATA["):
						self._xml_current_data = self._xml_current_data[9:-5]
					else:
						self._xml_current_data = self._xml_current_data.strip()
					fn[0](path, self._xml_current_data, self._xml_attrs[-1])
		# Keep the XML state
		self._xml_current_data = ""
		self._xml_attrs.pop()
		self._xml_elements.pop()

	##
	# Brief description of function
	# @param self Parameter description
	# @param data Parameter description
	def characters(self, data):
		"""
		XML SAX character data handler

		Called when the SAX parser encounters character data.
		"""

		# This converts data to a string instead of being Unicode
		# Maybe we should use Unicode strings instead of normal strings?
		self._xml_current_data += str(data)

	##
	# Brief description of function
	# @param self Parameter description
	def _xml_element_path(self):
		"""
		Return path to current XML node
		"""                
		return string.join(self._xml_elements, '/')

	##
	# Brief description of function
	# @param self Parameter description
	# @param path=None Parameter description
	def parse(self, path=None):
		"""
		Parse serialized configuration file.
		"""
#		self._prepass = True
		if path == None and self._path == None:
			raise GLIException("NoFileGiven",'fatal', 'parse', "You must specify a file to parse!")
		elif path == None:       
			xml.sax.parse(self._path, self)
		else:
			xml.sax.parse(path, self)
