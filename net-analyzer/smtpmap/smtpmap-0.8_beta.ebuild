# Copyright 1999-2005 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: /root/portage/net-analyzer/smtpmap/smtpmap-0.8_beta.ebuild,v 1.1.1.1 2006/02/27 20:03:41 grimmlin Exp $

inherit eutils
DESCRIPTION="Smtpmap is a very complete and weel done fingerprinter for SMTP, FTP and POP3 fingerprinter"
HOMEPAGE="http://plasmahh.hopto.org/down_tool"
SRC_URI="http://plasmahh.hopto.org/${PN}-0.8-beta.tar.bz2"

MY_P=${PN}-0.8.234-BETA

LICENSE="GPL"
SLOT="0"
KEYWORDS="~x86"

IUSE=""
DEPEND=""
S=${WORKDIR}/${MY_P}

src_compile(){
	./configure
#	It has is own configuration script... maybe some sed here after needs to be done
	emake || die "make failed"
}

src_install() {
	insinto /usr/share/smtpmap
	doins share/*
	dobin src/smtpmap
	dodoc ChangeLog README TODO
}
