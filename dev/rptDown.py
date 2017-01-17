#!/usr/bin/python
import time
import socket
import os.path
import RPi.GPIO as GPIO
import subprocess
import sys
from threading import Timer
import radio
#import soft_decode
import audioCtl as AC

def talkingClock():
    os.environ['ALSA_CARD'] = 'Device'
    myTime = subprocess.check_output(['/bin/date', '+"shutting down at  %I %M %p, %A %B %_d"'])
    subprocess.call(['/usr/bin/espeak', myTime], shell=False)

# main program starts here
GPIO.setmode(GPIO.BOARD)
tx0=radio.tx(0,False,103.5,"N1DDK/R",590,30,3600,1,2)
state0= 'idle'
AC.WriteRes(0,100)
AC.WriteRes(1,100)
AC.WriteRes(2,20)
AC.WriteRes(3,128)
tx0.tx()
time.sleep(1)
tx0.sendId()
time.sleep(1)
tx0.idPid.wait()
time.sleep(1)
talkingClock()
time.sleep(1)

tx0.down()
AC.spi.close()
tx0.timeoutTimer.stop()
tx0.tailTimer.stop()
tx0.hangTimer.stop()
tx0.idTimer.stop()
tx0.politeIdTimer.stop()
if(tx0.idPid and tx0.idPid.returncode==None) :
    tx0.idPid.kill()
GPIO.cleanup
