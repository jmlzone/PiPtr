def defaultCallback(object, value) :
    print( 'object ' + object + ' was set to ' + str(value))
 
def voltageAlarm(name,value) :
    if(value < 10.5) :
        print( "voltage %s too low: %d" %(name,value))
    elif (value >13.6) :
        print( "voltage %s too high: %d" %(name,value))
    else :
        print( "voltage %s OK: %d" %(name,value))
 
class GlobalData(object):
    def __init__(self, name, defValue=False, callbacks=None):
        self._value = defValue
        self.callbacks = callbacks if callbacks else list()
        self.name = name
    @property
    def value(self):
        return(self._value)
    @value.setter
    def value(self,value) :
        self.setValue(self,value)
    def setValue(self,value,color=None) :
        if(self._value != value or True) :
            self._value = value
            self._color = color
            for callback in self.callbacks:
                if(color == None) :
                    callback(self.name,self.value)
                else :
                    callback(self.name,self.value,color)
    def addCallback(self,callback):
        if callable(callback):
            self.callbacks.append(callback)
        else:
            print("Callback is not callable")
    def rmCallback(self,callback) :
        self.callbacks.remove(callback)

class state(object):    
    def __init__(self,top,gui) :
        self.top = top
        self.cor1 = GlobalData('cor1')
        self.ctcss1 = GlobalData('ctcss1')
        self.softCtcss1 = GlobalData('softCtcss1')
        self.tx1 = GlobalData('tx1')
        self.cor2 = GlobalData('cor2')
        self.ctcss2 = GlobalData('ctcss2')
        self.softCtcss2 = GlobalData('softCtcss2')
        self.tx2 = GlobalData('tx2')
        self.battVolts = GlobalData('Battvolts')
        if(gui.gui) :
            self.cor1.addCallback(gui.updateItem)
            self.ctcss1.addCallback(gui.updateItem)
            self.softCtcss1.addCallback(gui.updateArray)
            self.tx1.addCallback(gui.updateItem)
            self.cor2.addCallback(gui.updateItem)
            self.ctcss2.addCallback(gui.updateItem)
            self.softCtcss2.addCallback(gui.updateArray)
            self.tx2.addCallback(gui.updateItem)

