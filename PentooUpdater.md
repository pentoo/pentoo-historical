# Update Commands #

To eliminate most of the question in IRC (#pentoo) and to start a good documentation process, here are the steps to bring your system up to date.

WARNING: The errors on your screen need to be read and acted upon, following these directions blindly will result in failure, then ridicule, then more failure.

## For the first time ##

```
# Sync with the portage tree
emerge --sync

# Modify /etc/portage/make.conf file for your system:

# Please adjust your CFLAGS as desired, information can be found here: https://wiki.gentoo.org/wiki/CFLAGS
# Do not modify these FLAGS unless you know what you are doing, always check the defaults first with: 
portageq envvar CFLAGS
# This is the default for pentoo at the time of build:
# CFLAGS="-Os -mtune=nocona -pipe -ggdb"
# A safe choice would be to keep whatever Pentoo defaults are, but optimize for your specific machine:
CFLAGS="${CFLAGS} -march=native"
CXXFLAGS="${CFLAGS}"
FCFLAGS="${CFLAGS}"
FFLAGS="${CFLAGS}"
#MAKEOPTS is set automatically by the profile to jobs equal to processors, you do not need to set it.
ACCEPT_LICENSE="Oracle-BCLA-JavaSE NVIDIA-CUDA google-chrome Google-TOS PUEL baudline"
# You may wish to edit your VIDEO_CARDS line to match your system better.
# Example, for nvidia/ati users should add nvdia/fglrx flags
VIDEO_CARDS="fbdev vga vesa nvidia"
# Guest OS users should add virtualbox/vmware or qxl flag(s):
VIDEO_CARDS="fbdev vga vesa virtualbox"

# Modify your profile only if you know what you are doing, default should be fine for most users
eselect profile list
eselect profile set <number>

Follow the pentoo-updater below
```

## On regular basis ##

Pay extra attention on upgrading [kernel](http://www.gentoo.org/doc/en/kernel-upgrade.xml), [gcc](http://www.gentoo.org/doc/en/gcc-upgrading.xml), python or any other system package. It is important to upgrade these packages properly before moving to the next step. You might also need to understand [Upgrading Gentoo](https://wiki.gentoo.org/wiki/Upgrading_Gentoo) generic guideline

```
# This will become the pentoo-updater script soon

# This syncs the gentoo and pentoo repos like "apt-get update" in debian
emerge --sync
# This updates all the normal packages like "apt-get upgrade" in debian
emerge --deep --update --newuse world -vt
# This optionally merges in changed config files. unchanged files are merged automatically
etc-update
# This removes old packages which are not needed like "apt-get autoremove" in debian
emerge --depclean
# This rebuilds anything which may have been broken in update
emerge @preserved-rebuild
# This checks all the programs installed from VCS for new revisions and updates if needed
smart-live-rebuild
# Verifies there is no breakage after updates
revdep-rebuild
#merge in any new config files
etc-update
#clean up the distfiles/packages dirs to remove old/un-needed files
eclean-dist -d && eclean-pkg -d
# Check /var/log/portage/elog/summary.log file
# You might need to run extra commands. For example:
emerge @x11-module-rebuild
eselect java-vm set system icedtea-bin-7

# Run the following command under each regular user's account
# Regenerate the main menu for XFCE WM (or "-e" for e17, "-k" for KDE)
genmenu.py -x

```

## after python/perl upgrade: ##
```
perl-cleaner --modules
python-updater
```