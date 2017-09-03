""" Routines to read and write non gpio hardware devices
"""

# Import all the libraries we need to run
import spidev
import RPi.GPIO as GPIO
import smbus
import alsaaudio
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
CPPUB    = 13
INTFA    = 14 # Intereupt flags
INTFB    = 15
INTCAPA =  16 # Captured values when an interup occurs
INTCAPB =  17
GPIOA   =  18 # IO Values
GPIOB   =  19
OLATA   =  20 # read back written value
OLATB   =  21
MCP23017BASE = 32
GPIOEX1 = MCP23017BASE +1
GPIOEX2 = MCP23017BASE +2
GPIOEX3 = MCP23017BASE +3
INTPOL = 1<<1 # Interupt polarity, 1 = active high
ODR    = 1<<2 # Open drain for the interupt pins, 1= open drain active low
HAEN   = 1<<3 # used in spi only to ignore the address pins
DISSLW = 1<<4 # disables slew rate control when 1
SEQOP  = 1<<5 # automatic address incementing disabled when 1
MIRROR = 1<<6 # both interpt pins do the same thing
BANK   = 1<<7 # Keep as zero or address map is different
""" The MCP23017 base address is the same as the max7314 default used in the kenwoods instead of PROMs
"""
class hwio :
    def __init__ (self,top) :
        self.top = top
        self.selPins = [32, 31, 29] # msb to lsb
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
        self.xmlvars = ['vals','tcon', 'gain', 'mics', 'speakers', 'GPIOEX1A', 'GPIOEX1B']
        self.GPIOEX1A = 0
        self.GPIOEX1B = 0
        self.haveIO = True
        self.i2cBus = smbus.SMBus(1)
        try:
            self.i2cBus.write_byte_data(GPIOEX1, IODIRA, 0) # port A as output
            self.i2cBus.write_byte_data(GPIOEX1, IODIRB, 0) # port B as output
        except:
            self.haveIO = False

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
        if (self.haveIO) :
            try: 
                self.i2cBus.write_byte_data(busaddr, regaddr, val)
            except:
                pass
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
        self.GPIOEX1A = self.getBit(self.GPIOEX1A,self.top.port1.rx.deemp,4)
        self.GPIOEX1A = self.getBit(self.GPIOEX1A,self.top.port1.rx.descEn,5)
        self.GPIOEX1A = self.getBit(self.GPIOEX1A,self.top.port1.rx.portDet,6)
        self.GPIOEX1B = self.getBit(self.GPIOEX1B,self.top.port2.rx.deemp,4)
        self.GPIOEX1B = self.getBit(self.GPIOEX1B,self.top.port2.rx.descEn,5)
        self.GPIOEX1B = self.getBit(self.GPIOEX1B,self.top.port2.rx.portDet,6)
        self.i2cSafeWrite(GPIOEX1, GPIOA, self.GPIOEX1A) # port A default values
        self.i2cSafeWrite(GPIOEX1, GPIOB, self.GPIOEX1B) # port B default values

    def muteUnmute(self,port,link,en) :
        maskbit = 1<< link
        if(port == 1) :
            if (en) :
                self.GPIOEX1A = self.GPIOEX1A | maskbit
            else:
                self.GPIOEX1A = self.GPIOEX1A &  ~maskbit
            self.i2cSafeWrite(GPIOEX1, GPIOA, self.GPIOEX1A)
        elif (port ==2) :
            if (en) :
                self.GPIOEX1B = self.GPIOEX1B | maskbit
            else:
                self.GPIOEX1B = self.GPIOEX1B &  ~maskbit
            self.i2cSafeWrite(GPIOEX1, GPIOB, self.GPIOEX1B)
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
    
