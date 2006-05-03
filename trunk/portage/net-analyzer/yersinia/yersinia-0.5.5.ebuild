# Copyright 1999-2005 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: /root/portage/net-analyzer/yersinia/yersinia-0.5.5.ebuild,v 1.1.1.1 2006/02/27 20:03:41 grimmlin Exp $

DESCRIPTION="Yersinia is a framework for performing layer 2 attacks"
HOMEPAGE="http://yersinia.sourceforge.net/"
SRC_URI="mirror://sourceforge/${PN}/${P}.tar.gz"
LICENSE="GPL-2"
SLOT="0"

KEYWORDS="~x86"
IUSE=""

DEPEND="sys-libs/ncurses
	>=virtual/libpcap-0.8.3
	>=net-libs/libnet-1.1.2"
S=${WORKDIR}/${P}

src_install() {
	einstall || die
	doman *.8
	dodoc ChangeLog FAQ NEWS README TODO AUTHORS
}
