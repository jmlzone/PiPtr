#!/usr/bin/python
import time
import socket
import os.path
import RPi.GPIO as GPIO
import subprocess
import sys
from threading import Timer
import radio
import soft_decode
import audioCtl as AC
import datetime
import signal, os
import code
import re
from multiprocessing import Process, Value, Array, Queue


def hup_handler(signum, frame):
    print 'Hup interrupt, Going interactive', signum
    code.interact(local=dict(globals(), **locals()))

def int_handler(signum, frame):
    global p0
    print 'Int interrupt, Shutting down', signum
    tx0.down()
    GPIO.cleanup()
    p0.terminate()
    exit(-1)

signal.signal(signal.SIGHUP, hup_handler)
signal.signal(signal.SIGINT, int_handler)

cmdlist =[("123$","test123"), # the $ at the end forces an exact match
          ("456","test456"),
          ("789","test789")]
cmdlist = cmdlist + [("123(\d+)", "cmdWithArg")] # rexexp type argument needed 1 ore more decimal digits.
cmdlist = cmdlist + [("DDDDD", "rptDown")]
cmd0 = ""

def test123():
    print "test123"
    tx0.tailBeepWav = './sounds/Tink.wav'
    sys.stdout.flush()

def test456():
    print "test456"
    tx0.tailBeepWav = './sounds/Submarine.wav'
    sys.stdout.flush()

def test789():
    print "test789"
    tx0.tailBeepWav = './sounds/Glass.wav'
    sys.stdout.flush()

def cmdWithArg(arg):
    print "command got %d" %arg
    sys.stdout.flush()

def rptDown():
    global p0
    print "Shutting down"
    tx0.down()
    GPIO.cleanup()
    p0.terminate()
    exit(-1)


def talkingClock(prefix = 'its'):
    dt = datetime.datetime.now()
    ds = dt.strftime("%I %M %p, %A %B %_d")
    myTime = prefix + " "+ ds
    os.environ['ALSA_CARD'] = 'Device'
    subprocess.call(['/usr/bin/espeak', myTime], shell=False)

def logit(msg) :
    dt = datetime.datetime.now()
    ds = dt.strftime("%B %d, %Y %I:%M:%S%p")
    print ds + " - " + msg
    sys.stdout.flush()

def runCmd():
    global cmd0
    global cmdlist
    if(len(cmd0) >0) :
        found = 0
        for c in cmdlist :
            print c
            (name,func) = c
            m = re.match(name,cmd0)
            if(m != None) :
                found = 1
                if(len(m.groups()) ==1) :
                    result = eval(func+"("+m.group(1)+")")
                else:
                    result = eval(func+"()")
                    break
        if(not found) :
            print "oops not found" # que no sound
    cmd0=""

tcon = 0x1ff
def muterx(onoff) :
    global tcon
    if(onoff) : #true = start muting
        tcon = tcon &  0x1df # bit 5 is b wiper disconnect.
    else :
        tcon = tcon | 0x20
    AC.WriteTcon(0,tcon)

# main program starts here
GPIO.setmode(GPIO.BOARD)
rx0=radio.rx(0,False,103.5,180,600)
tx0=radio.tx(0,False,103.5,"N1DDK/R",300,30,3600,0.5,1)
n0=Value('i',99)
ctcss_arr0 = Array('b', range(8))
q0 = Queue()
for i in range(len(ctcss_arr0)):
    ctcss_arr0[i] = False
p0=Process( target=soft_decode.soft_decode, args=('sysdefault:CARD=Device', n0, ctcss_arr0,q0))
p0.start()

state0= 'idle'
lastState = None
logit("Startup")
rx0.idleTimer.reset()
# audio config 
AC.WriteRes(0,150)
AC.WriteRes(1,2)
AC.WriteRes(2,50)
AC.WriteRes(3,20)
AC.WritePGAGain(6)
#
tx0.tx()
time.sleep(1)
logit("Initial ID")
tx0.sendId()
time.sleep(1)
tx0.idPid.wait()
time.sleep(1)
logit("Initial Clock")
talkingClock("Start up at")
time.sleep(1)

tx0.down()
logit("Startup Done.")

while(1) :
    time.sleep(0.010)
    # look at received touch tone codes.
    while(not q0.empty()):
        tone = q0.get()
        cmd0 = cmd0 + tone
        print tone
    if(state0 != lastState):
        logit(state0)
        lastState = state0
        runCmd()
    if(state0 == 'idle'):
        if(rx0.active()) :
            rx0.timer.reset()
            tx0.tx()
            rx0.idleTimer.stop()
            tx0.idTimer.run()
            tx0.politeIdTimer.run()
            state0 = 'rpt'
        elif(tx0.idTimer.expired) :
            state0 = 'beacon_id'
        elif(rx0.idleTimer.expired) :
            rx0.idleTimer.expired = False
            # method,msg,cancelable,isid,requeue,alt
            tx0.add_tail_msg(['/usr/bin/aplay', '-D'], './sounds/idle.wav', True, True, False, None)
                
    elif (state0 == 'rpt'):
        if(rx0.timer.expired) :
            state0 = 'timeoutenter'
        elif( not rx0.active()):
            state0 = 'taildelay'
            tx0.tailTimer.reset()
    elif (state0 == 'timeoutenter'):
        tx0.down()
        state0 = 'timeoutwait'
    elif (state0 == 'timeoutwait'):
        if(not rx0.active):
            state0 == 'taildelay'
            tx0.tx()
            tx0.tailTimer.reset()
    elif (state0 == 'taildelay'):
        if(rx0.active()):
            state0 = 'rpt'
        elif (tx0.tailTimer.expired) :
            state0 = 'tailmessages'
            tx0.runTailMessages()
            #tx0.startTailMessages()
    elif (state0 == 'tailmessages'):
        if(tx0.TailMessagesDone and not tx0.idRunning() and not rx0.active()):
            state0 = 'tailreset'
        elif (rx0.active()) :
            state0 = 'rpt'
    elif (state0 == 'tailreset'):
        tx0.tailbeep()
        rx0.timer.reset()
        tx0.hangTimer.reset()
        state0 = 'tailhang'
    elif (state0 == 'tailhang'):
        if(rx0.active()):
            state0 = 'rpt'
        elif(tx0.hangTimer.expired) :
            state0 = 'txoff'
    elif (state0 == 'txoff'):
        tx0.down()
        state0 = 'idle'
        rx0.idleTimer.reset()
    elif (state0 == 'beacon_id'):
        tx0.tx()
        tx0.sendId()
        state0 = 'beacon_finish'
    elif (state0 == 'beacon_finish'):
        if(not tx0.idRunning()):
            tx0.down()
            tx0.idTimer.stop()
            state0 = 'idle'
