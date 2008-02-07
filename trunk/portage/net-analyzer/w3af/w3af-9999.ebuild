# Copyright 1999-2006 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

inherit distutils subversion
DESCRIPTION="Web Application Attack and Audit Framework"
HOMEPAGE="http://w3af.sourceforge.net/"
ESVN_REPO_URI="https://w3af.svn.sourceforge.net/svnroot/w3af/trunk"

LICENSE="GPL-2"
KEYWORDS="-*"
IUSE=""

RDEPEND="dev-python/utidylib
	 dev-python/soappy"

src_compile() {
	einfo "Nothing to compile"
}

src_install() {
        dodir /usr/lib/
        dodir /usr/bin/

        # should be as simple as copying everything into the target...
        cp -pPR ${S} ${D}usr/lib/w3af || die

        # and creating symlinks in the /usr/bin dir
        cd ${D}/usr/bin
       	ln -s ../lib/w3af/w3af ./w3af || die

        chown -R root:0 ${D}
}
