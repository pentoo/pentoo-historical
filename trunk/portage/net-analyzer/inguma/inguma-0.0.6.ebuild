# Copyright 1999-2006 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

DESCRIPTION="Inguma is an open source penetration testing toolkit written completely in Python"
HOMEPAGE="http://inguma.sourceforge.net/"
SRC_URI="mirror://sourceforge/${PN}/${P}.tar.gz"

LICENSE="GPL-2"
KEYWORDS="~amd64 ~ppc ~x86"
IUSE="qt oracle"

RDEPEND="dev-python/Impacket
	 oracle? ( dev-python/cxoracle )
	 dev-python/paramiko
	 dev-python/pysnmp
	 app-fuzz/scapy
	 qt? ( dev-python/PyQt )"

src_compile() {
	einfo "Nothing to compile"
}

src_install() {
	if ! use qt; then
		rm -rf gui ingumagui.py
	fi
        dodir /usr/lib/${PN}
	dodoc AUTHORS  COPYING.txt  ChangeLog  LICENSE  MODULES.txt  README  REQUIRES  THANKS  TODO  TUTORIAL.txt doc/*
	rm -rf AUTHORS  COPYING.txt  ChangeLog  LICENSE  MODULES.txt  README  REQUIRES  THANKS  TODO  TUTORIAL.txt doc
	rm -rf scapy* winscapy*
	cp -pPR ${S}/* ${D}usr/lib/${PN} || die
	chown -R root:0 ${D}
	dosbin ${FILESDIR}/inguma
}
