# Makefile for C programs for Pi Repeater
BINDIR = ../bin

BINS = mout tout multimon gpio_alt

all: $(BINDIR) $(addprefix $(BINDIR)/, $(BINS))


$(BINDIR)/mout: mout.c mout.h multimon/costabi.c
	cc mout.c multimon/costabi.c -lasound -o $(BINDIR)/mout

$(BINDIR)/tout: tout.c tout.h multimon/costabi.c
	cc tout.c multimon/costabi.c -lasound -o $(BINDIR)/tout

$(BINDIR)/multimon:
	cd multimon; make
	mv multimon/bin-$(shell uname -m)/multimon $(BINDIR)

$(BINDIR)/gpio_alt:
	cc gpio-alt.c -o $(BINDIR)/gpio_alt
	sudo chown root:root $(BINDIR)/gpio_alt
	sudo chmod u+s $(BINDIR)/gpio_alt
