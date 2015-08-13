Pentoo comes in many flavors and it is important to choose wisely.

Right now, you have two main choices:

Choice 1: hardened or default

You want hardened.  No seriously, you want hardened.  When was the last time
you thought to yourself "I need less security in my pen-testing environment?"
In all seriousness, nearly everything works in the hardened builds, and it is
vastly more stable than anything you have ever used before with the added bonus
of being more secure.  You only want default if you are doing exploit
against yourself, or you **need** opengl support.  OpenCL and CUDA work fine in
the hardened release, but right now, opengl support still eludes us.  If you
cannot live without opengl acceleration pick default, otherwise, you really
want hardened.

Choice 2: x86\_64 or i686

Reality is, no one tests things on x86 anymore.  I don't just mean us, I mean
software devs, distro devs, and even kernel devs.  No one cares about old
hardware.  If you download the i686 builds, it will run on anything Pentium M
or higher, but reality is that the x86\_64 builds are not only faster, but
hugely better tested. Pick x86\_64 unless you have a really good reason (like
wanting to support ancient hardware).