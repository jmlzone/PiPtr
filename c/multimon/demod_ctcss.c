/*
 *      demod_ctcss.c -- CTCSS signalling demodulator/decoder
 *
 *      Copyright (C) 2016  
 *          James Lee N1DDK
 *
 *      This program is free software; you can redistribute it and/or modify
 *      it under the terms of the GNU General Public License as published by
 *      the Free Software Foundation; either version 2 of the License, or
 *      (at your option) any later version.
 *
 *      This program is distributed in the hope that it will be useful,
 *      but WITHOUT ANY WARRANTY; without even the implied warranty of
 *      MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *      GNU General Public License for more details.
 *
 *      You should have received a copy of the GNU General Public License
 *      along with this program; if not, write to the Free Software
 *      Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
 */

/* ---------------------------------------------------------------------- */

#include "multimon.h"
#include "filter.h"
#include <math.h>
#include <string.h>
#include <stdio.h>
//#include <stdbool.h>

/* ---------------------------------------------------------------------- */

/*
 *
 * CTCSS frequencies
 *
 67.0
 69.4
 71.9
 74.4
 77.0
 79.7
 82.5
 85.4
 88.5
 91.5
 94.8
 97.4
 100.0
 103.5
 107.2
 110.9
 114.8
 118.8
 123.0
 127.3
 131.8
 136.5
 141.3
 146.2
 151.4
 156.7
 159.8
 162.2
 165.5
 167.9
 171.3
 173.8
 177.3
 179.9
 183.5
 186.2
 189.9
 192.8
 196.6
 199.5
 203.5
 206.5
 210.7
 218.1
 225.7
 229.1
 233.6
 241.8
 250.3
 254.1
 * 
 */

#define SAMPLE_RATE 22050
#define BLOCKLEN (SAMPLE_RATE/20)  /* 50ms blocks */
#define BLOCKNUM 4    /* must match numbers in multimon.h */

#define PHINC(x) ((int) ((x)*(float)0x10000)/SAMPLE_RATE)


static const unsigned int ctcss_phinc[8] = {
	PHINC(77.0), PHINC(88.5), PHINC(103.5), PHINC(110.9),
	PHINC(114.8), PHINC(123.0), PHINC(146.2), PHINC(165.5)
};
static const char* const ctcss_names[] = {"77.0", "88.5", "103.5", "110.9",
					  "114.8", "123.0", "146.2", "165.5"};

/* ---------------------------------------------------------------------- */
	
static void ctcss_init(struct demod_state *s)
{
	memset(&s->l1.ctcss, 0, sizeof(s->l1.ctcss));
}

/* ---------------------------------------------------------------------- */

static inline bool* process_block(struct demod_state *s)
{
	float tote;
	float totte[16];
	int i, j;
	float threshold;
	static bool det[8];

	tote = 0;
	for (i = 0; i < BLOCKNUM; i++)
		tote += s->l1.ctcss.energy[i];
	for (i = 0; i < 16; i++) {
		totte[i] = 0;
		for (j = 0; j < BLOCKNUM; j++)
			totte[i] += s->l1.ctcss.tenergy[j][i];
	}
	for (i = 0; i < 8; i++)
		totte[i] = fsqr(totte[i]) + fsqr(totte[i+8]);
	memmove(s->l1.ctcss.energy+1, s->l1.ctcss.energy, 
		sizeof(s->l1.ctcss.energy) - sizeof(s->l1.ctcss.energy[0]));
	s->l1.ctcss.energy[0] = 0;
	memmove(s->l1.ctcss.tenergy+1, s->l1.ctcss.tenergy, 
		sizeof(s->l1.ctcss.tenergy) - sizeof(s->l1.ctcss.tenergy[0]));
	memset(s->l1.ctcss.tenergy, 0, sizeof(s->l1.ctcss.tenergy[0]));
	tote *= (BLOCKNUM*BLOCKLEN*0.5);  /* adjust for block lengths */
	verbprintf(10, "CTCSS: Energies: %8.5f  %8.5f %8.5f %8.5f %8.5f  %8.5f %8.5f %8.5f %8.5f\n",
		   tote, totte[0], totte[1], totte[2], totte[3], totte[4], totte[5], totte[6], totte[7]);
	threshold = 2000;
	for (i = 0; i < 8; i++) {
	  det[i] = (totte[i]>threshold);
	}
	return (det);
}

/* ---------------------------------------------------------------------- */

static void ctcss_demod(struct demod_state *s, float *buffer, int length)
{
	float s_in;
	int i;
	bool *ldet;

	for (; length > 0; length--, buffer++) {
		s_in = *buffer;
		s->l1.ctcss.energy[0] += fsqr(s_in);
		for (i = 0; i < 8; i++) {
			s->l1.ctcss.tenergy[0][i] += COS(s->l1.ctcss.ph[i]) * s_in;
			s->l1.ctcss.tenergy[0][i+8] += SIN(s->l1.ctcss.ph[i]) * s_in;
			s->l1.ctcss.ph[i] += ctcss_phinc[i];
		}
		if ((s->l1.ctcss.blkcount--) <= 0) {
			s->l1.ctcss.blkcount = BLOCKLEN;
			ldet = process_block(s);
			for (i = 0; i < 8; i++) {
			  if(ldet[i] != s->l1.ctcss.det[i]) {
			    s->l1.ctcss.det[i] = ldet[i];
			    if(ldet[i]) {
			      verbprintf(0, "CTCSS D: %d %s\n", i, ctcss_names[i]);
			      fflush(stdout);
			    } else {
			      verbprintf(0, "CTCSS L: %d %s\n", i, ctcss_names[i]);
			      fflush(stdout);
			    }
			  }
			}
		}
	}
}
/* ---------------------------------------------------------------------- */

const struct demod_param demod_ctcss = {
	"CTCSS", SAMPLE_RATE, 0, ctcss_init, ctcss_demod
};

/* ---------------------------------------------------------------------- */
