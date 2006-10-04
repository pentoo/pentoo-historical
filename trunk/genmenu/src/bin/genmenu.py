#!/bin/python

import sys,os,re,shutil

db=[["net-analyzer/nmap", "nmap.eap", "Scanners/Nmap"], ["net-analyzer/nessus", "nessus.eap toto.eap", "Scanners"], ["net-analyzer/xprobe", "xprobe.eap", "Fingerprinters"], ["net-irc/xchat", "xchat.eap", "Internet"]]

toto = [["e"],
        ["baf"]]

PORTDIR="/var/db/pkg/"
#PORTDIR = 'c:/Pentoo/test/portage'
EAPDIR = '/usr/share/genmenu/e17/all'
ENVDIR = '/etc/env.d/'
ICONDIR = getHomeDir() + '/.e/e/applications/all/'
MENUDIR = getHomeDir() + '/.e/e/applications/menu'
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
    """Function that removed unused menu entries, usually called at the end"""
    all_menus = []
    for y in range(db.__len__()):
        if not all_menus.__contains__(db[y][2]):
            all_menus.append(db[y][2])
    for x in range(menus_used.__len__()):
        all_menus.remove(menus_used[x])
    # This just generated the list of unused menu entries.
        
        

def make_menu_entry(eapfile="" , category="" ):
    file = os.path.join(EAPDIR, eapfile)
    if os._exists(file):
        if options.simulate:
            print "Copying " + eapfile + " to " + ICONDIR
            if not os.path.exists(os.path.join(MENUDIR, "all", category)):
                print "Making menu entry for " + eapfile + " in " 
            return 0
        else:
            if not os.path.exists(ICONDIR):
                os.mkdir(ICONDIR)
            try:
                shutil.copyfile(file, ICONDIR)
            except:
                sys.stderr.write("Unable to copy " + eapfile + " to " + ICONDIR)
                sys.stderr.write("Verify that you have write permissions in " + ICONDIR)
                return -1
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
    pkginstalled = []
    pkginstalled = listpackages(PORTDIR)
    notthere = []
    for y in range(db.__len__()):
        if pkginstalled.__contains__(db[y][0]):
            # calls makemenuentry file.eap, menu category
            for single_entry in db[y][1].split(" "):
                try:
                    make_menu_entry(single_entry,db[y][2])
                except:
                    print >> sys.stderr, "Can't find " + single_entry + " in " + EAPDIR
        else:
            notthere.append(db[y][0])
                
    
    
if __name__ == "__main__":

    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("-t", "--term", dest="e17term", default="Eterm",
                      help="Sets the terminal used by e17 for cli-only tools")
    parser.add_option("-n", "--dry-run", action="store_true", dest="simulate", default=False,
                      help="Simulate only, show missing eap files and show"
                           "what will be done")
    (options, args) = parser.parse_args()

    if options.simulate:
        print "*****************************************"
        print "          Starting Simulation"
        print "*****************************************"

    try:
        main()
    except KeyboardInterrupt:
        # If interrupted, exit nicely
        print >> sys.stderr, 'Interrupted.'
