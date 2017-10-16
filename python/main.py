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
class top:
    def __init__ (self) :
        self.host = socket.gethostname()
        self.installPath = os.path.dirname(os.path.realpath(__file__))
        self.localPath = os.path.abspath(self.installPath + "/../" + self.host)
        self.xmlvars = []
    def findFileOnPath (self,baseNameList) :
        for basename in baseNameList :
            for f in [os.path.join(self.localPath,basename), os.path.join(self.installPath,basename)] :
                if os.path.isfile(f) :
                    return f
        return False
    def localPath(self,file) :
        return (os.path.abspath(os.path.join(self.installPath,file)))
top = top()
sys.path.insert(0,top.localPath)
import gui
from logit import logit
import xmlio
import hwio

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
    GPIO.cleanup()
    #p0.terminate()
    sys.exit(-1)
signal.signal(signal.SIGHUP, hup_handler)
signal.signal(signal.SIGINT, int_handler)

# lists of the data that will be stored in the xml configuration
xmlvars = ( )
GPIO.setmode(GPIO.BOARD)
q1 = queue.Queue()
q2 = queue.Queue()
gui = gui.gui(top)
globalState = state.state(top,gui)
port1 = radioPort.radioPort(1, q1, globalState)
port2 = radioPort.radioPort(2, q2, globalState)
port1.other = port2
port2.other = port1
hwio = hwio.hwio(top)
port1.hwio = hwio
port2.hwio = hwio
top.port1 = port1
top.port2 = port2
top.gui=gui
top.hwio=hwio
top.globalState=globalState
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
if(gui.gui) :
    gui.init()
hwio.init_all()
# commend out the fp.connect when no pixes to reduce load and hangs
#fp.connect()
if(port1.enabled) :
    p1 = threading.Thread(target=port1.run)
    p1.daemon = True
    p1.start()
    d1 = threading.Thread(target=cmdprocess, args=(q1,port1))
    d1.daemon = True
    d1.start()
if(port2.enabled) :
    p2 = threading.Thread(target=port2.run)
    p2.daemon = True
    p2.start()
    d2 = threading.Thread(target=cmdprocess, args=(q2,port2))
    d2.daemon = True
    d2.start()

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
