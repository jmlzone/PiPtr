#!/bin/bash
#
# this script will install all the needed updates and packages for
# running PiPtr
echo "Updating and upgrading"
sudo apt-get update
sudo apt-get upgrade
echo "----------------------------------------------------------------------\n"
echo " installing needed packages"
sudo apt-get install -y python-dev python-pyaudio libasound2-dev espeak python3-smbus scons python-dev swig raspi-gpio
echo "----------------------------------------------------------------------\n"

echo " installing python3 alsa audio"
sudo -H pip3 install pyalsaaudio
echo "----------------------------------------------------------------------\n"

echo "installing pixel driiver"
cd ~
git clone https://github.com/jgarff/rpi_ws281x
cd rpi_ws281x/
scons
cd python
python3 ./setup.py build
sudo python3 ./setup.py install
echo "----------------------------------------------------------------------\n"

echo "installing dht driiver"
cd ~
git clone https://github.com/adafruit/Adafruit_Python_DHT.git
cd Adafruit_Python_DHT
sudo python3 setup.py install
echo "----------------------------------------------------------------------\n"
