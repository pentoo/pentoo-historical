# Copyright 1999-2012 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

EAPI=4

inherit toolchain-funcs

DESCRIPTION="http://www.gat3way.eu/hashkill"
HOMEPAGE="Multi-threaded password recovery tool with multi-GPU support"
SRC_URI="https://github.com/downloads/gat3way/hashkill/${P}.tar.gz"

LICENSE=""
SLOT="0"
KEYWORDS="~amd64 ~x86"
IUSE=""

DEPEND="virtual/opencl-sdk"
RDEPEND="${DEPEND}"

src_prepare() {
	sed -i 's#all: install#all:#' src/kernels/Makefile
	sed -i 's#all: install#all:#' src/dict/Makefile
	sed -i 's#all: install#all:#' src/rules/Makefile

	sed -i 's#$(IDATADIR)#${D}/$(IDATADIR)#' src/kernels/Makefile
	sed -i 's#$(IDATADIR)#${D}/$(IDATADIR)#' src/kernels/compiler/Makefile
	sed -i 's#$(IDATADIR)#${D}/$(IDATADIR)#' src/plugins/Makefile
	sed -i 's#$(IDATADIR)#${D}/$(IDATADIR)#' src/markov/Makefile
	sed -i 's#$(IDATADIR)#${D}/$(IDATADIR)#' src/dict/Makefile
	sed -i 's#$(IDATADIR)#${D}/$(IDATADIR)#' src/rules/Makefile

	sed -i 's#$(BINDIR)#${D}/$(BINDIR)#' src/tools/Makefile
}

src_configure() {
	econf
	#the following might fail if gcc is built with USE="multislot"
	if [[ $(gcc-version) == 4.5 ]] && has_version sys-devel/gcc:4.5[-lto]; then
	    einfo "Compiling without LTO optimisaiton"
	    sed -i 's| -flto -fwhole-program||g' src/Makefile
	fi
}

src_install() {
	#src/tools/Makefile workaround
	dodir /usr/bin

	emake DESTDIR="${D}" install || die
	dodoc INSTALL README
}