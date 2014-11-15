# Copyright 1999-2012 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

EAPI=5

inherit firefox-plugin

FFP_XPI_FILE="${P}"
FFP_XPI_FILEID="281364"
DESCRIPTION="Simple security audit / penetration test tool."
HOMEPAGE="http://code.google.com/p/hackbar"
SRC_URI="http://addons.mozilla.org/firefox/downloads/file/${FFP_XPI_FILEID} -> ${FFP_XPI_FILE}.xpi"

LICENSE="MPL-1.1"
SLOT="0"
KEYWORDS="amd64 x86"
IUSE=""