# timezone_map_gui.py: gui timezone map widget.
#
# Copyright 2001 - 2005 Red Hat, Inc.
# Copyright 1999-2005 Gentoo Foundation
#
# This software may be freely redistributed under the terms of the GNU
# library public license.
#
# You should have received a copy of the GNU Library Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
#
#Originally written by Matt Wilson <msw@redhat.com>
#Additions by:
#Brent Fox <bfox@redhat.com>
#Nils Philippsen <nphilipp@redhat.com>

# heavy modifications to remove dependency on gnomecanvas
# by John N. Laliberte <allanonjl@gentoo.org>

import gobject
import pango
import gtk
import string
import re
import math
import zonetab

class Enum:
    def __init__(self, *args):
        i = 0
        for arg in args:
            self.__dict__[arg] = i
            i += 1

class TimezoneMap(gtk.VBox):
    #force order of destruction for a few items.
    def __del__(self):
        del self.markers
        del self.current

    def __init__(self, zonetab, default="America/New_York", map='./map480.png'):
        gtk.VBox.__init__(self, False, 5)

        # set up class member objects
        self.zonetab = zonetab
        self.markers = {}
        self.highlightedEntry = None
        self.currentEntry = None
        self.filename = map

        # set up the map canvas
        self.default = default
        self.already_shown = False
        self.mapWidth = 480; self.mapHeight = 240 # size of the map
        self.boxWidth = 2; self.boxHeight = 2; # size of yellow filled rectangles
        
        self.canvas = gtk.Layout()
        self.canvas.set_size(self.mapWidth, self.mapHeight)
        # this next line is very important! ( or it won't show anything! )
        self.canvas.set_size_request(self.mapWidth, self.mapHeight)
        
        self.drawing_area = gtk.DrawingArea()
        self.drawing_area.set_size_request(self.mapWidth, self.mapHeight)
        self.drawing_area.connect("expose-event", self.area_expose_cb)
        
        self.pangolayout = self.drawing_area.create_pango_layout("")
        
        self.drawing_area.add_events(gtk.gdk.BUTTON_PRESS_MASK |
                                     gtk.gdk.POINTER_MOTION_MASK |
                                     gtk.gdk.LEAVE_NOTIFY_MASK )

        self.drawing_area.connect("event", self.mapEvent)
        
        self.canvas.add(self.drawing_area)
        
        self.canvas.show()
        self.drawing_area.show()
        
        x1,y1,x2,y2 = (0,0,self.mapWidth,self.mapHeight)
        hbox = gtk.HBox(True,0)
        hbox.pack_start(self.canvas, False, False, 5)
        self.pack_start(hbox, False, False)

        self.canvas.connect("event", self.canvasEvent)

        # set up status bar
        self.status = gtk.Statusbar()
        self.status.set_has_resize_grip(False)
        self.statusContext = self.status.get_context_id("")
        self.pack_start(self.status, False, False)

        self.columns = Enum("TZ", "COMMENTS", "ENTRY")
        
        # set up list of timezones
        self.listStore = gtk.ListStore(gobject.TYPE_STRING,
                                       gobject.TYPE_STRING,
                                       gobject.TYPE_PYOBJECT)

        self.listStore.set_sort_column_id(self.columns.TZ, gtk.SORT_ASCENDING)

        self.listView = gtk.TreeView(self.listStore)
        selection = self.listView.get_selection()
        selection.connect("changed", self.selectionChanged)
        self.listView.set_property("headers-visible", False)
        col = gtk.TreeViewColumn(None, gtk.CellRendererText(), text=0)
        self.listView.append_column(col)
        col = gtk.TreeViewColumn(None, gtk.CellRendererText(), text=1)
        self.listView.append_column(col)

        sw = gtk.ScrolledWindow ()
        sw.add(self.listView)
        sw.set_shadow_type(gtk.SHADOW_IN)
        self.pack_start(sw, True, True)
        
	# setup the gc
	self.style2 = self.drawing_area.get_style()
	self.gc = self.style2.fg_gc[gtk.STATE_NORMAL]
	
        self.line_status = True

    def getCurrent(self):
        return self.currentEntry

    def selectionChanged(self, selection, *args):
        (model, iter) = selection.get_selected()
        if iter is None:
            return
        entry = self.listStore.get_value(iter, self.columns.ENTRY)
        self.setCurrent(entry, skipList=1)

    def mapEvent(self, widget, event=None):
        if event.type == gtk.gdk.MOTION_NOTIFY:
            self.repaint_background()
            
            x1, y1 = (event.x, event.y)
            
            lat, long = self.canvas2map(x1, y1)
            last = self.highlightedEntry
            self.highlightedEntry = self.zonetab.findNearest(lat, long)
            if last != self.highlightedEntry:
                self.status.pop(self.statusContext)
                status = self.highlightedEntry.tz
                if self.highlightedEntry.comments:
                    status = "%s - %s" % (status,
                                          self.highlightedEntry.comments)
                self.status.push(self.statusContext, status)

            x2, y2 = self.map2canvas(self.highlightedEntry.lat,
                                       self.highlightedEntry.long)
            gc2 = self.drawing_area.window.new_gc()
            colormap = self.drawing_area.get_colormap()
            gc2.foreground = colormap.alloc_color('green')
            
            if self.line_status == True:
                self.drawing_area.window.draw_line(gc2,int(x1),int(y1),int(x2),int(y2))
            
        elif event.type == gtk.gdk.BUTTON_PRESS:
            if event.button == 1:
                self.setCurrent(self.highlightedEntry)
                
        elif event.type == gtk.gdk.LEAVE_NOTIFY:
            self.repaint_background()
        #else:
        #    print "map event triggered: "+str(event.type)
            
    def setCurrent(self, entry, skipList=0, default=True):
        # redraw the background to get rid of the green line
        self.repaint_background(original=True)
        
        if not entry:
            # If the value in /etc/sysconfig/clock is invalid, default to New York
            self.currentEntry = self.fallbackEntry
        else:
            self.currentEntry = entry
        
        # set the new one
        self.show_mark(self.markers[self.currentEntry.tz])
        
        # now create a pixbuf that holds that information from the drawing area
        # this will be used to repaint the screen each time
        pixbuf=gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB,0,8,1000,1000)
        self.pixbuf_plus=pixbuf.get_from_drawable(self.drawing_area.window,
                                                  self.drawing_area.get_colormap(),0,0,0,0,
                                                  self.mapWidth,self.mapHeight)
        
        if skipList:
            return

        iter = self.listStore.get_iter_first()
        while iter:
            if self.listStore.get_value(iter, self.columns.ENTRY) == self.currentEntry:
                selection = self.listView.get_selection()
                selection.unselect_all()
                selection.select_iter(iter)
                path = self.listStore.get_path(iter)
                col = self.listView.get_column(0)
                self.listView.set_cursor(path, col, False)
                self.listView.scroll_to_cell(path, col, True, 0.5, 0.5)
                break
            iter = self.listStore.iter_next(iter)
        
    def canvasEvent(self, widget, event=None):
        if event.type == gtk.gdk.LEAVE_NOTIFY:
            print "canvas event triggered"
        
    def map2canvas(self, lat, long):
        x2 = self.mapWidth
        y2 = self.mapHeight
        x = x2 / 2.0 + (x2 / 2.0) * long / 180.0
        y = y2 / 2.0 - (y2 / 2.0) * lat / 90.0
        return (x, y)

    def canvas2map(self, x, y):
        x2 = self.mapWidth
        y2 = self.mapHeight
        long = (x - x2 / 2.0) / (x2 / 2.0) * 180.0
        lat = (y2 / 2.0 - y) / (y2 / 2.0) * 90.0
        return (lat, long)

    def area_expose_cb(self, area, event):
        # need to only do this ONCE! or if it gets behind a window to
        # refresh, it'll keep on calling this event.
        if self.already_shown == False:
            self.style2 = self.drawing_area.get_style()
            self.gc = self.style2.fg_gc[gtk.STATE_NORMAL]
            self.pixbuf = gtk.gdk.pixbuf_new_from_file(self.filename)
            
            # first draw the map background
            self.drawing_area.window.draw_pixbuf(self.gc, self.pixbuf, 0, 0, 0, 0, self.mapWidth, 
                                                 self.mapHeight, gtk.gdk.RGB_DITHER_NORMAL, 0, 0)
            # now generate the yellow cities
            self.generate_timezone_map_stuff()
            self.already_shown = True
        else:
            self.repaint_background()

        return True
    
    def repaint_background(self, original = False):
    	# only repaint if the area has already been exposed
	# at least 1 time.
	if self.already_shown == True:
	        if original == False:
	            self.drawing_area.window.draw_pixbuf(self.gc, self.pixbuf_plus, 0, 0, 0, 0, self.mapWidth, 
	                                                 self.mapHeight, gtk.gdk.RGB_DITHER_NORMAL, 0, 0)
	        else:
	            self.drawing_area.window.draw_pixbuf(self.gc, self.pixbuf_original, 0, 0, 0, 0, self.mapWidth, 
	                                                 self.mapHeight, gtk.gdk.RGB_DITHER_NORMAL, 0, 0)
        return
    
    def generate_timezone_map_stuff(self):
        self.currentEntry = None
        self.fallbackEntry = None
        self.gc_yellow = self.drawing_area.window.new_gc()
        colormap = self.drawing_area.get_colormap()
        self.gc_yellow.foreground = colormap.alloc_color('yellow')
        
        gc2 = self.drawing_area.window.new_gc()
        colormap = self.drawing_area.get_colormap()
        gc2.foreground = colormap.alloc_color(0, 65535, 65535)
        
        self.zoneEntries = self.zonetab.getEntries()
        for entry in self.zoneEntries:
            iter = self.listStore.append()
            self.listStore.set_value(iter, self.columns.TZ, entry.tz)
            if entry.comments:
                self.listStore.set_value(iter, self.columns.COMMENTS,
                                         entry.comments)
            else:
                self.listStore.set_value(iter, self.columns.COMMENTS, "")
            self.listStore.set_value(iter, self.columns.ENTRY, entry)
            
            x, y = self.map2canvas(entry.lat, entry.long)
            
            # adds the yellow square at each city.
            self.drawing_area.window.draw_rectangle(self.gc_yellow, True, int(x), int(y), 2, 2)
            
            marker = { "long":x, "lat":y }

            self.markers[entry.tz] = marker
            if entry.tz == self.default:
                self.currentEntry = entry

            if entry.tz == "America/New_York":
                #In case the /etc/sysconfig/clock is messed up, use New York as default
                self.fallbackEntry = entry

        pixbuf=gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB,0,8,1000,1000)
        self.pixbuf_original=pixbuf.get_from_drawable(self.drawing_area.window,
                                                  self.drawing_area.get_colormap(),0,0,0,0,
                                                  self.mapWidth,self.mapHeight)
        
        self.setCurrent(self.currentEntry)
        return
    
    def show_mark(self, location):
        gc = self.drawing_area.window.new_gc()
        colormap = self.drawing_area.get_colormap()
        gc.foreground = colormap.alloc_color('red')
        
        x=location["long"]; y=location["lat"]
        self.pangolayout.set_markup("<span foreground=\"red\" weight=\"bold\">x</span>")
        self.drawing_area.window.draw_layout(gc, int(x-2), int(y-8), self.pangolayout)
        return
    
if __name__ == "__main__":
    zonetab = zonetab.ZoneTab()
    win = gtk.Window()
    if gtk.__dict__.has_key ("main_quit"):
        win.connect('destroy', gtk.main_quit)
    else:
        win.connect('destroy', gtk.mainquit)
    map = TimezoneMap(zonetab)
    vbox = gtk.VBox()
    vbox.pack_start(map)
    button = gtk.Button("Quit")
    if gtk.__dict__.has_key ("main_quit"):
        button.connect("pressed", gtk.main_quit)
    else:
        button.connect("pressed", gtk.mainquit)
    vbox.pack_start(button, False, False)
    win.add(vbox)
    win.show_all()
    if gtk.__dict__.has_key ("main"):
        gtk.main ()
    else:
        gtk.mainloop()
    
