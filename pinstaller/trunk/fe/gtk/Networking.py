# Copyright 1999-2005 Gentoo Foundation
# This source code is distributed under the terms of version 2 of the GNU
# General Public License as published by the Free Software Foundation, a copy
# of which can be found in the main directory of this project.

import gtk,gobject
import os
import re
import GLIScreen
import GLIUtility
import commands, string
import copy
#import subprocess
from Widgets import Widgets

class Panel(GLIScreen.GLIScreen):
	"""
	The Networking section of the installer.
	
	@author:    John N. Laliberte <allanonjl@gentoo.org>
	@license:   GPL
	"""
	# Attributes:
	title="Networking Settings"
	_helptext = """
<b><u>Networking</u></b>

If you previously set up a network interface in the Pre-install Configuration
screen, it should show up configured again in the Device list.

All detected interfaces should show up in the list, but you also have the option
to type in your own interface. Once you select an interface, select DHCP or
Static Configuration.  Then once you have set your network settings make sure to
click Save to add the interface to the list.

Wireless support currently is unavailable, but coming soon!  We even have the
boxes for it all ready to go.

Don't forget to set a hostname and domain name in the
"Hostname / Proxy Information / Other" tab!
"""
	
	# Operations
	def __init__(self, controller):
		GLIScreen.GLIScreen.__init__(self, controller)
	
		vert = gtk.VBox(False, 0)
		vert.set_border_width(10)
		self.gateway = ["",""] # device, ip
		self.gateway_is_set = False
		self.first_run = False
		
		# Treestore that holds the currently setup devices
		# -----------------------------------------------
		treedata = gtk.ListStore(gobject.TYPE_INT, gobject.TYPE_STRING, gobject.TYPE_STRING, gobject.TYPE_STRING, 
					 gobject.TYPE_STRING, gobject.TYPE_STRING, gobject.TYPE_STRING)
		columns = []
		treedatasort = gtk.TreeModelSort(treedata)
		treeview = gtk.TreeView(treedatasort)
		#self.treeview.connect("cursor-changed", self.selection_changed)
		columns.append(gtk.TreeViewColumn("Device    ", gtk.CellRendererText(), text=1))
		columns.append(gtk.TreeViewColumn("IP Address", gtk.CellRendererText(), text=2))
		columns.append(gtk.TreeViewColumn("Broadcast ", gtk.CellRendererText(), text=3))
		columns.append(gtk.TreeViewColumn("Netmask      ", gtk.CellRendererText(), text=4))
		columns.append(gtk.TreeViewColumn("DHCP Options ", gtk.CellRendererText(), text=5))
		columns.append(gtk.TreeViewColumn("Gateway      ", gtk.CellRendererText(), text=6))
		col_num = 0
		for column in columns:
				column.set_resizable(True)
				column.set_sort_column_id(col_num)
				treeview.append_column(column)
				col_num += 1
		treewindow = gtk.ScrolledWindow()
		treewindow.set_size_request(-1, 125)
		treewindow.set_shadow_type(gtk.SHADOW_IN)
		treewindow.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
		treewindow.add(treeview)
		# -----------------------------------------------
		
		
		# Interface frame where you select the device
		# -----------------------------------------------
		#create the outside box for the ethernet device
		frame = gtk.Frame()
		# create the ethernet dropdown
		ethernet_select_combo = gtk.combo_box_entry_new_text()
		# pack it all into a box
		ethernet_and_label = gtk.HBox(False,0)
		label = gtk.Label(" _Interface: ")
		label.set_use_underline(True)
		save_button = gtk.Button("Save")
		save_button.set_size_request(100,-1)
		delete_button = gtk.Button("Delete")
		delete_button.set_size_request(100,-1)
		ethernet_and_label.pack_start(label, expand=False, fill=False, padding=5)
		ethernet_and_label.pack_start(ethernet_select_combo, expand=False, fill=False, padding=5)
		ethernet_and_label.pack_start(save_button, expand=False, fill=False, padding=5)
		ethernet_and_label.pack_start(delete_button, expand=False, fill=False, padding=5)
		# set the new widget to be the label plus the ethernet dropdown
		frame.set_label_widget(ethernet_and_label)
		# align it to the top left of the frame
		frame.set_label_align(0.0, .5)
		# -----------------------------------------------
		
		# Type Frame where you select static or dhcp
		# -----------------------------------------------
		# create the type of ethernet frame
		ethernet_type_frame_hbox = gtk.HBox(False, 0)
		ethernet_type_frame = gtk.Frame()
		ethernet_type_frame.set_border_width(5)
		# create the combo that holds the different types of interfaces
		ethernet_type_select_combo = gtk.combo_box_new_text()
		ethernet_type_select_combo.append_text("DHCP")
		ethernet_type_select_combo.append_text("Static")
		self.dhcp = 0
		self.static = 1
		# pack it into a box
		ethernet_type_and_label = gtk.HBox(False,0)
		label = gtk.Label(" _Configuration: ")
		label.set_use_underline(True)
		ethernet_type_and_label.pack_start(label, expand=False, fill=False, padding=5)
		ethernet_type_and_label.pack_start(ethernet_type_select_combo, expand=False, fill=False, padding=5)		
		# set the new widget to be the label plus the ethernet dropdown
		ethernet_type_frame.set_label_widget(ethernet_type_and_label)
		# align it to the top left of the frame
		ethernet_type_frame.set_label_align(0.0, .5)
		# -----------------------------------------------
		
		# Create the gtk.Notebook to hold the static and dhcp configurations
		# -----------------------------------------------
		static_and_dhcp_notebook = gtk.Notebook()
		static_and_dhcp_notebook.set_show_tabs(False) # hide the tabs
		static_and_dhcp_notebook.set_show_border(False) # hide the border
		#------------------------------------------------
		
		# Static configuration frame of the gtk.Notebook ( page 1 )
		# -----------------------------------------------
		# create the static configuration frame
		ethernet_static_frame_hbox = gtk.HBox(False, 0)
		ethernet_static_frame = gtk.Frame()
		ethernet_static_frame.set_border_width(5)
		ethernet_static_frame.set_shadow_type(gtk.SHADOW_NONE)
		#ethernet_static_frame.set_label("Static Configuration")
		#ethernet_static_frame.set_label_align(0.0, .5)
		# the hbox to pack the entry boxes into
		static_entry_table = gtk.Table(rows=4, columns=2, homogeneous=False)
		static_entry_table.set_row_spacings(5)
		
		# create the static ip box
		staticip_entry = gtk.Entry()
		staticip_entry.set_max_length(15)
		# pack it all into a box
		label = gtk.Label(" _IP Address: ")
		label.set_size_request(50,-1)
		label.set_use_underline(True)
		label.set_alignment(0.0, 0.5)
		#label.set_size_request(150, -1)
		static_entry_table.attach(label,0,1,0,1)
		static_entry_table.attach(staticip_entry,1,2,0,1)
	
		# create the broadcast box
		broadcastip_entry = gtk.Entry()
		broadcastip_entry.set_max_length(15)
		# pack it all into a box
		label = gtk.Label(" _Broadcast: ")
		label.set_use_underline(True)
		label.set_alignment(0.0, 0.5)
		static_entry_table.attach(label,0,1,1,2)
		static_entry_table.attach(broadcastip_entry,1,2,1,2)
		
		# create the netmask box
		netmaskip_entry = gtk.Entry()
		netmaskip_entry.set_max_length(15)
		# pack it all into a box
		label = gtk.Label(" _Netmask: ")
		label.set_use_underline(True)
		label.set_alignment(0.0, 0.5)
		static_entry_table.attach(label,0,1,2,3)
		static_entry_table.attach(netmaskip_entry,1,2,2,3)
		
		# create the gateway box
		gatewayip_entry = gtk.Entry()
		gatewayip_entry.set_max_length(15)
		# pack it all into a box
		label = gtk.Label(" _Gateway: ")
		label.set_use_underline(True)
		label.set_alignment(0.0, 0.5)
		static_entry_table.attach(label,0,1,3,4)
		static_entry_table.attach(gatewayip_entry,1,2,3,4)
		
		# now add the 1 table to the ethernet_static_frame
		static_entry_hbox = gtk.HBox(False,0)
		static_entry_hbox.set_border_width(5)
		static_entry_hbox.pack_start(static_entry_table, expand=False, fill=False, padding=5)
		ethernet_static_frame.add(static_entry_hbox)
		static_and_dhcp_notebook.append_page(ethernet_static_frame, gtk.Label("static"))
		#------------------------------------------------
		
		# Create the DHCP page of the gtk.Notebook ( page 2 )
		# -----------------------------------------------
		# create the dhcp configuration frame
		ethernet_dhcp_frame_hbox = gtk.HBox(False, 0)
		ethernet_dhcp_frame = gtk.Frame()
		ethernet_dhcp_frame.set_border_width(5)
		ethernet_dhcp_frame.set_shadow_type(gtk.SHADOW_NONE)
		#ethernet_dhcp_frame.set_label("DHCP Configuration")
		#ethernet_dhcp_frame.set_label_align(0.0, .5)
		# the hbox to pack the entry boxes into
		dhcp_entry_table = gtk.Table(rows=3, columns=2, homogeneous=False)
		dhcp_entry_table.set_row_spacings(5)
		
		# create the dhcp box
		dhcp_options_entry = gtk.Entry()
		dhcp_options_entry.set_max_length(15)
		# pack it all into a box
		label = gtk.Label(" _DHCP Options: ")
		label.set_size_request(50,-1)
		label.set_use_underline(True)
		label.set_alignment(0.0, 0.5)
		#label.set_size_request(150, -1)
		dhcp_entry_table.attach(label,0,1,0,1)
		dhcp_entry_table.attach(dhcp_options_entry,0,1,1,2)
		
		# now add the 1 table to the ethernet_static_frame
		dhcp_entry_hbox = gtk.HBox(False,0)
		dhcp_entry_hbox.set_border_width(50)
		dhcp_entry_hbox.pack_start(dhcp_entry_table, expand=False, fill=False, padding=5)
		ethernet_dhcp_frame.add(dhcp_entry_hbox)
		
		static_and_dhcp_notebook.append_page(ethernet_dhcp_frame, gtk.Label("dhcp"))
		# -----------------------------------------------
		
		# Create the wireless frame to hold wireless information
		# -----------------------------------------------
		# create the wireless frame
		wireless_frame_hbox = gtk.HBox(False, 0)
		wireless_frame = gtk.Frame()
		#wireless_frame.set_border_width(5)
		# align it to the top left of the frame
		wireless_frame.set_label_align(0.0, .5)
		# create the checkbox that will determine if you have wireless or not
		wireless_checkbox = gtk.CheckButton("Wireless")
		# pack it all into a box
		wireless_and_label = gtk.HBox(False,0)
		wireless_and_label.pack_start(wireless_checkbox, expand=False, fill=False, padding=5)
		# set the new widget to be the checkbox
		wireless_frame.set_label_widget(wireless_and_label)
		# create the wireless input boxes
		wireless_entry_table = gtk.Table(rows=2, columns=2, homogeneous=False)
		wireless_entry_table.set_row_spacings(5)
		# create the ESSID box
		essid_entry = gtk.Entry()
		essid_entry.set_max_length(30)
		# pack it all into a box
		essid_and_label = gtk.HBox(False,0)
		label = gtk.Label(" _ESSID: ")
		label.set_use_underline(True)
		label.set_alignment(0.0, 0.5)
		label.set_size_request(50,-1)
		wireless_entry_table.attach(label,0,1,0,1)
		wireless_entry_table.attach(essid_entry,1,2,0,1)
		# create the Key box
		key_entry = gtk.Entry()
		key_entry.set_max_length(15)
		# pack it all into a box
		key_and_label = gtk.HBox(False,0)
		label = gtk.Label(" _Key: ")
		label.set_use_underline(True)
		label.set_alignment(0.0, 0.5)
		wireless_entry_table.attach(label,0,1,1,2)
		wireless_entry_table.attach(key_entry,1,2,1,2)
		
		# add it to the wireless frame
		wireless_entry_hbox = gtk.HBox(False,0)
		wireless_entry_hbox.set_border_width(5)
		wireless_entry_hbox.pack_start(wireless_entry_table, expand=False, fill=False, padding=5)
		wireless_frame.add(wireless_entry_hbox)
		# -----------------------------------------------
		
		# Ethernet hardware information frame
		# -----------------------------------------------
		hardware_frame = gtk.Frame()
		#hardware_frame.set_border_width(5)
		# align it to the top left of the frame
		hardware_frame.set_label_align(0.0, .5)
		hardware_frame.set_label("Hardware Information")
		# create the textview to hold the hardware information
		#textview = gtk.TextView(buffer=None)
		#textview.set_editable(False)
		#textbuffer = textview.get_buffer()
		hardware_label = gtk.Label("No Device Selected")
		hardware_label.set_size_request(250,75)
		hardware_label.set_line_wrap(True)
		#textbuffer.set_text(string)
		hardware_frame.add(hardware_label)
		# -----------------------------------------------
		
		# add the configuration ethernet frame and wireless frame to the hbox.
		configuration_and_wireless_hbox = gtk.HBox(False, 0)
		wireless_and_hardware_vbox = gtk.VBox(False,0)
		wireless_and_hardware_vbox.pack_start(wireless_frame, expand=True, fill=True, padding=5)
		wireless_and_hardware_vbox.pack_start(hardware_frame, expand=True, fill=True, padding=5)		
		configuration_and_wireless_hbox.pack_start(ethernet_type_frame, expand=True, fill=True, padding=5)
		configuration_and_wireless_hbox.pack_start(wireless_and_hardware_vbox, expand=True, fill=True, padding=5)
			
		# add wireless and configuration to interface frame
		frame.add(configuration_and_wireless_hbox)
		
		# add the 1 hbox to the ethernet_type frame
		#ethernet_type_frame.add(ethernet_static_frame)
		
		# add the gtk.Notebook to the ethernet_type frame.
		ethernet_type_frame.add(static_and_dhcp_notebook)
		
		# finally show the frames ( after everything has been added )
		ethernet_static_frame.show()
		wireless_frame.show()
		ethernet_type_frame.show()
		frame.show()
		
		# add hostname
		bottom_hbox = gtk.VBox(False,0)
		hostname_entry = gtk.Entry()
		hostname_entry.set_max_length(50) # only as long as ipv4 addresses
		hostname_entry.set_size_request(150,-1)
		
		hostname_and_label = gtk.HBox(False,0)
		label = gtk.Label(" _Hostname: ")
		label.set_use_underline(True)
		label.set_size_request(150,-1)
		hostname_and_label.pack_start(label, expand=False, fill=False, padding=5)
		hostname_and_label.pack_start(hostname_entry, expand=False, fill=False, padding=5)
		
		# add dnsdomainname
		dnsdomainname_entry = gtk.Entry()
		dnsdomainname_entry.set_max_length(50) # only as long as ipv4 addresses
		dnsdomainname_entry.set_size_request(150,-1)
		
		dnsdomainname_and_label = gtk.HBox(False,0)
		label = gtk.Label(" _DNS Domain Name: ")
		label.set_use_underline(True)
		label.set_size_request(150,-1)
		dnsdomainname_and_label.pack_start(label, expand=False, fill=False, padding=5)
		dnsdomainname_and_label.pack_start(dnsdomainname_entry, expand=False, fill=False, padding=5)

		# pack the treewindow and overall options into an hbox
		top_window_hbox = gtk.HBox(False, 0)
		#static_options_vbox = gtk.VBox(False,0)
		#static_options_vbox.pack_start(hostname_and_label, expand=False, fill=False, padding=5)
		#static_options_vbox.pack_start(dnsdomainname_and_label, expand=False, fill=False, padding=5)
		#static_options_vbox.pack_start(gateway_and_label, expand=False, fill=False, padding=5)
		treeview_vbox = gtk.VBox(False,0)
		#treeview_vbox.pack_start(gtk.Label("Currently Saved Devices:"), expand=False, fill=False, padding=5)
		treeview_vbox.pack_start(treewindow, expand=False, fill=False, padding=5)
		top_window_hbox.pack_start(treeview_vbox, expand=True, fill=True, padding=5)
		#top_window_hbox.pack_end(static_options_vbox, expand=False, fill=False, padding=5)
		
		bottom_hbox.pack_start(hostname_and_label, expand=False, fill=False, padding=5)
		bottom_hbox.pack_start(dnsdomainname_and_label, expand=False, fill=False, padding=5)
		
		# pack the topmost frame
		vert.pack_start(top_window_hbox, expand=False, fill=False, padding=0)
		vert.pack_start(frame, expand=True, fill=True, padding=10)
		#vert.pack_start(bottom_hbox, expand=True, fill=True, padding=5)
		
		notebook = gtk.Notebook()
		#notebook.set_show_tabs(False)
		#self.add_content(vert)
		notebook.set_show_border(False)
		notebook.append_page(vert, gtk.Label("Device Information"))
		notebook.append_page(bottom_hbox, gtk.Label("Hostname / Proxy Information / Other"))
		self.add_content(notebook)
		
		# connect to widget events
		treeview.connect("cursor-changed", self.selection_changed)
		wireless_checkbox.connect("toggled", self.wireless_clicked)
		ethernet_type_select_combo.connect("changed", self.ethernet_type_changed)
		ethernet_select_combo.connect("changed", self.ethernet_device_selected)
		ethernet_select_combo.child.connect("activate", self.ethernet_device_added)
		static_and_dhcp_notebook.connect("switch-page", self.switch)
		save_button.connect("clicked", self.save_clicked)
		delete_button.connect("clicked", self.delete_clicked)
		
		# add all the boxes that we access later to a dictionary
		self.widgets = {"essid":essid_entry, "key":key_entry,
				"ipaddress":staticip_entry, "broadcast":broadcastip_entry, "netmask":netmaskip_entry,
				"ethernet_type":ethernet_type_select_combo, "wireless_checkbox":wireless_checkbox,
				"ethernet_device":ethernet_select_combo, "hardware_info":hardware_label,
				"static_dhcp_notebook":static_and_dhcp_notebook, "dhcp_options":dhcp_options_entry,
				"treedata":treedata, "treeview":treeview, "gateway":gatewayip_entry,
				"hostname":hostname_entry, "domainname":dnsdomainname_entry
				}
	
	# sets the initial default condition of the frame
	def set_initial_conditions(self):
		
		# populate the ethernet devices
		self.populate_ethernet_device_widget()
		
		# disable the static entries
		self.set_static_entries(False)
		
		# set DHCP to be the default selected
		self.widgets["ethernet_type"].set_active(self.dhcp)
		
		# disable the wireless entries
		self.set_wireless_entries(False)
		
		# disable the ethernet type dropdown, and wireless checkbox
		self.set_overall_widgets(False)
		
		# set variable for the "first run" through
		self.first_run = True
		
	def set_wireless_entries(self, value):
		# always clear the entries
		self.widgets["essid"].set_text("")
		self.widgets["key"].set_text("")
		
		# they checked the box so enable the boxes for input
		self.widgets["essid"].set_sensitive(value)
		self.widgets["key"].set_sensitive(value)

	def set_static_entries(self,value):
		# always clear the entries
		self.widgets["ipaddress"].set_text("")
		self.widgets["broadcast"].set_text("")
		self.widgets["netmask"].set_text("")
		
		self.widgets["ipaddress"].set_sensitive(value)
		self.widgets["broadcast"].set_sensitive(value)
		self.widgets["netmask"].set_sensitive(value)
	
	def set_overall_widgets(self, value):
		self.widgets["ethernet_type"].set_sensitive(value)
		self.widgets["wireless_checkbox"].set_sensitive(value)
	
	def populate_ethernet_device_widget(self):
		device_list = self.get_ethernet_devices()
		for device in device_list:
			self.widgets["ethernet_device"].append_text(device)
			
	# below here are the events connected to widgets
	def wireless_clicked(self, widget):
		
		if widget.get_active():
			self.set_wireless_entries(True)
		else:
			self.set_wireless_entries(False)
			
	def ethernet_type_changed(self, widget):
		selected_text = self.get_active_text(widget)
		if selected_text == "DHCP":
			# disable 3 input boxes and set ip address to dhcp
			self.set_static_entries(False)
			self.widgets["dhcp_options"].set_text("")
			self.widgets["ipaddress"].set_text("dhcp")
			
			# flip the gtk.Notebook to allow input of dhcp options
			self.widgets["static_dhcp_notebook"].set_current_page(1)
			
		elif selected_text == "Static":
			self.set_static_entries(True)
			self.widgets["static_dhcp_notebook"].set_current_page(0)
	
	def ethernet_device_selected(self, widget):
		# enable the selection of wireless and static configurations
		self.set_overall_widgets(True)
		
		# clear the boxes so things aren't dragged over
		#self.set_static_entries(True)
		self.widgets["dhcp_options"].set_text("")
		
		# get the hardware information about the device and set it
		info = self.get_ethernet_device_info(widget.get_child().get_text())
		self.widgets["hardware_info"].set_text(info)
		
		# if the gateway is not set, or if its the ethernet device it should be set for, enable it.
		if self.gateway_is_set == False or self.gateway[0] == self.widgets["ethernet_device"].get_child().get_text():
			self.widgets["gateway"].set_sensitive(True)
			self.widgets["gateway"].set_text(self.gateway[1])
		else:
			self.widgets["gateway"].set_text("")
			self.widgets["gateway"].set_sensitive(False)
			
		# figure out if its in the list, and if so, flip to the right page
		# and display ( get ) the info.
		device = self.widgets["ethernet_device"].get_child().get_text()
		row_number = self.device_in_treeview(device)
		if self.device_in_treeview(device) != None:
			# select it
			sel = self.widgets["treeview"].get_selection()
			sel.select_path(row_number)
			# force the click event so it selects the correct
			# things.
			self.selection_changed(self.widgets["treeview"])
			
	def ethernet_device_added(self, widget):
		self.widgets["ethernet_device"].append_text(widget.get_text())
	
	def save_clicked(self, widget, data=None):
		# retrieve the data
		data = self.get_information()
		
		# only proceed if the ethernet device isn't blank
		if data["ethernet_device"] != "":
			
			# save the gateway if its not set
			# the user must unset the gateway to change it to a different device.
			if self.widgets["gateway"].get_text() != "":
				self.gateway[0] = self.widgets["ethernet_device"].get_child().get_text()
				self.gateway[1] = self.widgets["gateway"].get_text()
				self.gateway_is_set = True
				
			# this will occur when the gateway is unset!
			if self.widgets["gateway"].get_text() == "" and self.gateway_is_set == True and \
			   self.widgets["ethernet_device"].get_child().get_text() == self.gateway[0]:
				self.gateway[0] = ""
				self.gateway[1] = ""
				self.gateway_is_set = False
			
			if self.gateway_is_set == True and self.widgets["ethernet_device"].get_child().get_text() == self.gateway[0]:
				gateway = self.gateway[1]
			else:
				gateway = ""
				
			# store it in the top box.
			self.add_to_treedata([0, data["ethernet_device"], data["ipaddress"], data["broadcast"],
							data["netmask"], data["dhcp_options"],gateway])
		
		else:
			msgdialog = Widgets().error_Box("No Ethernet Device","Please enter a device!")
			result = msgdialog.run()
			msgdialog.destroy()
	
	def delete_clicked(self, widget, data=None):
		# gets which one is currently selected
		treeselection = self.widgets["treeview"].get_selection()
		treemodel, treeiter = treeselection.get_selected()
		#selected_row = gtk.TreeRowReference(treemodel, treemodel.get_path(treeiter))
		#print str(treemodel.get_value(treeiter, 1))
		device = treemodel.get_value(treeiter, 1) # this is the number that identifies the row
		#if treeiter != None:
		#	self.widgets["treedata"].remove(treeiter)
			
		# iterate over the liststore to find the row, and then delete it
		store = self.widgets["treedata"]
		model = self.widgets["treeview"].get_model()
		#iter = model.get_iter_root()
		iter = store.get_iter_first()
		
		while(iter != None):
			dev = store.get_value(iter, 1)
			print dev + " " + device
			#print model.get_path(iter)
			#temp_row_ref = gtk.TreeRowReference(model, model.get_path(iter))
			#if selected_row.get_path() == temp_row_ref.get_path():
				#store.remove(iter)
				#break
				
			if dev == device:
				store.remove(iter)
				break
			# necessary b/c w/o it, iter error
			else:
				iter = store.iter_next(iter)
	
	def switch(self, widget, page, page_num, data=None):
		# debug only
		pass
		#print "page num: "+str(page_num)
		#print self.widgets["static_dhcp_notebook"].get_current_page()
		#print "current page: "+str(widget.get_current_page())
	
	def selection_changed(self, widget, data=None):
		# gets which one is currently selected
		treeselection = self.widgets["treeview"].get_selection()
		treemodel, treeiter = treeselection.get_selected()
		row = treemodel.get_value(treeiter, 1) # this is the device that identifies the row
		
		# iterate over the liststore to find the row
		store = self.widgets["treedata"]
		iter = store.get_iter_first()
		
		while(iter != None):
			dev = store.get_value(iter, 1)
			if dev == row:
				number, device, ip, broadcast, netmask, options = store.get(iter, 0, 1, 2, 3, 4, 5)
				break
			# necessary b/c w/o it, iter error
			else:
				iter = store.iter_next(iter)
		
		# is it dhcp or static? ( to set the type selected )
		if ip == "dhcp":
			self.widgets["ethernet_type"].set_active(self.dhcp)
		else:
			# its static
			self.widgets["ethernet_type"].set_active(self.static)
			
		# load them all, because they will just be blank if not set.
		self.widgets["ethernet_device"].get_child().set_text(device)
		self.widgets["ipaddress"].set_text(ip)
		self.widgets["broadcast"].set_text(broadcast)
		self.widgets["netmask"].set_text(netmask)
		self.widgets["dhcp_options"].set_text(options)
		
		# only set if it is the gateway
		if device == self.gateway[0]:
			self.widgets["gateway"].set_text(self.gateway[1])
		
		


	# helper functions
	def get_active_text(self,combobox):
		model = combobox.get_model()
		active = combobox.get_active()
		if active < 0:
			return None
		return model[active][0]
	
	def get_ethernet_devices(self):
		put, get = os.popen4("ifconfig -a | egrep -e '^[^ ]'|sed -e 's/ .\+$//'")
		devices=[]
		for device in get.readlines():
			device=device.strip()
			if device!="lo":
				devices.append(device)
		return devices
	
	def get_ethernet_device_info(self, device):
		# grab the first line from dmesg for the detected device..
		# this may change later.
		try:
			put, get = os.popen4("dmesg | grep " + device + " | head -n 1")
	
			info = get.readlines()
			if len(info) != 1:
				if len(info) != 0:
					info = "An error occurred retrieving hardware information"
				else:
					info = "No information was found in dmesg about your device."
			else:
				info = info[0]
			
		except:
			print "Error"
		return info
	
	def get_information(self):
		# retrieve all the information from the input boxes.
				#self.widgets = {"essid":essid_entry, "key":key_entry,
				#"ipaddress":staticip_entry, "broadcast":broadcastip_entry, "netmask":netmaskip_entry,
				#"ethernet_type":ethernet_type_select_combo, "wireless_checkbox":wireless_checkbox,
				#"ethernet_device":ethernet_select_combo, "hardware_info":hardware_label,
				#"static_dhcp_notebook":static_and_dhcp_notebook
				#}
		data ={}
		data["ipaddress"]=self.widgets["ipaddress"].get_text()
		data["broadcast"] = self.widgets["broadcast"].get_text()
		data["netmask"] = self.widgets["netmask"].get_text()
		data["eth_type"] = self.get_active_text(self.widgets["ethernet_type"])
		data["ethernet_device"] = self.widgets["ethernet_device"].get_child().get_text()
		data["dhcp_options"] = self.widgets["dhcp_options"].get_text()
		
		# add in wireless support when supported in the backend
		
		return data
	
	def add_to_treedata(self, data ):
		# need to figure out if this already exists in the treeview, 
		# and if not, add it as a new entry.  If it does already exist,
		# modify the entry. need to modify data[0]
		
		store = self.widgets["treedata"]
		iter = store.get_iter_first()
		new_item = True
		#count = 0
		# if the value of ethernet_device = value in any of
		# the treeviews ethernet column, we need to edit that column.
		# if not, its a new entry.
		while ( iter != None ):
			values = store.get(iter, 0, 1, 2, 3, 4, 5, 6)
			
			if values[1] == data[1]:
				# modify this entry!
				store.set(iter, 0, 0, 1, data[1], 2, data[2],
					  3, data[3], 4, data[4], 5, data[5], 6, data[6])
				
				# and set to False
				new_item = False
				
			#count+=1
			iter = store.iter_next(iter)
		
		if new_item == True:
			# this is a new entry
			#data[0] = count+1
			store.append(data)
	
	def device_in_treeview(self, device):
		return_val = None
		
		store = self.widgets["treedata"]
		iter = store.get_iter_first()
		
		row_num=0
		while(iter != None):
			dev = store.get_value(iter, 1)
			if dev == device:
				return_val = row_num
				break
			# necessary b/c w/o it, iter error
			else:
				iter = store.iter_next(iter)
			row_num=row_num+1
		return return_val
	
	###
	def activate(self):
		if self.first_run == False:
			self.set_initial_conditions()
		
		# load everything
		interfaces = self.controller.install_profile.get_network_interfaces()

		# Preload networking info from CC...stolen from gli-dialog
		CC_iface = self.controller.client_profile.get_network_interface()
		if CC_iface and (CC_iface not in interfaces):
			#The CC has a network config that's not already there.  Preload it.
			CC_net_type = self.controller.client_profile.get_network_type()
			if CC_net_type == 'dhcp':
				interfaces[CC_iface] = ('dhcp', self.controller.client_profile.get_network_dhcp_options(), None)
			elif CC_net_type == 'static':
				interfaces[CC_iface] = (self.controller.client_profile.get_network_ip(), self.controller.client_profile.get_network_broadcast(), self.controller.client_profile.get_network_netmask())

		try:
			dev, gatewayip = self.controller.install_profile.get_default_gateway()
		except:
			dev = None
		
		for interface in interfaces.keys():
			if interfaces[interface][0] == "dhcp":
				if interfaces[interface][1] == None:
					options = ""
				else:
					options = interfaces[interface][1]
					
				self.add_to_treedata( [0, interface, interfaces[interface][0], "",
						       "", options, ""] )
			else:
				gateway = ""
				# if this is the device that is the gateway
				if dev == interface:
					gateway = gatewayip
					self.gateway = [dev, gatewayip]
					self.gateway_is_set = True
					
				self.add_to_treedata( [0, interface, interfaces[interface][0], interfaces[interface][1],
						       interfaces[interface][2], "", gateway] )
		
		self.widgets["hostname"].set_text(self.controller.install_profile.get_hostname())
		self.widgets["domainname"].set_text(self.controller.install_profile.get_domainname())
			
		self.controller.SHOW_BUTTON_EXIT    = True
		self.controller.SHOW_BUTTON_HELP    = True
		self.controller.SHOW_BUTTON_BACK    = True
		self.controller.SHOW_BUTTON_FORWARD = True
		self.controller.SHOW_BUTTON_FINISH  = False
		
	def deactivate(self):
		return_value = False
		
		# save everything to profile
		interfaces={}
		# iterate over the liststore
		store = self.widgets["treedata"]
		iter = store.get_iter_first()
		
		while(iter != None):
			number, device, ip, broadcast, netmask, options, gateway = store.get(iter, 0, 1, 2, 3, 4, 5, 6)
			
			if ip != "dhcp":
				interfaces[device] = (ip, broadcast, netmask)
			else:
				print options
				interfaces[device]=(ip, options, None)
			
			if gateway != "":
				# store the gateway
				try:
					self.controller.install_profile.set_default_gateway(None,self.gateway[1], \
										    {'interface':self.gateway[0]})
				except:
					msgdialog=Widgets().error_Box("Malformed IP","Malformed IP address in your gateway!")
					result = msgdialog.run()
					msgdialog.destroy()
					return False
				
			iter = store.iter_next(iter)

		# If there are no interfaces configured, confirm this is what the user actually wants
		if not interfaces:
			msgdlg = gtk.MessageDialog(parent=self.controller.window, type=gtk.MESSAGE_QUESTION, buttons=gtk.BUTTONS_YES_NO, message_format="You have not configured any interfaces. Continue?")
			resp = msgdlg.run()
			msgdlg.destroy()
			if resp == gtk.RESPONSE_NO:
				return False
		
		# store the stuff
		try:
			self.controller.install_profile.set_network_interfaces(interfaces)
		except:
			msgdialog=Widgets().error_Box("Malformed IP","Malformed IP address in one of your interfaces!")
			result = msgdialog.run()
			msgdialog.destroy()
			return False
		
		# store dnsdomainname and hostname
		hostname = self.widgets["hostname"].get_text()
		domainname = self.widgets["domainname"].get_text()
		if( hostname != "" and domainname != ""):
			self.controller.install_profile.set_hostname(None, hostname, None)
			self.controller.install_profile.set_domainname(None, domainname, None)
			return_value = True
		elif( self.first_run == True):
			msgdialog=Widgets().error_Box("Missing information","You didn't set your hostname and/or dnsdomainname!")
			result = msgdialog.run()
			msgdialog.destroy()
			return_value = False
		else:
			return_value = True
		
		return return_value
