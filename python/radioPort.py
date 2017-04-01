#!/usr/bin/python
import time
import socket
import os.path
import RPi.GPIO as GPIO
import subprocess
import sys
import re
import signal
import threading
#import tail

from multiprocessing import Process, Value, Array, Queue

class gpTimer:
    def __init__(self, timeout, userHandler=None):  # timeout in seconds
        self.timeout = timeout
        self.expired = False
        self.isrunning = False
        self.handler = userHandler if userHandler is not None else self.defaultHandler
        self.timer = threading.Timer(self.timeout, self.handler)
        self.timer.start()
        self.isrunning = True
        
    def reset(self):
        self.timer.cancel()
        self.expired = False
        self.timer = threading.Timer(self.timeout, self.handler)
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
    def __init__(self, port):
        self.port = port # handle to parent
        self.pltone = 100.0
        self.id = "n0call"
        self.tail =  []
        self.timeout = 3600 # 1 hour max tx up continously
        self.taildly = 0.5 # seconds
        self.txupdly = 1 # seconds When coming up to beacon, delay bedore sending
        self.hangtime = 1 #seconds
        self.idtime = 300 # seconds
        self.polite = 30
        self.disable = False
        self.TailMessagesDone = False
        self.txPinLvl = 1
        if(self.port.portnum == 1) :
            self.pttPin = 12
        else :
            self.pttPin = 22

        GPIO.setup(self.pttPin, GPIO.OUT)
        GPIO.output(self.pttPin,(not self.txPinLvl))
        self.timeoutTimer = gpTimer(self.timeout)
        self.tailTimer = gpTimer(self.taildly)
        self.hangTimer = gpTimer(self.hangtime)
        self.idTimer = gpTimer(self.idtime)
        self.politeIdTimer = gpTimer(self.idtime - self.polite)
        self.tailPid=None
        self.idPid=None
        #self.tail_msg = tail.tail_msg(self.port.card)
        self.beepMethod = 2 # 0=none, 1=tone, 2=wave 3=morse
        self.beepTone = "660 5000 30 440 5000 30 1000 5000 30"
        self.tailBeepWav = './sounds/Tink.wav'
        self.beepMorse = "20 440 5000 beep"
        self.xmlvars = ( 'pltone', 'id', 'idtime', 'polite', 'timeout',
                         'taildly', 'hangtime', 'disable', 'txupdly',
                         'txPinLvl', 'beepMethod', 'beepTone',
                         'tailBeepWav', 'beepMorse') # data to store in xml config

    def add_tail_msg(self, method,msg,cancelable,isid,requeue,alt):
        #self.tail_msg.add(method,msg,cancelable,isid,requeue,alt)
        False

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
        #id_played = self.tail_msg.play()
        if(id_played) :
            self.politeIdTimer.reset()
            self.idTimer.reset()
        if(self.politeIdTimer.expired) :
            self.sendId()
        self.TailMessagesDone = True

    def sendId(self) :
        self.idPid = subprocess.Popen(['./bin/mout', self.port.card, '20', '660', '5000', self.id])
        self.politeIdTimer.reset()
        self.idTimer.reset()

    def tailbeep(self) :
        if(self.beepMethod == 1) : # tone
            args = ['./bin/tout',self.port.card] + self.beepTone.split()
            print args
            beepPid = subprocess.call(args)
        elif(self.beepMethod == 2) : # wave
            beepPid = subprocess.Popen(['/usr/bin/aplay', '-D', self.port.card, self.tailBeepWav])
        elif(self.beepMethod == 3) : # morse
            args = ['./bin/mout',self.port.card] + self.beepMorse.split()
            print args
            beepPid = subprocess.call(args)
        else : # none
            return

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
    def __init__(self, port, q):
        self.port = port # handle to parent port
        self.q = q
        self.cor = 0
        self.plDet = 0
        self.idle_timer = 0
        self.busy_timer = 0
        self.kerchunk_timer = 0
        self.anti_kerchunk = False
        self.timeout = 180     # seconds
        self.IdleTimeout = 600 # seconds
        self.disabled = False
        self.expired = False
        self.idle = True
        self.useCtcssPin = True
        self.ctcssPinLvl = 0
        self.useCorPin = True
        self.corPinLvl = 0
        self.rxActive = threading.Event()
        self.useSoftCtcss = False
        self.ctcssAct = [ 0, 0, 0, 0, 0, 0, 0, 0]
        self.softCtcssAllow = [ 0, 0, 0, 0, 0, 0, 0, 0]
        self.softCtcssCmd   = [ 0, 0, 0, 0, 0, 0, 0, 0]
        self.cmdMode = False

        if(self.port.portnum == 1) :
            self.corPin = 11
            self.ctcssPin = 13
        else :
            self.corPin = 16
            self.ctcssPin = 18
            
        GPIO.setup(self.ctcssPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.corPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        self.timer = gpTimer(self.timeout)
        self.idleTimer = gpTimer(self.IdleTimeout)
        self.xmlvars = ('timeout', 'IdleTimeout', 'disabled', 'useCtcssPin',
                     'ctcssPinLvl', 'useCorPin', 'corPinLvl', 'useSoftCtcss',
                     'softCtcssAllow', 'softCtcssCmd', 'cmdMode')

    def ctcss(self):
        if(GPIO.input(self.ctcssPin) == self.ctcssPinLvl) :
            rx = True
        else :
            rx = False
        return(rx)

    def active(self):
        if(GPIO.input(self.corPin) == self.corPinLvl or self.useCorPin == False) :
            if(self.useCtcssPin):
                rx=self.ctcss()
            else:
                rx = True
        else :
            rx = False
        return(rx)

    def update(self):
        ctcssCmd = False
        softCtcss = False
        if(self.useSoftCtcss) :
            for i in range(8) :
                if( softCtcss[i] and self.softCtcssAllow[i] ) :
                     softCtcss = True
                if( softCtcss[i] and self.softCtcssCmd[i] ) :
                    ctcssCmd[i] = True
        if(softCtcss or self.useSoftCtcss == False):
            rx = active()
        if( rx ) :
            self.rxActive.set()
        else :
            self.rxActive.clear()

        if(ctcssCmd) :
           self.cmdMode = True
           self.cmdTimer.Reset()

    def soft_decode (self,q):
        p=subprocess.Popen(['./bin/multimon', self.port.card, '-a', 'dtmf', '-a', 'ctcss'], stdout=subprocess.PIPE)
        time.sleep(1)
        while(True) :
            txt = p.stdout.readline()
            ctcss = re.search(r'CTCSS (?P<state>[DL]): (?P<num>\d)',txt)
            dtmf = re.search(r'DTMF: (?P<tone>[0123456789ABCDEF])',txt)
            if(ctcss != None) :
                self.ctcssAct[int(ctcss.group('num'))] = (ctcss.group('state') == 'D')
                self.update() # update the RX status
            if(dtmf != None) :
                q.put(dtmf.group('tone'))

    def run(self) :
        self.sd = threading.Thread(target=self.softdecode, args=(q))
        self.sd.daemon = True
        self.sd.start()


class radioPort :
    """ The port class has a reciever and a transmitter and houses any common data 
    it has multiple threads.
    The soft deode thread runs multimon to decode PL and DTMF
    The ctcss pin and cor pins are handled by interups.
    """
    def __init__(self, portnum,q) :
        self.portnum = portnum
        if(portnum == 1 ) :
            self.card = "sysdefault:CARD=Device"
        elif (portnum == 2 ) :
            self.card = "sysdefault:CARD=Device_1"
        else :
            self.card = "sysdefault"
        
        self.islink = False
        self.linkstate = 0; 
        self.q = q;
        self.rx = rx(self,q) # self passed in is the port instance for parent refences to this data
        self.tx = tx(self)
        self.xmlvars = ( 'card', 'islink', 'linkstate')

        
    
        
def stopALL(signum, frame):
    print 'SoftDecode Stoping, Shutting down', signum
    #p.terminate()
    sys.exit(1)
