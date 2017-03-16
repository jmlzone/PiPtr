/*
 *      unixinput.c -- input sound samples
 *
 *      Copyright (C) 1996  
 *          Thomas Sailer (sailer@ife.ee.ethz.ch, hb9jnx@hb9w.che.eu)
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
#include <stdio.h>
#include <stdarg.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include <errno.h>
#include <string.h>
#include <sys/wait.h>
#include <stdlib.h>
#include <signal.h>
#include <alsa/asoundlib.h>


/* ---------------------------------------------------------------------- */

static const char *allowed_types[] = {
	"raw", "aiff", "au", "hcom", "sf", "voc", "cdr", "dat", 
	"smp", "wav", "maud", "vwe", NULL
};

/* ---------------------------------------------------------------------- */

static const struct demod_param *dem[] = { ALL_DEMOD };

#define NUMDEMOD (sizeof(dem)/sizeof(dem[0]))

static struct demod_state dem_st[NUMDEMOD];
static unsigned int dem_mask[(NUMDEMOD+31)/32];

#define MASK_SET(n) dem_mask[(n)>>5] |= 1<<((n)&0x1f)
#define MASK_RESET(n) dem_mask[(n)>>5] &= ~(1<<((n)&0x1f))
#define MASK_ISSET(n) (dem_mask[(n)>>5] & 1<<((n)&0x1f))

/* ---------------------------------------------------------------------- */

static int verbose_level = 0;

/* ---------------------------------------------------------------------- */

void verbprintf(int verb_level, const char *fmt, ...)
{
        va_list args;
        
        va_start(args, fmt);
        if (verb_level <= verbose_level)
                vfprintf(stdout, fmt, args);
        va_end(args);
}

/* ---------------------------------------------------------------------- */

static void process_buffer(float *buf, unsigned int len)
{
	int i;

	for (i = 0; i <  NUMDEMOD; i++) 
		if (MASK_ISSET(i) && dem[i]->demod)
			dem[i]->demod(dem_st+i, buf, len);
}

/* ---------------------------------------------------------------------- */

/* ---------------------------------------------------------------------- */
#define ALSA_BUF_SIZE 4086
static void input_sound(unsigned int sample_rate, unsigned int overlap,
			const char *ifname)
{
	float fbuf[16384];
	unsigned int fbuf_cnt = 0;
	int i;
	int err;
	short alsa_buf[ALSA_BUF_SIZE];
	snd_pcm_t *capture_handle;
	snd_pcm_hw_params_t *hw_params;
	unsigned int sampleRate=44100;
	
	//	printf("trying to open %s\n for rate %u and overlap %d", ifname, sample_rate,overlap);
	if ((err = snd_pcm_open (&capture_handle, ifname, SND_PCM_STREAM_CAPTURE, 0)) < 0) {
	  fprintf (stderr, "cannot open audio device %s (%s)\n", 
		   ifname,
		   snd_strerror (err));
	  exit (1);
	}
	//printf("success\n");

	//printf("trying to Malloc for hardware params\n");
	if ((err = snd_pcm_hw_params_malloc (&hw_params)) < 0) {
	  fprintf (stderr, "cannot allocate hardware parameter structure (%s)\n",
		   snd_strerror (err));
	  exit (1);
	}
	//printf("success\n");
				 
	//printf("trying to initialize hardware params\n");
	if ((err = snd_pcm_hw_params_any (capture_handle, hw_params)) < 0) {
	  fprintf (stderr, "cannot initialize hardware parameter structure (%s)\n",
		   snd_strerror (err));
	  exit (1);
	}
	//printf("success\n");
	
	//printf("trying to set access\n");
	if ((err = snd_pcm_hw_params_set_access (capture_handle, hw_params, SND_PCM_ACCESS_RW_INTERLEAVED)) < 0) {
	  fprintf (stderr, "cannot set access type (%s)\n",
		   snd_strerror (err));
	  exit (1);
	}
	//printf("success\n");
	
	//printf("trying to set format to S16_LE\n");
	if ((err = snd_pcm_hw_params_set_format (capture_handle, hw_params, SND_PCM_FORMAT_S16_LE)) < 0) {
	  fprintf (stderr, "cannot set sample format (%s)\n",
		   snd_strerror (err));
	  exit (1);
	}
	//printf("success\n");
	sampleRate= (unsigned) sample_rate;
	//printf("trying to set rate to %u\n",sampleRate);
	if ((err = snd_pcm_hw_params_set_rate_near (capture_handle, hw_params, &sampleRate, 0)) < 0) {
	  fprintf (stderr, "cannot set sample rate (%s)\n",
		   snd_strerror (err));
	  exit (1);
	}
	//printf("success\n");
	
	//printf("trying to get channel count to 1\n");
	if ((err = snd_pcm_hw_params_set_channels (capture_handle, hw_params, 1)) < 0) {
	  fprintf (stderr, "cannot set channel count (%s)\n",
		   snd_strerror (err));
	  exit (1);
	}
	//printf("success\n");
	//printf("trying to set paramaters\n");
	if ((err = snd_pcm_hw_params (capture_handle, hw_params)) < 0) {
	  fprintf (stderr, "cannot set parameters (%s)\n",
		   snd_strerror (err));
	  exit (1);
	}
	
	//printf("trying to free\n");
	snd_pcm_hw_params_free (hw_params);
	
	//printf("trying to prepare\n");
	if ((err = snd_pcm_prepare (capture_handle)) < 0) {
	  fprintf (stderr, "cannot prepare audio interface for use (%s)\n",
		   snd_strerror (err));
	  exit (1);
	}
	//printf("success\n");
	
	fbuf_cnt = 0;
	for (;;) {
	  // read a buffer of ALSA_BUF_SIZE frames of 16S_LE
	  if ((err = snd_pcm_readi (capture_handle, alsa_buf, ALSA_BUF_SIZE)) != ALSA_BUF_SIZE) {
	    fprintf (stderr, "read from audio interface failed (%s)\n",
		     snd_strerror (err));
	    exit (1);
	  }
	  // convert to float
	  for(i=0; i<ALSA_BUF_SIZE; i++) {
	    fbuf[fbuf_cnt++] = (float) alsa_buf[i] * (1.0/32768.0);
	  }
	  if (fbuf_cnt > overlap) {
	    process_buffer(fbuf, fbuf_cnt-overlap);
	    memmove(fbuf, fbuf+fbuf_cnt-overlap, overlap*sizeof(fbuf[0]));
	    fbuf_cnt = overlap;
	  }
	}
	snd_pcm_close (capture_handle);
}

