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


def talkingClock(card,prefix = 'its'):
    dt = datetime.datetime.now()
    ds = dt.strftime("%I %M %p, %A %B %_d")
    myTime = prefix + " "+ ds
    device = string.replace(card,'sysdefault:CARD=','')
    os.environ['ALSA_CARD'] = device
    subprocess.call(['/usr/bin/espeak', myTime], shell=False)


# command table.
# the command table can be in the format of the long list or you can add things like shown at the end.
#
cmdlist =[("123$","test123"), # the $ at the end forces an exact match
          ("456","test456"),
          ("789","test789")]
cmdlist = cmdlist + [("123(\d+)", "cmdWithArg")] # rexexp type argument needed 1 or more decimal digits.
cmdlist = cmdlist + [("DDDDD", "rptDown")]
cmdlist = cmdlist + [("2337(\d)", "beepMethod")]

# command processor
def cmdprocess (q,port) :
    """ This is a touch tone command processor routine.  There is a queue
and a process thread for each port it gets the port specific touch
tone queue and the port for context.  Its up to a command to decide if
it acts globally or uses port context """
    while (True) :
        tone = q.get() # block until somthing is ready
        if (tone == " ") : # terminator at end of rx
            if(len(port.cmd) >0) :
                found = 0
                for c in cmdlist :
                    print(c)
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
