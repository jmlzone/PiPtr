#!/usr/bin/python3
# test program for finding sound card ports and connectiions
# program flow:
# 1) turn on power to usb audio section
# 2) wait 1 second for the USB bus to enumerate
# 3) list all audio devices with mics and speakers both
# Import all the libraries we need to run
import spidev
import RPi.GPIO as GPIO
import smbus
import alsaaudio
import threading
import time
import datetime
import sys
import os
import subprocess
import re
import hwio as HWIO

# this init of HWIO will turn on the USB power by default
#hwio=HWIO.hwio()
HWIO.i2cBus = smbus.SMBus(1)

HWIO.i2cBus.write_byte_data(HWIO.GPIOEX1, HWIO.IODIR,0)
HWIO.i2cBus.write_byte_data(HWIO.GPIOEX2, HWIO.IODIR,0)
HWIO.i2cBus.write_byte_data(HWIO.GPIOEX3, HWIO.IODIR,0)
# turn off sound cards
HWIO.i2cBus.write_byte_data(HWIO.GPIOEX3, HWIO.GPIOR,1)
# turn on sound card
HWIO.i2cBus.write_byte_data(HWIO.GPIOEX3, HWIO.GPIOR,0)
time.sleep(3)
c=alsaaudio.cards()
cardList = []
for i in range(len(c)) :
    m = alsaaudio.mixers(i)
    if ('Mic' in m and 'Speaker' in m) :
        print("Card %d: %s has both" % (i,c[i]))
        cardList.append(c[i])
        mix = alsaaudio.Mixer(control='Mic', cardindex=i)
        mix.setvolume(65,0, alsaaudio.PCM_CAPTURE)
# disable both port detects
HWIO.i2cBus.write_byte_data(HWIO.GPIOEX1, HWIO.GPIOR,1<<6)
HWIO.i2cBus.write_byte_data(HWIO.GPIOEX2, HWIO.GPIOR,1<<6)

#set playback to 50
mix = alsaaudio.Mixer(control='PCM', cardindex=0)
mix.setvolume(83,0, alsaaudio.PCM_PLAYBACK)
cardDict={}
d0 = threading.Thread(target=decodeTone, args=[cardList[0],cardDict])
d1 = threading.Thread(target=decodeTone, args=[cardList[1],cardDict])
d2 = threading.Thread(target=decodeTone, args=[cardList[2],cardDict])
d0.daemon = True
d0.start()
d1.daemon = True
d1.start()
d2.daemon = True
d2.start()

HWIO.i2cBus.write_byte_data(HWIO.GPIOEX1, HWIO.GPIOR,0) # enable detect 1
p=subprocess.Popen(['/usr/bin/aplay', '-D', 'sysdefault:CARD=ALSA', '../sounds/audiocheck.net_dtmf_1.wav'])
HWIO.i2cBus.write_byte_data(HWIO.GPIOEX1, HWIO.GPIOR,1<<6) # disable port 1
HWIO.i2cBus.write_byte_data(HWIO.GPIOEX2, HWIO.GPIOR,0) # enable port 2
p=subprocess.Popen(['/usr/bin/aplay', '-D', 'sysdefault:CARD=ALSA', '../sounds/audiocheck.net_dtmf_2.wav'])
HWIO.i2cBus.write_byte_data(HWIO.GPIOEX2, HWIO.GPIOR,1<<6) # disable port 2

HWIO.i2cBus.write_byte_data(HWIO.GPIOEX3, HWIO.GPIOR,6) # enable port 3 to both!




def decodeTone(card,cardDict):
    mmPath = '../bin/multimon'
    print("card %s : starting multimon %s" % (card, mmPath)) 
    try:
        p=subprocess.Popen([mmPath, 'sysdefault:CARD='+card, '-a', 'dtmf'], stdout=subprocess.PIPE)
    except:
        PRINT("Error could not start MultiMon on card %s",card)
    time.sleep(1)
    cardDict[card+'_p'] = p
    while(True) :
        txt = str(p.stdout.readline())
        dtmf = re.search(r'DTMF: (?P<tone>[0123456789ABCDEF])',txt)
        if(dtmf != None) :
            tone = dtmf.group('tone')
            p.terminate()
            cardDict[card] = tone
            break

