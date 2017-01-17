#!/usr/bin/python
# $Id$

# routines to read and write digital audio controls
#

# Import all the libraries we need to run
import sys
import os
from time import sleep
import spidev


# Function to read SPI data from MCP3008 chip
# Open SPI bus
spi = spidev.SpiDev()
# Channel must be an integer 0-7
def ReadLoc(loc):
    cmd = ((loc & 0x0f) << 4)+12
    #print "cmd is %x" % cmd
    spi.open(0,1)
    data16 = spi.xfer2([cmd,0])
    data = ((data16[0]&1) << 8) + data16[1]
    if((data16[0] & 1) == 2) :
        print "SPI Command Error"
    spi.close()
    return data

def WriteRes(r,val):
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
    spi.open(0,1)
    data16 = spi.xfer2([cmd,val])
    if((data16[0] & 1) == 2) :
        print "SPI Command Error"
    spi.close()

def WritePGAChan(chan):
    cmd = 65
    val = chan & 7
    spi.open(0,0)
    data16 = spi.xfer2([cmd,val])
    spi.close()

def WritePGAGain(gain):
    cmd = 64
    val = gain & 7
    spi.open(0,0)
    data16 = spi.xfer2([cmd,val])
    spi.close()


#WriteRes(0,128)
#WriteRes(1,1)
#WriteRes(2,255)
#WriteRes(3,244)

#WritePGAChan(0)
#WritePGAGain(4)

def ReadAll():
    for i in range(11):
        d = ReadLoc(i)
        print "Address %d data %x" % (i,d)

