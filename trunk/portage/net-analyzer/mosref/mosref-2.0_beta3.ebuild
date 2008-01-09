# Copyright 1999-2008 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

inherit eutils
MY_P="${P/_/-}"
DESCRIPTION="A secure remote execution framework using a compact Scheme-influenced VM"
HOMEPAGE="http://sourceforge.net/projects/mosref/"
SRC_URI="mirror://sourceforge/${PN}/${MY_P}.tar.gz
	 doc? ( mirror://sourceforge/${PN}/${MY_P}-documentation.tar.gz )"
LICENSE="GPL-2"
SLOT="0"
KEYWORDS="~x86"
IUSE="doc"
DEPEND=""
RDEPEND="${DEPEND}"
S="${WORKDIR}"/"${MY_P}"

src_compile() {
	epatch ${FILESDIR}/${PN}-gentoo.patch
	sed -i -e "s|%%DESTDIR%%|\"${D}/usr/\"|" bin/install.ms || die "sed failed"
	emake || die "emake failed"
}

src_install() {
	emake DESTDIR="${D}" install || die "emake install failed"
	# installs the sources to /usr/src for cross-compiling & doc
	make clean
	dodir /usr/src/"${PN}"
	dodoc doc/vm-implementation*
	rm -rf doc
	cp -R * "${D}"/usr/src/"${PN}"/
	if use doc;then
		cd "${WORKDIR}"/"${PN}"-reference
		dodoc *
	fi
}
