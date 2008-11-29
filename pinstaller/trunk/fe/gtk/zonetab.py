#
# zonetab.py: timezone classes
#
# Copyright 2001, 2002, 2003 Red Hat, Inc.
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
#Additions by Brent Fox <bfox@redhat.com>

import string
import re
import math

class ZoneTabEntry:
    def __init__(self, code=None, lat=0, long=0, tz=None, comments=None):
        self.code = code
        self.lat = lat
        self.long = long
        self.tz = tz
        self.comments = comments

class ZoneTab:
    def __init__(self, fn='/usr/share/zoneinfo/zone.tab'):
        self.entries = []
        self.readZoneTab(fn)

    def getEntries(self):
        return self.entries

    def findEntryByTZ(self, tz):
        for entry in self.entries:
            if entry.tz == tz:
                return entry
        return None

    def findNearest(self, lat, long):
        nearestEntry = None
        min = -1
        for entry in self.entries:
            dx = entry.long - long
            dy = entry.lat - lat
            dist = (dy * dy) + (dx * dx)
            if dist < min or min == -1:
                min = dist
                nearestEntry = entry
        return nearestEntry

    def convertCoord(self, coord, type="lat"):
        if type != "lat" and type != "long":
            raise TypeError, "invalid coord type"
        if type == "lat":
            deg = 3
        else:
            deg = 4
        degrees = string.atoi(coord[0:deg])
        order = len(coord[deg:])
        minutes = string.atoi(coord[deg:])
        if degrees > 0:
            return degrees + minutes/math.pow(10, order)
        return degrees - minutes/math.pow(10, order)
        
    def readZoneTab(self, fn):
        f = open(fn, 'r')
        comment = re.compile("^#")
        coordre = re.compile("[\+-]")
        while 1:
            line = f.readline()
            if not line:
                break
            if comment.search(line):
                continue
            fields = string.split(line, '\t')
            if len(fields) < 3:
                continue
            code = fields[0]
            split = coordre.search(fields[1], 1)
            lat = self.convertCoord(fields[1][:split.end() - 1], "lat")
            long = self.convertCoord(fields[1][split.end() - 1:], "long")
            tz = string.strip(fields[2])
            if len(fields) > 3:
                comments = string.strip(fields[3])
            else:
                comments = None
            entry = ZoneTabEntry(code, lat, long, tz, comments)
            self.entries.append(entry)

