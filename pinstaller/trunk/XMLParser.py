# Copyright 1999-2005 Gentoo Foundation
# This source code is distributed under the terms of version 2 of the GNU
# General Public License as published by the Free Software Foundation, a copy
# of which can be found in the main directory of this project.
import xml.sax, string, xml.dom.minidom

class XMLTag(object):

	def __init__(self, name=None, attr=None, children=None, contents=None):
		self._tag = { 'name': "", 'attr': {}, 'children': [], 'contents': "" }
		if name:
			self.set_name(name)
		if attr:
			self.set_attrs(attr)
		if children:
			self.set_children(children)
		if contents:
			self.set_contents(contents)

	def get_name(self):
		return self._tag['name']

	def set_name(self, name):
		self._tag['name'] = name

	def get_attrs(self):
		return self._tag['attr']

	def get_attr(self, attrname):
		try:
			return self._tag['attr'][attrname]
		except KeyError:
			return None

	def set_attr(self, attrname, attrvalue):
		self._tag['attr'][attrname] = attrvalue

	def set_attrs(self, attr):
		self._tag['attr'] = attr

	def del_attr(self, attrname):
		del self._tag['attr'][attrname]

	def get_children(self):
		return self._tag['children']

	def set_children(self, children):
		self._tag['children'] = children

	def get_child(self, index):
		return self._tag['children'][index]

	def add_child(self, child, index=-1):
		if index == -1:
			self._tag['children'].append(child)
		else:
			self._tag['children'].insert(child, index)

	def del_child(self, index):
		del self._tag['children'][index]

	def get_contents(self):
		return self._tag['contents']

	def set_contents(self, contents):
		self._tag['contents'] = contents

	def xml(self, output_this_tag=True, make_pretty=False):
		_xml = ""
		if output_this_tag:
			_xml += "<" + self.get_name()
			tag_attrs = self.get_attrs()
			if tag_attrs:
				sorted_attrs = tag_attrs.keys()
				sorted_attrs.sort()
				for attr in sorted_attrs:
					_xml += " " + attr + '="' + tag_attrs[attr] + '"'
			_xml += ">"
			for child in self.get_children():
				_xml += child.xml()
			_xml += self.get_contents() + "</" + self.get_name() + ">"
		else:
			for child in self.get_children():
				_xml += child.xml()
		if make_pretty:
			dom = xml.dom.minidom.parseString(_xml)
			return dom.toprettyxml()
		else:
			return _xml

	def get_value(self, path):
		pathlist = path.split(".")
		if not path:
			return self.get_contents()
		if len(pathlist) == 1:
			if pathlist[0] in self.get_attrs():
				return self.get_attrs()[path]
		for child in self.get_children():
			if child.get_name() == pathlist[0]:
				return child.get_value(".".join(pathlist[1:]))
		return None

	def get_tag(self, path):
		pathlist = path.split(".")
		if len(pathlist) == 1:
			for child in self.get_children():
				if child.get_name() == path:
					return child
			return None
		else:
			for child in self.get_children():
				if child.get_name() == pathlist[0]:
					return child.get_tag(".".join(pathlist[1:]))
			return None

	def set_value(self, path, value):
		pathlist = path.split(".")
		if not path:
			self.set_contents(value)
			return True
		if len(pathlist) == 1:
			if pathlist[0] in self.get_attrs():
				self.get_attrs()[path] = value
				return True
		for child in self.get_children():
			if child.get_name() == pathlist[0]:
				return child.set_value(".".join(pathlist[1:]), value)
		return False

	def __getitem__(self, item):
		return self.get_value(item)

	def __setitem__(self, item, value):
		return self.set_value(item, value)

	name = property(get_name, set_name)
	attr = property(get_attrs, set_attrs)
	children = property(get_children, set_children)
	contents = property(get_contents, set_contents)

class XMLParser(xml.sax.ContentHandler, XMLTag):

	def __init__(self, file=None):
		XMLTag.__init__(self, name="__top__")
		self._xml_elements = []
		self._xml_attrs = []
		self._xml_current_data = ""
		self._xml_tags = [self]
		self._path = file

	def startElement(self, name, attr): 
		"""
		XML SAX start element handler

		Called when the SAX parser encounters an XML opening element.
		"""

		self._xml_elements.append(name)
		self._xml_attrs.append(attr)
		self._xml_current_data = ""
		self._xml_tags.append(XMLTag(name=name, attr=dict(attr)))
		self._xml_tags[-2].add_child(self._xml_tags[-1])

	def endElement(self, name):
		path = self._xml_element_path()

		if self._xml_current_data:
			self._xml_tags[-1].set_contents(self._xml_current_data)

		# Keep the XML state
		self._xml_current_data = ""
		self._xml_attrs.pop()
		self._xml_elements.pop()
		self._xml_tags.pop()

	def characters(self, data):
		"""
		XML SAX character data handler

		Called when the SAX parser encounters character data.
		"""

		self._xml_current_data += data.strip()

	def _xml_element_path(self):
		"""
		Return path to current XML node
		"""                
		return string.join(self._xml_elements, '/')

	def parse(self, path=None):
		"""
		Parse serialized configuration file.
		"""
		if path == None and self._path == None:
			raise GLIException("NoFileGiven",'fatal', 'parse', "You must specify a file to parse!")
		elif path == None:       
			xml.sax.parse(self._path, self)
		else:
			xml.sax.parse(path, self)

	def serialize(self):
		return self.xml(output_this_tag=False, make_pretty=True)
