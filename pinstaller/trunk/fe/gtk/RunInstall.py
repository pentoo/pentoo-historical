# Copyright 1999-2005 Gentoo Foundation
# This source code is distributed under the terms of version 2 of the GNU
# General Public License as published by the Free Software Foundation, a copy
# of which can be found in the main directory of this project.

import GLIInstallProfile
import GLIClientConfiguration
import GLIClientController
import GLIUtility
import gtk
import gobject
import sys
import time
import os
import select
import re

class RunInstall(gtk.Window):

	which_step = 0
	install_done = False
	install_fail = False
	output_log_is_link = False
	pulsing = False
	outputfile_contents = []
	logfile_contents = []

	def __init__(self, controller):
		gtk.Window.__init__(self, gtk.WINDOW_TOPLEVEL)

		self.controller = controller
		self.connect("delete_event", self.delete_event)
		self.connect("destroy", self.destroy)
		self.set_default_size(800,600)
		self.set_geometry_hints(None, min_width=800, min_height=600, max_width=800, max_height=600)
		self.set_title("Gentoo Linux Installer")

		self.globalbox = gtk.VBox(False, 0)
		self.globalbox.set_border_width(10)

		self.notebook = gtk.Notebook()

		self.logpage = gtk.VBox(False, 0)
		self.logtextbuff = gtk.TextBuffer()
		self.logtextbuff.set_text("")
		self.logtextview = gtk.TextView(self.logtextbuff)
		self.logtextview.set_editable(False)
		self.logtextview.set_wrap_mode(gtk.WRAP_CHAR)
		self.logtextviewscroll = gtk.ScrolledWindow()
		self.logtextviewscroll.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
		self.logtextviewscroll.add(self.logtextview)
		self.logpage.pack_start(self.logtextviewscroll, expand=True, fill=True)
		self.notebook.append_page(self.logpage, tab_label=gtk.Label("Log"))

		self.tailpage = gtk.VBox(False, 0)
		self.textbuffer = gtk.TextBuffer()
		self.textbuffer.set_text("")
		self.textview = gtk.TextView(self.textbuffer)
		self.textview.set_editable(False)
		self.textview.set_wrap_mode(gtk.WRAP_CHAR)
#		self.textbuffer.create_tag(tag_name="good", foreground="green")
#		self.textbuffer.create_tag(tag_name="warn", foreground="yellow")
#		self.textbuffer.create_tag(tag_name="bad", foreground="red")
		self.textviewscroll = gtk.ScrolledWindow()
		self.textviewscroll.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
		self.textviewscroll.add(self.textview)
		self.tailpage.pack_start(self.textviewscroll, expand=True, fill=True)
		self.notebook.append_page(self.tailpage, tab_label=gtk.Label("Output"))

#		self.docpage = gtk.VBox(False, 0)
		# documentation
#		self.notebook.append_page(self.docpage, tab_label=gtk.Label("Documentation"))

		self.globalbox.add(self.notebook)

		# This one comes first because it needs to be at the bottom....yes, that confuses me too :P
		self.progress = gtk.ProgressBar()
		self.progress.set_orientation(gtk.PROGRESS_LEFT_TO_RIGHT)
		self.progress.set_text("Preparing...")
		self.globalbox.pack_end(self.progress, expand=False, fill=False, padding=10)

		self.subprogress = gtk.ProgressBar()
		self.subprogress.set_orientation(gtk.PROGRESS_LEFT_TO_RIGHT)
		self.subprogress.set_text("Working...")
		self.subprogress.set_pulse_step(0.03)
		self.globalbox.pack_end(self.subprogress, expand=False, fill=False, padding=10)

		self.add(self.globalbox)
		self.make_visible()

		self.controller.cc.set_install_profile(self.controller.install_profile)
		self.controller.cc.start_install()

		self.output_log = None
		self.install_log = None
		gobject.timeout_add(500, self.tail_outputfile)
		gobject.timeout_add(500, self.tail_logfile)
		gobject.timeout_add(500, self.poll_notifications)

	def poll_notifications(self):
		if self.install_done: return False
		notification = self.controller.cc.getNotification()
		if notification == None:
			if self.pulsing:
				self.subprogress.pulse()
				self.subprogress.set_text("Working...")
			return True
		ntype = notification.get_type()
		ndata = notification.get_data()
		if ntype == "exception":
#			msgdlg = gtk.MessageDialog(parent=self, type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK, message_format="An error occured during the install. Consult the output display for more information.")
#			msgdlg.run()
#			msgdlg.destroy()
			error_msg = "Exception received:\n" + str(ndata) + "\nPlease submit a bug report (after searching to make sure it's not a known issue and verifying you didn't do something stupid) with the contents of /var/log/installer.log.failed, /tmp/installprofile.xml, the last ~50 lines of /tmp/compile_output.log, and the version of the installer you used (release or CVS snapshot w/ date)\n"
			iter_end = self.textbuffer.get_iter_at_offset(-1)
			self.textbuffer.insert(iter_end, error_msg, -1)
			iter_end = self.textbuffer.get_iter_at_offset(-1)
			self.textview.scroll_to_iter(iter_end, 0.0)
			self.progress.set_fraction(1)
			self.progress.set_text("Performing install failure cleanup")
			self.controller.cc.start_failure_cleanup()
			self.progress.set_text("Install failed!")
			self.install_fail = True
			return False
		elif ntype == "int" and not self.install_fail:
			if ndata == GLIClientController.NEXT_STEP_READY:
				num_steps = self.controller.cc.get_num_steps()
				if self.controller.cc.has_more_steps():
					next_step = self.controller.cc.get_next_step_info()
