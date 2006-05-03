# Copyright 1999-2004 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2

inherit gnome2 mono

DESCRIPTION="LAT stands for LDAP Administration Tool. The tool allows you to browse LDAP-based directories and add/edit/delete entries contained within."
HOMEPAGE="http://people.mmgsecurity.com/~lorenb/lat"
SRC_URI="${HOMEPAGE}/releases/${P}.tar.gz"
LICENSE="GPL-2"
IUSE=""
SLOT="0"
KEYWORDS="~x86 ~amd64"

RDEPEND=">=dev-lang/mono-1.1.12.1
	=dev-dotnet/gtk-sharp-2.4*
	=dev-dotnet/gnome-sharp-2.4*
	=dev-dotnet/glade-sharp-2.4*
	=dev-dotnet/gconf-sharp-2.4*
	=gnome-base/gnome-keyring-0.4*"

DEPEND="${RDEPEND}
	app-text/scrollkeeper
	dev-util/pkgconfig"

DOCS="AUTHORS COPYING ChangeLog INSTALL NEWS README TODO"

src_unpack() {
	unpack ${A}
	cd ${S}
	libtoolize --force --copy || die "libtoolize failed"
	aclocal || die
	autoconf || die
}
