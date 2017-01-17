#!/usr/bin/python
from multiprocessing import Process, Value, Array, Queue
import subbool
import time
n=Value('i',99)
bool_arr = Array('b', range(8))
q = Queue()
for i in range(len(bool_arr)):
    bool_arr[i] = False
p=Process( target=subbool.twiddle_bool, args=(n, bool_arr,q))
p.start()
for i in range(25) :
    time.sleep(0.4)
    print "%d : %s " % (i, str(bool_arr[:]))
    while(not q.empty()):
        print q.get()
p.terminate()
