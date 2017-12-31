""" Routines to read and write non gpio hardware devices
    User IO to the io expander is caller here like Raspberri pi GPIO
    but use 
      hwio.setup
      hwio.output
      hwio.input
      hwio.add_event_detect
      hwio.remove_event_detect
"""

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
import Adafruit_DHT

""" User IO pin naames
"""
GPA0 = 0
GPA1 = 1
GPA2 = 2
GPA3 = 3
GPA4 = 4
GPA5 = 5
GPA6 = 6
GPA7 = 7
GPB0 = 8
GPB1 = 9
GPB2 = 10
GPB3 = 11
GPB4 = 12
GPB5 = 13
GPB6 = 14
GPB7 = 15
# HWIO directions
INPUT = 1
OUTPUT = 0
# interupt directions same as GPIO
RISING = 31
FALLING = 32
BOTH = 33
PUD_UP = 22
PUD_OFF = 20
# the MCP23017 does not have a pull down
""" MCP23008 Register names
"""
IODIR    = 0
IPOL     = 1
GPINTEN  = 2
DEFVAL   = 3
INTCON   = 4
IOCON    = 5
GPPU     = 6
INTF     = 7
INTCAP   = 8
GPIOR    = 9
OLAT     = 10
""" MCP23017 Register names
"""
IODIRA   =  0  # 1 = input, 0 = output
IODIRB   =  1
IPOLA    =  2  # 1 = Interrupt inverted from IO state
IPOLB    =  3
GPINTENA =  4  # Interupt on change
GPINTENB =  5
DEFVALA  =  6  # Default value for interupt on change compare
DEFVALB  =  7
INTCONA  =  8  # 1 = compare aginst def val, 0= compare against previous value
INTCONB  =  9
IOCONA   = 10
IOCONB   = 11
GPPUA    = 12 # Enables Pullups
GPPUB    = 13
INTFA    = 14 # Interrupt flags
INTFB    = 15
INTCAPA =  16 # Captured values when an interup occurs
INTCAPB =  17
GPIOA   =  18 # IO Values
GPIOB   =  19
OLATA   =  20 # read back written value
OLATB   =  21
""" The MCP23017 and MCP23008 base address is the same as the max7314 default used in the kenwoods instead of PROMs
"""
MCP23017BASE = 32
GPIOEX1 = MCP23017BASE +1
GPIOEX2 = MCP23017BASE +2
GPIOEX3 = MCP23017BASE +3
GPIOEX4 = MCP23017BASE +4
INTPOL = 1<<1 # Interupt polarity, 1 = active high
ODR    = 1<<2 # Open drain for the interupt pins, 1= open drain active low
HAEN   = 1<<3 # used in spi only to ignore the address pins
DISSLW = 1<<4 # disables slew rate control when 1
SEQOP  = 1<<5 # automatic address incementing disabled when 1
MIRROR = 1<<6 # both interpt pins do the same thing
BANK   = 1<<7 # Keep as zero or address map is different
""" user IO related pins
"""
UINTA = 8
UINTB = 10
ADCSS = 7

