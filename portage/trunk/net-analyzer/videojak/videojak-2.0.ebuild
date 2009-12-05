# Copyright 1999-2009 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

DESCRIPTION="VideoJak is an IP Video security assessment tool"
HOMEPAGE="http://videojak.sourceforge.net/"
SRC_URI="mirror://sourceforge/${PN}/${P}.tar.gz"

EAPI=2
inherit eutils
LICENSE="GPL-2"
SLOT="0"
KEYWORDS="-*"
IUSE=""

DEPEND="net-analyzer/ettercap"
RDEPEND="${DEPEND}"

src_install() {
	emake DESTDIR="${D}" install || die "install failed"
	rm -rf "${D}/usr/share/man/" "${D}/usr/bin/etterlog" "${D}/usr/bin/etterfilter" "${D}/etc/etter.conf"
}