/* ---------------------------------------------------------------------- */

static void input_file(unsigned int sample_rate, unsigned int overlap,
		       const char *fname, const char *type)
{
	struct stat statbuf;
	int pipedes[2];
	int pid = 0, soxstat;
	int fd;
	int i;
	short buffer[8192];
	float fbuf[16384];
	unsigned int fbuf_cnt = 0;
	short *sp;

	/*
	 * if the input type is not raw, sox is started to convert the
	 * samples to the requested format
	 */
	if (!type || !strcmp(type, "raw")) {
		if ((fd = open(fname, O_RDONLY)) < 0) {
			perror("open");
			exit(10);
		}
	} else {
		if (stat(fname, &statbuf)) {
			perror("stat");
			exit(10);
		}
		if (pipe(pipedes)) {
			perror("pipe");
			exit(10);
		}
		if (!(pid = fork())) {
			char srate[8];
			/*
			 * child starts here... first set up filedescriptors,
			 * then start sox...
			 */
			sprintf(srate, "%d", sample_rate);
			close(pipedes[0]); /* close reading pipe end */
			close(1); /* close standard output */
			if (dup2(pipedes[1], 1) < 0) 
				perror("dup2");
			close(pipedes[1]); /* close writing pipe end */
			execlp("sox", "sox", 
			       "-t", type, fname,
			       "-t", "raw", "-s", "-w", "-r", srate, "-",
			       NULL);
			perror("execlp");
			exit(10);
		}
		if (pid < 0) {
			perror("fork");
			exit(10);
		}
		close(pipedes[1]); /* close writing pipe end */
		fd = pipedes[0];
	}
	/*
	 * demodulate
	 */
	for (;;) {
		i = read(fd, sp = buffer, sizeof(buffer));
		if (i < 0 && errno != EAGAIN) {
			perror("read");
			exit(4);
		}
		if (!i)
			break;
		if (i > 0) {
			for (; i >= sizeof(buffer[0]); i -= sizeof(buffer[0]), sp++)
				fbuf[fbuf_cnt++] = (*sp) * (1.0/32768.0);
			if (i)
				fprintf(stderr, "warning: noninteger number of samples read\n");
			if (fbuf_cnt > overlap) {
				process_buffer(fbuf, fbuf_cnt-overlap);
				memmove(fbuf, fbuf+fbuf_cnt-overlap, overlap*sizeof(fbuf[0]));
				fbuf_cnt = overlap;
			}
		}
	}
	close(fd);
	waitpid(pid, &soxstat, 0);
}

/* ---------------------------------------------------------------------- */