#					print "Next step: " + next_step
					self.progress.set_fraction(round(float(self.which_step)/num_steps, 2))
					self.progress.set_text(self.controller.cc.get_next_step_info())
					self.which_step += 1
					self.controller.cc.next_step()
					self.pulsing = True
				return True
			elif ndata == GLIClientController.INSTALL_DONE:
				self.install_done = True
				self.progress.set_fraction(1)
				self.progress.set_text("Install complete!")
#				print "Install done!"
#				msgdlg = gtk.MessageDialog(parent=self, type=gtk.MESSAGE_INFO, buttons=gtk.BUTTONS_OK, message_format="Install completed successfully!")
#				msgdlg.run()
#				msgdlg.destroy()
				return False
		elif ntype == "progress":
			self.pulsing = False
			self.subprogress.set_fraction(ndata[0])
			self.subprogress.set_text(ndata[1])
			return True
		return True

	def tail_outputfile(self):
		if self.install_done:
			self.output_log.close()
			return False
		if not self.output_log:
			try:
				self.output_log = open("/tmp/compile_output.log")
			except:
				return True
		while 1:
			line = self.output_log.readline()
			if not line:
				if not self.output_log_is_link and os.path.islink("/tmp/compile_output.log"):
					filepos = self.output_log.tell()
					self.output_log.close()
					self.output_log = open("/tmp/compile_output.log")
					self.output_log.seek(filepos)
					self.output_log_is_link = True
					continue
				break
			if len(self.outputfile_contents) >= 1000:
				self.outputfile_contents.pop(0)
			self.outputfile_contents.append(line)
		self.textbuffer.set_text("".join(self.outputfile_contents))
		self.textview.scroll_to_iter(self.textbuffer.get_iter_at_offset(-1), 0.0)
#			vadj = self.textviewscroll.get_vadjustment()
#			iter_end = self.textbuffer.get_iter_at_offset(-1)
#			self.textbuffer.insert(iter_end, line, -1)
#			iter_end = self.textbuffer.get_iter_at_offset(-1)
#			self.textview.scroll_to_iter(iter_end, 0.0)
#			if vadj.value == vadj.upper:
#				vadj = self.textviewscroll.get_vadjustment()
#				vadj.value = vadj.upper
#				self.textviewscroll.set_vadjustment(vadj)
		return True

	def tail_logfile(self):
		if self.install_done:
			self.install_log.close()
			return False
		if not self.install_log:
			try:
				self.install_log = open(self.controller.client_profile.get_log_file())
			except:
				return True
		while 1:
			line = self.install_log.readline()
			if not line: break
			if len(self.logfile_contents) >= 1000:
				self.logfile_contents.pop(0)
			self.logfile_contents.append(line)
		self.logtextbuff.set_text("".join(self.logfile_contents))
		self.logtextview.scroll_to_iter(self.logtextbuff.get_iter_at_offset(-1), 0.0)
#			vadj = self.logtextviewscroll.get_vadjustment()
#			vvalue = vadj.value
#			vmax = vadj.upper - vadj.page_size
#			print "vadj before adding text: upper - " + str(vadj.upper) + ", lower - " + str(vadj.lower) + ", max - " + str(vadj.upper - vadj.page_size) + ", value - " + str(vadj.value)
#			iter_end = self.logtextbuff.get_iter_at_offset(-1)
#			self.logtextbuff.insert(iter_end, line, -1)
#			iter_end = self.logtextbuff.get_iter_at_offset(-1)
#			self.logtextview.scroll_to_iter(iter_end, 0.0)
#			if vvalue == vmax:
#				print "vadj after adding text: upper - " + str(vadj.upper) + ", lower - " + str(vadj.lower) + ", max - " + str(vadj.upper - vadj.page_size) + ", value - " + str(vadj.value)
#				vadj.value = vadj.upper - vadj.page_size
#				print "vadj after adjusting: upper - " + str(vadj.upper) + ", lower - " + str(vadj.lower) + ", max - " + str(vadj.upper - vadj.page_size) + ", value - " + str(vadj.value)
#				print
		return True

	def make_visible(self):
		self.show_all()
		self.present()

	def make_invisible(self):
		self.hide_all()

	def delete_event(self, widget, event, data=None):
		# If you return FALSE in the "delete_event" signal handler,
		# GTK will emit the "destroy" signal. Returning TRUE means
		# you don't want the window to be destroyed.
		# This is useful for popping up 'are you sure you want to quit?'
		# type dialogs.
#		print "delete event occurred"
		# Change TRUE to FALSE and the main window will be destroyed with
		# a "delete_event".
		return False

	# Destroy callback
	def destroy(self, widget, data=None):
#		print "destroy function"
		gtk.main_quit()
		return True
