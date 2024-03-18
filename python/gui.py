#!/usr/bin/python
import threading
import time
from tkinter import *
from tkinter import ttk
import socket
import os
import sys, traceback
import pdb
from xmlio import dumpXml
import hwio
import pbfreq

class ToolTip(object):

    def __init__(self, widget):
        self.widget = widget
        self.tipwindow = None
        self.id = None
        self.x = self.y = 0

    def showtip(self, text):
        "Display text in tooltip window"
        self.text = text
        if self.tipwindow or not self.text:
            return
        x, y, cx, cy = self.widget.bbox("insert")
        x = x + self.widget.winfo_rootx() + 20
        y = y + cy + self.widget.winfo_rooty() -15
        self.tipwindow = tw = Toplevel(self.widget)
        tw.wm_overrideredirect(1)
        tw.wm_geometry("+%d+%d" % (x, y))
        label = Label(tw, text=self.text, justify=LEFT,
                      background="#ffffe0", relief=SOLID, borderwidth=1,
                      font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)

    def hidetip(self):
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()

def CreateToolTip(widget, text):
    toolTip = ToolTip(widget)
    def enter(event):
        toolTip.showtip(text)
    def leave(event):
        toolTip.hidetip()
    widget.bind('<Enter>', enter)
    widget.bind('<Leave>', leave)

toolTips= {'idtime': 'Time in seconds when ID is required',
           'polite': 'Time in seconds when ID will be sent on a tail',
           'txto': 'Maximum time in seconds for continuous transmitter operation',
           'taildly': 'Delay from rx drop to tail messages and tail beep',
           'hangtime': 'Time from last tail message/beep until the transmitter drops.',
           'updly' : 'TX up delay before a tail will be enabled',
           'rxto': 'Maximum time in seconds for continuous reciever operation before it is disabled',
           'rxres': 'rx down time required for rx time out to reset.',
           'rxidle': 'After no reciever operation for the idle time, Welcome and other messages may be queued',
           'cmdto' : 'Timeout in seconds from RX until new tones are ignored'
              }

