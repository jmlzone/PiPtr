import datetime
import os
import subprocess
import re
import string


# This file is the "user level commands" and the mapping from the
# touch tone codes to the functions.

# user functions or "marcos" below are some examples.
# the commands here work on both ports.
# for commands that should work on the port where they came in...
# a command can affect the other port....

def test123(port):
    print("test123")
    port.tx.tailBeepWav = '../sounds/Tink.wav'
    sys.stdout.flush()

def test456(port):
    print("test456")
    port.tx.tailBeepWav = '../sounds/Submarine.wav'
    sys.stdout.flush()

def test789(port):
    print("test789")
    port.tx.tailBeepWav = '../sounds/Glass.wav'
    sys.stdout.flush()

def cmdWithArg(port,arg):
    print("port %d command got %d" %(port.portnum, arg))
    sys.stdout.flush()

def beepMethod(port,arg):
    port.tx.beepMethod = arg
    print("port %d Tail Method Set to %d" %(port.portnum,arg))
    sys.stdout.flush()

def rptDown(port):
    print("Shutting down")
    port1.tx.down()
    port2.tx.down()
    GPIO.cleanup()
    exit(-1)

def rptOn(port):
    port.rx.disabled = False
def rptOff(port):
    port.rx.disabled = True
    port.tx.down()
    
def setLinkState(port,arg) :
    port.linkState = arg # should probably queue some message
    if(arg == 0) :
        port.linkVotes = 0

def linkBoth(port,arg) :
    setLinkState(port,arg)
    setLinkState(port.other,arg)
    
def talkingClock(card,prefix = 'its',format="%I %M %p, %A %B %_d"):
    dt = datetime.datetime.now()
    ds = dt.strftime(format)
    myTime = prefix + " "+ ds
#    device = string.replace(card,'sysdefault:CARD=','')
    device = card.replace('sysdefault:CARD=','')
    os.environ['ALSA_CARD'] = device
    subprocess.call(['/usr/bin/espeak', myTime], shell=False)

def say(card,msg):
    device = card.replace('sysdefault:CARD=','')
    os.environ['ALSA_CARD'] = device
    subprocess.call(['/usr/bin/espeak', msg], shell=False)

def tailClock(port) :
    port.tx.addTailMsg(talkingClock,{'format': "%I %M %p"},True,False,False,None)

def badCmd(port) :
    resp = "I did not undertsnad the command on port %d" % (port.portnum)
    port.tx.addTailMsg(say,resp,False,False,False,None)
    port.tx.addTailMsg([port.tx.localPath('../bin/mout')],[ '20', '660', '5000', "bad"],True,False,False,None)

def cmdMode(port) :
    port.fsm.cmdOn()
    resp = "Set port %d Command mode on" % (port.portnum)
    port.tx.addTailMsg(say,resp,False,False,False,None)
    print("Command Mode")
    sys.stdout.flush()

def setHwioIn(port,arg) :
    if(arg <0 or arg >7) :
        badCmd(port)
    else :
        resp = "Set port %d bit %d to input" % (port.portnum,arg)
        port.tx.addTailMsg(say,resp,False,False,False,None)
        if(port.portnum ==2) :
            arg = arg+8
        hwio.setup(arg,1,pull_up_down=1)
        port.tx.addTailMsg([port.tx.localPath('../bin/mout')],[ '20', '660', '5000', "OK"],False,False,False,None)
def setHwioOut(port,arg) :
    if(arg <0 or arg >7) :
        badCmd(port)
    else :
        resp = "Set port %d bit %d to output" % (port.portnum,arg)
        port.tx.addTailMsg(say,resp,False,False,False,None)
        if(port.portnum ==2) :
            arg = arg+8
        hwio.setup(arg,0,initial=0)
        port.tx.addTailMsg([port.tx.localPath('../bin/mout')],[ '20', '660', '5000', "OK"],False,False,False,None)
def hwioOut0(port,arg) :
    if(arg <0 or arg >7) :
        badCmd(port)
    else :
        resp = "Set port %d bit %d low" % (port.portnum,arg)
        port.tx.addTailMsg(say,resp,False,False,False,None)
        if(port.portnum ==2) :
            arg = arg+8
        hwio.output(arg,0)
        port.tx.addTailMsg([port.tx.localPath('../bin/mout')],[ '20', '660', '5000', "OK"],False,False,False,None)
def hwioOut1(port,arg) :
    if(arg <0 or arg >7) :
        badCmd(port)
    else :
        resp = "Set port %d bit %d high" % (port.portnum,arg)
        port.tx.addTailMsg(say,resp,False,False,False,None)
        if(port.portnum ==2) :
            arg = arg+8
        hwio.output(arg,1)
        port.tx.addTailMsg([port.tx.localPath('../bin/mout')],[ '20', '660', '5000', "OK"],False,False,False,None)

# command table.
# the command table can be in the format of the long list or you can add things like shown at the end.
#
cmdlist =[("123$","test123"), # the $ at the end forces an exact match
          ("456","test456"),
          ("789","test789")]
cmdlist = cmdlist + [("123(\d+)", "cmdWithArg")] # rexexp type argument needed 1 or more decimal digits.
cmdlist = cmdlist + [("DDDDD", "rptDown")]
cmdlist = cmdlist + [("2337(\d)", "beepMethod")]
cmdlist = cmdlist + [("5465(\d)", "linkBoth")]
cmdlist = cmdlist + [("84$", "tailClock")]
cmdlist = cmdlist + [("CCCC$", "cmdMode")]
cmdlist = cmdlist + [("1011(\d)", "setHwioIn")]
cmdlist = cmdlist + [("1010(\d)", "setHwioOut")]
cmdlist = cmdlist + [("1001(\d)", "hwioOut1")]
cmdlist = cmdlist + [("1000(\d)", "hwioOut0")]

# command processor
def cmdprocess (q,port) :
    """ This is a touch tone command processor routine.  There is a queue
and a process thread for each port it gets the port specific touch
tone queue and the port for context.  Its up to a command to decide if
it acts globally or uses port context """
    while (True) :
        tone = str(q.get()) # block until somthing is ready
        if (tone == " ") : # terminator at end of rx
            if(len(port.cmd) >0) :
                logit("Looking for command: %s on port %d" %( port.cmd, port.portnum))
                found = 0
                for c in cmdlist :
                    #print(c)
                    (name,func) = c
                    m = re.match(name,port.cmd)
                    if(m != None) :
                        found = 1
                        if(len(m.groups()) ==1) :
                            result = eval(func+"(port,"+m.group(1)+")")
                        else:
                            result = eval(func+"(port)")
                        break
                if(not found) :
                    print("oops not found") # que no sound

            port.cmd = "" # null out the command
        else :
            port.cmd = port.cmd + tone
            print("Port" + str(port.portnum) + ": " + tone)
