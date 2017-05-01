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
INTSTATIC = 0xff   # all intesisies static
class kenwoodTK:
    """ A Kenwood TK701 (VHF) or Kenwood TK801 (UHF) With the proms removed and
    a max7314 driging the prom outputs to be frequency agile 
    """
    def __init__ (self,addr) :
        self.addr = addr
        self.i2cBus = smbus.SMBus(1)
        """ initialize max7314 for static outputs,
            txrx switching with the blink input 
        """
        self.i2cBus.write_i2c_block_data(self.addr,CONFIG_L,[ALLOUT,ALLOUT]);
        self.i2cBus.write_byte_data(self.addr,MASTERO16,(MASTERSTATIC |  O16STATIC))
        self.i2cBus.write_byte_data(self.addr,CONFIG,(O16P0 |  GLOBINTEN |  BLINKEN))

    def setFreqDirect(self,tx_freq, rx_freq) :
        if(tx_freq < 200000) :
            tx_code = (tx_freq -21400) /5 # vhf settings
            rx_code = (rx_freq -21400) /5
        else :
            tx_code = ((tx_freq -21400) * 2) / 25 # uhf settings
            rx_code = ((rx_freq -21400) * 2) / 25
            
        self.pllSetTx(tx_code)
        self.pllSetRx(rx_code)


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