static const char usage_str[] = "multimod\n"
"Demodulates many different radio transmission formats\n"
"(C) 1996 by Thomas Sailer HB9JNX/AE4WA\n"
"Alsa Port 2016 by James Lee N1DDK\n"
"  -t <type>  : input file type (any other type than raw requires sox)\n"
"  -a <demod> : add demodulator\n"
"  -s <demod> : subtract demodulator\n"
"On Raspberry Pi with USB sound try something like\n"
"  bin-armv7l/multimon sysdefault:CARD=Device\n"
"or\n"
"  bin-armv7l/multimon sysdefault:CARD=Device_1\n" ;

void sighandler(int signum){
  printf("Multimon:: Caught signal %d, stopping...\n", signum);
  exit(1);
}

int main(int argc, char *argv[])
{
	int c;
	int errflg = 0;
	int i;
	char **itype;
	int mask_first = 1;
	int sample_rate = -1;
	unsigned int overlap = 0;
	char *input_type = "hw";
	signal(SIGINT, sighandler);
	signal(SIGTERM, sighandler);
	signal(SIGPIPE, sighandler);

	fprintf(stdout, "multimod  (C) 1996/1997 by Tom Sailer HB9JNX/AE4WA\n"
		"Alsa Port 2016 James Lee N1DDK\n"
		"available demodulators:");
	for (i = 0; i < NUMDEMOD; i++) 
		fprintf(stdout, " %s", dem[i]->name);
	fprintf(stdout, "\n");
	fflush(stdout);
	while ((c = getopt(argc, argv, "t:a:s:v:")) != EOF) {
		switch (c) {
		case '?':
			errflg++;
			break;

		case 'v':
			verbose_level = strtoul(optarg, 0, 0);
			break;

		case 't':
			for (itype = (char **)allowed_types; *itype; itype++) 
				if (!strcmp(*itype, optarg)) {
					input_type = *itype;
					goto intypefound;
				}
			fprintf(stderr, "invalid input type \"%s\"\n"
				"allowed types: ", optarg);
			for (itype = (char **)allowed_types; *itype; itype++) 
				fprintf(stderr, "%s ", *itype);
			fprintf(stderr, "\n");
			errflg++;
		intypefound:
			break;
		
		case 'a':
			if (mask_first)
				memset(dem_mask, 0, sizeof(dem_mask));
			mask_first = 0;
			for (i = 0; i < NUMDEMOD; i++)
				if (!strcasecmp(optarg, dem[i]->name)) {
					MASK_SET(i);
					break;
				}
			if (i >= NUMDEMOD) {
				fprintf(stderr, "invalid mode \"%s\"\n", optarg);
				errflg++;
			}
			break;

		case 's':
			if (mask_first)
				memset(dem_mask, 0xff, sizeof(dem_mask));
			mask_first = 0;
			for (i = 0; i < NUMDEMOD; i++)
				if (!strcasecmp(optarg, dem[i]->name)) {
					MASK_RESET(i);
					break;
				}
			if (i >= NUMDEMOD) {
				fprintf(stderr, "invalid mode \"%s\"\n", optarg);
				errflg++;
			}
			break;
			
		}
	}
	if (errflg) {
		(void)fprintf(stderr, usage_str);
		exit(2);
	}
	if (mask_first)
		memset(dem_mask, 0xff, sizeof(dem_mask));

	fprintf(stdout, "Enabled demodulators:");
	for (i = 0; i < NUMDEMOD; i++) 
		if (MASK_ISSET(i)) {
			fprintf(stdout, " %s", dem[i]->name);
			memset(dem_st+i, 0, sizeof(dem_st[i]));
			dem_st[i].dem_par = dem[i];
			if (dem[i]->init)
				dem[i]->init(dem_st+i);
			if (sample_rate == -1)
				sample_rate = dem[i]->samplerate;
			else if (sample_rate != dem[i]->samplerate) {
				fprintf(stdout, "\n");
				fprintf(stderr, "Error: Current sampling rate %d, "
					" demodulator \"%s\" requires %d\n",
					sample_rate, dem[i]->name, dem[i]->samplerate);
				exit(3);
			}
			if (dem[i]->overlap > overlap)
				overlap = dem[i]->overlap;
		}
	fprintf(stdout, "\n");

	if (!strcmp(input_type, "hw")) {
		if ((argc - optind) >= 1)
			input_sound(sample_rate, overlap, argv[optind]);
		else 
			input_sound(sample_rate, overlap, NULL);
		exit(0);
	}
	if ((argc - optind) < 1) {
		(void)fprintf(stderr, "no source files specified\n");
		exit(4);
	}
	for (i = optind; i < argc; i++)
		input_file(sample_rate, overlap, argv[i], input_type);
	exit(0);
}


/* ---------------------------------------------------------------------- */
