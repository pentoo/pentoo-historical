# Copyright 1999-2007 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

K_NOUSENAME="yes"
K_NOSETEXTRAVERSION="yes"
K_SECURITY_UNSUPPORTED="1"
ETYPE="sources"
inherit kernel-2
detect_version

DESCRIPTION="Sources for the pentoo livecd"
HOMEPAGE="http://www.pentoo.ch"
SRC_URI="http://dev.pentoo.ch/~grimmlin/${P}-r1.tbz2"

KEYWORDS="~alpha ~amd64 ~arm ~hppa ~ia64 ~ppc ~ppc64 ~sparc x86"

src_unpack() {
	unpack ${A}
}
