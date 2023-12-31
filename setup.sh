#!/bin/bash
#
# this script will install all the needed updates and packages for
# running PiPtr
echo "Updating and upgrading"
sudo apt-get update
sudo apt-get upgrade -y
echo "----------------------------------------------------------------------"

echo " installing needed packages"
sudo apt-get install -y python-dev python-pyaudio libasound2-dev espeak python3-smbus scons python-dev swig raspi-gpio emacs telnet
echo "----------------------------------------------------------------------"

echo " installing python3 alsa audio"
sudo -H pip3 install pyalsaaudio
echo "----------------------------------------------------------------------"

echo "installing pixel driiver"
cd ~
git clone https://github.com/jgarff/rpi_ws281x
cd rpi_ws281x/
scons
cd python
python3 ./setup.py build
sudo python3 ./setup.py install
echo "----------------------------------------------------------------------"

echo "installing dht driver"
cd ~
git clone https://github.com/adafruit/Adafruit_Python_DHT.git
cd Adafruit_Python_DHT
sudo python3 setup.py install
echo "----------------------------------------------------------------------"

sudo apt install -y automake libtool alsa-utils alsaplayer-alsa libasound2 libasound2-dev python3-alsaaudio python3-pyalsa
echo "getting updated espreak with asla interface:"
cd ~
git clone https://github.com/jmlzone/espeak-ng
cd espeak-ng/
./autogen.sh
./configure
make
sudo make install



echo "done"

