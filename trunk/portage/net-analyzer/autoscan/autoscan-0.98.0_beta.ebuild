# Copyright 1999-2004 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: 

inherit gnome2

DESCRIPTION="Utility for network exploration with Samba support."
HOMEPAGE="http://autoscan.free.fr"
LICENSE="GPL-2"

SLOT="0"
KEYWORDS="~x86 ~ppc ~alpha ~sparc ~hppa ~amd64 ~ia64 ~mips"
IUSE=""

MY_P="AutoScan-${PV}"
MY_P="${MY_P/_beta/b}"
SRC_URI="mirror://sourceforge/autoscan/${MY_P}.tar.gz"

RDEPEND=">=gnome-base/libgnomeui-2.0 \
	net-fs/samba \
	>=gnome-extra/gtkhtml-2.0 \
	net-analyzer/nmap \
	>=net-analyzer/net-snmp-5.0"

DEPEND="${RDEPEND}
	dev-util/pkgconfig"

S="${WORKDIR}/${MY_P}"

src_compile() {
	cd "${S}"/Sources/AutoScan
        NOCONFIGURE=1 ./autogen.sh
	econf || die
        emake || die

	cd "${S}"/Sources/AutoScan_Agent
        NOCONFIGURE=1 ./autogen.sh
	econf || die
	emake || die
}

src_install() {

	dobin "${S}"/Sources/AutoScan/src/AutoScan_Network
	dobin "${S}"/Sources/AutoScan_Agent/src/AutoScan_Agent

	dodir /usr/share/apps/AutoScan
	insinto /usr/share/apps/AutoScan
	doins "${S}"/Data/apps/AutoScan/*

	dodir /usr/share/pixmaps/AutoScan
	insinto /usr/share/pixmaps/AutoScan
	doins "${S}"/Data/pixmaps/AutoScan/*

	dodir /usr/share/doc/"${MY_P}"
	docinto /usr/share/doc/"${MY_P}"
	dodoc "${S}"/Data/doc/AutoScan/*
}
