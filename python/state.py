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
        if(self._value != value) :
            self._value = value
            for callback in self.callbacks:
                callback(self.name,self.value)
    def addCallback(self,callback):
        if callable(callback):
            self.callbacks.append(callback)
        else:
            print("Callback is not callable")
    def rmCallback(self,callback) :
        self.callbacks.remove(callback)

class state(obj):    
    def __init__(self,top) :
        self.top = top
        self.cor1 = defStateObj('cor1')
        self.ctcss1 = stateObj('ctcss1')
        self.softCtcss1 = stateObj('softCtcss1')
        self.tx1 = stateObj('tx1')
        self.cor2 = stateObj('cor2')
        self.ctcss2 = stateObj('ctcss2')
        self.softCtcss2 = stateObj('softCtcss2')
        self.tx2 = stateObj('tx2')
        self.battVolts('Battvolts')
        if(self.top.gui.gui) :
            self.cor1.addCallback(self.top.gui.updateItem)
            self.ctcss1.addCallback(self.top.gui.updateItem)
            self.ctcss1.addCallback(self.top.gui.updateArray)
            self.tx1.addCallback(self.top.gui.updateItem)
            self.cor2.addCallback(self.top.gui.updateItem)
            self.ctcss2.addCallback(self.top.gui.updateItem)
            self.ctcss2.addCallback(self.top.gui.updateArray)
            self.tx2.addCallback(self.top.gui.updateItem)

