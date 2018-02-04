import time
def gpiosweep(port=0,rate=0.1) :
    startLed = port * 8
    endLed = startLed+7
    dir = 1
    prevLed = startLed
    curLed = startLed
    hwio.setup(list(range(startLed,(endLed+1))),0,initial=0)
    run = True
    while(run) :
        hwio.output(prevLed,0)
        hwio.output(curLed,1)
        prevLed = curLed
        if(curLed == startLed) :
            dir = 1
        elif(curLed == endLed) :
            dir = -1
        curLed = curLed + dir
        time.sleep(rate)
    hwio.output(list(range(startLed,(endLed+1))),0)
    hwio.setup(list(range(startLed,(endLed+1))),1)
        
