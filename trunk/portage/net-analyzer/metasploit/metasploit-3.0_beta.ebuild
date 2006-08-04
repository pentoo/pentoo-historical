# Copyright 1999-2006 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

inherit eutils

MY_P="${PN/metasploit/framework}-${PV/_/-}-1"
S="${WORKDIR}/${MY_P}"
DESCRIPTION="The Metasploit Framework is an advanced open-source platform for developing, testing, and using vulnerability exploit code."
HOMEPAGE="http://www.metasploit.org/"
SRC_URI="${MY_P}.tar.gz"

LICENSE="MSF-1.1"
SLOT="0"
KEYWORDS="~amd64 ~ppc ~x86"
RESTRICT="fetch"
IUSE="gtk"

RDEPEND="dev-lang/ruby
	 dev-ruby/ruby-zlib
	 gtk? ( >=dev-ruby/wxruby-0.6 )"

pkg_nofetch() {
	# Fetch restricted due to license acceptation
	einfo "Please download the framework from:"
	einfo "http://metasploit.com/projects/Framework/msf3/download.html?Release=${MY_P}.tar.gz"
	einfo "and move it to ${DISTDIR}"
}

src_compile() {
	epatch ${FILESDIR}/metasploit-gentoo.patch
}
src_install() {
        dodir /usr/lib/
        dodir /usr/bin/

        # should be as simple as copying everything into the target...
        cp -pPR ${S} ${D}usr/lib/metasploit || die

        # and creating symlinks in the /usr/bin dir
        cd ${D}/usr/bin
        ln -s ../lib/metasploit/msf* ./ || die
        chown -R root:0 ${D}

        newinitd ${FILESDIR}/msfweb.initd msfweb || die "newinitd failed"
        newconfd ${FILESDIR}/msfweb.confd msfweb || die "newconfd failed"
}

#pkg_postinst() {
#	msfupdate not available in this release
#	ewarn "You may wish to perform a metasploit update to get"
#	ewarn "the latest modules (e.g. run 'msfupdate -u')"
#}
