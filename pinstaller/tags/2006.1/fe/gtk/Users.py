# Copyright 1999-2005 Gentoo Foundation
# This source code is distributed under the terms of version 2 of the GNU
# General Public License as published by the Free Software Foundation, a copy
# of which can be found in the main directory of this project.

import gtk,gobject
import os
import re
import GLIScreen
from Widgets import Widgets
import GLIUtility

class Panel(GLIScreen.GLIScreen):
	"""
	The Users section of the installer.
	
	@author:    John N. Laliberte <allanonjl@gentoo.org>
	@license:   GPL
	"""
	
	# Attributes:
	title="User Settings"
	columns = []
	users = []
	current_users=[]
	root_verified = False
	_helptext = """
<b><u>Users</u></b>

Start off by setting the root password.  This will be the root password on the
newly-installed system, *NOT* the Livecd. Type it again to verify, and then
click the Verify button to check your typing.

Once you have clicked Verify you can then click Add user to add a normal user.

Adding a User for Daily Use:

Working as root on a Unix/Linux system is dangerous and should be avoided as
much as possible. Therefore it is strongly recommended to add a user for
day-to-day use.

Enter the username and password in respective boxes.  Make sure to type your
password carefully, it is not verified. All other fields are optional, but
setting groups is highly recommended.

The groups the user is member of define what activities the user can perform.
The following table lists a number of important groups you might wish to use:

<u>Group</u> 		<u>Description</u>
audio 		be able to access the audio devices
cdrom 		be able to directly access optical devices
floppy 		be able to directly access floppy devices
games 		be able to play games
portage 	be able to use emerge --pretend as a normal user
usb 		be able to access USB devices
plugdev 	Be able to mount and use pluggable devices such as cameras and USB sticks
video 		be able to access video capturing hardware and doing hardware acceleration
wheel 		be able to use su

Enter them in a comma-separated list in the groups box.

Optinally you may also specify the user's shell.  The default is /bin/bash.  If
you want to disable the user from logging in you can set it to /bin/false. You
can also specify the user's home directory (default is /home/username), userid
(default is the next available ID), and a comment describing the user.

Make sure to click Accept Changes to save the changes to your user.  They will
then show up in the list.
"""
	
	def __init__(self,controller):
		GLIScreen.GLIScreen.__init__(self, controller)

		content_str = "User screen!"
		
		vert = gtk.VBox(False, 0)
		vert.set_border_width(10)
		
		# setup the top box that data will be shown to the user in.
		self.treedata = gtk.ListStore(gobject.TYPE_STRING,gobject.TYPE_STRING, gobject.TYPE_STRING, 
										gobject.TYPE_STRING, gobject.TYPE_STRING, gobject.TYPE_STRING,
										gobject.TYPE_STRING)
			
		self.treeview = gtk.TreeView(self.treedata)
		self.treeview.connect("cursor-changed", self.selection_changed)
		self.columns.append(gtk.TreeViewColumn("Username    ", gtk.CellRendererText(), text=1))
		self.columns.append(gtk.TreeViewColumn("Groups", gtk.CellRendererText(), text=2))
		self.columns.append(gtk.TreeViewColumn("Shell      ", gtk.CellRendererText(), text=3))
		self.columns.append(gtk.TreeViewColumn("HomeDir ", gtk.CellRendererText(), text=4))
		self.columns.append(gtk.TreeViewColumn("UserID", gtk.CellRendererText(), text=5))
		self.columns.append(gtk.TreeViewColumn("Comment", gtk.CellRendererText(), text=6))
		col_num = 0
		for column in self.columns:
				column.set_resizable(True)
				column.set_sort_column_id(col_num)
				self.treeview.append_column(column)
				col_num += 1
		
		self.treewindow = gtk.ScrolledWindow()
		self.treewindow.set_size_request(-1, 125)
		self.treewindow.set_shadow_type(gtk.SHADOW_IN)
		self.treewindow.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
		self.treewindow.add(self.treeview)
		#vert.pack_start(self.treewindow, expand=False, fill=False, padding=0)
		
		# now add in the gtk.Notebook
		self.notebook = gtk.Notebook()
		self.notebook.set_tab_pos(gtk.POS_BOTTOM)
		#notebook.set_size_request(-1, -1)
		self.notebook.show()
		self.notebook.set_show_tabs(False)
		self.notebook.set_show_border(False)
		#notebookshow_border = True

		frame = gtk.Frame("")
		frame.set_border_width(10)
		frame.set_size_request(100, 75)
		frame.show()
		
		frame_vert = gtk.VBox(False,0)
		hbox = gtk.HBox(False, 0)
		#frame.add(frame_vert)
		
		vbox = gtk.VBox(False,0)
		# setup the action buttons
		reset = gtk.Button("Root Password", stock=None)
		reset.connect("clicked", self.root, "root")
		reset.set_size_request(150, -1)
		reset.show()
		vbox.pack_start(reset, expand=False, fill=False, padding=5)

		add = gtk.Button("Add user", stock=None)
		add.connect("clicked", self.addu, "add")
		add.set_size_request(150, -1)
		add.show()
		vbox.pack_start(add, expand=False, fill=False, padding=5)
		
		delete = gtk.Button("Delete user", stock=None)
		delete.connect("clicked", self.delete, "delete")
		delete.set_size_request(150, -1)
		delete.show()
		vbox.pack_start(delete, expand=False, fill=False, padding=5)
		
		hbox.pack_start(self.treewindow, expand=True, fill=True, padding=5)
		hbox.pack_start(vbox, expand=False, fill=False, padding=5)
		
		vert.pack_start(hbox, expand=False, fill=False, padding=0)
		
		# setup the first page
		frame_vert = gtk.VBox(False,0)
		
		# three blank hboxes
		hbox = gtk.HBox(False, 0)
		label = gtk.Label("")
		label.set_size_request(150, -1)
		hbox.pack_start(label, expand=False, fill=False, padding=5)
		frame_vert.add(hbox)
		hbox = gtk.HBox(False, 0)
		label = gtk.Label("")
		label.set_size_request(150, -1)
		hbox.pack_start(label, expand=False, fill=False, padding=5)
		frame_vert.add(hbox)
		hbox = gtk.HBox(False, 0)
		label = gtk.Label("")
		label.set_size_request(150, -1)
		hbox.pack_start(label, expand=False, fill=False, padding=5)
		frame_vert.add(hbox)
		
		hbox = gtk.HBox(False, 0)
		label = gtk.Label("Root Password")
		label.set_size_request(150, -1)
		hbox.pack_start(label, expand=False, fill=False, padding=5)
		self.root1 = gtk.Entry()
		self.root1.set_visibility(False)
		self.root1.set_size_request(150, -1)
		hbox.pack_start(self.root1, expand=False, fill=False, padding=5)
		frame_vert.add(hbox)
		
		hbox = gtk.HBox(False, 0)
		label = gtk.Label("Verify Password")
		label.set_size_request(150, -1)
		label.show()
		hbox.pack_start(label, expand=False, fill=False, padding=5)
		self.root2 = gtk.Entry()
		self.root2.set_visibility(False)
		self.root2.set_size_request(150, -1)
		hbox.pack_start(self.root2, expand=False, fill=False, padding=5)
		verify = gtk.Button("Verify!")
		verify.connect("clicked", self.verify_root_password, "delete")
		verify.set_size_request(150, -1)
		hbox.pack_start(verify, expand=False, fill=False, padding=5)
		self.verified = gtk.Image()
		self.verified.set_from_stock(gtk.STOCK_CANCEL, gtk.ICON_SIZE_SMALL_TOOLBAR)
		hbox.pack_start(self.verified, expand=False, fill=False, padding=5)
		frame_vert.add(hbox)
		
		# two more blank hboxes
		hbox = gtk.HBox(False, 0)
		# reset button if they want to reset the root password
		# loaded from a user profile
		self.reset_pass2 = gtk.Button("Reset root password")
		self.reset_pass2.connect("clicked", self.reset, "root")
		self.reset_pass2.set_size_request(150, -1)
		self.reset_pass2.set_sensitive(True)
		fake_label=gtk.Label("")
		fake_label.set_size_request(150,-1)
		fake_label2=gtk.Label("")
		fake_label2.set_size_request(150,-1)
		hbox.pack_start(fake_label, expand=False, fill=False, padding=5)
		hbox.pack_start(fake_label2, expand=False, fill=False, padding=5)
		hbox.pack_start(self.reset_pass2, expand=False, fill=False, padding=5)
		frame_vert.add(hbox)
		hbox = gtk.HBox(False, 0)
		label = gtk.Label("")
		label.set_size_request(150, -1)
		hbox.pack_start(label, expand=False, fill=False, padding=5)
		frame_vert.add(hbox)
		label = gtk.Label("Please Setup Your Root Password")
		self.notebook.append_page(frame_vert, label)
		
		# setup the second page
		frame_vert = gtk.VBox(False,0)
		self.user = {}
		
		hbox = gtk.HBox(False, 0)
		label = gtk.Label("Username")
		label.set_size_request(300, -1)
		hbox.pack_start(label, expand=False, fill=False, padding=5)
		self.username = gtk.Entry()
		self.user['username'] = self.username
		self.username.set_size_request(150, -1)
		self.username.set_name("username")
		hbox.pack_start(self.username, expand=False, fill=False, padding=5)
		frame_vert.add(hbox)
		
		hbox = gtk.HBox(False, 0)
		label = gtk.Label("Password")
		label.set_size_request(300, -1)
		hbox.pack_start(label, expand=False, fill=False, padding=5)
		self.password = gtk.Entry()
		self.user['password'] = self.password
		self.password.set_size_request(150, -1)
		self.password.set_name("password")
		self.password.set_visibility(False)
		hbox.pack_start(self.password, expand=False, fill=False, padding=5)
		# reset button if they want to reset a user password that was
		# loaded from a user profile
		self.reset_pass = gtk.Button("Reset loaded password")
		self.reset_pass.connect("clicked", self.reset_userpass_from_profile, "reset loaded pass")
		self.reset_pass.set_size_request(150, 5)
		self.reset_pass.set_sensitive(False)
		hbox.pack_start(self.reset_pass, expand=False, fill=False, padding=5)
		frame_vert.add(hbox)
		
		hbox = gtk.HBox(False, 0)
		label = gtk.Label("Groups")
		label.set_size_request(300, -1)
		hbox.pack_start(label, expand=False, fill=False, padding=5)
		self.groups = gtk.Entry()
		self.user['groups'] = self.groups
		self.groups.set_size_request(150, -1)
		self.groups.set_name("groups")
		hbox.pack_start(self.groups, expand=False, fill=False, padding=5)
		frame_vert.add(hbox)
		
		hbox = gtk.HBox(False, 0)
		label = gtk.Label("Shell")
		label.set_size_request(300, -1)
		hbox.pack_start(label, expand=False, fill=False, padding=5)
		self.shell = gtk.Entry()
		self.user['shell'] = self.shell
		self.shell.set_size_request(150, -1)
		self.shell.set_name("shell")
		hbox.pack_start(self.shell, expand=False, fill=False, padding=5)
		frame_vert.add(hbox)
		
		hbox = gtk.HBox(False, 0)
		label = gtk.Label("HomeDir")
		label.set_size_request(300, -1)
		hbox.pack_start(label, expand=False, fill=False, padding=5)
		self.homedir = gtk.Entry()
		self.user['homedir'] = self.homedir
		self.homedir.set_size_request(150, -1)
		self.homedir.set_name("homedir")
		hbox.pack_start(self.homedir, expand=False, fill=False, padding=5)
		frame_vert.add(hbox)
		
		hbox = gtk.HBox(False, 0)
		label = gtk.Label("UserID")
		label.set_size_request(300, -1)
		hbox.pack_start(label, expand=False, fill=False, padding=5)
		self.userid = gtk.Entry()
		self.user['userid'] = self.userid
		self.userid.set_size_request(150, -1)
		self.userid.set_name("userid")
		hbox.pack_start(self.userid, expand=False, fill=False, padding=5)
		frame_vert.add(hbox)
		
		hbox = gtk.HBox(False, 0)
		label = gtk.Label("Comment")
		label.set_size_request(300, -1)
		hbox.pack_start(label, expand=False, fill=False, padding=5)
		self.comment = gtk.Entry()
		self.user['comment'] = self.comment
		self.comment.set_size_request(150, -1)
		self.comment.set_name("comment")
		hbox.pack_start(self.comment, expand=False, fill=False, padding=5)
		button = gtk.Button("Accept Changes")
		button.connect("clicked", self.add_edit_user, "add/edit user")
		button.set_size_request(150, -1)
		hbox.pack_start(button, expand=False, fill=False, padding=5)
		frame_vert.add(hbox)
		
		label = gtk.Label("Add/Edit a user")
		self.notebook.append_page(frame_vert, label)
		
		# add a blank page
		frame_vert = gtk.VBox(False,0)
		label = gtk.Label("Blank page")
		
		self.notebook.append_page(frame_vert, label)
		
		vert.pack_start(self.notebook, expand=False, fill=False, padding=50)
		self.add_content(vert)

		
	def selection_changed(self, treeview, data=None):
		treeselection = treeview.get_selection()
		treemodel, treeiter = treeselection.get_selected()
		self.edit(treemodel,treeiter)
		#row = treemodel.get(treeiter, 0)
		#print row
	
	def reset(self, widget, data=None):
		# enable the boxen
		self.root_verified=False
		self.root1.set_sensitive(True)
		self.root2.set_sensitive(True)
		self.root1.set_text("")
		self.root2.set_text("")
		self.verified.set_from_stock(gtk.STOCK_CANCEL, gtk.ICON_SIZE_SMALL_TOOLBAR)
		# blank the password in the installprofile
		# this allows detection to reset the hash
		self.controller.install_profile.set_root_pass_hash(None,"",None)
		self.blank_the_boxes()
		self.notebook.set_current_page(0)
	
	def root(self,widget, data=None):
		# select the root notebook page.
		self.notebook.set_current_page(0)
	
	def addu(self,widget, data=None):
		self.blank_the_boxes()
		self.password.set_sensitive(True)
		# select that page
		self.notebook.set_current_page(1)
		
	def edit(self, treemodel=None,treeiter=None):
		self.blank_the_boxes()
		# retrieve the selected stuff from the treeview
		#treeselection = self.treeview.get_selection()
		#treemodel, treeiter = treeselection.get_selected()
		
		# if theres something selected, need to show the details
		if treeiter != None:
			data={}
			data["password"],data["username"],data["groups"],data["shell"],\
				data["homedir"],data["userid"],data["comment"] = \
				treemodel.get(treeiter, 0,1,2,3,4,5,6)
			
			# fill the current entries
			for entry_box in self.user:
				box=self.user[entry_box]
				box.set_text(data[box.get_name()])
		
			# if the user was loaded from a profile, disable password box, and enable button
			if self.is_user_from_stored_profile(data["username"]):
				self.reset_pass.set_sensitive(True)
				self.password.set_sensitive(False)
			else:
				# if not from a profile, enable password box, disable reset button
				self.reset_pass.set_sensitive(False)
				self.password.set_sensitive(True)
			
		# show the edit box
		self.notebook.set_current_page(1)
	
	def delete(self, widget, data=None):
		self.blank_the_boxes()
		self.notebook.set_current_page(2)
		self.delete_user()
	
	def add_edit_user(self, widget, data=None):
		# retrieve the entered data
		data={}
		for entry_box in self.user:
			box=self.user[entry_box]
			data[box.get_name()] = box.get_text()
			
		success = self.add_user(data)
		
		# if it was successful, blank the current entries and 
		# ensure password box is sensitive
		if success == True:
			self.blank_the_boxes()
			self.password.set_sensitive(True)
			
	def add_user(self,data):
		return_val = False
		
		# test to make sure uid is an INT!!!
		if data["userid"] != "":
			test = False
			try:
				uid_test = int(data["userid"])
				test = True
			except:
				# its not an integer, raise the exception.
				msgbox=Widgets().error_Box("Error","UID must be an integer, and you entered a string!")
				msgbox.run()
				msgbox.destroy()
		else:
			test = True
			
		if self.is_data_empty(data) and test==True:
			# now add it to the box
			# ( <user name>, <password hash>, (<tuple of groups>), <shell>, 
			#    <home directory>, <user id>, <user comment> )
			
			# if they were previously added, modify them
			if self.is_in_treeview(data['username']):
				list = self.find_iter(data)
				self.treedata.set(list[data['username']],0,data["password"],
									1,data['username'],
									2,data["groups"],
									3,data["shell"],
									4,data["homedir"],
									5,data["userid"],
									6,data["comment"]
									)
			else:
				self.treedata.append([data["password"],data["username"], data["groups"],
										data["shell"], data["homedir"], 
										data["userid"], data["comment"]])
			#self.current_users.append(data['username'])
			return_val=True
		
		return return_val
			
	def delete_user(self):
		# get which one is selected
		treeselection = self.treeview.get_selection()
		treemodel, treeiter = treeselection.get_selected()
		# if something is selected, remove it!
		if treeiter != None:
			row = treemodel.get(treeiter, 1)
			
			# remove it from the current_users
			#self.current_users.remove(row[0])
			
			# remove it from the profile
			self.controller.install_profile.remove_user(row[0])
			
			# remove it from the treeview
			iter = self.treedata.remove(treeiter)
	
	def verify_root_password(self, widget, data=None):
		if self.root1.get_text() == self.root2.get_text() and self.root1.get_text()!="":
			# passwords match!
			self.root_verified = True
			# disable the boxen
			self.root1.set_sensitive(False)
			self.root2.set_sensitive(False)
			self.verified.set_from_stock(gtk.STOCK_APPLY, gtk.ICON_SIZE_SMALL_TOOLBAR)
		else:
			# password's don't match.
			msgbox=Widgets().error_Box("Error","Passwords do not match! ( or they are blank )")
			msgbox.run()
			msgbox.destroy()
			
	def blank_the_boxes(self):
		# blank the current entries
		for entry_box in self.user:
			box=self.user[entry_box]
			box.set_text("")
	
	def reset_userpass_from_profile(self, widget, data=None):
		# need to remove the user from the loaded profile
		# so that it will hash the password
		self.controller.install_profile.remove_user(self.username.get_text())
		self.users_from_profile.remove(self.username.get_text())
		# make the button sensitive again
		self.reset_pass.set_sensitive(False)
		self.password.set_sensitive(True)
		# clear the password box
		self.password.set_text("")
	
	def is_data_empty(self,data):
		value = True
		for item in data:
			# if any of the items are blank, return False!
			if item == "":
				value = False
			
		return value
	
	def is_user_from_stored_profile(self,username):
		value = False
		users = self.controller.install_profile.get_users()
		for user in users:
			if user[0] == username:
				value = True
		return value
	
	def is_root_pass_set(self):
		value = False
		pass_hash = self.controller.install_profile.get_root_pass_hash()
		if pass_hash != "":
			# its set!
			value = True
		
		return value
	
	def is_in_treeview(self,username):
		value = False
		# if the username appears in the treestore, display error
		username_list = self.get_treeview_usernames()
		if username in username_list:
			value = True	
			
		return value
	
	def find_iter(self,data):
		data_stor = {}
		treeiter = self.treedata.get_iter_first()
		
		while treeiter != None:
			username = self.treedata.get_value(treeiter, 1)
			if username == data["username"]:
				data_stor[username]=treeiter
			treeiter = self.treedata.iter_next(treeiter)

		return data_stor
	
	def get_treeview_usernames(self):
		data = []
		treeiter = self.treedata.get_iter_first()
		
		while treeiter != None:
			data.append(self.treedata.get_value(treeiter, 1))
			treeiter = self.treedata.iter_next(treeiter)

		return data

	def get_treeview_data(self):
		data = []
		treeiter = self.treedata.get_iter_first()
		
		while treeiter !=None:
			user = self.treedata.get_value(treeiter,1)
			passwd = self.treedata.get_value(treeiter,0)
			
			# if the user was loaded from a profile, do NOT
			# hash the password, but carry it through
			if user not in self.users_from_profile:
				pass_hash = GLIUtility.hash_password(passwd)
			else:
				pass_hash = passwd
				
			groups = self.treedata.get_value(treeiter,2)
			shell = self.treedata.get_value(treeiter,3)
			homedir = self.treedata.get_value(treeiter,4)
			userid = self.treedata.get_value(treeiter,5)
			comment = self.treedata.get_value(treeiter,6)
			try:
				group_tuple = tuple(groups.split(","))
			except:
				# must be only 1 group
				group_tuple = (groups)
			
			data.append([user,pass_hash,group_tuple,shell,homedir,userid,comment])
			treeiter = self.treedata.iter_next(treeiter)
			
		return data
	
	def activate(self):
		self.controller.SHOW_BUTTON_EXIT    = True
		self.controller.SHOW_BUTTON_HELP    = True
		self.controller.SHOW_BUTTON_BACK    = True
		self.controller.SHOW_BUTTON_FORWARD = True
		self.controller.SHOW_BUTTON_FINISH  = False
		
		self.users_from_profile = [] # This structure can be taken out
		self.users_iprofile = self.controller.install_profile.get_users()
		
		# load the saved users
		for user in self.users_iprofile:
			groups = ",".join(user[2])
			
			# if the uid field is blank, it will be set to None.
			if user[5] == None:
				# it is a tuple, so we have to thaw it and re-harden.
				user_temp = list(user)
				user_temp[5]=""
				user = tuple(user_temp)
				
			self.add_user({'password':user[1], 'username':user[0], 'groups':groups, 
					      'shell':user[3], 'homedir':user[4], 
					      'userid':user[5], 'comment':user[6]})
			# add them to the list so we know it was loaded from the profile
			# to pass the hash through ( this can be taken out and replaced )
			self.users_from_profile.append(user[0])
		
		# determine if root password is set, if so, automatically say its verified,
		# load the hash into both boxes, change icon to green check, and disable the boxes.
		if self.is_root_pass_set():
			self.root_verified=True
			self.verified.set_from_stock(gtk.STOCK_APPLY, gtk.ICON_SIZE_SMALL_TOOLBAR)
			hash = self.controller.install_profile.get_root_pass_hash()
			self.root1.set_text(hash)
			self.root2.set_text(hash)
			self.root1.set_sensitive(False)
			self.root2.set_sensitive(False)
			
			
	def deactivate(self):
		# store everything
		if (self.root_verified):
			
			if self.is_root_pass_set():
				# don't hash the password, just store it
				root_hash = self.root1.get_text()
			else:
				# hash the password
				root_hash = GLIUtility.hash_password(self.root1.get_text())
				
			# store the root password
			self.controller.install_profile.set_root_pass_hash(None,root_hash,None)
			
			# now store all the entered users
			#( <user name>, <password hash>, (<tuple of groups>), <shell>, 
			#  <home directory>, <user id>, <user comment> )
			# retrieve everything
			data = self.get_treeview_data()

			stored_users = []
			# get the array of stored usernames
			for item in list(self.controller.install_profile.get_users()):
				stored_users.append(item[0])
				
			for user in data:
				if user[0] not in self.current_users and user[0] not in stored_users:
					# user is not in stored profile, and hasn't been previously added
					self.controller.install_profile.add_user(None, (user[0], user[1], user[2], user[3], user[4], user[5], user[6]), None)
					#self.current_users.append(user[0])
				elif user[0] in stored_users:
					# user is in stored profile, need to remove, then readd the user
					self.controller.install_profile.remove_user(user[0])
					self.controller.install_profile.add_user(None, (user[0], user[1], user[2], user[3], user[4], user[5], user[6]), None)
					#self.current_users.append(user[0])
				
			return True
		else:
			msgbox=Widgets().error_Box("Error","You have not verified your root password!")
			msgbox.run()
			msgbox.destroy()
