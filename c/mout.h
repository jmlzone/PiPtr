#define SAMPLE_RATE 22050
#define MS(x) ((float)(x)*SAMPLE_RATE/1000)

extern const int costabi[0x400];

#define COS(x) costabi[(((x)>>6)&0x3ffu)]
void mout(char * msg);

void write_buf(void);
void send_sample(int sample);
void gen_tone(int samples);
void gen_space(int samples);