class gui :
    def __init__(self,top) :
        try: 
            self.tk=Tk()
            self.tk.title("PiPtr")
            self.tk.geometry("550x420")
            self.tabs = ttk.Notebook(self.tk)
            self.audioTab = ttk.Frame(self.tabs)
            self.timerTab = ttk.Frame(self.tabs)
            self.portIOTab = ttk.Frame(self.tabs)
            self.radioTab = ttk.Frame(self.tabs)
            self.tabs.add(self.audioTab, text="Audio")
            self.tabs.add(self.timerTab, text="Timers")
            self.tabs.add(self.radioTab, text="Radio")
            self.tabs.add(self.portIOTab, text="Port IO")
            self.tabs.pack(expand = 1, fill = "both")
        
            self.radioCanvas = Canvas(self.radioTab,bg="black",height = 400, width = 550)
            self.radioCanvas.place(x=0, y=80, height = 400, width = 550)
            self.radioCanvas.pack() # extends window to fit.
            self.audioCanvas = Canvas(self.audioTab,bg="black",height = 400, width = 550)
            self.audioCanvas.place(x=0, y=80, height = 400, width = 550)
            self.audioCanvas.pack() # extends window to fit.
            self.timerCanvas = Canvas(self.timerTab,bg="black",height = 400, width = 550)
            self.timerCanvas.place(x=0, y=80, height = 400, width = 550)
            self.timerCanvas.pack() # extends window to fit.
            self.ioCanvas = Canvas(self.portIOTab,bg="black",height = 400, width = 550)
            self.ioCanvas.place(x=0, y=80, height = 400, width = 550)
            self.ioCanvas.pack() # extends window to fit.
            self.gui = True
        except:
            print("Gui Start failed")
            traceback.print_exc()
            self.gui = False
        self.top = top
    linkStates = ['Off','Internal', 'Ext 1', 'Ext 2']
    def mytriangle (self,canvas,x,y,text) :
        """ draw a horizontal triangle centered starting at startxy """
        incr=100
        t=canvas.create_polygon(x,y-(incr/2),x,y+(incr/2),x+incr,y,x,y-(incr/2), fill="grey")
        tx=canvas.create_text(x + ((incr/2) -10),y, text=text)

    def myres(self,canvas,startx,starty,hv) :
        # if HV = true Horizontal otherwise vert
        points = (startx,starty)
        incr=10
        #start stub
        # and half line
        if(hv) :
            cx = startx + incr
            cy = starty
            points = points + (cx,cy)
            cx = cx + (incr/2)
            cy = cy + incr
            points = points + (cx,cy)
        else :
            cx = startx
            cy = starty + incr
            points = points + (cx,cy)
            cx = cx + incr 
            cy = cy + (incr/2)
            points = points + (cx,cy)
        fb =-1 # forward or backward
        for zigs in range(5) :
            if(hv) :
                cx = cx + incr
                cy = cy + incr * 2 * fb
            else:
                cx = cx + incr  * 2 * fb
                cy = cy + incr
            points = points + (cx,cy)
            fb = fb * -1
            # final half zig and stub
        if(hv) :
            cx = cx + (incr/2)
            cy = cy + incr
            points = points + (cx,cy)
            cx = cx + incr
            cy = cy
            points = points + (cx,cy)
        else :
            cx = cx + incr 
            cy = cy + (incr/2)
            points = points + (cx,cy)
            cx = cx
            cy = cy + incr
            points = points + (cx,cy)
        return(canvas.create_line(points ,fill="white"))

    def guiSave(self) :
        host = socket.gethostname()
        path = os.path.dirname(os.path.realpath(__file__))
        abspath = os.path.abspath(path + "/../" + host)
        f = os.path.abspath(abspath + "/" + host + ".xml")
        if not os.path.exists(abspath) :
            print("Warning Local host specific directory %s does not exist, creating" % abspath)
            os.makedirs(abspath)
        dumpXml(self.top,f)
        print("Wrote config file %s" % f)
        return(f)

    def getPortNum(self) :
        if(self.gui) :
            val = self.ps.get()
            if (val == 'port1') :
                return(0)
            else :
                return(1)
        
    def portSelect(self) :
        if(self.gui) :
            val = self.ps.get()
            pn = self.getPortNum()
            if (val == 'port1') :
                self.RA = self.top.hwio.vals[0]
                self.RB = self.top.hwio.vals[1]
                self.RC = self.top.hwio.vals[2]
                self.RD = self.top.hwio.vals[3]
                self.deempVal = self.top.port1.rx.deemp
                self.descEnVal = self.top.port1.rx.descEn
                self.portDetVal = self.top.port1.rx.portDet
                self.isLinkVal = self.top.port1.isLink
                self.callBox.delete(1.0, 'end')
                self.callBox.insert(1.0, self.top.port1.tx.id)
                self.callBox.edit_modified(False)
            else :
                self.RA = self.top.hwio.vals[4]
                self.RB = self.top.hwio.vals[5]
                self.RC = self.top.hwio.vals[6]
                self.RD = self.top.hwio.vals[7]
                self.deempVal = self.top.port2.rx.deemp
                self.descEnVal = self.top.port2.rx.descEn
                self.portDetVal = self.top.port2.rx.portDet
                self.isLinkVal = self.top.port2.isLink
                self.callBox.delete(1.0, 'end')
                self.callBox.insert(1.0, self.top.port2.tx.id)
                self.callBox.edit_modified(False)
            self.RS = self.top.hwio.speakers[pn]
            self.RM = self.top.hwio.mics[pn]
            self.updateRs()
            self.updateChecks()
            self.initLinkState()

    def updateRs(self):
        self.rA.set(self.RA)
        self.rB.set(self.RB)
        self.rC.set(self.RC)
        self.rD.set(self.RD)
        self.rS.set(self.RS)
        self.rM.set(self.RM)

    def updateRn(self,val,offset,step=4) :
        port = self.ps.get()
        if(port == 'port2') :
            offset = offset + step
        self.top.hwio.vals[offset] = int(val)
        self.top.hwio.WriteRes(offset,int(val),0)
    def rAcb(self,val) :
        self.updateRn(val,0)
    def rBcb(self,val) :
        self.updateRn(val,1)
    def rCcb(self,val) :
        self.updateRn(val,2)
    def rDcb(self,val) :
        self.updateRn(val,3)
    def rScb(self,val) :
        self.top.hwio.speakers[self.getPortNum()] = int(val)
        self.top.hwio.setMixerByName(self.getPortNum(), 'Speaker', int(val))
    def rMcb(self,val) :
        self.top.hwio.mics[self.getPortNum()] = int(val)
        self.top.hwio.setMixerByName(self.getPortNum(), 'Mic', int(val))
    def updateChecks(self) :
        if(self.deempVal) :
            self.deemp.select()
        else:
            self.deemp.deselect()
        if(self.descEnVal) :
            self.descEn.select()
        else:
            self.descEn.deselect()
        if(self.portDetVal) :
            self.portDet.select()
        else:
            self.portDet.deselect()
        if(self.isLinkVal) :
            self.isLink.select()
        else:
            self.isLink.deselect()
    def deempCb(self) :
        val = True if self.deempVar.get() else False
        port = self.ps.get()
        if(port == 'port1') :
            self.top.port1.rx.deemp = val
            self.top.hwio.CH1CTL = self.top.hwio.getBit(self.top.hwio.CH1CTL,not self.top.port1.rx.deemp,4)
            self.top.hwio.i2cSafeWrite(hwio.GPIOEX1, hwio.GPIOR, self.top.hwio.CH1CTL)
        else:
            self.top.port2.rx.deemp = val
            self.top.hwio.CH2CTL = self.top.hwio.getBit(self.top.hwio.CH2CTL,not self.top.port2.rx.deemp,4)
            self.top.hwio.i2cSafeWrite(hwio.GPIOEX2, hwio.GPIOR, self.top.hwio.CH2CTL)
    def descEnCb(self) :
        val = True if self.descEnVar.get() else False
        port = self.ps.get()
        if(port == 'port1') :
            self.top.port1.rx.descEn = val
            self.top.hwio.CH1CTL = self.top.hwio.getBit(self.top.hwio.CH1CTL,not self.top.port1.rx.descEn,5)
            self.top.hwio.i2cSafeWrite(hwio.GPIOEX1, hwio.GPIOR, self.top.hwio.CH1CTL)
        else:
            self.top.port2.rx.descEn = val
            self.top.hwio.CH2CTL = self.top.hwio.getBit(self.top.hwio.CH2CTL,not self.top.port2.rx.descEn,5)
            self.top.hwio.i2cSafeWrite(hwio.GPIOEX2, hwio.GPIOR, self.top.hwio.CH2CTL)
    def portDetCb(self) :
        val = True if self.portDetVar.get() else False
        port = self.ps.get()
        if(port == 'port1') :
            self.top.port1.rx.portDet = val
            self.top.hwio.CH1CTL = self.top.hwio.getBit(self.top.hwio.CH1CTL,not self.top.port1.rx.portDet,6)
            self.top.hwio.i2cSafeWrite(hwio.GPIOEX1, hwio.GPIOR, self.top.hwio.CH1CTL)
        else:
            self.top.port2.rx.portDet = val
            self.top.hwio.CH2CTL = self.top.hwio.getBit(self.top.hwio.CH2CTL,not self.top.port2.rx.portDet,6)
            self.top.hwio.i2cSafeWrite(hwio.GPIOEX2, hwio.GPIOR, self.top.hwio.CH2CTL)
    def isLinkCb(self) :
        val = True if self.isLinkVar.get() else False
        port = self.ps.get()
        if(port == 'port1') :
            self.top.port1.isLink = val
        else:
            self.top.port2.isLink = val
    def linkStateCb (self) :
        port = self.ps.get()
        val = self.linkState.get()
        vn = self.linkStates.index(val)
        if(port == 'port1') :
            self.top.port1.linkState = vn
        else:
            self.top.port2.linkState = vn
    def initLinkState(self) :
        port = self.ps.get()
        if(port == 'port1') :
            vn = self.top.port1.linkState
        else:
            vn = self.top.port2.linkState
        self.linkState.set(self.linkStates[vn])

    def callChangedCb(self):
        port = self.ps.get()
        if(port == 'port1') :
            self.top.port1.tx.id=self.callBox.get(1.0, 'end').strip()
        else:
            self.top.port2.tx.id=self.callBox.get(1.0, 'end').strip()
        self.callBox.edit_modified(False)

    def initRadioCanvas(self,canvas) :
        if(self.top.options.tunekenwood) :
        
            self.rxf = pbfreq.mySixDigit(canvas,10,20,"Receive",int(self.top.kenwood.rxFreq),self.txrxUpdate)
            self.txf = pbfreq.mySixDigit(canvas,200,20,"Transmit",int(self.top.kenwood.txFreq),self.txrxUpdate)
            self.pl = pbfreq.myPlSelect(canvas,390,20, sorted(self.top.kenwood.plVal.keys()),self.top.kenwood.plName,self.plupdate)
        else :
            canvas.create_text(50,250,text="No tunable radio interfaces defined",fill="white",anchor=W)
        
    def initAudioCanvas(self,canvas) :
        self.mytriangle (canvas,60,100,"RX Main")
        self.mytriangle (canvas,180,70,"PGA")
        self.mytriangle (canvas,300,70,"TX Sum")
        self.mytriangle (canvas,180,200,"Computer")
        #self.myres(canvas,190,30,False)
        desc = canvas.create_text(5,30,text="Desc\n in",fill="green", anchor=W)
        rx = canvas.create_text(5,100,text="from\n RX",fill="green", anchor=W)
        tc = canvas.create_text(450,20,text="To\nComputer",fill="green", anchor=W)
        dci = canvas.create_line(30,30, 50,30,fill="white")
        #dco = canvas.create_line(150,30, 170,30,fill="white")
        l = canvas.create_line(30,100, 60,100,fill="white")
        l2 = canvas.create_line(160,100, 170,100, 170,10, 345,10, fill="white")
        l2a = canvas.create_line(170,70, 180,70, fill="white")
        l3 = canvas.create_line(280,70, 300,70, fill="white")
        #l3a = canvas.create_line(200,70,270,70, fill="white", arrow=FIRST)
        l4 = canvas.create_line(400,70, 420,70, fill="white")
        l5 = canvas.create_line(280,200, 290,200, 290,70, fill="white")
        tx = canvas.create_text(420,70,text="to\nTX",fill="green", anchor=W)
        tx = canvas.create_text(420,220,text="CTCSS\nTX",fill="green", anchor=W)
        self.rA = Scale(canvas,from_=0, to=256, orient=HORIZONTAL, command=self.rAcb)
        self.rA.place(x=40,y=150,height=40,width=120)
        self.rB = Scale(canvas,from_=0, to=256, orient=HORIZONTAL, command=self.rBcb)
        self.rB.place(x=40,y=10,height=40,width=120)
        self.rC = Scale(canvas,from_=0, to=256, orient=HORIZONTAL, command=self.rCcb)
        self.rC.place(x=295,y=200,height=40,width=120)
        self.rD = Scale(canvas,from_=0, to=256, orient=HORIZONTAL, command=self.rDcb)
        self.rD.place(x=295,y=120,height=40,width=120)
        self.rS = Scale(canvas,from_=0, to=100, orient=HORIZONTAL, command=self.rScb)
        self.rS.place(x=70,y=195,height=40,width=100)
        self.rM = Scale(canvas,from_=0, to=100, orient=HORIZONTAL, command=self.rMcb)
        self.rM.place(x=345,y=5,height=40,width=100)
        self.deempVar = IntVar()
        self.deemp = Checkbutton(canvas,text="DeEmphasis", variable=self.deempVar,command=self.deempCb, bg='black', fg='green', bd=0, selectcolor='black')
        self.deemp.place(x=185,y=125,height=20,width=100)
        self.descEnVar = IntVar()
        self.descEn = Checkbutton(canvas,text="Desc En", variable=self.descEnVar,command=self.descEnCb, bg='black', fg='green', bd=0, selectcolor='black')
        self.descEn.place(x=225,y=20,height=20,width=75)
        self.portDetVar = IntVar()
        self.portDet = Checkbutton(canvas,text="Port Detect", variable=self.portDetVar,command=self.portDetCb, bg='black', fg='green', bd=0, selectcolor='black')
        self.portDet.place(x=310,y=260,height=20,width=95)

        tx = canvas.create_text(495,130,text="Call",fill="green", anchor=W)
        self.callBox = Text(canvas,height=1,width=10)
        self.callBox.place(x=465,y=140,width=75)
        self.callBox.bind('<<Modified>>', lambda event: self.callChangedCb())
        tx = canvas.create_text(495,210,text="Link",fill="green", anchor=W)
        self.linkState = ttk.Spinbox(canvas,values=(self.linkStates), command=self.linkStateCb, wrap=True)
        self.linkState.place(x=465,y=220,width=75)
        self.isLinkVar = IntVar()
        self.isLink = Checkbutton(canvas,text="is Link", variable=self.isLinkVar,command=self.isLinkCb, bg='black', fg='green', bd=0, selectcolor='black')
        self.isLink.place(x=465,y=250,height=20,width=75)

        #all  GUI needs to be defined before the port select since port select
        #initialzes all the values
        self.ps = Spinbox(canvas,values=('port1','port2'), command=self.portSelect, wrap=True)
        self.ps.place(x=485,y=40,width=55)
        self.portSelect()

        co = canvas.create_text(5,215,text="From\nComputer", anchor=W, fill="green")
        l6 = canvas.create_line(105,200, 180,200,fill="white")
        canvas.create_text(35,300,text="COR",fill="green")
        canvas.create_text(75,300,text="CTCSS",fill="green")
        canvas.create_text(115,300,text="CMD",fill="yellow")
        canvas.create_text(515,300,text="TX",fill="green")
        self.ref['cor1'] = canvas.create_oval(20,310, 50,340, fill="grey")
        self.ref['ctcss1'] = canvas.create_oval(60,310, 90,340, fill="grey")
        self.ref['cmd1'] = canvas.create_oval(100,310, 130,340, fill="grey")
        self.ref['tx1'] = canvas.create_oval(500,310, 530,340, fill="grey")
        self.ref['cor2'] = canvas.create_oval(20,360, 50,390, fill="grey")
        self.ref['ctcss2'] = canvas.create_oval(60,360, 90,390, fill="grey")
        self.ref['cmd2'] = canvas.create_oval(100,360, 130,390, fill="grey")
        self.ref['tx2'] = canvas.create_oval(500,360, 530,390, fill="grey")
        x=140
        y1=310
        y2=360
        tone = ["77.0", "88.5", "103.5", "110.9",
                "114.8", "123.0", "146.2", "165.5" ]
        self.ref['softCtcss1'] = []
        self.ref['softCtcss2'] = []
        for i in range (8) :
            canvas.create_text(x+15,300,text=tone[i],fill="green")
            t=canvas.create_oval(x,y1,x+30,y1+30, fill="grey")
            self.ref['softCtcss1'].append(t)
            t=canvas.create_oval(x,y2,x+30,y2+30, fill="grey")
            self.ref['softCtcss2'].append(t)
            x=x+40
        self.SaveButton(canvas)
        canvas.tag_bind(self.ref['tx1'], '<Button-1>', self.txClick1)
        canvas.tag_bind(self.ref['tx2'], '<Button-1>', self.txClick2)
        
    def SaveButton(self,canvas) :
        SaveButton = Button(canvas,text="Save",command=self.guiSave)
        SaveButton.place(x=500,y=70, height = 30, width = 40)

    def timerChangedCb(self,thisTimer,valPoint):
        valPoint = thisTimer.get(1.0, 'end')

    def createTimerBox(self,canvas,x,y,name,valPoint,helpText) :
        timerText = canvas.create_text(x+50,y,text=name,fill="green", anchor=NW)
        thisTimer= Text(canvas,height=1,width=10)
        thisTimer.place(x=x,y=y,width=40)
        #thisTimer.pack()
        thisTimer.bind('<<Modified>>', lambda event: self.timerChangedCb(thisTimer,valPoint))
        thisTimer.delete(1.0, 'end')
        thisTimer.insert(1.0, valPoint)
        thisTimer.edit_modified(False)
        CreateToolTip(thisTimer,helpText)
        
    def initTimerCanvas(self,canvas) :
        self.SaveButton(canvas)
        portText = canvas.create_text(50,0,text='Port 1',fill="white", anchor=NW)
        self.createTimerBox(canvas,20,20,'Id Timer',self.top.port1.tx.idtime,toolTips['idtime'])
        self.createTimerBox(canvas,20,40,'Polite ID',self.top.port1.tx.polite,toolTips['polite'])
        self.createTimerBox(canvas,20,60,'TX Timeout',self.top.port1.tx.timeout,toolTips['txto'])
        self.createTimerBox(canvas,20,80,'Tail Delay',self.top.port1.tx.taildly,toolTips['taildly'])
        self.createTimerBox(canvas,20,100,'Hang Time',self.top.port1.tx.hangtime,toolTips['hangtime'])
        self.createTimerBox(canvas,20,120,'Anti Kerchunk',self.top.port1.tx.txupdly,toolTips['updly'])
        self.createTimerBox(canvas,20,140,'RX Timeout',self.top.port1.rx.timeout,toolTips['rxto'])
        self.createTimerBox(canvas,20,160,'RX Reset',self.top.port1.rx.resetTimeout,toolTips['rxres'])
        self.createTimerBox(canvas,20,180,'RX Idle',self.top.port1.rx.IdleTimeout,toolTips['rxidle'])
        self.createTimerBox(canvas,20,200,'CMD Timeout',self.top.port1.rx.cmdTimeout,toolTips['cmdto'])

        portText = canvas.create_text(250,0,text='Port 2',fill="white", anchor=NW)
        self.createTimerBox(canvas,200,20,'Id Timer',self.top.port2.tx.idtime,toolTips['idtime'])
        self.createTimerBox(canvas,200,40,'Polite ID',self.top.port2.tx.polite,toolTips['polite'])
        self.createTimerBox(canvas,200,60,'TX Timeout',self.top.port2.tx.timeout,toolTips['txto'])
        self.createTimerBox(canvas,200,80,'Tail Delay',self.top.port2.tx.taildly,toolTips['taildly'])
        self.createTimerBox(canvas,200,100,'Hang Time',self.top.port2.tx.hangtime,toolTips['hangtime'])
        self.createTimerBox(canvas,200,120,'Anti Kerchunk',self.top.port2.tx.txupdly,toolTips['updly'])
        self.createTimerBox(canvas,200,140,'RX Timeout',self.top.port2.rx.timeout,toolTips['rxto'])
        self.createTimerBox(canvas,200,160,'RX Reset',self.top.port2.rx.resetTimeout,toolTips['rxres'])
        self.createTimerBox(canvas,200,180,'RX Idle',self.top.port2.rx.IdleTimeout,toolTips['rxidle'])
        self.createTimerBox(canvas,200,200,'CMD Timeout',self.top.port2.rx.cmdTimeout,toolTips['cmdto'])
    def createReadOut(self,canvas,x,y,name,valPoint,) :
        lableText = canvas.create_text(x+45,y,text=name,fill="green", anchor=NW)
        thisDisplay= Text(canvas,height=1,width=8)
        thisDisplay.place(x=x,y=y,width=40)
        thisDisplay.delete(1.0, 'end')
        thisDisplay.insert(1.0, valPoint)
        thisDisplay.edit_modified(False)
        thisDisplay['state'] = 'disabled'
        self.measurments.append((thisDisplay,valPoint))
    def updateMeasurements(self) :
        if self.gui :
            for m in self.measurments :
                (widget,val) = m
                widget.delete(1.0, 'end')
                widget.insert(1.0, val)
                print("update to %f" % val)
                widget.edit_modified(False)

    def inOutCb(self) :
        pass

    def inOutBox(self,canvas,x,y,bitNum,valPoint) :
        sbVals = ['out','in']
        sb = ttk.Spinbox(canvas,values=(sbVals), command=self.inOutCb, wrap=True)
        sb.place(x=x,y=y,width=44)
        sb.set(sbVals[(valPoint>>bitNum) & 1])
        

        
    def initPortIOCanvas(self,canvas) :
        self.measurments = []
        self.createReadOut(canvas,20,20,'Temperature',self.top.hwio.temp)
        self.createReadOut(canvas,160,20,'Humidity',self.top.hwio.hum)
        self.createReadOut(canvas,300,20,'Voltage',self.top.hwio.adc[7].val)
        self.createReadOut(canvas,450,20,'Light',self.top.hwio.adc[6].val)
        for i in range(5):
            self.createReadOut(canvas,(20 + (102*i)),50,'ADC[%d]'%i,self.top.hwio.adc[i].val)
        for i in range(8) :
            self.inOutBox(canvas,(20 + (64*i)),90,i,self.top.hwio.iodirA)
            self.inOutBox(canvas,(20 + (64*i)),130,i,self.top.hwio.iodirB)

    def init(self) :
        if(self.gui) :
            self.ref = {}
            self.initRadioCanvas(self.radioCanvas)
            self.initAudioCanvas(self.audioCanvas)
            self.initTimerCanvas(self.timerCanvas)
            self.initPortIOCanvas(self.ioCanvas)


    def updateItem(self,name,value,color=None):
        if(self.gui) :
            if(value) :
                if(color == None):
                    self.audioCanvas.itemconfig(self.ref[name], fill="green")
                else :
                    self.audioCanvas.itemconfig(self.ref[name], fill=color)
            else :
                self.audioCanvas.itemconfig(self.ref[name], fill="grey")

    def updateArray(self,name,value):
        if(self.gui) :
            for i in range (8) :
                if (value[i]) :
                    self.audioCanvas.itemconfig(self.ref[name][i], fill="green")
                else:
                    self.audioCanvas.itemconfig(self.ref[name][i], fill="grey")

    def run(self) :
        if(self.gui) :
            self.tabs.mainloop()

    def txClick1(self,event) :
        #print( 'clicked tx 1')
        if(self.top.globalState.tx1.value) :
            self.top.port1.tx.down()
            #print('was on')
        else :
            self.top.port1.tx.tx()
            #print('was off')

    def txClick2(self,event) :
        #print( 'clicked tx 2')
        if(self.top.globalState.tx2.value) :
            self.top.port2.tx.down()
            #print('was on')
        else :
            self.top.port2.tx.tx()
            #print('was off')

    def rxupdate(self,event) :
        print("rxupdate")
        rf=int(self.rxFreq.get("1.0",END))
        tf=int(self.txFreq.get("1.0",END))
        print("RX %d, TX %d" %(rf,tf));
        self.top.kenwood.setFreqDirect(tf,rf)
        
    def txupdate(self,event) :
        print("txupdate")
        rf=int(self.rxFreq.get("1.0",END))
        tf=int(self.txFreq.get("1.0",END))
        print("RX %d, TX %d" %(rf,tf));
        self.top.kenwood.setFreqDirect(tf,rf)
    def txrxUpdate(self) :
        print("TX RX Update")
        rf=int(self.rxf.val)
        tf=int(self.txf.val)
        print("RX %d, TX %d" %(rf,tf));
        self.top.kenwood.setFreqDirect(tf,rf)

    def plupdate(self) :
        print("plupdate")
        #n=self.plName.get("1.0",END)
        n=self.pl.val
        print(n);
        self.top.kenwood.setPlByName(n)
