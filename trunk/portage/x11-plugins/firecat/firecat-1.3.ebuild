# Copyright 1999-2004 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: /root/portage/app-fuzz/protos/protos-1.0.ebuild,v 1.1.1.1 2006/03/08 18:55:18 grimmlin Exp $

inherit mozextension multilib

DESCRIPTION="FireCAT is a Firefox Framework Map collection of the most useful security oriented extensions."
HOMEPAGE="http://www.security-database.com/toolswatch/FireCAT-Firefox-Catalog-of,302.html"
SRC_URI="recon? (https://addons.mozilla.org/en-US/firefox/downloads/file/17470/shazou-1.2-fx.xpi
				https://addons.mozilla.org/fr/firefox/downloads/file/7473/domainfinder-0.3-fx.xpi
				https://addons.mozilla.org/en-US/firefox/downloads/file/15850/hostip.info_geolocation_plugin-0.4.3.3-fx+mz+ns+sm+fl.xpi
				https://addons.mozilla.org/en-US/firefox/downloads/file/2875/showip-0.8.05-fx+mz.xpi
				https://addons.mozilla.org/en-US/firefox/downloads/file/8145/asnumber-1.0-beta-8-fx.xpi)"

LICENSE="GPL-2"
SLOT="0"
KEYWORDS="~x86"
IUSE="recon proxy editors security network misc"

RDEPEND="|| (
	>=www-client/mozilla-firefox-bin-1.5.0.7
	>=www-client/mozilla-firefox-1.5.0.7
)"
DEPEND="${RDEPEND}"

S=${WORKDIR}

src_unpack() {
	for x in $A
	do
		xpi_unpack "${x}"
	done
}

src_compile () {
	einfo "Nothing to compile"
}

src_install () {
	declare MOZILLA_FIVE_HOME
	for x in `ls "${S}/"`
	do
		if has_version '>=www-client/mozilla-firefox-1.5.0.7'; then
			MOZILLA_FIVE_HOME="/usr/$(get_libdir)/mozilla-firefox"
			xpi_install "${S}"/"${x}"
		fi
		if has_version '>=www-client/mozilla-firefox-bin-1.5.0.7'; then
			MOZILLA_FIVE_HOME="/opt/firefox"
			xpi_install "${S}"/"${x}"
		fi
	done
}
