# Introduction #

This is DRAFT page. Please expand it.

# Pentoo Installation #

Boot Pentoo LiveUSB<br>
Update pentoo-installer (optional):<br>
<pre><code>layman -s pentoo<br>
mkdir /usr/portage/distfiles/svn-src<br>
chown portage:portage /usr/portage/distfiles/svn-src<br>
emerge -1 pentoo-installer<br>
</code></pre>

Run pentoo-installer<br>
Follow steps in the menu<br>
Don't forget to assign root password and create a regular user<br>

Next, clean up live configuration (the installer still need to be improved here):<br>
<pre><code># Fix the /etc/inittab file<br>
rc-update delete fixinittab<br>
emerge -1 sys-apps/sysvinit<br>
<br>
# Remove live-related configuration <br>
rm /etc/gconf /usr/share/livecd<br>
emerge -1 gnome-base/gconf<br>
</code></pre>
Remove live media and reboot from the installed copy<br>
Login as a regular user and run:<br>
<pre><code>startx<br>
</code></pre>

<h1>Updating Pentoo</h1>
Update the installed copy as described in the <a href='PentooUpdater#On_regular_basis.md'>Pentoo Updater</a> section