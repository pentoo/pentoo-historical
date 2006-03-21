# Copyright 1999-2006 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: /root/portage/net-analyzer/metacoretex-ng/metacoretex-ng-0.9999.ebuild,v 1.1.1.1 2006/03/09 21:57:23 grimmlin Exp $

inherit cvs

DESCRIPTION="A nice, java-based, MYSQL/Oracle/MSSQL/ODBC attack framework"
HOMEPAGE="http://metacoretex-ng.sourceforge.net"
LICENSE="GPL-2"

ECVS_SERVER="cvs.sourceforge.net:/cvsroot/"
ECVS_MODULE="MetaCoreTex-NG"
ECVS_LOCALNAME="${P}"

KEYWORDS="-*"
IUSE=""
RDEPEND="virtual/jre"


pkg_setup() {
	einfo "nothing to setup"
}

src_compile() {
	einfo "nothing to compile"
}

src_install() {
	einfo "nothing to setup"
	dodoc CHANGELOG COPYING README THANKS
}

pkg_postinst() {
	linux-mod_pkg_postinst

	ewarn
	ewarn "This is a CVS ebuild - please report any bugs to the rt2x00 forums"
	ewarn "http://rt2x00.serialmonkey.com/phpBB2/viewforum.php?f=5"
	ewarn
	ewarn "Any bugs reported to Gentoo will be marked INVALID"
	ewarn
}
