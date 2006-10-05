#!/bin/python

import sys,os,re,shutil
from output import red, green, blue, bold

db=[["net-analyzer/nmap", "nmap.eap", "Scanners"], ["net-analyzer/nmap", "nmap.eap", "Scanners Nmap"], ["net-analyzer/nessus", "nessus.eap toto.eap", "Scanners"], ["net-analyzer/xprobe", "xprobe.eap", "Fingerprinters"], ["net-irc/xchat", "xchat.eap", "Internet"]]

toto = [["e"],
        ["baf"]]

PORTDIR="/var/db/pkg/"
#PORTDIR = 'c:/Pentoo/test/portage'
EAPDIR = '/usr/share/genmenu/e17/all'
MENUSRC = '/usr/share/genmenu/e17/menu/all'
ENVDIR = '/etc/env.d/'
menus_used = []


def getHomeDir():
    ''' Try to find user's home directory, otherwise return current directory.'''
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
                return os.getcwd()
            else: return path3
        else: return path2
    else: return path1

ICONDIR = getHomeDir() + '/.e/e/applications/all/'
MENUDIR = getHomeDir() + '/.e/e/applications/menu'

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
    file = open(ENVDIR + "99pentoo-terms" , "w")
    file.write("E17TERM=\"" + options.e17term + "\"")
    file.newlines
    file.close()

def clean_menu():
    """Function removing unused menu entries, usually called at the end"""
    all_menus = []
    for y in range(db.__len__()):
        if not all_menus.__contains__(db[y][2]):
            all_menus.append(db[y][2])
        # This will "save" submenus entries
    for x in range(menus_used.__len__()):
        # Preserve menu if only submenu inside
        for single_entry in menus_used[x].split(" "):
            if all_menus.__contains__(single_entry):
                all_menus.remove(single_entry)
        if all_menus.__contains__(menus_used[x]):
            all_menus.remove(menus_used[x])
    # This just generated the list of unused menu entries.
    for x in range(all_menus.__len__()):
        if not options.simulate:
            if os.path.exists(os.path.join(MENUDIR, "all", all_menus[x])):
                os.rmdir(os.path.join(MENUDIR, "all", all_menus[x]))
            else:
                print MENUDIR + "/all/" + all_menus[x] + " NOT FOUND"
        else:
            print MENUDIR + "/all/" + all_menus[x] + " NOT FOUND"

#REM Function done     
def copy_menu_struct():
    try:
        shutil.copyfile(MENUSRC, MENUDIR)
    except:
        sys.stderr.write("Unable to copy menu structure to" + MENUDIR)
        sys.stderr.write("Verify that you have right permissions")
        return -1

def make_menu_entry(eapfile="" , category="" ):
    file = os.path.join(EAPDIR, eapfile)
    if os.path.exists(file):
        # Check if dry-run
        if options.simulate:
            print "Copying " + eapfile + " to " + ICONDIR
            if not menus_used.__contains__(category):
                menus_used.append(category)
            if not os.path.exists(os.path.join(MENUDIR, "all", category)):
                print "Making menu entry for " + eapfile + " in " + MENUDIR + "/all/" + category
            return 0
        # Create the menu entry
        else:
            if not os.path.exists(ICONDIR):
                os.mkdir(ICONDIR)
            try:
                shutil.copyfile(file, ICONDIR)
            except:
                sys.stderr.write("Unable to copy " + eapfile + " to " + ICONDIR)
                sys.stderr.write("Verify that you have write permissions in " + ICONDIR)
                return -1
            if not menus_used.__contains__(category):
                menus_used.append(category)
            # Eventually remove the space from the category; only for submenus
            category = re.sub(" ", "/", category, 1)
            menuorder = open(os.path.join(MENUDIR, "all", category, ".order"), "w")
            menuorder.write(eapfile)
            menuorder.close()
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
        print green("*****************************************")
        print green("          Starting Simulation")
        print green("*****************************************")

    pkginstalled = []
    pkginstalled = listpackages(PORTDIR)
    notthere = []
    if not options.simulate:
        copy_menu_struct()
    for y in range(db.__len__()):
        if pkginstalled.__contains__(db[y][0]):
            if options.listonly:
                print "*****************************************"
                print "   Listing supported packages installed"
                print "*****************************************"
                print "Package\t\tIcon file\t\tMenu category"
                print db[y][0] + "\t" + db[y][1] + "\t\t" + db[y][2] + "\t"
            else:
                # calls makemenuentry file.eap, menu category
                for single_entry in db[y][1].split(" "):
                    try:
                        make_menu_entry(single_entry,db[y][2])
                    except:
                        print >> sys.stderr, "Can't find " + single_entry + " in " + EAPDIR
                        return -1
        else:
            notthere.append(db[y][0])
    clean_menu()
    # Final move, show the unfound icons in the db
    print red("*****************************************")
    print red("         Missing applications :")
    print red("*****************************************")
    for i in range(notthere.__len__()):
        print " ---> " + notthere[i]


if __name__ == "__main__":

    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("-l", "--list", action="store_true", dest="listonly", default=False,
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
