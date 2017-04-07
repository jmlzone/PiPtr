import threading
class gpTimer:
    def __init__(self, timeout, userHandler=None):  # timeout in seconds
        self.timeout = timeout
        self.expired = False
        self.isrunning = False
        self.handler = userHandler if userHandler is not None else self.defaultHandler
        self.timer = threading.Timer(self.timeout, self.handler)
        self.timer.start()
        self.isrunning = True
        
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
        self.txTimeoutTimer = gpTimer(self.port.tx.timeout )
        self.tailTimer = gpTimer(self.port.tx.taildly, userHandler = self.tailMessagePlay)
        self.hangTimer = gpTimer(self.port.tx.hangtime, userHandler = self.tailDone)
        self.idTimer = gpTimer(self.port.tx.idtime,userHandler = self.beaconId)
        self.politeIdTimer = gpTimer(self.port.tx.idtime - self.port.tx.polite)
        self.beaconUpTimer = gpTimer(self.port.tx.txupdly, userHandler = self.beaconRun)

        #rx related
        self.rxTimer = gpTimer(self.port.rx.timeout, userHandler = self.rxTo)
        self.rxIdleTimer = gpTimer(self.port.rx.IdleTimeout)

        self.lock = threading.Lock()

    """ Input event functions here
        they need to
        1) acquire the lock
        2) do the next state
        3) releae the lock
    """
    def startUp(self) :
        logit("Port %d startup" % self.port.portnum)
        time.sleep(5 * self.port.portnum)
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
        self.getLock()
        self.releaseLock()
        
    def updateRx(self, rx) :
        # will need to be smarter about the link state
        self.getLock()
        if(rx) :
            if(self.state == 'idle') :
                rpt()
            elif (self.state == 'beacon') :
                self.cancelBeacon()
            elif (self.state == 'tail') :
                canceltail()
        else : # rx inactive
            if(self.state == 'repeat') :
                self.tail()
            elif(self.state == 'rxTimeOut') :
                self.rxTimoutRelease()
        self.releaseLock()
                
    def rxTo(self) :
        self.getLock()
        self.state = 'rxTimeOut'
        # send time out message
        # turn off transmitter (if not linked)
        self.port.tx.down()
        self.releaseLock()

    def rxTimeOutRelease(self) :
        self.getLock()
        # queue up the time out reset message
        self.beacon()
        self.releaseLock()

    def tailDone(self):
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
        self.port.tx.down()
        self.state = 'idle'
        
    def repeat(self) :
        self.state = 'repeat'
        self.txTimeoutTimer.reset()
        self.port.tx.tx()
        self.port.tx.plGen()
        
    def tail(self) :
        self.state = 'tail'
        self.tailTimer.reset()

    def tailMessagePlay(self) :
        """ Will run on the tail Timers Thread """
        self.port.tx.playMsgs(self.port.tx.tailMsgList)
        self.port.tx.pid = False
        if( not self.port.tx.cancel) :
            self.port.tx.tailBeep()
            self.hangTimer.reset()


    def cancelTail(self) :
        self.port.tx.cancel = True
        self.tailTimer.stop()
        self.hangTimer.stop()
        if(self.port.tx.pid) :
            self.port.tx.pid.terminate()
        
    def beacon(self) :
        self.state = 'beacon'
        self.beaconUpTimer.reset()

    def beaconRun(self) :
        """ Will run on the beaconUp Timers Thread """
        self.port.tx.sendId()
        self.port.tx.playMsgs(self.port.tx.beaconMsgList)
        self.port.tx.pid = False
        if( not self.port.tx.cancel) :
            self.getLock()
            self.idle()
            self.releaseLock()

    def canceBeacon(self) :
        self.beaconUpTimer.stop()
        self.port.tx.cancel = True
        if(self.port.tx.pid) :
            self.port.tx.pid.terminate()
