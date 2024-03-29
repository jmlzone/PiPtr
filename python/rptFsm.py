from logit import logit
import threading
import time
from mycmd import talkingClock
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
        self.rxState = 'idle'
        self.rptState = 'idle'
        # Tx related
        self.txTimeoutTimer = gpTimer(self.port.tx.timeout, userHandler = self.txTimeout )
        self.tailTimer = gpTimer(self.port.tx.taildly, userHandler = self.tailMessagePlay)
        self.hangTimer = gpTimer(self.port.tx.hangtime, userHandler = self.tailDone)
        self.idTimer = gpTimer(self.port.tx.idtime,userHandler = self.beaconId)
        self.politeIdTimer = gpTimer(self.port.tx.idtime - self.port.tx.polite)
        self.beaconUpTimer = gpTimer(self.port.tx.txupdly, userHandler = self.beaconRun)

        #rx related
        self.rxTimer = gpTimer(self.port.rx.timeout, userHandler = self.rxTo)
        self.rxResetTimer = gpTimer(self.port.rx.resetTimeout, userHandler = self.rxTimerStop)
        self.rxIdleTimer = gpTimer(self.port.rx.IdleTimeout, userHandler = self.idleTimeout)
        self.cmdTimer = gpTimer(self.port.rx.cmdTimeout, userHandler = self.cmdTimeout_cb)
        self.muteTimer = gpTimer(self.port.rx.muteTime, userHandler = self.muteTimeout)
        self.linkVotes = 0

        self.lock = threading.Lock()

    """ fsm.linkVotes is a bit vector of the links we are connected to.
        port.linkState = 0 not linked
        port.linkState = 1 internal soft link
        port.linkState = 2 externallink 1 (LINK1O, LINK1I)
        port.linkState = 3 externallink 2 (LINK2O, LINK2I)
        So:
        self.linkVotes bit[0] is not used
        self.linkVotes bit[1] is the local link
        self.linkVotes bit[2] is external 1
        self.linkVotes bit[3] is external 2
    """
    def setLinkRx(self,linkNum) :
        oldVotes = self.linkVotes
        self.linkVotes = oldVotes | (1<<linkNum)
        if(oldVotes == 0) : # coming up based on this vote update fsm RX entry is: self.port.fsm.updateRx(rx)
            self.rxUpAny()
    def clrLinkRx(self,linkNum) :
        self.linkVotes = self.linkVotes &  ~(1<<linkNum)
        if(self.linkVotes == 0) : # going down based on this vote update fsm. rx entry is: self.port.fsm.updateRx(rx)
            self.rxDownAll()
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
        self.rxResetTimer.timeout = self.port.rx.resetTimeout
        self.rxIdleTimer.timeout = self.port.rx.IdleTimeout
        self.cmdTimer.timeout = self.port.rx.cmdTimeout
        self.muteTimer.timeout = self.port.rx.muteTime

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
        if(self.port.isLink) :
            logit("Port %d is a link" % self.port.portnum)
        else :
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
        #logit("Update RX state is " + self.rxState + str(rx))
        # will need to be smarter about the link state
        self.getLock()
        #logit("Update RX state got lock " + self.rxState)
        if(rx) :
            if(self.rxState == 'idle') :
                self.rxUp()
            elif (self.rxState == 'rx') :
                pass
            else:
                logit("Port %d Error Rx active again in rxState %s " % (self.port.portnum, self.rxState) )
        else : # rx inactive
            if(self.rxState == 'rx') :
                self.rxDown()
            elif(self.rxState == 'rxTimeOut') :
                self.rxTimeoutRelease()
            elif(self.rxState == 'idle') :
                pass
            else:
                logit("Port %d Error Rx off again in rxState %s " % (self.port.portnum, self.rxState) )
        self.releaseLock()
    def rxUp(self) : # part of rx state machine
        self.rxState = 'rx'
        self.rxTimer.run()
        self.rxResetTimer.stop() 
        self.port.hwio.muteUnmute(self.port.portnum, self.port.linkState, self.port.rx.audioEnable) #enable audio
        if((self.port.linkState==1) & (self.port.other.linkState==1) & self.port.other.enabled) :
            self.port.other.fsm.setLinkRx(1) # port 1 linking is special and software only
        if(self.port.linkState == 2 or self.port.linkState == 3) :
            self.port.hwio.linkVoteSet(self.port.portnum, self.port.linkState)
        self.rxUpAny()
    def rxUpAny(self):
        if(self.port.isLink) :
            print("Port %d link rx" % self.port.portnum)
            if(self.rxState != 'rx') :
                if(self.rptState == 'idle') :
                    self.linkTX();
                elif (self.rptState == 'beacon') :
                    self.cancelBeacon()
                    self.linkTX();
                elif (self.rptState == 'tail') :
                    self.cancelTail()
                    self.repeat()
                elif (self.rptState == 'linkTX') :
                    pass
                else:
                    logit("Port %d Error Link Rx active again in state %s " % (self.port.portnum, self.rxState) )
        else:
            if(self.rptState == 'idle') :
                self.repeat()
            elif (self.rptState == 'beacon') :
                self.cancelBeacon()
                self.repeat()
            elif (self.rptState == 'tail') :
                self.cancelTail()
                self.repeat()
            elif (self.rptState == 'repeat') :
                pass
            else:
                logit("Port %d Error Rx active again in state %s " % (self.port.portnum, self.rxState) )
    def rxDown(self) : # part of rx state machine
        self.rxResetTimer.reset() 
        self.rxIdle()
        self.port.hwio.muteUnmute(self.port.portnum, self.port.linkState, False) #mute audio
        self.rxUnlink()
        if(self.linkVotes==0) :
            self.rxDownAll()
        if(self.rxState == 'rxTimeOut') :
            self.rxTimeoutRelease()

    def rxUnlink(self) :
        if((self.port.linkState==1) & (self.port.other.linkState==1) & self.port.other.enabled) :
            self.port.other.fsm.clrLinkRx(1) # port 1 linking is special and software only
        if(self.port.linkState == 2 or self.port.linkState == 3) :
            self.port.hwio.linkVoteClr(self.port.portnum, self.port.linkState)
        
    def rxDownAll(self):
        if(self.port.isLink) :
            print("Port %d: link rx down" % self.port.portnum)
            if(self.rptState == 'linkTX') :
                self.idle()
        else:
            if(self.rptState == 'repeat') :
                if(self.port.isLink) :
                    self.idle()
                else :
                    self.tail()
            elif(self.rxState == 'idle' or self.rptState == 'idle') :
                pass
            else:
                logit("Port %d Error Rx off again in state %s " % (self.port.portnum, self.rptState) )
        
    def rxIdle(self) :
        self.rxState = 'idle'
        
    def rxTo(self) :
        """ Entered by the RX time out event 
            Entered into from a timer threadf so no need to be quick.
            Needs to get the lock before changing any state information
        """
        self.rxTimer.expired=True
        self.rxTimer.isRunning=False
        self.getLock()
        self.rxState = 'rxTimeOut'
        logit("Port %d Rx Time Out" % self.port.portnum)
        self.releaseLock()
        self.rxUnlink()
        self.rxTimer.expired = True
        self.rxTimer.isrunning = False
        if(not self.port.isLink) :
            idPlayed = self.port.tx.playMsgs([(["../bin/mout"],[ '20', '660', '5000', "to"],False,False,False,None)])
            # send time out message
            # turn off transmitter (if not linked)
            self.port.tx.plStop()
            self.port.tx.down()
        logit("Port %d Rx Time Out complete" % self.port.portnum)

    def rxTimerStop(self) :
        """ Called when the RS reset timer expires to de-glitch and ensure a real drop
        of the RX.
        Does not do much but here as a holding place for the other call. for logging or debug
        """
        self.rxTimer.stop()

    def txTimeout(self) :
        """ Entered by the TX time out event """
        self.getLock()
        self.rptState = 'TxTimeOut'
        logit("Port %d Tx Time Out" % self.port.portnum)
        self.port.tx.playMsgs([(["../bin/mout"],[ '20', '660', '5000', "TX to"],False,False,False,None)])
        # send time out message
        # turn off transmitter (if not linked)
        self.port.tx.down()
        self.idle()
        self.releaseLock()

    def idleTimeout(self) :
        if(self.port.isLink) :
            pass
        else :
            logit("Port %d idle Time Out queued Idle message" % self.port.portnum)
            self.port.tx.addTailMsg(['/usr/bin/aplay', '-D'], [self.port.idleWav], True, True, False, None)

    def cmdTimeout_cb(self) :
        self.port.rx.cmdModeClr()
    def cmdOn(self) :
        self.port.fsm.cmdTimer.reset()
        self.port.rx.cmdModeSet()
        #self.port.tx.addTailMsg(['/usr/bin/aplay', '-D'], ["enterCmd.wav"], True, True, False, None)

    def muteTimeout(self) :
        self.port.rx.audioEnable = True
        self.port.hwio.muteUnmute(self.port.portnum, self.port.linkState, self.port.rx.rxActive.isSet()) #enable audio

    def mute(self) :
        self.muteTimer.reset()
        self.port.rx.audioEnable = False
        self.port.hwio.muteUnmute(self.port.portnum, self.port.linkState, False) #disable audio

    def rxTimeoutRelease(self) :
        """ Entered when the RX goes off when in state rxTimeOut
            Entered from the RX state cchange code so it needs to be short
        """
        logit("Port %d Rx Time Out release" % self.port.portnum)
        self.rxIdle()
        # queue up the time out reset message
        self.port.tx.addBeaconMsg(["../bin/mout"],[ '20', '660', '5000', "to rst"],False,False,False,None)
        self.beacon()

    def tailDone(self):
        """Entered When the hang timer expires.
        if the link is active we stay up, otherwise we ca go idle.
        """
        self.getLock()
        if (self.linkVotes !=0) :
            self.repeat()
        else :
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
        self.rptState = 'idle'
        logit("Port %d Idle" % self.port.portnum)
        self.rxIdleTimer.reset()
        
    def repeat(self) :
        """ Entered when the RX goes active """
        self.rxIdleTimer.stop()
        self.idTimer.run()     # start or run the ID timers since they may be stopped
        self.politeIdTimer.run()
        self.rptState = 'repeat'
        logit("Port %d Repeat" % self.port.portnum)
        if (not self.port.tx.up) :
            self.txTimeoutTimer.reset()
            self.port.tx.tx()
        self.port.tx.plGen()
        """ Exited when the RX goes off or times out """

    def linkTX(self) :
        self.idTimer.run()     # start or run the ID timers since they may be stopped
        self.politeIdTimer.run()
        self.rptState = 'linkTX'
        logit("Port %d Link TX" % self.port.portnum)
        if (not self.port.tx.up) :
            self.txTimeoutTimer.reset()
            self.port.tx.tx()
        self.port.tx.plGen()
        """ Exited when the link RX goes off or times out """
    def linkTXDown() : # kind of link a tail but shorter
        self.rptState = 'linkTXDown'
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
            self.idle()
        
    def tail(self) :
        """ Entered when the RX goes in active and in the repeat state"""
        self.rptState = 'tail'
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
            #self.rxTimer.stop() # handle with separate reset timer to allow linking to work
            self.hangTimer.reset()
            """ when the hang timer expires, controll will go to tail done then to idle"""


    def cancelTail(self) :
        """ Cancel tail will be enter when the RX goes active but we are in the tail state"""
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
        self.rptState = 'beacon'
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
            if(self.rptState != 'beacon' ) : # due to cancel
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
