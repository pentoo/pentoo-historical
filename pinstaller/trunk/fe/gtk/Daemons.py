# Copyright 1999-2005 Gentoo Foundation
# This source code is distributed under the terms of version 2 of the GNU
# General Public License as published by the Free Software Foundation, a copy
# of which can be found in the main directory of this project.

import gtk
import GLIScreen

class Panel(GLIScreen.GLIScreen):

	title = "Daemons"
	active_selection_cron = None
	active_selection_logger = None
	cron_daemons = {}
	log_daemons = {}
	_helptext = """
<b><u>Daemons</u></b>

System Logger:

Some tools are missing from the stage3 archive because several packages provide
the same functionality. 

Unix and Linux have an excellent history of logging capabilities -- if you want
you can log everything that happens on your system in logfiles. This happens
through the system logger.

Gentoo offers several system loggers to choose from. There are sysklogd, which
is the traditional set of system logging daemons, syslog-ng, an advanced system
logger, and metalog which is a highly-configurable system logger. Others might
be available through Portage as well - our number of available packages
increases on a daily basis.

If you plan on using sysklogd or syslog-ng you might want to install logrotate
afterwards as those system loggers don't provide any rotation mechanism for the
log files.

Syslog-ng is provided by GRP and is the default, though the others are just as
good.

Cron Daemon:

Although it is optional and not required for your system, it is wise to install
one. But what is a cron daemon? A cron daemon executes scheduled commands. It is
very handy if you need to execute some command regularly (for instance daily,
weekly or monthly).

Gentoo offers three possible cron daemons: dcron, fcron and vixie-cron.
Installing one of them is similar to installing a system logger. However, dcron
and fcron require an extra configuration command, namely crontab /etc/crontab.
If you don't know what to choose, use vixie-cron.

Vixie-cron is provided by GRP and is the recommended default. 
"""

	def __init__(self, controller):
		GLIScreen.GLIScreen.__init__(self, controller)
		vert = gtk.VBox(False, 0)
		vert.set_border_width(10)

		content_str = """Here, you will select which cron and logger daemons you would like to use. Each option has
a brief description beside it.
"""
		content_label = gtk.Label(content_str)
		vert.pack_start(content_label, expand=False, fill=False, padding=0)

		hbox = gtk.HBox(False, 0)
		label = gtk.Label()
		label.set_markup("<b>Cron Daemon</b> (runs tasks at scheduled times)")
		hbox.pack_start(label, False, fill=False, padding=0)
		vert.pack_start(hbox, expand=False, fill=False, padding=10)

		self.cron_daemons['vixie-cron'] = gtk.RadioButton(None, "vixie-cron")
		self.cron_daemons['vixie-cron'].set_name("vixie-cron")
		self.cron_daemons['vixie-cron'].connect("toggled", self.cron_selected, "vixie-cron")
		self.cron_daemons['vixie-cron'].set_size_request(150, -1)
		hbox = gtk.HBox(False, 0)
		hbox.pack_start(self.cron_daemons['vixie-cron'], expand=False, fill=False, padding=5)
		tmplabel = gtk.Label("Paul Vixie's cron daemon, a fully featured crond implementation")
		tmplabel.set_line_wrap(True)
		hbox.pack_start(tmplabel, expand=False, fill=False, padding=20)
		vert.pack_start(hbox, expand=False, fill=False, padding=10)

		self.cron_daemons['fcron'] = gtk.RadioButton(self.cron_daemons['vixie-cron'], "fcron")
		self.cron_daemons['fcron'].set_name("fcron")
		self.cron_daemons['fcron'].connect("toggled", self.cron_selected, "fcron")
		self.cron_daemons['fcron'].set_size_request(150, -1)
		hbox = gtk.HBox(False, 0)
		hbox.pack_start(self.cron_daemons['fcron'], expand=False, fill=False, padding=5)
		tmplabel = gtk.Label("A command scheduler with extended capabilities over cron and anacron")
		tmplabel.set_line_wrap(True)
		hbox.pack_start(tmplabel, expand=False, fill=False, padding=20)
		vert.pack_start(hbox, expand=False, fill=False, padding=10)

		self.cron_daemons['dcron'] = gtk.RadioButton(self.cron_daemons['vixie-cron'], "dcron")
		self.cron_daemons['dcron'].set_name("dcron")
		self.cron_daemons['dcron'].connect("toggled", self.cron_selected, "dcron")
		self.cron_daemons['dcron'].set_size_request(150, -1)
		hbox = gtk.HBox(False, 0)
		hbox.pack_start(self.cron_daemons['dcron'], expand=False, fill=False, padding=5)
		tmplabel = gtk.Label("A cute little cron from Matt Dillon")
		tmplabel.set_line_wrap(True)
		hbox.pack_start(tmplabel, expand=False, fill=False, padding=20)
		vert.pack_start(hbox, expand=False, fill=False, padding=10)

		self.cron_daemons['none'] = gtk.RadioButton(self.cron_daemons['vixie-cron'], "None")
		self.cron_daemons['none'].set_name("none")
		self.cron_daemons['none'].connect("toggled", self.cron_selected, "none")
		self.cron_daemons['none'].set_size_request(150, -1)
		hbox = gtk.HBox(False, 0)
		hbox.pack_start(self.cron_daemons['none'], expand=False, fill=False, padding=5)
		tmplabel = gtk.Label("Choose this if you don't want a cron daemon")
		tmplabel.set_line_wrap(True)
		hbox.pack_start(tmplabel, expand=False, fill=False, padding=20)
		vert.pack_start(hbox, expand=False, fill=False, padding=10)


		hbox = gtk.HBox(False, 0)
		label = gtk.Label()
		label.set_markup("<b>System Logger</b> (provides logging facilities)")
		hbox.pack_start(label, False, fill=False, padding=0)
		vert.pack_start(hbox, expand=False, fill=False, padding=10)

		self.log_daemons['syslog-ng'] = gtk.RadioButton(None, "syslog-ng")
		self.log_daemons['syslog-ng'].set_name("syslog-ng")
		self.log_daemons['syslog-ng'].connect("toggled", self.logger_selected, "syslog-ng")
		self.log_daemons['syslog-ng'].set_size_request(150, -1)
		hbox = gtk.HBox(False, 0)
		hbox.pack_start(self.log_daemons['syslog-ng'], expand=False, fill=False, padding=5)
		tmplabel = gtk.Label("syslog replacement with advanced filtering features")
		tmplabel.set_line_wrap(True)
		hbox.pack_start(tmplabel, expand=False, fill=False, padding=20)
		vert.pack_start(hbox, expand=False, fill=False, padding=10)

		self.log_daemons['metalog'] = gtk.RadioButton(self.log_daemons['syslog-ng'], "metalog")
		self.log_daemons['metalog'].set_name("metalog")
		self.log_daemons['metalog'].connect("toggled", self.logger_selected, "metalog")
		self.log_daemons['metalog'].set_size_request(150, -1)
		hbox = gtk.HBox(False, 0)
		hbox.pack_start(self.log_daemons['metalog'], expand=False, fill=False, padding=5)
		tmplabel = gtk.Label("A highly configurable replacement for syslogd/klogd")
		tmplabel.set_line_wrap(True)
		hbox.pack_start(tmplabel, expand=False, fill=False, padding=20)
		vert.pack_start(hbox, expand=False, fill=False, padding=10)

		self.log_daemons['sysklogd'] = gtk.RadioButton(self.log_daemons['syslog-ng'], "sysklogd")
		self.log_daemons['sysklogd'].set_name("sysklogd")
		self.log_daemons['sysklogd'].connect("toggled", self.logger_selected, "sysklogd")
		self.log_daemons['sysklogd'].set_size_request(150, -1)
		hbox = gtk.HBox(False, 0)
		hbox.pack_start(self.log_daemons['sysklogd'], expand=False, fill=False, padding=5)
		tmplabel = gtk.Label("Standard log daemon")
		tmplabel.set_line_wrap(True)
		hbox.pack_start(tmplabel, expand=False, fill=False, padding=20)
		vert.pack_start(hbox, expand=False, fill=False, padding=10)

		self.add_content(vert)

	def cron_selected(self, widget, data=None):
		self.active_selection_cron = data

	def logger_selected(self, widget, data=None):
		self.active_selection_logger = data

	def activate(self):
		self.controller.SHOW_BUTTON_EXIT    = True
		self.controller.SHOW_BUTTON_HELP    = True
		self.controller.SHOW_BUTTON_BACK    = True
		self.controller.SHOW_BUTTON_FORWARD = True
		self.controller.SHOW_BUTTON_FINISH  = False
		self.active_selection_cron = self.controller.install_profile.get_cron_daemon_pkg() or "vixie-cron"
		self.active_selection_logger = self.controller.install_profile.get_logging_daemon_pkg() or "syslog-ng"
		self.cron_daemons[self.active_selection_cron].set_active(True)
		self.log_daemons[self.active_selection_logger].set_active(True)

	def deactivate(self):
		self.controller.install_profile.set_cron_daemon_pkg(None, self.active_selection_cron, None)
		self.controller.install_profile.set_logging_daemon_pkg(None, self.active_selection_logger, None)
		return True
