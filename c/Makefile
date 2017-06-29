# Makefile for C programs for Pi Repeater
BINDIR = ../bin

BINS = mout tout

all: $(BINDIR) $(addprefix $(BINDIR)/, $(BINS))

COPTS=-O2 -Wall -Wpedantic -Wextra -Warray-bounds

DIST:=$(shell uname -m)


$(BINDIR)/mout: mout.c costabi.c
	$(CC) $(COPTS) $^ -lasound -o $@

$(BINDIR)/tout:  tout.c costabi.c 
	$(CC) $(COPTS) $^ -lasound -o $@

clean:
	$(RM) $(BINDIR)/*
