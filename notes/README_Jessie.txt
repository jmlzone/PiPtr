 diskutil list
 diskutil unmountDisk /dev/disk3
 sudo dd bs=1m if=/Users/jml/Downloads/2016-05-27-raspbian-jessie.img of=/dev/rdisk3
 diskutil eject /dev/disk3

sudo apt-get install gnustep-gui-runtime
say "hello"

espeak
libttspico-utils

see also pyalsaaudio

git clone git://github.com/swharden/Python-GUI-examples

* sudo apt-get install -y python-dev
wget https://sourceforge.net/projects/pyqt/files/sip/sip-4.18.1/sip-4.18.1.tar.gz
tar xfz sip-4.18.1.tar.gz
cd sip-4.18.1/
make
sudo make install

sudo apt-get install qt4-dev-tools

wget http://sourceforge.net/projects/pyqt/files/PyQt4/PyQt-4.11.4/PyQt-x11-gpl-4.11.4.tar.gz
python configure-ng.py
make
sudo make install

git clone https://github.com/pyqtgraph/pyqtgraph
cd pyqtgraph/
python setup.py build
sudo python setup.py install

sudo apt-get install -y python-pyaudio
sudo apt-get install -y python-matplotlib
sudo apt-get install -y python-scipy

sudo apt-get install -y libasound2-dev
  cc ... -lasound
  ./alsaOut sysdefault:CARD=Device

cc mout.c multimon/costabi.c -lasound -o mout
        device             wpm freq amplitiude
mout sysdefault:CARD=Device 13 440  1000
./mout sysdefault:CARD=Device 22 660  1000 "de N1ddk/r "
on mac:
ssh-keygen -t rsa -b1024
scp ~/.ssh/id_rsa.pub pi@192.168.0.114:/home/pi/.ssh/authorized_keys

sudo pip install cython

wget http://www.whence.com/minimodem/minimodem-0.24.tar.gz

see ~/c/multipmon, now working with alsa_input

how to set the audio ouput with a variable:
 export ALSA_CARD=Device
 export ALSA_PCM_CARD=Device
 speaker-test -f 600
 
Or Device_1 for the next card

sudo apt-get install espeak
espeak -v en-us "hello world"
talking clocks
   say `date +"its %I %M %p, %A %B %_d"`
   date +"its %I %M %p, %A %B %_d" | espeak
 
#!/usr/bin/python
import time
import socket
import os.path
import RPi.GPIO as GPIO
import subprocess
import sys
from threading import Timer
#!/usr/bin/python
import time
import socket
import os.path
import RPi.GPIO as GPIO
import subprocess
import sys
from threading import Timer


enable spi in rapi-config

speaker-test -f 1000 -D sysdefault:CARD=Device -c1 -t sine
amixer -c 1 sset 'Speaker' 100%
amixer -c 1 sset 'Mic' 0
amixer -c 1 sset 'Mic' capture 87%

arecord -D sysdefault:CARD=Device_1 -F S16_LE -r 22050 idle.wav
aplay -D sysdefault:CARD=Device idle.wav

sudo apt-get install realvnc-vnc-server
(connect using user password, not vnc password)
