#!/usr/bin/python
import subprocess

class tail_msg:
    def __init__ (self, card):
        self.card = card
        self.msglist =[]
        self.pid = None
        self.cancel = False
        self.cancelable = False

# example
#tail.add(['/usr/bin/aplay', '-D'], './sounds/Tink.wav', True, False, None)
#tail.add('./bin/mout', [ '20', '660', '5000', 'TEST'], True, False, None)
        
    def add(self, method,msg,cancelable,isid,requeue,alt):
        self.msglist.append((method,msg,cancelable,isid,requeue,alt))
        print "added tail message %s " % msg

    def play(self) :
        tmplist = self.msglist;
        self.msglist = []
        self.cancel = False
        id_played = False
        for ele in tmplist:
            (method,msg,cancelable,isid,requeue,alt) = ele
            self.cancellable = cancelable
            # run it
            if(not self.cancel or not cancelable) :
                # realy run it
                args = method + [self.card,msg]
                print "tail message play: (args)"
                print args
                try: 
                    self.pid = subprocess.Popen(args)
                except:
                    print "error could not run the tail message"
                if(isid and not self.cancel and not cancelable) :
                    id_played = True
            if (self.cancel and requeue ):
                self.msglist.append(ele)
        self.pid = None
        return (id_played)

    def cancel(self) :
        if(self.pid):
            self.pid.poll()
            self.cancel = True
            if (self.cancelable and self.pid.returncode == None):
                self.pid.kill()
