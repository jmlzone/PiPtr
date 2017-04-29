#!/usr/bin/python
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

import time
import socket
import os.path
import RPi.GPIO as GPIO
import subprocess
import sys
import threading
import radioPort
import datetime
import signal, os
import code
import re
import queue
from multiprocessing import Process
class top:
    def __init__ (self) :
        self.host = socket.gethostname()
        self.installPath = os.path.dirname(os.path.realpath(__file__))
        self.localPath = os.path.abspath(self.installPath + "/../" + self.host)
        self.xmlvars = []
top = top()
sys.path.insert(0,top.localPath)
import gui
from logit import logit
import xmlio
import hwio

exec(compile(open('cmd.py').read(), 'cmd.py', 'exec'))

def hup_handler(signum, frame):
    print('Hup interrupt, Going interactive', signum)
    code.interact(local=dict(globals(), **locals()))

def int_handler(signum, frame):
    print('Int interrupt, Shutting down', signum)
    port1.tx.down()
    port2.tx.down()
    GPIO.cleanup()
    #p0.terminate()
    exit(-1)
signal.signal(signal.SIGHUP, hup_handler)
signal.signal(signal.SIGINT, int_handler)

# audio control value defaults (overridden by xml config)
R0 = 150
R1 = 2
R2 = 50
R3 = 20
PGA0 = 6
TCON0 = 0x1ff
# lists of the data that will be stored in the xml configuration
xmlvars = ( 'R0', 'R1', 'R2', 'R3', 'PGA0', 'TCON0' )
GPIO.setmode(GPIO.BOARD)
q1 = queue.Queue()
q2 = queue.Queue()
gui = gui.gui(top)
port1 = radioPort.radioPort(1, q1, gui)
port2 = radioPort.radioPort(2, q2, gui)
port1.other = port2
port2.other = port1
hwio = hwio.hwio(top)
port1.hwio = hwio
port2.hwio = hwio
# load the config
top.port1 = port1
top.port2 = port2
top.gui=gui
top.hwio=hwio
logit("Load XML config")
for f in [top.localPath +"/" + top.host +".xml" , top.localPath +"/config.xml", top.installPath +"/config.xml"] :
    if os.path.isfile(f) :
        logit("Load XML config : " + f )
        xmlio.loadXml(top,f)
        break
logit("Load XML Done")
gui.init()
hwio.init_all()
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
gui.run()
