#include "mout.h"
#include <stdio.h>
#include <stdlib.h>
#include <alsa/asoundlib.h>

const unsigned char mlookup[] = {115  /*,--..--*/ ,1   /*-*/ ,
  106 /*..-.-.-*/ ,41  /*/-..-.*/ ,63  /*0-----*/ ,62  /*1.----*/ ,
  60  /*2..---*/ ,56  /*3...--*/ ,48  /*4....-*/ ,32  /*5.....*/ ,
  33  /*6-....*/ ,35  /*7--...*/ ,39  /*8---..*/ ,47  /*9----.*/ ,
  1   /*:*/ ,1   /*;*/ ,1   /*<*/ ,49  /*=-...-*/ ,1   /*>*/ ,
  76  /*?..--..*/ ,1   /*@*/ ,6   /*A.-*/ ,17  /*B-...*/ ,21  /*C-.-.*/ ,
  9   /*D-..*/ ,2   /*E.*/ ,20  /*F..-.*/ ,11  /*G--.*/ ,16  /*H....*/ ,
  4   /*I..*/ ,30  /*J.---*/ ,13  /*K-.-*/ ,18  /*L.-..*/ ,7   /*M--*/ ,
  5   /*N-.*/ ,15  /*O---*/ ,22  /*P.--.*/ ,27  /*Q--.-*/ ,10  /*R.-.*/ ,
  8   /*S...*/ ,3   /*T-*/ ,12  /*U..-*/ ,24  /*V...-*/ ,14  /*W.--*/ ,
  25  /*X-..-*/ ,29  /*Y-.--*/ ,19  /*Z--..*/};

int elesamples;
#define DIT elesamples
#define DAH DIT*3
#define WSPACE DIT*6
#define BUFLEN 128
#define CHAN 1
int ch_idx;
int ph;
int phinc;
int samples;
int ampl;
short buf[BUFLEN * CHAN];
snd_pcm_t *playback_handle;
int buf_idx;
int err;

/*----------------------------------------------------------------------
  mout Morse Output 
----------------------------------------------------------------------*/
void mout(char * msg){
  int i = 0;
  int cindex;
  int mchar;
  while (msg[i] != 0) {
    cindex = msg[i] & 0x7f; //remove any parity
    if(cindex <= 'z'){
      if(cindex >= 'a') cindex = cindex-0x20; // make upper case
      cindex = cindex - ','; // comma is zero based in the table
      if(cindex <0) { // a space
	gen_space(WSPACE);
      } else { // send the charater from the lookup table
	mchar = mlookup[cindex];
	while(mchar !=1) {
	  //ON
	  if(mchar & 0x01) {// test lsb
	    gen_tone(DAH);
	  } else {
	    gen_tone(DIT);
	  }
	  //OFF
	  gen_space(DIT);
	  mchar = mchar >>1; // shift down the bits
	}
      }
    }
    gen_space(DAH);
    i++; // move to next char
  }
}
void write_buf(void){
    if ((err = snd_pcm_writei (playback_handle, buf, BUFLEN)) != BUFLEN) {
      fprintf (stderr, "write to audio interface failed (%s)\n",
	       snd_strerror (err));
      exit(EXIT_FAILURE);
    }
}
void send_sample(int sample) {
  int i;
  for (i=0; i<CHAN; i++){
    buf[buf_idx++] = sample;
    if( buf_idx == BUFLEN) {
      write_buf();
      buf_idx=0;
    }
  }
}
void gen_tone(int samples){
  int i;
  for (i=0; i<samples; i++){
    send_sample((ampl * COS(ph)) >> 15);
    ph += phinc;
  }
}

void gen_space(int samples){
  int i;
  for (i=0; i<samples; i++){
    send_sample(0);
  }
}

int main (int argc, char *argv[]) {
  int wpm;
  int toneFreq;
  char *msg;
  if(argc != 6) {
    printf("must use exactly 6 arguments %d given\n", argc);
    printf("%s         device        wpm freq amplitude message (in quotes)\n",argv[0]);
    printf("%s         default       22  660  10000     \"test \"\n",argv[0]);
    return EXIT_FAILURE;
  }

  wpm = atoi(argv[2]);
  toneFreq = atoi(argv[3]);
  ampl = atoi(argv[4]);
  msg = argv[5];
  unsigned int sampleRate = 22050;
  float elelen = 92.31 * 13.0 / (float) wpm;
  elesamples = (int) ((float) sampleRate * elelen /1000.0);
  int err;
  snd_pcm_hw_params_t *hw_params;

  buf_idx=0; 
  ph = 0;
  phinc = (float)0x10000 * toneFreq / sampleRate;
  //  printf("trying to open %s\n", argv[1]);
  if ((err = snd_pcm_open (&playback_handle, argv[1], SND_PCM_STREAM_PLAYBACK, 0)) < 0) {
    fprintf (stderr, "cannot open audio device %s (%s)\n", 
	     argv[1],
	     snd_strerror (err));
    return EXIT_FAILURE;
  }

  if ((err = snd_pcm_hw_params_malloc (&hw_params)) < 0) {
    fprintf (stderr, "cannot allocate hardware parameter structure (%s)\n",
	     snd_strerror (err));
    return EXIT_FAILURE;
  }
				 
  if ((err = snd_pcm_hw_params_any (playback_handle, hw_params)) < 0) {
    fprintf (stderr, "cannot initialize hardware parameter structure (%s)\n",
	     snd_strerror (err));
    return EXIT_FAILURE;
  }
	
  if ((err = snd_pcm_hw_params_set_access (playback_handle, hw_params, SND_PCM_ACCESS_RW_INTERLEAVED)) < 0) {
    fprintf (stderr, "cannot set access type (%s)\n",
	     snd_strerror (err));
    return EXIT_FAILURE;
  }

  if ((err = snd_pcm_hw_params_set_format (playback_handle, hw_params, SND_PCM_FORMAT_S16_LE)) < 0) {
    fprintf (stderr, "cannot set sample format (%s)\n",
	     snd_strerror (err));
    return EXIT_FAILURE;
  }
	
  if ((err = snd_pcm_hw_params_set_rate_near (playback_handle, hw_params, &sampleRate, 0)) < 0) {
    fprintf (stderr, "cannot set sample rate (%s)\n",
	     snd_strerror (err));
    return EXIT_FAILURE;
  }
	
  if ((err = snd_pcm_hw_params_set_channels (playback_handle, hw_params, CHAN)) < 0) {
    fprintf (stderr, "cannot set channel count (%s)\n",
	     snd_strerror (err));
    return EXIT_FAILURE;
  }
	
  if ((err = snd_pcm_hw_params (playback_handle, hw_params)) < 0) {
    fprintf (stderr, "cannot set parameters (%s)\n",
	     snd_strerror (err));
    return EXIT_FAILURE;
  }
	
  snd_pcm_hw_params_free (hw_params);
	
  if ((err = snd_pcm_prepare (playback_handle)) < 0) {
    fprintf (stderr, "cannot prepare audio interface for use (%s)\n",
	     snd_strerror (err));
    return EXIT_FAILURE;
  }
  printf("SampleRate = %d, wpm = %d eleSamples = %d\n", sampleRate, wpm, elesamples);
	
  mout(msg);
  if(buf_idx != 0) {
    gen_space(BUFLEN-buf_idx);
  }
  snd_pcm_drain (playback_handle);
  snd_pcm_close (playback_handle);
  return EXIT_SUCCESS;
  
}
