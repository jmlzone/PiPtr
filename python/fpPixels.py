"""Front Panel LED's implemented as neopixels
"""
from neopixel import *
from rptFsm import gpTimer
import re
# LED strip configuration:
LED_COUNT      = 24      # Number of LED pixels.
LED_PIN        = 21      # GPIO pin connected to the pixels (18 uses PWM!).
LED_FREQ_HZ    = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA        = 10       # DMA channel to use for generating signal (try 5)
LED_BRIGHTNESS = 255     # Set to 0 for darkest and 255 for brightest
LED_INVERT     = False   # True to invert the signal (when using NPN transistor level shift)
LED_CHANNEL    = 0       # set to '1' for GPIOs 13, 19, 41, 45 or 53
LED_STRIP      = ws.WS2811_STRIP_GRB   # Strip type and colour ordering

class fpPixels :
    def __init__ (self,state) :
        # Create NeoPixel object with appropriate configuration.
        self.strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, freq_hz=LED_FREQ_HZ, dma=LED_DMA, invert=LED_INVERT, brightness=LED_BRIGHTNESS, channel=LED_CHANNEL, strip_type=LED_STRIP)
        # Intialize the library (must be called once before other functions).
        self.strip.begin()
        self.state=state
        self.brightness = 50 # 0 = off 100 = full bright 
        self.leds = {'cor1':0,  'ctcss1':1,  'cmd1':2,  'softCtcss1':3,  'tx1':11,
                     'cor2':12, 'ctcss2':13, 'cmd2':14, 'softCtcss2':15, 'tx2':23}
        self.refreshTimer = gpTimer(0.03,self.refresh)
        self.running = False # to prevent reentrance from multiple threads
        fi = "/usr/share/X11/rgb.txt"
        rgbExp = re.compile('\s*(\d+)\s+(\d+)\s+(\d+)\s+(.*)')
        f = open(fi,'r')
        self.rgbDict = {}
        for line in f:
            match = rgbExp.match(line)
            if(match) :
                (r,g,b,name) = match.groups()
                lname = name.lower()
                cname = lname.replace(" ","")
                rgb = (int(r)<<16) + (int(g)<<8) + int(b)
                #print( name + " -> " + lname  + " -> " + cname + r + " " + g + " " + b +" %X" % rgb)
                if not cname in self.rgbDict :
                    self.rgbDict[cname] = rgb
        f.close()
        self.clear()
    def clear (self) :
        for i in range(LED_COUNT) :
            self.strip.setPixelColor(i,0)
        #self.strip.show()
        self.refreshTimer.run()

    def cleanup (self) :
        for i in range(LED_COUNT) :
            self.strip.setPixelColor(i,0)
        self.strip.show()

    def dim(self,rgbval):
        b=(rgbval & 255) * self.brightness / 100
        g=((rgbval>>8) & 255) * self.brightness / 100
        r=((rgbval>>16) & 255) * self.brightness / 100
        rgb = (int(r)<<16) + (int(g)<<8) + int(b)
        return(rgb)
    
    def setColorByName (self,led,name) :
        cname = name.lower().replace(" ","")
        if cname in self.rgbDict :
            self.setColorByValue(led,self.rgbDict[cname])
        else:
            self.setColorByValue(led,self.rgbDict['pink'])
    def setColorByValue (self,led,value) :
        self.strip.setPixelColor(led,self.dim(value))
        self.refreshTimer.run()
        
    def refresh(self) :
        """ called from timer thread when the timer expires to gater all events in a 30 ms range
        """
        if not self.running:
            self.running = True
            self.strip.show()
            self.running = False
        self.refreshTimer.expired = True
        self.refreshTimer.isrunning = False
    def connect(self) :
         self.state.cor1.addCallback(self.updateItem)
         self.state.ctcss1.addCallback(self.updateItem)
         self.state.cmd1.addCallback(self.updateItem)
         self.state.softCtcss1.addCallback(self.updateArray)
         self.state.tx1.addCallback(self.updateItem)
         self.state.cor2.addCallback(self.updateItem)
         self.state.ctcss2.addCallback(self.updateItem)
         self.state.cmd2.addCallback(self.updateItem)
         self.state.softCtcss2.addCallback(self.updateArray)
         self.state.tx2.addCallback(self.updateItem)
    def updateItem(self,name,value,color=None) :
        if(value) :
            if(color == None):
                self.setColorByValue(self.leds[name], 127<<8)
            else :
                self.setColorByName(self.leds[name], color)
        else :
            self.setColorByValue(self.leds[name], 0)
    def updateArray(self,name,value):
        for i in range (8) :
            if (value[i]) :
                self.setColorByValue(self.leds[name]+i, 127<<8)
            else:
                self.setColorByValue(self.leds[name]+i, 0)
 
