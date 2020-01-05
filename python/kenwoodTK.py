import smbus
"""----------------------------------------------------------------------
Device Addresses
----------------------------------------------------------------------"""
ADDR0 = 0x60  # AD0=SCL
ADDR1 = 0x64  # AD0=SDA 
ADDR2 = 0x20  # AD0=GND
ADDR3 = 0x24  # AD0=V+

"""----------------------------------------------------------------------
Register Addresses
----------------------------------------------------------------------"""
DIN_L     = 0x00 # read inputs P7-P0
DIN_H     = 0x01 # read inputs P15-P8
DOUT_P0_L = 0x02 # Phase 0 outputs P7-P0
DOUT_P0_H = 0x03 # Phase 0 outputs P15-P8
CONFIG_L  = 0x06 # Port Config  P7-P0
CONFIG_H  = 0x07 # Port Config  P15-P8
DOUT_P1_L = 0x0a # Phase 1 outputs P7-P0
DOUT_P1_H = 0x0b # Phase 1 outputs P15-P8
MASTERO16 = 0x0e # Master and o16 intensity
CONFIG    = 0x0f # Configuration

INTENSITYP1P0     = 0x10 # Intensity P1, P0
INTENSITYP3P2     = 0x11 # Intensity P3, P2
INTENSITYP5P4     = 0x12 # Intensity P5, P4
INTENSITYP7P6     = 0x13 # Intensity P7, P6
INTENSITYP9P8     = 0x14 # Intensity P9, P8
INTENSITYP11P10   = 0x15 # Intensity P11, P10
INTENSITYP13P12   = 0x16 # Intensity P13, P12
INTENSITYP15P14   = 0x17 # Intensity P15, P14

"""----------------------------------------------------------------------
Register Bit Definitions
----------------------------------------------------------------------"""
"""
in registers  DOUT_P0_L and  DOUT_P0_H
individual bits can be configured as input or output
They reset to input.
"""
OUT = 0
IN = 1
ALLOUT = 0
ALLIN = 0xff

# Register MASTERO16
MASTERSTATIC = 0x00 # P0-p15 static
O16STATIC   = 0x0f # 016 is static

# Register CONFIG
INTSTAT   = (1<<7)  # Read Only
BLINKSTAT = (1<<6)  # Read Only
O16P1     = (1<<5)  # When '0' drive 016 low in phase 1
O16P0     = (1<<4)  # When '0' drive 016 low in phase 0
INTENABLE = (1<<3)  # When '1' 016 = int_n, when '0' GPO
GLOBINTEN = (1<<2)  # Global intensity
BLINKFLIP = (1<<1)  # Invert polarity of blink pin/bit
BLINKEN   = 1       # Enable two Phase Blinking

# Intestsity Registers
INTSTATIC = 0xff   # all intensities static
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
# HWIO directions
INPUT = 1
OUTPUT = 0
OFF = 1
ON = 0

#frequency table
plSwitchTable = {
    "67.0" : [OFF,ON ,OFF,OFF,OFF,ON ],
    "71.9" : [ON ,ON ,OFF,OFF,OFF,ON ],
    "74.4" : [OFF,OFF,ON ,OFF,OFF,ON ],
    "77.0" : [ON ,OFF,ON ,OFF,OFF,ON ],
    "79.7" : [OFF,ON ,ON ,OFF,OFF,ON ],
    "82.5" : [ON ,ON ,ON ,OFF,OFF,ON ],
    "85.4" : [OFF,OFF,OFF,ON ,OFF,ON ],
    "88.5" : [ON ,OFF,OFF,ON ,OFF,ON ],
    "91.5" : [OFF,ON ,OFF,ON ,OFF,ON ],
    "94.8" : [OFF,ON ,ON ,OFF,OFF,OFF],
    "100.0" : [ON ,ON ,ON ,OFF,OFF,OFF],
    "103.5" : [OFF,OFF,OFF,ON ,OFF,OFF],    
    "107.2" : [ON ,OFF,OFF,ON ,OFF,OFF],
    "110.9" : [OFF,ON ,OFF,ON ,OFF,OFF],
    "114.8" : [ON ,ON ,OFF,ON ,OFF,OFF],
    "118.8" : [OFF,OFF,ON ,ON ,OFF,OFF],
    "123.0" : [ON ,OFF,ON ,ON ,OFF,OFF],
    "127.3" : [OFF,ON ,ON ,ON ,OFF,OFF],
    "131.8" : [ON ,ON ,ON ,ON ,OFF,OFF],
    "136.5" : [OFF,OFF,OFF,OFF,ON, OFF],
    "141.3" : [ON ,OFF,OFF,OFF,ON ,OFF],
    "146.2" : [OFF,ON ,OFF,OFF,ON ,OFF],
    "151.4" : [ON ,ON ,OFF,OFF,ON ,OFF],
    "156.7" : [OFF,OFF,ON ,OFF,ON ,OFF],
    "162.2" : [ON ,OFF,ON ,OFF,ON ,OFF],
    "167.9" : [OFF,ON ,ON ,OFF,ON ,OFF],
    "173.8" : [ON ,ON ,ON ,OFF,ON ,OFF],
    "179.9" : [OFF,OFF,OFF,ON ,ON ,OFF],
    "186.2" : [ON ,OFF,OFF,ON ,ON ,OFF],
    "192.8" : [OFF,ON ,OFF,ON ,ON ,OFF],
    "203.5" : [ON ,ON ,OFF,ON ,ON ,OFF],
    "210.7" : [OFF,OFF,ON ,ON ,ON ,OFF],
    "218.1" : [ON ,OFF,ON ,ON ,ON ,OFF],
    "225.7" : [OFF,ON ,ON ,ON ,ON ,OFF],
    "233.6" : [ON ,ON ,ON ,ON ,ON ,OFF],
    "241.8" : [OFF,OFF,OFF,OFF,OFF,ON ],
    "250.3" : [ON ,OFF,OFF,OFF,OFF,ON ]
    }
        
