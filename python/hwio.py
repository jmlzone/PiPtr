""" Routines to read and write non gpio hardware devices
"""

# Import all the libraries we need to run
import spidev
import RPi.GPIO as GPIO
import smbus
class hwio :
    def __init__ (self,top) :
        self.top = top
        self.selPins = [32, 31, 29] # msb to lsb
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.selPins, GPIO.OUT)
        GPIO.output(self.selPins, GPIO.LOW)
        self.vals = [150,2,50,20,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
        self.tcon = [15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15]
        self.gain = [ [6,6,6,6], [6,6,6,6] ]
        # Open SELF.SPI bus
        self.spi = spidev.SpiDev()
        self.xmlvars = ['vals','tcon', 'gain']
        self.i2cBus = smbus.SMBus(1)
        self.i2cAddr = 0x20

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
            print "SPI Command Error"
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
            print "Bad resistor number must be 0-3"
        cmd = ((ra & 0x0f) << 4)
        val = val & 0x1ff
        if(val>255) :
            cmd=cmd+1
            val=val-256
        self.spi.open(0,bus)
        data16 = self.spi.xfer2([cmd,val])
        if((data16[0] & 1) == 2) :
            print "SPI Command Error"
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
            print "Bad tcon number must be 0-1"
        cmd = ((ra & 0x0f) << 4)
        val = val & 0x1ff
        if(val>255) :
            cmd=cmd+1
            val=val-256
        self.spi.open(0,bus)
        data16 = self.spi.xfer2([cmd,val])
        if((data16[0] & 1) == 2) :
            print "SPI Command Error"
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
            print "Address %d data %x" % (i,d)


    def init_all(self) :
        for r in range(20) :
            self.WriteRes(r,val[r],0)
            self.WriteTcon(r,tcon[r],0)
        for p in range(2) :
            if (p==0) :
                chan = self.top.port1.linkstate
            elif (p==1) :
                chan = self.top.port2.linkstate
                
            WritePGAChan(chan,p+5,0)
            WritePGAGain(self.gain[p][chan],p+5,0)