class hwio :
    def __init__ (self,top) :
        self.top = top
        self.selPins = [32, 31, 29] # msb to lsb
        self.userfuncs = [None,None,None,None,None,None,None,None,
                          None,None,None,None,None,None,None,None]
        self.intf = 0
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.selPins, GPIO.OUT)
        GPIO.output(self.selPins, GPIO.LOW)
        self.vals = [150,2,50,20,0,0,0,0]
        self.tcon = [15,15,15,15,15,15,15,15]
        self.gain = [ [6,6,6,6], [6,6,6,6] ]
        self.mics = [50,50,50]
        self.speakers = [50,50,50]
        self.pwmLevel = 50
        # Open SELF.SPI bus
        self.spi = spidev.SpiDev()
        self.CH1CTL = 0
        self.CH2CTL = 0
        self.CH3CTL = 0
        self.haveIO = {GPIOEX1:True, GPIOEX2:True, GPIOEX3:True, GPIOEX4:True}
        self.iodirA = 0xff
        self.iodirB = 0xff
        self.ovalA = 0
        self.ovalB = 0
        self.gppuA = 0
        self.gppuB = 0
        self.ivalA = 0xff
        self.ivalB = 0xff
        self.intenA = 0
        self.intenB = 0
        self.intcapA = 0
        self.intcapB = 0
        self.intEdge = [0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0]
        self.arate = 300
        self.cardWait = 4
        self.autoPortDetect = False
        self.xmlvars = ['vals','tcon', 'gain', 'mics', 'speakers', 'pwmLevel',
                        'CH1CTL', 'CH2CTL', 'CH3CTL', 'iodirA', 'ovalA',
                        'iodirB', 'ovalB', 'arate', 'cardWait',
                        'autoPortDetect']
        self.intRun = threading.Event()
        self.i2cBus = smbus.SMBus(1)
        # IOEX1 is the controls for radio port 1 
        try:
            self.i2cBus.write_byte_data(GPIOEX1, IODIR,0) # port as output
        except:
            self.haveIO[GPIOEX1] = False
        # IOEX2 is the controls for radio port 2 
        try:
            self.i2cBus.write_byte_data(GPIOEX2, IODIR,0) # port as output
        except:
            self.haveIO[GPIOEX2] = False
        # IOEX3 is the port 2 and sound card control
        try:
            self.i2cBus.write_byte_data(GPIOEX3, IODIR,0) # port as output
        except:
            self.haveIO[GPIOEX3] = False
        # IOEX4 is the User IO and has interupt expansion
        try:
            self.i2cBus.write_byte_data(GPIOEX4, IODIRA,self.iodirA) # port A as input
            self.i2cBus.write_byte_data(GPIOEX4, IODIRB,self.iodirB) # port B as input
        except:
            self.haveIO[GPIOEX4] = False
        if(self.haveIO[GPIOEX4]) :
            self.i2cBus.write_byte_data(GPIOEX4, GPINTENA,0) # default disable any interupts
            self.i2cBus.write_byte_data(GPIOEX4, GPINTENB,0)
            GPIO.setup([UINTA,UINTB], GPIO.IN)
            GPIO.add_event_detect(UINTA, GPIO.FALLING, callback=self.uinta)
            GPIO.add_event_detect(UINTB, GPIO.FALLING, callback=self.uintb)
        # set up adc channels
        self.adc = [adcChan(self.spi,0,(2.048/1024.0),0,2),
               adcChan(self.spi,1,(20.48/1024.0),12.4,13.6),
               adcChan(self.spi,2,(20.48/1024.0),0,20),
               adcChan(self.spi,3,(20.48/1024.0),0,20),
               adcChan(self.spi,4,(20.48/1024.0),0,20),
               adcChan(self.spi,5,(20.48/1024.0),0,20),
               adcChan(self.spi,6,(100.0/1024.0),0,20),
               adcChan(self.spi,7,(20.48/1024.0),11.0,13.9)]
        self.th = DHT(4) #IO pin 4 is board pin 7

    def splitBits(self,val) :
        v0 = val & 1
        v1 = (val >> 1) & 1 
        v2 = (val >> 2) & 1
        return [v2, v1, v0]

    def ReadLoc(self,chan,ss,bus):
        """ Function to read SELF.SPI data from MCP3008 chip
        Channel must be an integer 0-7
        SS is the bus slave number
        bus is the bus number
        """
        cmd = ((chan & 0x0f) << 4)+12
        #print "cmd is %x" % cmd
        GPIO.output(self.selPins, self.splitBits(ss))
        self.spi.open(0,bus)
        data16 = self.spi.xfer2([cmd,0])
        data = ((data16[0]&1) << 8) + data16[1]
        if((data16[0] & 1) == 2) :
            print("SPI Command Error")
        self.spi.close()
        return data


    def WriteRes(self,rn,val,bus):
        r = rn & 3
        ss = rn >> 2
        GPIO.output(self.selPins, self.splitBits(ss))
        if(r <2 ):
            ra=r
        elif (r<4):
            ra=r+4
        else :
            print("Bad resistor number must be 0-3")
        cmd = ((ra & 0x0f) << 4)
        val = val & 0x1ff
        if(val>255) :
            cmd=cmd+1
            val=val-256
        self.spi.open(0,bus)
        data16 = self.spi.xfer2([cmd,val])
        if((data16[0] & 1) == 2) :
            print("SPI Command Error")
        self.spi.close()

    def WriteTconPair(self,rn,val,bus):
        r = (rn & 3) >> 1
        ss = rn >> 2
        GPIO.output(self.selPins, self.splitBits(ss))
        if(r == 0 ):
            ra=4
        elif (r == 1):
            ra=10
        else :
            print("Bad tcon number must be 0-1")
        cmd = ((ra & 0x0f) << 4)
        val = val & 0x1ff
        if(val>255) :
            cmd=cmd+1
            val=val-256
        self.spi.open(0,bus)
        data16 = self.spi.xfer2([cmd,val])
        if((data16[0] & 1) == 2) :
            print("SPI Command Error")
        self.spi.close()

    def WriteTcon(self,rn,val,bus) :
        if(rn & 1) :
            th = val
            tl = self.tcon[rn-1]
        else:
            tl = val
            th = self.tcon[rn+1]
        wv = 0x100 + (th * 16) + tl
        self.WriteTconPair(rn,wv,bus)

    def WritePGAChan(self,chan,ss,bus):
        if(self.top.options.verbose) :
            print("WritePGAChan, chan %d, ss %d, bus %d" % (chan,ss,bus))
        GPIO.output(self.selPins, self.splitBits(ss))
        cmd = 65
        val = chan & 7
        self.spi.open(0,bus)
        data16 = self.spi.xfer2([cmd,val])
        self.spi.close()

    def WritePGAGain(self,gain,ss,bus):
        """ PGA Gain control selections
        000 gain =  1
        001 gain =  2
        010 gain =  4
        011 gain =  5
        101 gain = 10
        100 gain = 16
        111 gain = 32
        """
        if(self.top.options.verbose) :
            print("WritePGAGain, gain %d, ss %d, bus %d" % (gain,ss,bus))
        GPIO.output(self.selPins, self.splitBits(ss))
        cmd = 64
        val = gain & 7
        self.spi.open(0,bus)
        data16 = self.spi.xfer2([cmd,val])
        self.spi.close()

    def ReadAll(self,ss=0,bus=0):
        for i in range(11):
            d = self.ReadLoc(i,ss,bus)
            print("Address %d data %x" % (i,d))

    def getBit(self,baseVal,bitVal,bitPos) :
        maskbit = 1<<bitPos
        if(bitVal) :
            outval = baseVal | maskbit
        else:
            outval = baseVal &  ~maskbit & 0xff
        return outval
    def i2cSafeWrite(self,busaddr,regaddr,val) :
        if (self.haveIO[busaddr]) :
            try: 
                self.i2cBus.write_byte_data(busaddr, regaddr, val)
            except:
                pass
    def i2cSafeRead(self,busaddr,regaddr) :
        val = 0xff
        if (self.haveIO[busaddr]) :
            try: 
                val = self.i2cBus.read_byte_data(busaddr, regaddr)
            except:
                pass
        return(val)
    def init_all(self) :
        self.waitForCards(self.cardWait)
        if(self.autoPortDetect) :
            self.portDetect()
        for r in range(8) :
            self.WriteRes(r,self.vals[r],0)
            self.WriteTcon(r,self.tcon[r],0)
        for p in range(2) :
            if (p==0) :
                chan = self.top.port1.linkstate
            elif (p==1) :
                chan = self.top.port2.linkstate
                
            self.WritePGAChan(chan,p+5,0)
            self.WritePGAGain(self.gain[p][chan],p+5,0)
        self.CH1CTL = self.getBit(self.CH1CTL,not self.top.port1.rx.deemp,4)
        self.CH1CTL = self.getBit(self.CH1CTL,not self.top.port1.rx.descEn,5)
        self.CH1CTL = self.getBit(self.CH1CTL,not self.top.port1.rx.portDet,6)
        self.CH2CTL = self.getBit(self.CH2CTL,not self.top.port2.rx.deemp,4)
        self.CH2CTL = self.getBit(self.CH2CTL,not self.top.port2.rx.descEn,5)
        self.CH2CTL = self.getBit(self.CH2CTL,not self.top.port2.rx.portDet,6)
        self.i2cSafeWrite(GPIOEX1, GPIOR, self.CH1CTL) # chanel 1 default values
        self.i2cSafeWrite(GPIOEX2, GPIOR, self.CH2CTL) # chanel 2 default values
        self.i2cSafeWrite(GPIOEX3, GPIOR, self.CH3CTL) # chanel 3 default values
        # now initialize the values for the sound card controls
        for p in range(self.cardWait-1) :
            self.setMixerByName(p,'Mic', self.mics[p])
            self.setMixerByName(p,'Speaker', self.speakers[p])
        # set the level for the onboard PWM
        #mix = alsaaudio.Mixer(control='PCM', cardindex=0)
        #mix.setvolume(self.pwmLevel,0, alsaaudio.PCM_PLAYBACK)
        self.setMixerByName(4,'PCM',self.pwmLevel)
        

    def muteUnmute(self,port,link,en) :
        #print("muteUnmute:: Port %d, Link %d, en %d" %(port,link,en))
        maskbit = 1<< link
        if(port == 1) :
            if (en) :
                self.CH1CTL = self.CH1CTL | maskbit
            else:
                self.CH1CTL = self.CH1CTL &  ~maskbit
            self.i2cSafeWrite(GPIOEX1, GPIOR, self.CH1CTL)
        elif (port ==2) :
            if (en) :
                self.CH2CTL = self.CH2CTL | maskbit
            else:
                self.CH2CTL = self.CH2CTL &  ~maskbit
            self.i2cSafeWrite(GPIOEX2, GPIOR, self.CH2CTL)
        else :
            print( "Error Bad port number to mute or unmute")

    def setMixerByName(self, pn,  mixType, val) :
        c=alsaaudio.cards()
        if(pn==0) :
            pc = self.top.port1.card
        elif (pn==1) :
            pc = self.top.port2.card
        elif (pn==2) :
            pc = self.top.port3.card
        elif (pn==4) :
            pc = 'sysdefault:CARD=ALSA'
        if(self.top.options.verbose) :
            print("setMixerByName port %d, card %s, mix %s, val %d" %
                  (pn,pc,mixType,val))
        cn = pc[16:]
        if (mixType == 'Mic') :
            control = alsaaudio.PCM_CAPTURE
        elif (mixType == 'Speaker') :
            control = alsaaudio.PCM_PLAYBACK
        elif (mixType == 'PCM') :
            control = alsaaudio.PCM_PLAYBACK
        else :
            print("bad control type %s" % mixType)
            control = None
        if(self.top.options.verbose) :
            print("There are %d sound cards" % len(c))
        for i in range(len(c)) :
            m = alsaaudio.mixers(i)
            if ('Mic' in m and 'Speaker' in m) :
                if(self.top.options.verbose) :
                    print("Card %d: %s has both" % (i,c[i]))
                pass
            if(cn==c[i]) :
                if(mixType in m) :
                    mix = alsaaudio.Mixer(control=mixType, cardindex=i)
                    mix.setvolume(val,0,control)
                    if (mixType == 'Speaker') :
                        mix.setvolume(val,1,control) # set the other channel
                else:
                    print("Error: setMixerByName port %d card %s does not have mix %s.  CHECK CONFIG or run port detection" % (pn,pc,mixType))
                return(None)

    def linkVoteSet(self, port, link) :
        pass
    def linkVoteClr(self, port, link) :
        pass
    
    def updateMask(self,val,bp,bv) :
        amask = ~(1<<bp) & 0xff
        omask = bv<<bp &0xff
        return(val & amask | omask)
    def setup(self,pins, direction, pull_up_down=PUD_OFF, initial=None):
        if type(pins) is not list :
            pins = [pins]
        plen = len(pins)
        if type(pull_up_down) is not list:
            pull_up_down = [pull_up_down  for number in range(plen)]
        if ((initial is not None) and (type(initial) is not list)) :
            initial = [initial for number in range(plen)]
        updateA = False
        updateB = False
        for n in range(plen) :
            pin = pins[n]
            pu = pull_up_down[n]
            if(pin >=GPA0 and pin <=GPA7 ) :
                self.iodirA = self.updateMask(self.iodirA,pin,direction)
                self.gppuA = self.updateMask(self.gppuA,pin,pu)
                if(initial is not None) :
                    self.ovalA =  self.updateMask(self.ovalA,pin,initial[n])
                updateA = True
            elif(pin >=GPB0 and pin <=GPB7 ) :
                pin = pin - GPB0
                self.iodirB = self.updateMask(self.iodirB,pin,direction)
                self.gppuB = self.updateMask(self.gppuB,pin,pu)
                if(initial is not None) :
                    self.ovalB =  self.updateMask(self.ovalB,pin,initial[n])
                updateB = True
            else:
                print("Ilegal HWIO pin for SETUP %d" % pin)
        if updateA :
            self.i2cSafeWrite(GPIOEX4, IODIRA,self.iodirA)
            self.i2cSafeWrite(GPIOEX4, GPPUA,self.gppuA)
            if(initial is not None) :
                self.i2cSafeWrite(GPIOEX4, GPIOA,self.ovalA)
        if updateB :
            self.i2cSafeWrite(GPIOEX4, IODIRB,self.iodirB)
            self.i2cSafeWrite(GPIOEX4, GPPUB,self.gppuB)
            if(initial is not None) :
                self.i2cSafeWrite(GPIOEX4, GPIOB,self.ovalB)
    def output(self, pins, vals):
        if type(pins) is not list :
            pins = [pins]
        plen = len(pins)
        if type(vals) is not list :
            vals = [vals for number in range(plen)]
        updateA = False
        updateB = False
        for n in range(plen) :
            pn = pins[n]
            pv = vals[n]
            if(pn >=GPA0 and pn <=GPA7 ) :
                self.ovalA = self.updateMask(self.ovalA,pn,pv)
                updateA = True
            elif(pn >=GPB0 and pn <=GPB7 ) :
                pn = pn - GPB0
                self.ovalB = self.updateMask(self.ovalB,pn,pv)
                updateB = True
            else:
                print("Ilegal HWIO pin for OUTPUT %d" % pn)
        if updateA :
            self.i2cSafeWrite(GPIOEX4, GPIOA,self.ovalA)
        if updateB :
            self.i2cSafeWrite(GPIOEX4, GPIOB,self.ovalB)
    def getival(self,pin) :
        return((self.ival>>pin) &1)
    def input(self,pins):
        if type(pins) is not list :
            pinlist = [pins]
        else :
            pinlist = pins
        updateA = False
        updateB = False
        for pin in pinlist :
            if(pin >=GPA0 and pin <=GPA7 ) :
                updateA = True
            elif(pin >=GPB0 and pin <=GPB7 ) :
                pin = pin - GPB0
                updateB = True
            else:
                print("Ilegal HWIO pin for input %d" % pin)
        if updateA :
            self.ivalA = self.i2cSafeRead(GPIOEX4, GPIOA) & 0xff
        if updateB :
            self.ivalB = self.i2cSafeRead(GPIOEX4, GPIOB) & 0xff
        self.ival = self.ivalB <<8 | self.ivalA
        if type(pins) is not list :
            return(self.getival(pins))
        else :
            rv=[]
            for pin in pinlist :
                rv.append(self.getival(pin))
            return(rv)

    def add_event_detect(self,pin,intEdge,callback=None) :
        if(pin >=GPA0 and pin <=GPA7 ) :
            self.intenA = self.getBit(self.intenA,1,pin)
            self.userfuncs[pin] = callback
            self.intEdge[pin] = intEdge
            self.i2cSafeWrite(GPIOEX4,GPINTENA,self.intenA)
        elif(pin >=GPB0 and pin <=GPB7 ) :
            self.intenB = self.getBit(self.intenB,1,pin-8)
            self.userfuncs[pin] = callback
            self.intEdge[pin] = intEdge
            self.i2cSafeWrite(GPIOEX4,GPINTENB,self.intenB)
        else:
            print("Ilegal HWIO pin for add_event_detect %d" % pin)
            

    def remove_event_detect(self,pin) :
        if(pin >=GPA0 and pin <=GPA7 ) :
            self.intenA = self.getBit(self.intenA,0,pin)
            self.userfuncs[pin] = None
            self.i2cSafeWrite(GPIOEX4,GPINTENA,self.intenA)
        elif(pin >=GPB0 and pin <=GPB7 ) :
            self.intenB = self.getBit(self.intenB,0,pin-8)
            self.userfuncs[pin] = None
            self.i2cSafeWrite(GPIOEX4,GPINTENB,self.intenB)
        else:
            print("Ilegal HWIO pin for remove_event_detect %d" % pin)

    def uinta(self,pin) :
        val = self.i2cSafeRead(GPIOEX4,INTFA)
        self.intf = self.intf | val
        self.intcapA = self.i2cSafeRead(GPIOEX4,INTCAPA)
        inctrl = self.i2cSafeRead(GPIOEX4,GPIOA)
        self.intRun.set()
    def uintb(self,pin) :
        val = self.i2cSafeRead(GPIOEX4,INTFB)
        self.intf = self.intf | (val <<8)
        self.intcapB = self.i2cSafeRead(GPIOEX4,INTCAPB)
        inctrl = self.i2cSafeRead(GPIOEX4,GPIOB)
        self.intRun.set()

    def runUInts(self) :
        while True :
            self.intRun.wait()
            intcap = self.intcapB<<8 | self.intcapA
            while (self.intf != 0) :
                for i in range(16) :
                    if (self.intf & 1<<i) :
                        v = (intcap >>i) & 1;
                        if(((self.intEdge[i] == BOTH)
                            or ((self.intEdge[i]==FALLING) and (v==0))
                            or ((self.intEdge[i]==RISING) and (v==1))
                            ) and callable(self.userfuncs[i])) :
                            self.userfuncs[i](i)
                        self.intf = self.getBit(self.intf,0,i)
    def runAdc(self) :
        while(True) :
            time.sleep(self.arate)
            GPIO.output(self.selPins, self.splitBits(ADCSS))
            for c in range(8) :
                self.adc[c].measure()
            #Force GPIO reads before logging
            dummy = self.input([GPA0,GPB0])
            (self.hum,self.temp) = self.th.measure()
            self.csvLog("normal")

    def csvLog(self,msg) :
        dt = datetime.datetime.now()
        ls = dt.strftime("%B %d, %Y %I:%M:%S%p")
        logfn = os.path.join(self.top.localPath,"log.csv")
        for i in range(8) :
            ls = ls + ",%0.2f" % self.adc[i].val
        for i in range(8) :
            ls = ls + ",%d" %((self.ivalA>>i) &1)
        for i in range(8) :
            ls = ls + ",%d" %((self.ivalB>>i) &1)
        if(self.temp) :
            ls = ls + ",%3.1f" % self.temp    
        if(self.hum) :
            ls = ls + ",%3.1f" % self.hum    
        ls = ls + "," + msg + "\n"
        if os.path.exists(self.top.localPath) :
            log = open(logfn,"a")
            log.write(ls)
            log.close

    def waitForCards(self,ncards) :
        # turn on sound card
        print("turning on sound cards")
        self.i2cBus.write_byte_data(GPIOEX3, GPIOR,0)
        c=[]
        i=0
        while( i<10 and len(c) <ncards) :
            time.sleep(1)
            i=i+1
            c=alsaaudio.cards()
            print("%d: have %d cards" % (i,len(c)))
        # now that we see the cards, let's unbind the hid driver since it only caseses problems
        try: 
            hidfd = open('/sys/bus/hid/drivers/generic-usb/unbind','w')
            hidfd.write('0003:0D8C:0012.0005')
            hidfd.close()
        except :
            print('waitForCards:: could not disable HID driver')

    def portDetect(self):
        p=subprocess.Popen(['../bin/gpio_alt','-p','18','-f','5'])
        p.wait()
        p=subprocess.Popen(['../bin/gpio_alt','-p','19','-f','5'])
        p.wait()
        self.i2cBus.write_byte_data(GPIOEX1, IODIR,0)
        self.i2cBus.write_byte_data(GPIOEX2, IODIR,0)
        self.i2cBus.write_byte_data(GPIOEX3, IODIR,0)
        c=alsaaudio.cards()
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
        self.i2cBus.write_byte_data(GPIOEX1, GPIOR,1<<6)
        self.i2cBus.write_byte_data(GPIOEX2, GPIOR,1<<6)

        #set PCM hardware playback to 50
        #mix = alsaaudio.Mixer(control='PCM', cardindex=0)
        #mix.setvolume(83,0, alsaaudio.PCM_PLAYBACK)
        self.setMixerByName(4,'PCM',83)
        cardDict={}
        d0 = threading.Thread(target=self.decodeTone, args=[cardList[0],cardDict])
        d1 = threading.Thread(target=self.decodeTone, args=[cardList[1],cardDict])
        d2 = threading.Thread(target=self.decodeTone, args=[cardList[2],cardDict])
        d0.daemon = True
        d0.start()
        d1.daemon = True
        d1.start()
        d2.daemon = True
        d2.start()

        print("Detecting port 1")
        self.i2cBus.write_byte_data(GPIOEX1, GPIOR,0) # enable detect 1
        p=subprocess.Popen(['/usr/bin/aplay', '-D', 'sysdefault:CARD=ALSA', self.top.absPath('../sounds/audiocheck.net_dtmf_1.wav')])
        p.wait()
        time.sleep(2)
        self.i2cBus.write_byte_data(GPIOEX1, GPIOR,1<<6) # disable port 1
        print("Detecting port 2")
        self.i2cBus.write_byte_data(GPIOEX2, GPIOR,0) # enable port 2
        p=subprocess.Popen(['/usr/bin/aplay', '-D', 'sysdefault:CARD=ALSA', self.top.absPath('../sounds/audiocheck.net_dtmf_2.wav')])
        p.wait()
        time.sleep(2)
        self.i2cBus.write_byte_data(GPIOEX2, GPIOR,1<<6) # disable port 2
        p3=[]
        p3.append(cardList[0])
        p3.append(cardList[1])
        p3.append(cardList[2])
        p3.remove(cardDict['1'])
        p3.remove(cardDict['2'])
        c3=p3[0]

        print("Detecting port 3")
        self.i2cBus.write_byte_data(GPIOEX3, GPIOR,6) # enable port 3 to both!
        p=subprocess.Popen(['/usr/bin/aplay', '-D', 'sysdefault:CARD='+c3, self.top.absPath('../sounds/audiocheck.net_dtmf_3.wav')])
        p.wait()
        time.sleep(2)
        self.i2cBus.write_byte_data(GPIOEX3, GPIOR,0) # disable port 3 to both!

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
        self.top.port1.card=card1
        self.top.port2.card=card2
        self.top.port3.card=card3

    def decodeTone(self,card,cardDict):
        mmPath = self.top.absPath('../bin/multimon')
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

