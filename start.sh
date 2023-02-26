#!/bin/bash
#
# This can be auto run when the pi starts by addiing to
# ~/.config/lxsession/LXDE-pi/autostart
# ie:
# @lxpanel --profile LXDE-pi
# @pcmanfm --desktop --profile LXDE-pi
# @xscreensaver -no-splash
# @point-rpi
# @lxterminal
# @lxterminal --command /home/pi/PiPtr/start.sh
#
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
