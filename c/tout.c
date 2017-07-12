#include "tout.h"
#include <stdio.h>
#include <stdlib.h>
#include <alsa/asoundlib.h>

int samples;
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

int main (int argc, char *argv[]) {
  int toneFreq;
  int dur;
  int i;
  if(argc < 5 ) {
    printf("must use more  arguments %d given\n", argc);
    printf("%s         device         freq amplitude duration [freq amplitude duration...]\n",argv[0]);
    printf("%s         default        660  10000     100 \n",argv[0]);
    printf("%s         default        660  10000     100 100 0 10 440 900 48\n",argv[0]);
    return EXIT_FAILURE;
  }
  unsigned int sampleRate = SAMPLE_RATE;
  int err;
  snd_pcm_hw_params_t *hw_params;

  buf_idx=0; 
  ph = 0;
  //  printf("trying to open %s\n", argv[1]);
  if ((err = snd_pcm_open (&playback_handle, argv[1], SND_PCM_STREAM_PLAYBACK, 0)) < 0) {
    fprintf (stderr, "cannot open audio device %s (%s)\n", 
	     argv[1],
	     snd_strerror (err));
    return EXIT_FAILURE;
  }
  //printf("success\n");
		   
  //printf("trying to Malloc\n");
  if ((err = snd_pcm_hw_params_malloc (&hw_params)) < 0) {
    fprintf (stderr, "cannot allocate hardware parameter structure (%s)\n",
	     snd_strerror (err));
    return EXIT_FAILURE;
  }
  //printf("success\n");
				 
  //printf("trying to initialize hardware params\n");				 
  if ((err = snd_pcm_hw_params_any (playback_handle, hw_params)) < 0) {
    fprintf (stderr, "cannot initialize hardware parameter structure (%s)\n",
	     snd_strerror (err));
    return EXIT_FAILURE;
  }
  //printf("success\n");
  
  //printf("trying to set access\n");	
  if ((err = snd_pcm_hw_params_set_access (playback_handle, hw_params, SND_PCM_ACCESS_RW_INTERLEAVED)) < 0) {
    fprintf (stderr, "cannot set access type (%s)\n",
	     snd_strerror (err));
    return EXIT_FAILURE;
  }
  //printf("success\n");
	
  //printf("trying to set format\n");
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
	
  for(i=0; i+4 < argc; i=i+3) { 
    toneFreq = atoi(argv[i+2]);
    phinc = (float)0x10000 * toneFreq / sampleRate;
    ampl = atoi(argv[i+3]);
    dur = atoi(argv[i+4]);
    samples = (sampleRate * dur) / 1000;
    printf("SampleRate = %d, Tone= %d, amplitude=%d, Samples = %d\n", sampleRate, toneFreq, ampl, samples);
    gen_tone(samples);
  }
  if(buf_idx != 0) {
    gen_tone(BUFLEN-buf_idx);
  }
  snd_pcm_drain (playback_handle);
  snd_pcm_close (playback_handle);
  return EXIT_SUCCESS;
  
}
