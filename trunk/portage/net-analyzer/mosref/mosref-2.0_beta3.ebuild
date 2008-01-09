# Copyright 1999-2008 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

DESCRIPTION="A secure remote execution framework using a compact Scheme-influenced VM"

MY_P="${P/_/-}"
# Homepage, not used by Portage directly but handy for developer reference
HOMEPAGE="http://sourceforge.net/projects/mosref/"
SRC_URI="mirror://sourceforge/${PN}/${MY_P}.tar.gz
	 doc? ( mirror://sourceforge/${PN}/${MY_P}-documentation.tar.gz )"
LICENSE="GPL-2"
SLOT="0"
KEYWORDS="~x86"
IUSE="doc"
DEPEND=""
RDEPEND="${DEPEND}"

src_unpack() {
	unpack ${A}
	epatch ${FILESDIR}/${PN}-gentoo.patch
}

src_compile() {
	econf || die "econf failed"
	emake || die "emake failed"
}

src_install() {
	emake DESTDIR="${D}" install || die "emake install failed"
	# installs the sources to /usr/src for cross-compiling
	make clean
	dodir /usr/src/${PN}
	cp -R * /usr/src/${PN}
}
