## Raspberry Pi Ham Radio Repeater Controller
The Goal of this project is to develop an inexpensive linking repeater controller with a cost of approximately $50/port vs. current commercial solutions which are closer to $160/port.

This is an extensible linkable controller with both local and remote linking.

* for info on the MMRA network see mmra.org
* for info on this project contact N1DDK@mmra.org.

Most of the code will be in Python, however some of it is in C.

Eventually there will be good documentation and a bug/enhancement
tracking WIKI or some such thing.

Current state: The test repeater is stable on the air but many many
things are still to be done.

## External Programs

[Multimon-NG](https://github.com/EliasOenal/multimon-ng/) is an established, actively developed fork of the 1980's `multimon` by Tom Sailer, with much improved features and style.

## What is a Repeater?
The [MMRA maintains a network of 22 repeaters](http://mmra.org/repeaters/).  
A repeater is basically a receiver, a transmitter and a controller in-between. 
While the network generally works, there are some upgrades we are continually working on.  
One of these efforts being led by me, James N1DDK, is developing a new repeater controller to enhance the remote controllability, monitoring and adjusting of the repeaters. 
Most of the repeater controller in use today are based on designs over 20 years old. 
There have been many advances in technology in the past 20 years. 
This project is bringing a more modern, more scalable and more software based and controllable approach based on mostly standard hardware and using popular modern methods.

There are some guiding principles to this project:

1. No Jumpers, switches or mechanical pots that can be set incorrectly at a site needing a return visit.
2. Open source -- its part of the Ham culture to experiment and share. This will also ensure longevity of the project beyond the initial developers.
3. Better ease of use than similar commercial products.
4. Scalability and cost per port more effective than the commercial products.
5. Mostly software for simple functions like CTCSS encode / decode, DTMF encode / decode, timers, Morse etc.
6. Well documented

Goals:

* Ease of use for users and control operators.
* Web back end to view status and control linking.
* Ability to sell hardware as a fundraiser for MMRA.

To this end I have been working mostly solo with some input from K1IW and W1BRI (and some non members) and I have a working prototype on the air on 224.080 as part of a test platform. 
The next goals will be to make some boards and have further testing and development.

Here is a list of some of the help that is desired:

 * Programming help in C and Python (possibly java/java script for some of the web interface)
 * Schematics design/review for the custom audio board.
 * Documentation help -- there is some basic documentation, but it would be good to have much more on both hardware, software and user guides.
 * Mechanical/sheet metal design for an enclosure, etc
 * Building help, both mechanical and building the initial boards for testing.
 * Testing help using the controller on a bench and trying things before we put them on the air.
 * On the air testing.

Want to learn more?
 There is a Github repository for the software, documentation and issue tracking:
https://github.com/jmlzone/PiPtr
There may be a talk about the project at Boxborough!

Even if you don't know anything about software or repeater controllers you can still help! 
You don't need to know anything to be a documentation volunteer!

Ready to help?
Contact James, n1ddk@mmra.org.
