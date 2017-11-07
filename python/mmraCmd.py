def cmdMode(port) :
    port.fsm.cmdOn
    print("Command Mode")
    sys.stdout.flush()
cmdlist = cmdlist + [("1250$", "cmdMode")]

def link0(port) :
    setLinkState(port,1)
def link1(port) :
    setLinkState(port,1)
def link1(port) :
    setLinkState(port,1)
cmdlist = cmdlist + [("C0$", "link0")]
cmdlist = cmdlist + [("C1$", "link1")]
cmdlist = cmdlist + [("C2$", "link2")]

def mOk(port) :
    port.tx.addTailMsg([port.localPath('../bin/mout')],[ '20', '660', '5000', "OK"],False,False,False,None)
cmdlist = cmdlist + [("123A$", "mOk")]
cmdlist = cmdlist + [("456B$", "mOk")]
cmdlist = cmdlist + [("789C$", "mOk")]
cmdlist = cmdlist + [("84$", "tailClock")]

def disableAlarm(port) :
    if(port.rx.cmdMode) :
        top.hwio.remove_event_detect(top.hwio.GPA7)
        port.tx.addBeaconMsg(['/usr/bin/aplay', '-D'], self.tx.localPath('../sounds/alarmOff.wav'),True,False,False,None)
def armAlarm(port) :
    if(port.rx.cmdMode) :
        top.hwio.add_event_detect(top.hwio.GPA7, top.hwio.BOTH,alarm)
        port.tx.addBeaconMsg(['/usr/bin/aplay', '-D'], self.tx.localPath('../sounds/alarmOn.wav'),True,False,False,None)
def alarm:
    pass

