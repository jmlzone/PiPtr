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
IOCON    = 10
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
        self.intconA = 0
        self.intconB = 0
        self.arate = 300
        self.xmlvars = ['vals','tcon', 'gain', 'mics', 'speakers', 'CH1CTL', 'CH2CTL', 'CH3CTL'
                        'iodirA', 'ovalA', 'iodirB', 'ovalB', 'arate']
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
            self.have[GPIOEX2] = False
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
            GPIO.add_event_detect(UINTA, GPIO.RISING, callback=self.uinta)
            GPIO.add_event_detect(UINTB, GPIO.RISING, callback=self.uintb)
        # set up adc channels
        self.adc = [adcChan(self.spi,0,(2.048/1024.0),0,2),
               adcChan(self.spi,1,(20.48/1024.0),12.4,13.6),
               adcChan(self.spi,2,(20.48/1024.0),0,20),
               adcChan(self.spi,3,(20.48/1024.0),0,20),
               adcChan(self.spi,4,(20.48/1024.0),0,20),
               adcChan(self.spi,5,(20.48/1024.0),0,20),
               adcChan(self.spi,6,(100.0/1024.0),0,20),
               adcChan(self.spi,7,(20.48/1024.0),11.0,13.9)]
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
        GPIO.output(self.selPins, self.splitBits(ss))
        cmd = 64
        val = gain & 7
        self.spi.open(0,bus)
        data16 = self.spi.xfer2([cmd,val])
        self.spi.close()

    def ReadAll(self):
        for i in range(11):
            d = self.ReadLoc(i)
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
        self.CH1CTL = self.getBit(self.CH1CTL,self.top.port1.rx.deemp,4)
        self.CH1CTL = self.getBit(self.CH1CTL,self.top.port1.rx.descEn,5)
        self.CH1CTL = self.getBit(self.CH1CTL,self.top.port1.rx.portDet,6)
        self.CH2CTL = self.getBit(self.CH2CTL,self.top.port2.rx.deemp,4)
        self.CH2CTL = self.getBit(self.CH2CTL,self.top.port2.rx.descEn,5)
        self.CH2CTL = self.getBit(self.CH2CTL,self.top.port2.rx.portDet,6)
        self.i2cSafeWrite(GPIOEX1, GPIOR, self.CH1CTL) # chanel 1 default values
        self.i2cSafeWrite(GPIOEX2, GPIOR, self.CH2CTL) # chanel 2 default values
        self.i2cSafeWrite(GPIOEX3, GPIOR, self.CH3CTL) # chanel 3 default values

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
        cn = pc[16:]
        if (mixType == 'Mic') :
            control = alsaaudio.PCM_CAPTURE
        elif (mixType == 'Speaker') :
            control = alsaaudio.PCM_PLAYBACK
        else :
            print("bad controtl type %s" % mixType)
            control = None
        #print("There are %d sound cards" % len(c))
        for i in range(len(c)) :
            m = alsaaudio.mixers(i)
            if ('Mic' in m and 'Speaker' in m) :
                #print("Card %d: %s has both" % (i,c[i]))
                if(cn==c[i]) :
                    mix = alsaaudio.Mixer(control=mixType, cardindex=i)
                    mix.setvolume(val,0,control)
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

    def add_event_detect(self,pin,intdir,callback=None) :
        if(pin >=GPA0 and pin <=GPA7 ) :
            self.intconA = self.getBit(self.intconA,1,pin)
            self.userfuncs[pin] = callback
            self.i2cSafeWrite(GPIOEX4,INTCONA,self.intconA)
        elif(pin >=GPB0 and pin <=GPB7 ) :
            self.intconB = self.getBit(self.intconB,1,pin-8)
            self.userfuncs[pin] = callback
            self.i2cSafeWrite(GPIOEX4,INTCONB,self.intconB)
        else:
            print("Ilegal HWIO pin for add_event_detect %d" % pin)
            

    def remove_event_detect(self,pin) :
        if(pin >=GPA0 and pin <=GPA7 ) :
            self.intconA = self.getBit(self.intconA,0,pin)
            self.userfuncs[pin] = None
            self.i2cSafeWrite(GPIOEX4,INTCONA,self.intconA)
        elif(pin >=GPB0 and pin <=GPB7 ) :
            self.intconB = self.getBit(self.intconB,0,pin-8)
            self.userfuncs[pin] = None
            self.i2cSafeWrite(GPIOEX4,INTCONB,self.intconB)
        else:
            print("Ilegal HWIO pin for remove_event_detect %d" % pin)

    def uinta(self,pin) :
        val = self.i2cSafeRead(GPIOEX4,INTFA)
        self.intf = self.intf | val
        self.intRun.set()
    def uintb(self,pin) :
        val = self.i2cSafeRead(GPIOEX4,INTFB)
        self.intf = self.intf | (val <<8)
        self.intRun.set()

    def runUInts(self) :
        while True :
            self.intRun.wait()
            while (self.intf != 0) :
                for i in range(16) :
                    if (self.intf & 1<<i) :
                        if(callable(self.userfuncs[i])) :
                            self.userfuncs[i]()
                        self.intf = getBit(self.intf,0,i)
    def runAdc(self) :
        while(True) :
            time.sleep(self.arate)
            GPIO.output(self.selPins, self.splitBits(ADCSS))
            for c in range(8) :
                self.adc[c].measure()
            #Force GPIO reads before logging
            dummy = self.input([GPA0,GPB0])
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
        ls = ls + "," + msg + "\n"
        if os.path.exists(self.top.localPath) :
            log = open(logfn,"a")
            log.write(ls)
            log.close
                    

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
