#!/usr/bin/python
import time
def twiddle_bool(it,a,q):
    print "child started"
    while True :
        print "Itteration %d" % it.value
        it.value = it.value +1
        time.sleep(1)
        any = False
        for i in range(len(a)):
            any = any or a[i]
        for i in range((len(a)-1), 0, -1):
            a[i] = a[i-1]
        a[0] = not any
        if(not any) :
            q.put(it.value)
            q.put("this")
            q.put("is a")
            q.put("test")
