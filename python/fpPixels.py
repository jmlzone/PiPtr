"""Front Panel LED's implemented as neopixels
"""
from neopixel import *
# LED strip configuration:
LED_COUNT      = 60      # Number of LED pixels.
LED_PIN        = 21      # GPIO pin connected to the pixels (18 uses PWM!).
LED_FREQ_HZ    = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA        = 5       # DMA channel to use for generating signal (try 5)
LED_BRIGHTNESS = 255     # Set to 0 for darkest and 255 for brightest
LED_INVERT     = False   # True to invert the signal (when using NPN transistor level shift)
LED_CHANNEL    = 0       # set to '1' for GPIOs 13, 19, 41, 45 or 53
LED_STRIP      = ws.WS2811_STRIP_GRB   # Strip type and colour ordering

class fpPixels :
    def __init__ (self,state) :
        # Create NeoPixel object with appropriate configuration.
        self.strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL, LED_STRIP)
        # Intialize the library (must be called once before other functions).
        self.strip.begin()
        self.state=state
        self.leds = {'cor1':0, 'ctcss1':1, 'softCtcss1':2, 'tx1':10,
                     'cor2':12, 'ctcss2':13, 'softCtcss2':14, 'tx2':22}
    def clear (self) :
        for i in range(LED_COUNT) :
            self.strip.setPixelColor(i,0)
        self.strip.show()

    def setColorByName (self,led,name) :
        pass
    def setColorByValue (self,led,value) :
        self.strip.setPixelColor(led,value)
        self.strip.show()
    def connect(self) :
         self.state.cor1.addCallback(self.updateItem)
         self.state.ctcss1.addCallback(self.updateItem)
         self.state.softCtcss1.addCallback(self.updateArray)
         self.state.tx1.addCallback(self.updateItem)
         self.state.cor2.addCallback(self.updateItem)
         self.state.ctcss2.addCallback(self.updateItem)
         self.state.softCtcss2.addCallback(self.updateArray)
         self.state.tx2.addCallback(self.updateItem)
    def updateItem(self,name,value,color=None) :
        if(value) :
            if(color == None):
                self.setColorByValue(self.leds[name], 127<<8)
            else :
                self.setColorByValue(self.leds[name], 127<<16)
        else :
            self.setColorByValue(self.leds[name], 0)
    def updateArray(self,name,value):
        for i in range (8) :
            if (value[i]) :
                self.setColorByValue(self.leds[name]+i, 127<<8)
            else:
                self.setColorByValue(self.leds[name]+i, 0)
 