class kenwoodTK:
    """ A Kenwood TK701 (VHF) or Kenwood TK801 (UHF) With the proms removed and
    a max7314 driging the prom outputs to be frequency agile 
    """
    def __init__ (self,addr=ADDR2,plAddr=0x27) :
        self.addr = addr
        self.plAddr = plAddr # MCP3008 for frequency control
        self.i2cBus = smbus.SMBus(1)
        self.plVal=dict()
        self.SwitchTableToValue()
        """ initialize max7314 for static outputs,
            txrx switching with the blink input 
        """
        try:
            self.i2cBus.write_i2c_block_data(self.addr,CONFIG_L,[ALLOUT,ALLOUT]);
            self.i2cBus.write_byte_data(self.addr,MASTERO16,(MASTERSTATIC |  O16STATIC))
            self.i2cBus.write_byte_data(self.addr,CONFIG,(O16P0 |  GLOBINTEN |  BLINKEN))
            self.freqCtl = True
        except:
            print("Kenwood TK frequency control is offline");
            self.freqCtl = False
        try:
            self.i2cBus.write_byte_data(self.plAddr, IODIR,0) # port as output
            self.plCtl = True
            self.setPlByName("88.5")
        except:
            print("Kenwood TK PL control is offline");
            self.plCtl = False
           

    def setFreqDirect(self,tx_freq, rx_freq) :
        if(tx_freq < 200000) :
            tx_code = (tx_freq -21400) //5 # vhf settings
            rx_code = (rx_freq -21400) //5 # // is integer divide!
        else :
            tx_code = ((tx_freq -21400) * 2) // 25 # uhf settings
            rx_code = ((rx_freq -21400) * 2) // 25
            
        self.pllSetTx(int(tx_code))
        self.pllSetRx(int(rx_code))


    def pllSetRx(self,freq) :
        self.i2cBus.write_word_data(self.addr,DOUT_P0_L,freq)


    def pllSetTx(self,freq):
        self.i2cBus.write_word_data(self.addr,DOUT_P1_L,freq)

    def readAll(self) :
        [buf0,buf1] = self.i2cBus.read_i2c_block_data(self.addr,DIN_L,2)
        print("Din is %x %x" % (buf1,buf0))
        [buf0,buf1] = self.i2cBus.read_i2c_block_data(self.addr,CONFIG_L,2)
        print("IO Config is %x %x" %(buf1,buf0))
        [buf0,buf1] = self.i2cBus.read_i2c_block_data(self.addr,DOUT_P0_L,2)
        print("Dout (p0, rx) is %x %x" %(buf1,buf0))
        [buf0,buf1] = self.i2cBus.read_i2c_block_data(self.addr,DOUT_P1_L,2)
        print("Dout (p1, tx) is %x %x" %(buf1,buf0))
        buf0 = self.i2cBus.read_byte_data(self.addr,MASTERO16)
        print("Master and 016 intensity is %x" % buf0)
        buf0 = self.i2cBus.read_byte_data(self.addr,CONFIG)
        print("Configuration is %x" % buf0)

    def SwitchTableToValue (self):
        for x in plSwitchTable:
            a = plSwitchTable[x]
            v = 0
            for i in range(6):
                v = v + (a[i]<<i)
                self.plVal[x] = v

    def setPlByName(self,plName) :
        if(plName in self.plVal):
            if(self.plCtl) :
                try:
                    self.i2cBus.write_byte_data(self.plAddr, GPIOR, self.plVal[plName])
                except:
                    print("unexpected I2C error on PL write")
            else :
                print("There is not PLcontrol for theis kenwood")
        else :
            print("I dont know a code for PL %s" %plName)
