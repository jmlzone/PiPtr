# Makefile for C programs for Pi Repeater
BINDIR = ../bin

BINS = mout multimon

all: $(BINDIR) $(addprefix $(BINDIR)/, $(BINS))


$(BINDIR)/mout: mout.c mout.h multimon/costabi.c
	cc mout.c multimon/costabi.c -lasound -o mout

$(BINDIR)/multimon:
	cd multimon; make
	mv multimon/bin-$(shell uname -m)/multimon $(BINDIR)
