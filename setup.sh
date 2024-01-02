#!/bin/bash
#
# this script will install all the needed updates and packages for
# running PiPtr
echo "Updating and upgrading"
sudo apt update
sudo apt upgrade -y
echo "----------------------------------------------------------------------"

echo " installing needed packages"
sudo apt install -y python3-dev python3-pyaudio libasound2-dev espeak-ng \
     python3-smbus scons python3-dev swig raspi-gpio emacs telnet \
     cmake automake libtool alsa-utils alsaplayer-alsa libasound2 \
     libasound2-dev python3-alsaaudio python3-pyalsa
echo "----------------------------------------------------------------------"

#echo " installing python3 alsa audio"
#sudo -H pip3 install pyalsaaudio
#echo "----------------------------------------------------------------------"

echo "installing pixel driiver"
cd ~
git clone https://github.com/jgarff/rpi_ws281x
git clone https://github.com/rpi-ws281x/rpi-ws281x-python
cd rpi-ws281x-python/library
rmdir lib
ln -s ../../rpi_ws281x lib
python3 ./setup.py build
sudo python3 ./setup.py install
#sudo chmod a+rw /dev/mem
echo "----------------------------------------------------------------------"

echo "installing dht driver"
cd ~
git clone https://github.com/adafruit/Adafruit_Python_DHT.git
cd Adafruit_Python_DHT
sudo python3 setup.py install
echo "----------------------------------------------------------------------"

echo "getting updated espeak with asla interface:"
cd ~
git clone https://github.com/jmlzone/espeak-ng
cd espeak-ng/
./autogen.sh
./configure
make
sudo make install



echo "done"

