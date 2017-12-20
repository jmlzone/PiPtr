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
import Adafruit_DHT

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
            cardDict[tone] = card
            print("detected tone %s on card %s" % (tone,card))
            break

# this init of HWIO will turn on the USB power by default
#hwio=HWIO.hwio()
# setup the pwms for audio out
p=subprocess.Popen(['../bin/gpio_alt','-p','18','-f','5'])
p=subprocess.Popen(['../bin/gpio_alt','-p','19','-f','5'])
HWIO.i2cBus = smbus.SMBus(1)

HWIO.i2cBus.write_byte_data(HWIO.GPIOEX1, HWIO.IODIR,0)
HWIO.i2cBus.write_byte_data(HWIO.GPIOEX2, HWIO.IODIR,0)
HWIO.i2cBus.write_byte_data(HWIO.GPIOEX3, HWIO.IODIR,0)
# turn on sound card
print("turning on sound cards")
HWIO.i2cBus.write_byte_data(HWIO.GPIOEX3, HWIO.GPIOR,0)
c=[]
i=0
while( i<10 and len(c) <4) :
    time.sleep(1)
    i=i+1
    c=alsaaudio.cards()
    print("%d: have %d cards" % (i,len(c)))
cardList = []
for i in range(len(c)) :
    m = alsaaudio.mixers(i)
    if ('Mic' in m and 'Speaker' in m) :
        print("Card %d: %s has both" % (i,c[i]))
        cardList.append(c[i])
        mix = alsaaudio.Mixer(control='Mic', cardindex=i)
        mix.setvolume(65,0, alsaaudio.PCM_CAPTURE)
        mix = alsaaudio.Mixer(control='Speaker', cardindex=i)
        mix.setvolume(24,0, alsaaudio.PCM_PLAYBACK)
        mix.setvolume(24,1, alsaaudio.PCM_PLAYBACK)
# disable both port detects
print("preparing for port detection")
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

print("Detecting port 1")
HWIO.i2cBus.write_byte_data(HWIO.GPIOEX1, HWIO.GPIOR,0) # enable detect 1
p=subprocess.Popen(['/usr/bin/aplay', '-D', 'sysdefault:CARD=ALSA', '../sounds/audiocheck.net_dtmf_1.wav'])
time.sleep(2)
HWIO.i2cBus.write_byte_data(HWIO.GPIOEX1, HWIO.GPIOR,1<<6) # disable port 1
print("Detecting port 2")
HWIO.i2cBus.write_byte_data(HWIO.GPIOEX2, HWIO.GPIOR,0) # enable port 2
p=subprocess.Popen(['/usr/bin/aplay', '-D', 'sysdefault:CARD=ALSA', '../sounds/audiocheck.net_dtmf_2.wav'])
time.sleep(2)
HWIO.i2cBus.write_byte_data(HWIO.GPIOEX2, HWIO.GPIOR,1<<6) # disable port 2
p3=[]
p3.append(cardList[0])
p3.append(cardList[1])
p3.append(cardList[2])
p3.remove(cardDict['1'])
p3.remove(cardDict['2'])
c3=p3[0]

print("Detecting port 3")
HWIO.i2cBus.write_byte_data(HWIO.GPIOEX3, HWIO.GPIOR,6) # enable port 3 to both!
p=subprocess.Popen(['/usr/bin/aplay', '-D', 'sysdefault:CARD='+c3, '../sounds/audiocheck.net_dtmf_3.wav'])
time.sleep(2)

for card in cardList :
    cardDict[card+'_p'].kill()
    cardDict[card+'_p'].poll()

card1 = "sysdefault:CARD=" + cardDict['1']
card2 = "sysdefault:CARD=" + cardDict['2']
card3 = "sysdefault:CARD=" + cardDict['3']

print("completed card detection, ordered cards are")
print(card1)
print(card2)
print(card3)

th = HWIO.DHT(7)
(hum,temp) = th.measure()
if(temp) :
    print("Temperature: %3.1f" % temp)
if(self.hum) :
    print("Humidity: %3.1f" % hum)


HWIO.spi = spidev.SpiDev()
adc = [HWIO.adcChan(HWIO.spi,0,(2.048/1024.0),0,2),
       HWIO.adcChan(HWIO.spi,1,(20.48/1024.0),12.4,13.6),
       HWIO.adcChan(HWIO.spi,2,(20.48/1024.0),0,20),
       HWIO.adcChan(HWIO.spi,3,(20.48/1024.0),0,20),
       HWIO.adcChan(HWIO.spi,4,(20.48/1024.0),0,20),
       HWIO.adcChan(HWIO.spi,5,(20.48/1024.0),0,20),
       HWIO.adcChan(HWIO.spi,6,(100.0/1024.0),0,20),
       HWIO.adcChan(HWIO.spi,7,(20.48/1024.0),11.0,13.9)]

GPIO.setmode(GPIO.BOARD)
selPins = [32, 31, 29]
GPIO.setup(selPins, GPIO.OUT)
GPIO.output(selPins, [1,1,1])
for c in range(8) :
    adc[c].measure()
    print(" ADC[%d] = %0.2f" %(c,adc[c].val))

