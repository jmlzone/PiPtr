import subprocess
import re
import time
def soft_decode (card, n, ctcss_arr, q):
    p=subprocess.Popen(['./bin/multimon', card, '-a', 'dtmf', '-a', 'ctcss'], stdout=subprocess.PIPE)
    time.sleep(1)
    while(True) :
        txt = p.stdout.readline()
        ctcss = re.search(r'CTCSS (?P<state>[DL]): (?P<num>\d)',txt)
        dtmf = re.search(r'DTMF: (?P<tone>[0123456789ABCDEF])',txt)
        if(ctcss != None) :
            ctcss_arr[int(ctcss.group('num'))] = (ctcss.group('state') == 'D')
        if(dtmf != None) :
            q.put(dtmf.group('tone'))
