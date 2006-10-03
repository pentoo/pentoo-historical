#!/bin/python

import sys,os,re

db=[["net-analyzer/nmap", "nmap.eap", "Scanners"], ["net-analyzer/nessus", "nessus.eap toto.eap", "Scanners"], ["net-analyzer/xprobe", "xprobe.eap", "Fingerprinters"], ["net-irc/xchat", "xchat.eap", "Internet"]]

#PORTDIR="/var/db/pkg/"
PORTDIR = 'c:/Pentoo/test/portage'
EAPDIR = '/usr/share/genmenu/e17/all'
ENVDIR = '/etc/env.d/'

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
        
def settermenv():
    """This function creates the apropriate environment variable for the $E17TERM"""
    file = open(ENVDIR + "99pentoo-terms" , "w")
    file.write("E17TERM=\"" + options.e17term + "\"")
    file.newlines
    file.close()

def makemenuentry(eapfile="" , category="" ):
    test=""
    file = os.path.join(EAPDIR, eapfile)
    if os._exists(file):
        print "youpi"
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
            for singleentry in db[y][1].split(" "):
                print singleentry
                try:
                    makemenuentry(singleentry,db[y][2])
                except:
                    print >> sys.stderr, "Can't find " + singleentry + " in " + EAPDIR
        else:
            notthere.append(db[y][0])
                
    
    
if __name__ == "__main__":

    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("-t", "--term", dest="e17term",
                      help="Sets the terminal used by e17 for cli-only tools")
    (options, args) = parser.parse_args()

    try:
        main()
    except KeyboardInterrupt:
        # If interrupted, exit nicely
        print >> sys.stderr, 'Interrupted.'
