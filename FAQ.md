# Frequently Asked Questions - Pentoo #


## Installation ##

### Pentoo Linux Hard Disk Install ###
This feature is supported by the official Pentoo-installer.
  * More info: [Installation to disc](https://code.google.com/p/pentoo/wiki/PentooInstaller) page.
### Dual Boot Pentoo Linux with Windows ###
### Pentoo Linux Live USB Install ###
### Pentoo Linux Encrypted Disk Install ###
How to go about it? Grimmlin took care to make our life easier and now this feature is available from the pentoo-installer.
  * [r5245](https://code.google.com/p/pentoo/source/detail?r=5245) pentoo-installer: Added LUKS with pgp-encrypted keys support
### Pentoo Linux Overlay Install ###
More info: OverlayUsage page.

## Customization ##
### Can I install XXX instead of YYY? ###
Yes, there are number of packages which can replaced. For example:
```
emerge -C wicd
emerge -1 networkmanager
```

```
emerge -C chromium
emerge -1 google-chrome
```

### Can I uninstall XXX? Pentoo pulls it by default ###
There are number of USE flags which can be disabled. For example:
```
pentoo/pentoo kde -gnome -radio qemu
pentoo/pentoo-mobile -ios
pentoo/pentoo-wireless -drivers
pentoo/pentoo-system -drivers -windows-compat
pentoo/pentoo-misc -accessibility -atm -qt4 -gtk -X -office
app-exploits/packetstormexploits -2009 -2010 -2011 -2012

www-servers/lighttpd -mysql -php
net-analyzer/wireshark -ares -btbb -gcrypt -geoip -kerberos -portaudio -smi libadns
net-wireless/kismet -plugin-btscan -plugin-spectools

net-misc/networkmanager -modemmanager

```

Use eix or examine each ebuild for more details

### Restrict Thunar from showing encrypted partitions ###
For some reason, Thunar will sometimes show encrypted partitions as removable devices. To restrict thunar from showing encrypted partitions:
```
nano /etc/udev/rules.d/99-hide-disks.rules 
```
and add:
```
KERNEL=="sda3", ENV{UDISKS_IGNORE}="1"
```
where sda3 is an encrypted partition meant to hide.
Then use this command (as root) to trigger a refresh:
```
udevadm trigger
```
## Troubleshooting a Pentoo Installation ##
### Compilation errors ###

#### Unable to compile a kernel module ####
```
* ERROR: sys-kernel/spl-0.6.2-r3::gentoo failed:
* ERROR: sys-fs/zfs-kmod-0.6.2-r3::gentoo failed:
```

then do the same thing:
```
ls -l /usr/src/linux
lrwxrwxrwx 1 root root 12 Dec 25 07:50 /usr/src/linux -> /usr/src/linux-3.9.9-pentoo
cd /usr/src/linux
```
assuming /usr/src/linux links to the 3.9.9-pentoo sources,
```
zcat /proc/config.gz > .config
make clean && make clean
make prepare
make modules_prepare
```

### Upgrading ###
#### Unable to resolve blocks ####
Uninstall all blocks manually. For example:
```
emerge -C dev-lang/vala
emerge -C dev-libs/ecore
```