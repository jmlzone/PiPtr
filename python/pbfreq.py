#!/usr/bin/python3
from tkinter import *
class mySixDigit :
    def __init__ (self,canvas,x,y,text,val=446000,cb=False) :
        self.canvas=canvas
        self.x=x
        self.y=y
        self.label=text
        self.val=val
        self.incr=30
        self.width=180
        self.height=40
        if(cb):
            self.cb=cb
        else :
            self.cb=False
        self.hmhz=digit(canvas,x,y,100000,int(val/100000),self.updateSix)
        rm = val - (int(val/100000) * 100000)
        self.tmhz=digit(canvas,x+self.incr,y,10000,int(rm/10000),self.updateSix)
        rm = rm - (int(rm/10000) * 10000)
        self.mhz=digit(canvas,x+(self.incr *2),y,1000,int(rm/1000),self.updateSix)
        rm = rm - (int(rm/1000) * 1000)
        self.hkhz=digit(canvas,x+(self.incr*3),y,100,int(rm/100),self.updateSix)
        rm = rm - (int(rm/100) * 100)
        self.tkhz=digit(canvas,x+(self.incr*4),y,10,int(rm/10),self.updateSix)
        rm = rm - (int(rm/10) * 10)
        self.khz=digit(canvas,x+(self.incr*5),y,1,rm,self.updateSix)
        b=canvas.create_polygon(x,y,x,y+self.height,x+self.width,y+self.height,x+self.width,y,x,y,fill="grey")
        t=canvas.create_text(x+(self.width/2),y+30,text=text)

    def updateSix(self):
        self.val=self.khz.val + self.tkhz.val + self.hkhz.val + self.mhz.val + self.tmhz.val + self.hmhz.val
        print("New value = %d " % self.val)
        if(self.cb) :
            self.cb()
                        
class digit:
    def __init__(self,canvas,x,y,mult,val, parentcb) :
        self.canvas=canvas
        self.x=x
        self.y=y
        self.mult=mult
        self.val=val*self.mult
        self.parentcb=parentcb
        self.var=StringVar(canvas)
        self.var.set("%d" % val)
        self.db = Spinbox(self.canvas,from_=0,to=9, command=self.update, wrap=True, textvariable=self.var)
        self.db.place(x=x,y=y,width=30)
        #print("myval is %d" % self.val)
        #self.db.set(self.val)

    def update(self):
        self.val=int(self.db.get()) * self.mult
        #print("Digit %d got %d" % (self.mult,self.val))
        self.parentcb()

class myPlSelect :
    def __init__ (self,canvas,x,y,choices,default,cb=False) :
        self.canvas=canvas
        self.x=x
        self.y=y
        self.width=60
        self.height=40
        self.val=default
        self.var=StringVar(canvas)
        if(cb) :
            self.cb=cb
        else:
            self.cb=False
        #print("pl default is %s" % self.val)
        self.pl = Spinbox(self.canvas, values=choices, command=self.update, textvariable=self.var, wrap=True)
        self.pl.place(x=x,y=y,width=60)
        self.var.set(self.val)
        b=canvas.create_polygon(x,y,x,y+self.height,x+self.width,y+self.height,x+self.width,y,x,y,fill="grey")
        t=canvas.create_text(x+(self.width/2),y+30,text='PL tone')

    def update(self):
        self.val=self.pl.get()
        #print("PL got %s" % self.val)
        if(self.cb):
            self.cb()

if __name__ == "__main__" :
    try:
        tk=Tk()
        canvas = Canvas(tk,bg="black",height = 100, width = 650)
        canvas.place(x=0, y=0, height = 100, width = 650)
        canvas.pack()
    except:
        print("No TK, bye bye")
        exit(-1)
    import sys
    sys.path.append('/home/jml/PiPtr/python')
    import kenwoodTK
    rxf = mySixDigit(canvas,10,10,"Receive",449925)
    txf = mySixDigit(canvas,200,10,"Transmit",444925)
    pl = myPlSelect(canvas,390,10, sorted(kenwoodTK.plSwitchTable.keys()),'88.5')
    tk.mainloop()
    
