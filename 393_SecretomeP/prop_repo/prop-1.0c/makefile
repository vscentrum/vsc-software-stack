
#
# Makefile for ProP 1.0b
#
# This makefile is used to install the 'prop' script and manpage
# at proper quarters.
#
# Version: 6 Jan 2004,	K.Rapacki
#

# edit to taste
BINDIR	= /usr/opt/bin
MANDIR	= /usr/opt/man/cat1


# targets, do not change ======================================================
install:	prop
		cp prop $(BINDIR)
		chmod 755 $(BINDIR)/prop

install.man:	man/prop.1
		cp man/prop.1 $(MANDIR)
		chmod 644 $(MANDIR)/prop.1

installc.man:	man/prop.man
		cat man/prop.man | compress >$(MANDIR)/prop.Z
		chmod 644 $(MANDIR)/prop.Z

# end of makefile =============================================================
