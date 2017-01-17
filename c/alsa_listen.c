	#include <stdio.h>
	#include <stdlib.h>
	#include <alsa/asoundlib.h>
	      
	main (int argc, char *argv[])
	{
		int i;
		int j;
		int err;
		short buf[128];
		snd_pcm_t *capture_handle;
		snd_pcm_hw_params_t *hw_params;
	
		printf("trying to open %s\n", argv[1]);
		if ((err = snd_pcm_open (&capture_handle, argv[1], SND_PCM_STREAM_CAPTURE, 0)) < 0) {
			fprintf (stderr, "cannot open audio device %s (%s)\n", 
				 argv[1],
				 snd_strerror (err));
			exit (1);
		}
		printf("success\n");
		   
		printf("trying to Malloc\n");
		if ((err = snd_pcm_hw_params_malloc (&hw_params)) < 0) {
			fprintf (stderr, "cannot allocate hardware parameter structure (%s)\n",
				 snd_strerror (err));
			exit (1);
		}
		printf("success\n");
				 
		printf("trying to initialize hardware params\n");
		if ((err = snd_pcm_hw_params_any (capture_handle, hw_params)) < 0) {
			fprintf (stderr, "cannot initialize hardware parameter structure (%s)\n",
				 snd_strerror (err));
			exit (1);
		}
		printf("success\n");
	
		printf("trying to set access\n");
		if ((err = snd_pcm_hw_params_set_access (capture_handle, hw_params, SND_PCM_ACCESS_RW_INTERLEAVED)) < 0) {
			fprintf (stderr, "cannot set access type (%s)\n",
				 snd_strerror (err));
			exit (1);
		}
		printf("success\n");
	
		printf("trying to set format\n");
		if ((err = snd_pcm_hw_params_set_format (capture_handle, hw_params, SND_PCM_FORMAT_S16_LE)) < 0) {
			fprintf (stderr, "cannot set sample format (%s)\n",
				 snd_strerror (err));
			exit (1);
		}
		printf("success\n");
		unsigned int sampleRate=44100;
		printf("trying to set rate\n");
		if ((err = snd_pcm_hw_params_set_rate_near (capture_handle, hw_params, &sampleRate, 0)) < 0) {
			fprintf (stderr, "cannot set sample rate (%s)\n",
				 snd_strerror (err));
			exit (1);
		}
		printf("success\n");
	
		printf("trying to get channel count\n");
		if ((err = snd_pcm_hw_params_set_channels (capture_handle, hw_params, 1)) < 0) {
			fprintf (stderr, "cannot set channel count (%s)\n",
				 snd_strerror (err));
			exit (1);
		}
		printf("success\n");
	
		printf("trying to set paramaters\n");
		if ((err = snd_pcm_hw_params (capture_handle, hw_params)) < 0) {
			fprintf (stderr, "cannot set parameters (%s)\n",
				 snd_strerror (err));
			exit (1);
		}
	
		printf("trying to free\n");
		snd_pcm_hw_params_free (hw_params);
	
		printf("trying to prepare\n");
		if ((err = snd_pcm_prepare (capture_handle)) < 0) {
			fprintf (stderr, "cannot prepare audio interface for use (%s)\n",
				 snd_strerror (err));
			exit (1);
		}
		printf("success\n");
	

		printf("trying to capture 10 packets\n");
		for (i = 0; i < 10; ++i) {
			if ((err = snd_pcm_readi (capture_handle, buf, 128)) != 128) {
				fprintf (stderr, "read from audio interface failed (%s)\n",
					 snd_strerror (err));
				exit (1);
			}
			for (j=0; j<128; j++) {
			  printf("%4d, %d\n",j,buf[j]);
			}
		}
		printf("success\n");
	
		snd_pcm_close (capture_handle);
		exit (0);
	}
