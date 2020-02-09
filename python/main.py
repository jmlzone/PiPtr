#!/usr/bin/python3
# This is the main repeater code
#
# basic flow
# 1) create the instances for the 2 ports.
# 2) run auto tune routine to find which soundcard is connected to which port (TBD)
# 3) Load xml config
# 4) Annotate the ports with their sound card
# 5) start thread for gui (daemon) (tbd)
# 6) start thread for command back ends (daemon) (tdb) 
# 7) start the threads for the 2 ports by calling their run methods as deamons
# wait forever
import sys
import time
import socket
import os.path
try:
    import RPi.GPIO as GPIO
except:
    sys.path.append('hostsim')
    import RPi.GPIO as GPIO
import subprocess
import threading
import radioPort
import datetime
import signal, os
import code
import re
import queue
from multiprocessing import Process
import state
import fpPixels
import tcpSocketCmd
import socketPython
import ipPort

def create_parser():
    """ Create an object to parse the command line arguments."""
    from optparse import OptionParser
    usage = "Usage: %s [options]" %__file__
    parser = OptionParser(usage)
    parser.add_option("--writeXML", "-w", dest="writeXML", default=False,
                      action="store_true",
                      help="""read in current XML config (if one can be found)
or use built in defaults. Then write out a config file for editing."""
                      )
    parser.add_option("--verbose", "-v", dest="verbose", default=False,
                      action="store_true",
                      help="""Print extra debug messages"""
                      )
    parser.add_option("--portdetect", "-d", dest="portdetect", default=False,
                      action="store_true",
                      help="""force port detection even if configured off"""
                      )
    parser.add_option("--exitafterdetection", "-e", dest="exitdetect", default=False,
                      action="store_true",
                      help="""force port detection even if configured off then exit"""
                      )
    parser.add_option("--nosound", "-n", dest="nosound", default=False,
                      action="store_true",
                      help="""configure all ports to onboard sound output only"""
                      )
    parser.add_option("--tunekenwood", "-k", dest="tunekenwood", default=False,
                      action="store_true",
                      help="""Go into tune kenwood mode"""
                      )
    return parser
class top:
    def __init__ (self) :
        self.host = socket.gethostname()
        self.installPath = os.path.dirname(os.path.realpath(__file__))
        self.localPath = os.path.abspath(self.installPath + "/../" + self.host)
        self.xmlvars = []
        self.options = {}
    def findFileOnPath (self,baseNameList) :
        for basename in baseNameList :
            for f in [os.path.join(self.localPath,basename), os.path.join(self.installPath,basename)] :
                if os.path.isfile(f) :
                    return f
        return False
    def absPath(self,file) :
        return (os.path.abspath(os.path.join(self.installPath,file)))
top = top()
parser= create_parser()
top.options,args = parser.parse_args()
sys.path.insert(0,top.localPath)
import gui
from logit import logit
import xmlio
import hwio as HWIO
cmdFile = top.findFileOnPath([top.host + 'Cmd.py', 'mycmd.py'])
if cmdFile :
    logit("Load command file: " + cmdFile)
    exec(compile(open(cmdFile).read(), cmdFile, 'exec'))
    logit("Command file Load done")

def hup_handler(signum, frame):
    print('Hup interrupt, Going interactive', signum)
    code.interact(local=dict(globals(), **locals()))

def int_handler(signum, frame):
    print('Int interrupt, Shutting down', signum)
    port1.tx.down()
    port2.tx.down()
    print("turning off sound cards and GPIO interupts")
    hwio.i2cBus.write_byte_data(HWIO.GPIOEX3, HWIO.GPIOR,129)
    GPIO.cleanup()
    fp.cleanup()
    #p0.terminate()
    sys.exit(-1)
signal.signal(signal.SIGHUP, hup_handler)
signal.signal(signal.SIGINT, int_handler)

# lists of the data that will be stored in the xml configuration
xmlvars = ( )
GPIO.setmode(GPIO.BOARD)
q1 = queue.Queue()
q2 = queue.Queue()

if(top.options.tunekenwood) :
    import kenwoodTK
    top.kenwood=kenwoodTK.kenwoodTK()
    
gui = gui.gui(top)
top.gui=gui
globalState = state.state(top,gui)
top.globalState=globalState
port1 = radioPort.radioPort(1, q1, globalState)
port2 = radioPort.radioPort(2, q2, globalState)
port1.other = port2
port2.other = port1
top.port1 = port1
top.port2 = port2
port3 = ipPort.ipPort(top)
top.port3=port3
hwio = HWIO.hwio(top)
port1.hwio = hwio
port2.hwio = hwio
top.hwio=hwio
fp = fpPixels.fpPixels(top.globalState)
cmdSock = tcpSocketCmd.tcpSocketCmd(globals(), q1,q2)
sp = socketPython.socketPython((dict(globals(), **locals())))
# load the config
logit("Load XML config")
xmlFile = top.findFileOnPath([top.host + '.xml', 'config.xml'])
if xmlFile :
    logit("Load XML config : " + xmlFile )
    xmlio.loadXml(top,xmlFile)
logit("Load XML Done")
if(top.options.writeXML) :
    gui.guiSave()
    exit(0)
if(gui.gui) :
    gui.init()
hwio.init_all()
# commend out the fp.connect when no pixes to reduce load and hangs
fp.connect()
if(top.options.tunekenwood) :
    if (gui.gui) :
        gui.run()
   
if(port1.enabled) :
    port1.fsmThread = threading.Thread(target=port1.run)
    port1.fsmThread.daemon = True
    port1.fsmThread.start()
    port1.cmdThread = threading.Thread(target=cmdprocess, args=(q1,port1))
    port1.cmdThread.daemon = True
    port1.cmdThread.start()
if(port2.enabled) :
    port2.fsmThread = threading.Thread(target=port2.run)
    port2.fsmThread.daemon = True
    port2.fsmThread.start()
    port2.cmdThread = threading.Thread(target=cmdprocess, args=(q2,port2))
    port2.cmdThread.daemon = True
    port2.cmdThread.start()

#g = threading.Thread(target=gui.run)
#g.daemon = True
#g.start()
hwioIThread = threading.Thread(target=hwio.runUInts)
hwioIThread.daemon = True
hwioIThread.start()
hwioAThread = threading.Thread(target=hwio.runAdc)
hwioAThread.daemon = True
hwioAThread.start()
cmdSockThread = threading.Thread(target=cmdSock.run)
cmdSockThread.daemon = True
cmdSockThread.start()
spThread = threading.Thread(target=sp.run)
spThread.daemon = True
spThread.start()
if (gui.gui) :
    gui.run()
else:
    while(True) :
        time.sleep(100)
