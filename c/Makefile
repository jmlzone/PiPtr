# Makefile for C programs for Pi Repeater
BINDIR = ../bin

BINS = mout tout multimon

all: $(BINDIR) $(addprefix $(BINDIR)/, $(BINS))


$(BINDIR)/mout: mout.c mout.h multimon/costabi.c
	cc mout.c multimon/costabi.c -lasound -o $(BINDIR)/mout

$(BINDIR)/tout: tout.c tout.h multimon/costabi.c
	cc tout.c multimon/costabi.c -lasound -o $(BINDIR)/tout

$(BINDIR)/multimon:
	cd multimon; make
	mv multimon/bin-$(shell uname -m)/multimon $(BINDIR)
