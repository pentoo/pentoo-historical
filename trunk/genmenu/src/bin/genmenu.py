#!/bin/python

import sys,os,re,shutil

#from output import red, green, blue, bold
import genmenudb

from lxml import etree
from StringIO import StringIO

db = genmenudb.getdb()

#PORTDIR="/var/db/pkg/"
PORTDIR = 'V:/Linux/portage/db'
# Move to applications
APPSDIR = '/usr/share/genmenu/e17/all.desktop'
ENVDIR = '/etc/env.d/'
ICONDIR = '/usr/share/applications/'
star = "  *  "
arrow = " >>> "
warn = " !!! "


def getHomeDir():
    ''' Try to find user's home directory, otherwise return /root.'''
    try:
        path1=os.path.expanduser("~")
    except:
        path1=""
    try:
        path2=os.environ["HOME"]
    except:
        path2=""
    try:
        path3=os.environ["USERPROFILE"]
    except:
        path3=""

    if not os.path.exists(path1):
        if not os.path.exists(path2):
            if not os.path.exists(path3):
                return '/root'
            else: return path3
        else: return path2
    else: return path1

#REM Almost done, need to sanitize tabbed output
def listdb():
    print green("*****************************************")
    print green("    Listing all supported packages ")
    print green("*****************************************")
    print "Package\t\t\tIcon file\t\tMenu category"
    for y in range(db.__len__()):
        if db[y][0].__len__() < 15:
            tab="\t\t"
        else:
            tab="\t"
        print blue(db[y][0]) + tab + db[y][1] + "\t\t" + db[y][2] + "\t"


#REM Function done
def listpackages(pkgdir):
    """List packages installed as in the portage database directory (usually /var/db/pkg)"""
    packages = []
    categories = os.listdir(pkgdir)
    for category in categories:
        catdir = os.path.join(pkgdir, category)
        applications = os.listdir(catdir)
        for application in applications:
            packages.append(category + "/" + re.sub("-[0-9].*", "", application, 1))
    packages.sort()
    return packages
 
#REM Function done       
def settermenv():
    """This function creates the apropriate environment variable for the $E17TERM"""
    file = open(ENVDIR + "99pentoo-term" , "w")
    file.write("E17TERM=\"" + options.e17term + "\"")
    file.newlines
    file.close()

# Adds a desktop entry in the specified category, always under Pentoo.
def add_menu_entry(category, desktopEntry):

    new_menu_entry = etree.SubElement(category, "Include")
    new_menu_entry.text = desktopEntry


def find_menu_entry(menu, submenu):
    for x in menu.iterchildren():
        if x.text == submenu:
            foundMenu=x.getparent()
            return x.getparent()
        else:
            tmp = find_menu_entry(x, submenu)
            if not tmp == None:
                return tmp


def genxml():

    # Get the root of the XML tree.
    print pentoo

    #root_menu = etree.Element("Menu")

    print etree.tostring(root_menu, pretty_print=True)

def make_menu_entry(root_menu, iconfile="" , category=""):
    file = os.path.join(APPSDIR, iconfile)
    if os.path.exists(file):
        # Check if dry-run
        if options.simulate:
            print arrow + "Copying " + iconfile + " to " + ICONDIR
            if not os.path.exists(os.path.join(MENUDIR, "all", category)):
                print arrow + "Making menu entry for " + iconfile + " in " + MENUDIR + "/all/" + category
            new_menu_entry = etree.SubElement(find_menu_entry(root_menu, category), "Include")
            new_menu_entry.text = iconfile
            return 0
        # Create the menu entry
        else:
            if not os.path.exists(ICONDIR):
                os.mkdir(ICONDIR)
            try:
                shutil.copyfile(file, ICONDIR + iconfile)
            except:
                sys.stderr.write(red("Unable to copy " + iconfile + " to " + ICONDIR + "\n"))
                sys.stderr.write(red("Verify that you have write permissions in " + ICONDIR + "\n"))
                return -1

            new_menu_entry = etree.SubElement(find_menu_entry(root_menu, category), "Include")
            new_menu_entry.text = iconfile
            return 0
    else:
        return 1

def main():
    """
    This program is used to generate the menu in enlightenment for the pentoo livecd
    Future version _might_ support other VM like gnome or others but kde :-)
    """
    if options.listsupported:
        listdb()
        return 0

    if options.simulate:
        print star + "Starting simulation"

    if options.listonly:
        print star + "Listing supported packages installed"
        print "Package\t\tIcon file\t\tMenu category"

    pkginstalled = []
    pkginstalled = listpackages(PORTDIR)
    notthere = []
    menu = etree.parse("applications.menu")
    root_menu = menu.getroot()

    for y in range(db.__len__()):
        if pkginstalled.__contains__(db[y][0]):
            if options.listonly:
                print db[y][0] + "\t" + db[y][1] + "\t\t" + db[y][2] + "\t"
            else:
                # calls makemenuentry file.eap, menu category
                for single_entry in db[y][1].split(" "):
                    try:
                        make_menu_entry( root_menu, single_entry, db[y][2])
                    except:
                        print >> sys.stderr, "Can't find " + single_entry + " in " + EAPDIR
                        return -1
        else:
            notthere.append(db[y][0])

    #    settermenv()
    if options.verbose:
        # Final move, show the unfound icons in the db
        print warn + "Missing applications :"
        print star + "The following applications are available but not installed"
        for i in range(notthere.__len__()):
            print arrow + notthere[i]
    print etree.tostring(root_menu, pretty_print=True)


if __name__ == "__main__":

    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("-l", "--list", action="store_true", dest="listonly", default=False,
                      help="Show supported installed packages")
    parser.add_option("-x", "--xml", action="store_true", dest="simxml", default=False,
                      help="Test xml")
    parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False,
                      help="Show supported installed packages")
    parser.add_option("-L", "--list-supported", action="store_true", dest="listsupported", default=False,
                      help="Show supported installed packages")
    parser.add_option("-t", "--term", dest="e17term", default="Eterm",
                      help="Sets the terminal used by e17 for cli-only tools")
    parser.add_option("-n", "--dry-run", action="store_true", dest="simulate", default=False,
                      help="Simulate only, show missing eap files and show"
                           "what will be done")
    (options, args) = parser.parse_args()

    try:
        main()
    except KeyboardInterrupt:
        # If interrupted, exit nicely
        print >> sys.stderr, 'Interrupted.'