class adcChan :
    def __init__ (self,spi,chan,scale,llimit,hlimit,updateFunc=None, underFunc=None, overFunc=None, nomFunc=None) :
        self.spi = spi
        self.bus = 0
        self.chan = chan
        self.scale = scale
        self.llimit = llimit
        self.hlimit = hlimit
        self.updateFunc = updateFunc
        self.underFunc = underFunc
        self.overFunc = overFunc
        self.nomFunc = nomFunc
        self.state = None
        self.hiEdge = True
        self.loEdge = True
        self.nomEdge = True
        if(chan > 7 or chan < 0) :
            print("Error bad adc channel number must be 0-7")
            return -1
    def measure(self) :
        self.spi.open(0,self.bus)
        r = self.spi.xfer2([1, 8 + self.chan << 4, 0])
        self.spi.close()
        data = ((r[1] & 3) << 8) + r[2]
        self.val = (float(data) * self.scale)
        if(callable(self.updateFunc)) :
            self.updateFunc()
        if( self.val < self.llimit ) :
            if(self.state != 'low' or not self.loEdge) :
                self.state = 'low'
                if(callable(self.underFunc)) :
                    self.underFunc()
        elif (self.val > self.hlimit ) :
            if(self.state != 'high' or not self.hiEdge) :
                self.state = 'high'
                if(callable(self.overFunc)) :
                    self.overerFunc()
        else :
            if(self.state != 'nom' or not self.nomEdge) :
                self.state = 'nom'
                if(callable(self.nomFunc)) :
                    self.nomFunc()
        return ( self.val )

class DHT :
    def __init__(self,pin,thLimit=None,tlLimit=None,hhLimit=None,hlLimit=None,
                 updateFunc=None, underFunc=None, overFunc=None, nomFunc=None) :
        self.pin = pin
        self.tlLimit = tlLimit
        self.thLimit = thLimit
        self.hlLimit = hlLimit
        self.hhLimit = hhLimit
        self.updateFunc = updateFunc
        self.underFunc = underFunc
        self.overFunc = overFunc
        self.nomFunc = nomFunc
        self.tempState = None
        self.humState = None
        self.hiEdge = True
        self.loEdge = True
        self.nomEdge = True
        self.active = True

    def measure(self) :
        if(self.active) :
            (humidity, temperature) = Adafruit_DHT.read_retry(Adafruit_DHT.AM2302, self.pin)
            if humidity is not None and  temperature is not None:
                temperatureF = 9/5.0 * temperature + 32
            else:
                self.active=False
                humidity = None
                temperatureF = None
        else:
            humidity = None
            temperatureF = None
        return (humidity, temperatureF)

