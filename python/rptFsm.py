from logit import logit
import threading
import time
from cmd import talkingClock
class gpTimer:
    def __init__(self, timeout, userHandler=None):  # timeout in seconds
        self.timeout = timeout
        self.expired = False
        self.isrunning = False
        self.handler = userHandler if userHandler is not None else self.defaultHandler
        self.timer = threading.Timer(self.timeout, self.handler)
        #self.timer.start()
        #self.isrunning = True
        
    def reset(self):
        self.timer.cancel()
        self.expired = False
        self.timer = threading.Timer(self.timeout, self.handler)
        self.timer.start()
        self.isrunning = True
        
    def run(self):
        if(not self.isrunning) :
            self.reset()

    def stop(self):
        self.timer.cancel()
        self.isrunning = False
        self.expired = False
        
    def defaultHandler(self):
        self.expired = True
        self.isrunning = False
        #print "default handler called"
        #raise self



class rptFsm :
    """ this is the fsm for the repeater port """
    """ Has timers 
    ID timer
    Time out timer
    tail delay timer
    hang timer
    """

    def __init__(self,port) :
        self.port = port
        self.state = 'idle'
        # Tx related
        self.txTimeoutTimer = gpTimer(self.port.tx.timeout, userHandler = self.txTimeout )
        self.tailTimer = gpTimer(self.port.tx.taildly, userHandler = self.tailMessagePlay)
        self.hangTimer = gpTimer(self.port.tx.hangtime, userHandler = self.tailDone)
        self.idTimer = gpTimer(self.port.tx.idtime,userHandler = self.beaconId)
        self.politeIdTimer = gpTimer(self.port.tx.idtime - self.port.tx.polite)
        self.beaconUpTimer = gpTimer(self.port.tx.txupdly, userHandler = self.beaconRun)

        #rx related
        self.rxTimer = gpTimer(self.port.rx.timeout, userHandler = self.rxTo)
        self.rxIdleTimer = gpTimer(self.port.rx.IdleTimeout, userHandler = self.idleTimeout)
        self.cmdTimer = gpTimer(self.port.rx.cmdTimeout)

        self.lock = threading.Lock()

    def updateTimers(self) :
        """Since the timers are create very early and the times are updated by
           the XML load or commands to change the timing we need a function to
           update them.
        """
        # Tx related
        self.txTimeoutTimer.timeout = self.port.tx.timeout
        self.tailTimer.timeout = self.port.tx.taildly
        self.hangTimer.timeout = self.port.tx.hangtime
        self.idTimer.timeout = self.port.tx.idtime
        self.politeIdTimer.timeout = self.port.tx.idtime - self.port.tx.polite
        self.beaconUpTimer.timeout = self.port.tx.txupdly

        #rx related
        self.rxTimer.timeout = self.port.rx.timeout
        self.rxIdleTimer.timeout = self.port.rx.IdleTimeout
        self.cmdTimer.timeout = self.port.rx.cmdTimeout

        """ Input event functions here
        they need to
        1) acquire the lock
        2) do the next state
        3) releae the lock
    """
    def startUp(self) :
        logit("Port %d startup" % self.port.portnum)
        time.sleep(5 * self.port.portnum)
        self.updateTimers()
        self.getLock()
        self.port.tx.tx()
        time.sleep(1)
        self.port.tx.plGen()
        self.port.tx.sendId()
        logit("Port %d Initial Clock" % self.port.portnum)
        talkingClock(self.port.card, prefix="Start up at")
        time.sleep(1)
        self.port.tx.down()
        logit("Port %d Startup Done." % self.port.portnum)
        self.releaseLock()
        self.idle()

    def beaconId(self) :
        """ entered when the ID timer expires
        Since the default handle is not used, we need to set the expired flag outselves
        """
        self.getLock()
        self.idTimer.expired = True
        self.idTimer.isrunning = False
        self.beacon()
        self.releaseLock()
        
    def updateRx(self, rx) :
        #logit("Update RX state is " + self.state + str(rx))
        # will need to be smarter about the link state
        self.getLock()
        #logit("Update RX state got lock " + self.state)
        if(rx) :
            if(self.state == 'idle') :
                self.repeat()
            elif (self.state == 'beacon') :
                self.cancelBeacon()
                self.repeat()
            elif (self.state == 'tail') :
                self.cancelTail()
                self.repeat()
            elif (self.state == 'repeat') :
                pass
            else:
                logit("Port %d Error Rx active again in state %s " % (self.port.portnum, self.state) )
        else : # rx inactive
            if(self.state == 'repeat') :
                self.tail()
            elif(self.state == 'rxTimeOut') :
                self.rxTimeoutRelease()
            elif(self.state == 'idle' or self.state == 'tail') :
                pass
            else:
                logit("Port %d Error Rx off again in state %s " % (self.port.portnum, self.state) )
        self.releaseLock()
                
    def rxTo(self) :
        """ Entered by the RX time out event 
            Entered into from a timer threadf so no need to be quick.
            Needs to get the lock before changing any state information
        """
        self.getLock()
        self.state = 'rxTimeOut'
        logit("Port %d Rx Time Out" % self.port.portnum)
        self.releaseLock()
        self.rxTimer.expired = True
        self.rxTimer.isrunning = False
        idPlayed = self.port.tx.playMsgs([(["../bin/mout"],[ '20', '660', '5000', "to"],False,False,False,None)])
        # send time out message
        # turn off transmitter (if not linked)
        self.port.tx.plStop()
        self.port.tx.down()
        logit("Port %d Rx Time Out complete" % self.port.portnum)

    def txTimeout(self) :
        """ Entered by the TX time out event """
        self.getLock()
        self.state = 'TxTimeOut'
        logit("Port %d Tx Time Out" % self.port.portnum)
        self.port.tx.playMsgs([(["../bin/mout"],[ '20', '660', '5000', "TX to"],False,False,False,None)])
        # send time out message
        # turn off transmitter (if not linked)
        self.port.tx.down()
        self.idle()
        self.releaseLock()

    def idleTimeout(self) :
        logit("Port %d idle Time Out queued Idle message" % self.port.portnum)
        self.port.tx.addTailMsg(['/usr/bin/aplay', '-D'], ['../sounds/idle.wav'], True, True, False, None)

    def rxTimeoutRelease(self) :
        """ Entered when the RX goes off when in state rxTimeOut
            Entered from teh RX state cchange code so it needs to be short
        """
        logit("Port %d Rx Time Out release" % self.port.portnum)
        # queue up the time out reset message
        self.port.tx.addBeaconMsg(["../bin/mout"],[ '20', '660', '5000', "to rst"],False,False,False,None)
        self.beacon()

    def tailDone(self):
        """Entered When the hang timer expires"""
        self.getLock()
        self.idle()
        self.releaseLock()


    def getLock(self) :
        self.lock.acquire(True)

    def releaseLock(self) :
        self.lock.release()

    """ State functions
        Must not take any (long) time
        set the next state
        do appropriate state entry actions
        start threads for actions that take time like timers or sending morse or voice or wave etc.
        return to the thread that called for the state change
    """

    def idle(self) :
        """Entered from 
            * tailDone 
            * startup 
            * beaconRun
        """
        self.port.tx.down()
        self.txTimeoutTimer.stop()
        self.state = 'idle'
        logit("Port %d Idle" % self.port.portnum)
        self.rxIdleTimer.reset()
        
    def repeat(self) :
        """ Entered when the RX goes active """
        self.rxIdleTimer.stop()
        self.idTimer.run()     # start or run the ID timers since they may be stopped
        self.politeIdTimer.run()
        self.state = 'repeat'
        logit("Port %d Repeat" % self.port.portnum)
        if (not self.port.tx.up) :
            self.txTimeoutTimer.reset()
            self.port.tx.tx()
        self.port.tx.plGen()
        """ Exited when the RX goes off or times out """
        
    def tail(self) :
        """ Entered when the RX goes in active and in the repeat state"""
        self.state = 'tail'
        logit("Port %d Tail" % self.port.portnum)
        self.tailTimer.reset()
        """ when the tail timer expires (tail delay) The tail messages play state is entered """

    def tailMessagePlay(self) :
        """ Will run on the tail Timers Thread 
            Entered when the tail timer expires
        """
        if (self.politeIdTimer.expired) :
            self.port.tx.sendId()
            self.politeIdTimer.reset()
            self.idTimer.reset()
        idPlayed = self.port.tx.playMsgs(self.port.tx.tailMsgList)
        if(idPlayed) : # a message that counts as an ID
            logit("Port %d Played a tail message that counted for an ID " % self.port.portnum )
            self.politeIdTimer.reset()
            self.IdTimer.reset()
        self.port.tx.pid = False
        """ if the tail is cancelled, we must have been pulled back into repeat by an active RX"""
        if( not self.port.tx.cancel) :
            self.port.tx.tailBeep()
            self.port.tx.plStop()
            self.rxTimer.stop()
            self.hangTimer.reset()
            """ when the hang timer expires, controll will go to tail done then to idle"""


    def cancelTail(self) :
        """ Cancel tail will be enterer whtn the RX goes active but we are in the tail state"""
        """ in this case the tail thread shodul clean itself up as the state is switched to repeat """
        logit("Port %d Cancel Tail" % self.port.portnum )
        self.port.tx.cancel = True
        self.tailTimer.stop()
        self.hangTimer.stop()
        if(self.port.tx.pid) : # can only cancel messages and not ID.
            self.port.tx.pid.terminate()
        
    def beacon(self) :
        """ This state can be used to beacon out an ID if needed or other messages that are queued"""
        """ entered from beaconId or RX time out """
        self.state = 'beacon'
        self.port.tx.plGen()
        self.port.tx.tx()
        logit("Port %d Beacon" % self.port.portnum)
        self.beaconUpTimer.reset()
        """ When the beacon up (tx delay) timer expires Control moves to beaconRun """

    def beaconRun(self) :
        """ Will run on the beaconUp Timers Thread """
        if (self.idTimer.expired) :
            self.port.tx.sendId()
            self.idTimer.expired = False
            if(self.state != 'beacon' ) : # due to cancel
                self.idTimer.reset()
                self.politeIdTimer.reset()
        self.port.tx.playMsgs(self.port.tx.beaconMsgList)
        self.port.tx.pid = False
        if( not self.port.tx.cancel) :
            self.port.tx.plStop()
            self.getLock()
            self.idle()
            self.releaseLock()

    def cancelBeacon(self) :
        """ if the beacon is cancelled stop the messages and let this tread end
            Whoever cancelled the beacon (RX) should set the correct next state
        """
        self.beaconUpTimer.stop()
        self.port.tx.cancel = True
        if(self.port.tx.pid) :
            self.port.tx.pid.terminate()
