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
from threading import Timer
import radioPort
import datetime
import signal, os
import code
import re
import Queue
from multiprocessing import Process
execfile('xmlio.py')

def hup_handler(signum, frame):
    print 'Hup interrupt, Going interactive', signum
    code.interact(local=dict(globals(), **locals()))

def int_handler(signum, frame):
    print 'Int interrupt, Shutting down', signum
    port1.tx.down()
    port1.tx.down()
    GPIO.cleanup()
    #p0.terminate()
    exit(-1)

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
q1 = Queue.Queue
q2 = Queue.Queue
port1 = radioPort.radioPort(1, q1)
port2 = radioPort.radioPort(2, q2)

# load the config
loadXml('config.xml')
if(port1.enabled) :
    p1 = threading.Thread(target=p1.run)
    p1.daemon = True
    p1.start()
    d1 = threading.Thread(target=cmdprocess, args=(q1,port1))
    d1.daemon = True
    d1.start()
if(port2.enabled) :
    p2 = threading.Thread(target=p2.run)
    p2.daemon = True
    p2.start()
    d2 = threading.Thread(target=cmdprocess, args=(q2,port2))
    d2.daemon = True
    d2.start()
