#!/bin/bash
if [ $DISPLAY = ":0" ]; then
   echo "On console, starting PiPtr in 30 seconds"
   sleep 30
   echo "Now"
   mkdir -p /home/pi/log
   log=$(date +"/home/pi/log/%Y_%m_%d_%I_%M_%p.log")
   cd /home/pi/PiPtr/python
   sudo ./main.py >& $log
else
  echo "Not on console not starting"
fi
