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
import rptFsm

from multiprocessing import Process, Value, Array, Queue
class tx:
    """ class describing a transmitter """
    def __init__(self, port):
        self.port = port # handle to parent
        self.pltone = 100.0
        self.id = "n0call"
        self.tailMsgList =  []
        self.beaconMsgList = []
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
            self.pttPin = 15
            self.txState=self.port.globalState.tx1.setValue
        else :
            self.pttPin = 22
            self.txState=self.port.globalState.tx2.setValue

        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.pttPin, GPIO.OUT)
        GPIO.output(self.pttPin,(not self.txPinLvl))
        #self.tail_msg = tail.tail_msg(self.port.card)
        self.pid = False
        self.idPid = False
        self.beepMethod = 2 # 0=none, 1=tone, 2=wave 3=morse
        self.beepTone = "660 5000 30 440 5000 30 1000 5000 30"
        self.tailBeepWav = '../sounds/Tink.wav'
        self.beepMorse = "20 440 5000 beep"
        self.xmlvars = ( 'pltone', 'id', 'idtime', 'polite', 'timeout',
                         'taildly', 'hangtime', 'disable', 'txupdly',
                         'txPinLvl', 'beepMethod', 'beepTone',
                         'tailBeepWav', 'beepMorse') # data to store in xml config
        self.up = False

    def addTailMsg(self, method,msg,cancelable,isid,requeue,alt):
        self.tailMsgList.append((method,msg,cancelable,isid,requeue,alt))
        print("Added tail message %s " % msg)

    def addBeaconMsg(self, method,msg,cancelable,isid,requeue,alt):
        self.beaconMsgList.append((method,msg,cancelable,isid,requeue,alt))
        print("Added beacon message %s " % msg)


    def tx(self) :
        if( not self.disable) :
            #self.port.startPl(pltone)
            #self.port.tx_enable()
            GPIO.output(self.pttPin,self.txPinLvl)
            #self.port.gui.updateTxGui(self.port.portnum,True)
            self.txState(True)
            self.up = True

    def plGen(self) :
        """ Starts this transmitters Pl generator

        not going to worry about the details yet
        """
        print("pl gen on")
    def plStop(self) :
        """ Stops this transmitters Pl generator

       not going to worry about the details yet
       """
        print("pl gen off")
        
    def down(self):
        GPIO.output(self.pttPin,(not self.txPinLvl))
        #self.port.gui.updateTxGui(self.port.portnum,False)
        self.txState(False)
        self.up = False

    def playMsgs(self,msgList) :
        print(" play messages called")
        print(msgList)
        self.cancel = False
        id_played = False
        i=0;
        while(i<len(msgList)) :
            print("i = %d" %i)
            ele = msgList[i]
            print("ele =")
            print(ele)
            (method,msg,cancelable,isid,requeue,alt) = ele
            self.cancellable = cancelable
            # run it
            if(not self.cancel or not cancelable) :
                # realy run it
                args = method + [self.port.card] + msg
                print("tail message play: (args)")
                print(args)
                try:
                    print("Play messages Trying")
                    print(args)
                    self.pid = subprocess.Popen(args)
                    self.pid.wait()
                except:
                    print("error could not run the tail message")
            if(self.cancel and alt and self.pid.returncode() <0) :
                (method,msg) = alt
                args = method + [self.port.card] + msg
                print("tail message alt play: (args)")
                print(args)
                try: 
                    self.pid = subprocess.call(args)
                except:
                    print("error could not run the alternate message")
                if(isid and (alt or (not self.cancel and not cancelable))) :
                    id_played = True
            if (not requeue):
                msgList.pop(i)
            else :
                i=i+1
        self.pid = None
        print("Play messages Exit")
        return (id_played)
 
    def sendId(self) :
        self.idPid = subprocess.Popen(['../bin/mout', self.port.card, '20', '660', '5000', self.id])
        self.idPid.wait()

    def tailBeep(self) :
        if(self.beepMethod == 1) : # tone
            args = ['../bin/tout',self.port.card] + self.beepTone.split()
            print(args)
            beepPid = subprocess.call(args)
        elif(self.beepMethod == 2) : # wave
            beepPid = subprocess.Popen(['/usr/bin/aplay', '-D', self.port.card, self.tailBeepWav])
        elif(self.beepMethod == 3) : # morse
            args = ['../bin/mout',self.port.card] + self.beepMorse.split()
            print(args)
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
        self.rxState = 0
        self.plDet = 0
        self.idle_timer = 0
        self.busy_timer = 0
        self.kerchunk_timer = 0
        self.anti_kerchunk = False
        self.timeout = 180     # seconds
        self.resetTimeout = 1 # seconds
        self.IdleTimeout = 600 # seconds
        self.cmdTimeout = 600 # seconds
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
            self.corState=self.port.globalState.cor1.setValue
            self.ctcssState=self.port.globalState.ctcss1.setValue
            self.softCtcssState=self.port.globalState.softCtcss1.setValue
        else :
            self.corPin = 16
            self.ctcssPin = 18
            self.corState=self.port.globalState.cor2.setValue
            self.ctcssState=self.port.globalState.ctcss2.setValue
            self.softCtcssState=self.port.globalState.softCtcss2.setValue
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.ctcssPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.corPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        self.xmlvars = ('timeout', 'resetTimeout', 'IdleTimeout', 'disabled',
                        'useCtcssPin', 'ctcssPinLvl', 'useCorPin', 'corPinLvl',
                        'useSoftCtcss', 'softCtcssAllow', 'softCtcssCmd',
                        'cmdMode', 'cmdTimeout')

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

    def update(self,channel): # for when called by GPIO interrupt
        ctcssCmd = False
        softCtcss = False
        if(self.useSoftCtcss) :
            for i in range(8) :
                if( self.ctcssAct[i] and self.softCtcssAllow[i] ) :
                     softCtcss = True
                if( self.ctcssAct[i] and self.softCtcssCmd[i] ) :
                    ctcssCmd[i] = True
        if(softCtcss or self.useSoftCtcss == False):
            rx = self.active()
        rx = rx and not self.disabled
        if(rx != self.rxState) :
            if(rx) :
                self.rxActive.set()
                self.port.fsm.rxTimer.reset()
                self.port.fsm.rxIdleTimer.stop()
            else :
                self.rxActive.clear()
                if (self.port.cmd != "") :
                    self.q.put(" ")
            self.rxState = rx
        if(ctcssCmd) :
           self.cmdMode = True
           self.port.fsm.cmdTimer.reset()
        self.port.fsm.updateRx(rx)
        #self.port.gui.updateRxGui(self.port.portnum,(GPIO.input(self.corPin) == self.corPinLvl),
        #            (GPIO.input(self.ctcssPin) == self.ctcssPinLvl),self.ctcssAct)
        self.corState(GPIO.input(self.corPin) == self.corPinLvl)
        self.ctcssState(GPIO.input(self.ctcssPin) == self.ctcssPinLvl)
        self.softCtcssState(self.ctcssAct)
    def softDecode (self,q):
        try:
            p=subprocess.Popen(['../bin/multimon', self.port.card, '-a', 'dtmf', '-a', 'ctcss'], stdout=subprocess.PIPE)
        except:
            # dummy test wrapper to simulate multimon
            import io
            class dummy:
                def __init__(self):
                    self.stdout=io.StringIO("DTMF: 1")
            p=dummy()

        time.sleep(1)
        while(True) :
            txt = p.stdout.readline()
            ctcss = re.search(b'CTCSS (?P<state>[DL]): (?P<num>\d)',txt)
            dtmf = re.search(b'DTMF: (?P<tone>[0123456789ABCDEF])',txt)
            mute = re.search(b'MUTE',txt)
            if(ctcss != None) :
                self.ctcssAct[int(ctcss.group('num'))] = (ctcss.group('state') == 'D')
                self.update(False) # update the RX status
            if(dtmf != None) :
                q.put(dtmf.group('tone'))

    def run(self) :
        self.sd = threading.Thread(target=self.softDecode, args=[self.q])
        self.sd.daemon = True
        self.sd.start()
        if(self.useCorPin) :
            GPIO.add_event_detect(self.corPin, GPIO.BOTH, callback=self.update)
        if(self.useCtcssPin) :
            GPIO.add_event_detect(self.ctcssPin, GPIO.BOTH, callback=self.update)


class radioPort :
    """ The port class has a reciever and a transmitter and houses any common data 
    it has multiple threads.
    The soft deode thread runs multimon to decode PL and DTMF
    The ctcss pin and cor pins are handled by interups.
    """
    def __init__(self, portnum,q, globalState) :
        self.portnum = portnum
        if(portnum == 1 ) :
            self.card = "sysdefault:CARD=Device"
        elif (portnum == 2 ) :
            self.card = "sysdefault:CARD=Device_1"
        else :
            self.card = "sysdefault"
        
        self.isLink = False
        self.linkState = 0
        self.q = q
        self.globalState = globalState
        self.rx = rx(self,q) # self passed in is the port instance for parent refences to this data
        self.tx = tx(self)
        self.fsm = rptFsm.rptFsm(self)
        self.xmlvars = ( 'card', 'islink', 'linkstate', 'enabled', 'idleWav')
        self.cmd = ""
        self.enabled = True
        self.idleWav = '../sounds/idle.wav'

    def run(self) :
        if(self.enabled) :
            self.rx.run()
            self.fsm.startUp()
