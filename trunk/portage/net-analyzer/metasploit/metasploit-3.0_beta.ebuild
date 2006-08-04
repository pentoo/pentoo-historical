# Copyright 1999-2006 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

inherit ruby

MY_P="${PN/metasploit/framework}-${PV/_/-}-1"
S="${WORKDIR}/${MY_P}"
DESCRIPTION="The Metasploit Framework is an advanced open-source platform for developing, testing, and using vulnerability exploit code."
HOMEPAGE="http://www.metasploit.org/"
SRC_URI="http://metasploit.com/tools/${MY_P}.tar.gz"

LICENSE="MSF-1.1"
SLOT="0"
KEYWORDS="~amd64 ~ppc ~x86"
RESTRICT="fetch"
IUSE=""

RDEPEND="dev-lang/ruby
	 dev-ruby/ruby-zlib"
pkg_nofetch() {
	# Fetch restricted due to license acceptation
	einfo ${RUBY}
	einfo "Please download the framework from:"
	einfo ${SRC_URI}
	einfo "and move it to ${DISTDIR}"
}

src_install() {
	local siteruby

#	dodir /usr/lib/
	dodir /usr/bin/

	# should be as simple as copying everything into the target...
#	cp -pPR ${S} ${D}usr/lib/metasploit || die

	# and creating symlinks in the /usr/bin dir

	newinitd ${FILESDIR}/msfweb.initd msfweb || die "newinitd failed"
	newconfd ${FILESDIR}/msfweb.confd msfweb || die "newconfd failed"

	siteruby=$(${RUBY} -r rbconfig -e 'print Config::CONFIG["sitedir"]')
	insinto ${siteruby}
#	cd ${S}
	doins -r * | die "doins failed"
	cd ${D}/usr/bin
	ln -s ${siteruby}/msf* ./ || die
	chown -R root:0 ${D}
}

pkg_postinst() {
	ewarn "You may wish to perform a metasploit update to get"
	ewarn "the latest modules (e.g. run 'msfupdate -u')"
}
