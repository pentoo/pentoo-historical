# Copyright 1999-2014 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

EAPI=5

FFP_TARGETS="firefox"
inherit mozilla-addon

MOZ_FILEID="265690"
DESCRIPTION="Status bar widgets and progress indicators for Firefox 4+"
HOMEPAGE="http://addons.mozilla.org/en-US/firefox/addon/status-4-evar/"
SRC_URI="http://addons.mozilla.org/firefox/downloads/file/${MOZ_FILEID} -> ${FFP_XPI_FILE}.xpi"

LICENSE="|| ( MPL-1.1 GPL-2 LGPL-2.1 )"
SLOT="0"
KEYWORDS="amd64 x86"
