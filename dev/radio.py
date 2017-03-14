#!/usr/bin/python
import time
import socket
import os.path
import RPi.GPIO as GPIO
import subprocess
import sys
from threading import Timer
import tail
from multiprocessing import Process, Value, Array, Queue

class gpTimer:
    def __init__(self, timeout, userHandler=None):  # timeout in seconds
        self.timeout = timeout
        self.expired = False
        self.isrunning = False
        self.handler = userHandler if userHandler is not None else self.defaultHandler
        self.timer = Timer(self.timeout, self.handler)
        self.timer.start()
        self.isrunning = True
        
    def reset(self):
        self.timer.cancel()
        self.expired = False
        self.timer = Timer(self.timeout, self.handler)
        self.timer.start()
        self.isrunning = True
        
    def run(self):
        if(not self.isrunning) :
            self.reset()

    def stop(self):
        self.timer.cancel()
        self.isrunning = False
        self.expired = False
        
    def defaultHandler(self):
        self.expired = True
        self.isrunning = False
        #print "default handler called"
        #raise self



class tx:
    """ class describing a transmitter """
    """ Has timers 
            ID timer
            Time out timer
            tail delay timer
            hang timer
    """
    def __init__(self, port, islink, pl, id, idtime, polite, timeout, taildly, hangtime):
        self.port = port
        self.islink = islink
        self.pltone = pl
        self.id = id
        self.tail =  []
        self.timeout = timeout
        self.taildly = taildly
        self.hangtime = hangtime
        self.idtime = idtime
        self.polite = polite
        self.disable = False
        self.TailMessagesDone = False
        self.txPinLvl = 1
        if(port == 0) :
            self.pttPin = 12
            self.card = 'sysdefault:CARD=Device'

        GPIO.setup(self.pttPin, GPIO.OUT)
        GPIO.output(self.pttPin,(not self.txPinLvl))
        self.timeoutTimer = gpTimer(self.timeout)
        self.tailTimer = gpTimer(self.taildly)
        self.hangTimer = gpTimer(self.hangtime)
        self.idTimer = gpTimer(self.idtime)
        self.politeIdTimer = gpTimer(self.idtime - self.polite)
        self.tailPid=None
        self.idPid=None
        self.tail_msg = tail.tail_msg(self.card)
        self.tailBeepWav = './sounds/Tink.wav'

    def add_tail_msg(self, method,msg,cancelable,isid,requeue,alt):
        self.tail_msg.add(method,msg,cancelable,isid,requeue,alt)

    def tx(self) :
        if( not self.disable) :
            #self.port.startPl(pltone)
            #self.port.tx_enable()
            self.timeoutTimer.reset()
            GPIO.output(self.pttPin,self.txPinLvl)
    def down(self):
        GPIO.output(self.pttPin,(not self.txPinLvl))
        self.timeoutTimer.stop()

 #   def startTailMessages(self) :
 #       self.TailMessagesDone = False
 #       try:
 #           self.tailpid = Process(target=self.runTailMessages)
 #       except:
 #           print "Could not launch tail messages"
 #           self.TailMessagesDone = True            
 
    def runTailMessages(self) :
        self.TailMessagesDone = False
        id_played = self.tail_msg.play()
        if(id_played) :
            self.politeIdTimer.reset()
            self.idTimer.reset()
        if(self.politeIdTimer.expired) :
            self.sendId()
        self.TailMessagesDone = True

    def sendId(self) :
        self.idPid = subprocess.Popen(['./bin/mout', self.card, '20', '660', '5000', self.id])
        self.politeIdTimer.reset()
        self.idTimer.reset()

    def tailbeep(self) :
        beepPid = subprocess.Popen(['/usr/bin/aplay', '-D', self.card, self.tailBeepWav])

    def idRunning(self):
        if(self.idPid) :
            self.idPid.poll()
            if(self.idPid.returncode == None) :
                return True
            else :
                return False
        else :
            return True

class rx:
    """ class describing a receiver """
    def __init__(self, port, islink, pl, timeout, IdleTimeout):
        self.port = port
        self.linked = 0
        self.cor = 0
        self.plDet = 0
        self.idle_timer = 0
        self.busy_timer = 0
        self.kerchunk_timer = 0
        self.anti_kerchunk = 0
        self.timeout = timeout
        self.IdleTimeout = IdleTimeout
        self.disable = False
        self.expired = False
        self.idle = True
        self.useCtcssPin = True
        self.ctcssPinLvl = 0
        self.corPinLvl = 0
        if(port == 0) :
            self.corPin = 11
            self.ctcssPin = 13
        GPIO.setup(self.ctcssPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.corPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        self.timer = gpTimer(self.timeout)
        self.idleTimer = gpTimer(self.IdleTimeout)

    def active(self):
        if(GPIO.input(self.corPin) == self.corPinLvl) :
            if(self.useCtcssPin):
                rx=self.ctcss()
            else:
                rx = True
        else :
            rx = False
        return(rx)

    def ctcss(self):
        if(GPIO.input(self.ctcssPin) == self.ctcssPinLvl) :
            rx = True
        else :
            rx = False
        return(rx)


        
        
    
        
