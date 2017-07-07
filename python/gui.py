#!/usr/bin/python
import threading
import time
from tkinter import *
import socket
import os
import sys
import pdb
from xmlio import dumpXml
class gui :
    def __init__(self,top) :
        try: 
            self.tk=Tk()
            self.c = Canvas(self.tk,bg="black",height = 400, width = 550)
            self.c.place(x=0, y=0, height = 400, width = 550)
            self.c.pack() # extends window to fit.
            self.gui = True
        except:
            self.gui = False
        self.top = top

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
    def portSelect(self) :
        val = self.ps.get()
        if (val == 'port1') :
            self.RA = self.top.hwio.vals[0]
            self.RB = self.top.hwio.vals[1]
            self.RC = self.top.hwio.vals[2]
            self.RD = self.top.hwio.vals[3]
        else :
            self.RA = self.top.hwio.vals[4]
            self.RB = self.top.hwio.vals[5]
            self.RC = self.top.hwio.vals[6]
            self.RD = self.top.hwio.vals[7]
        self.updateRs()

    def updateRs(self):
        self.rA.set(self.RA)
        self.rB.set(self.RB)
        self.rC.set(self.RC)
        self.rD.set(self.RD)

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
    def rEcb(self,val) :
        self.updateRn(val,8,step=1)
    
    def init(self) :
        self.ref = {}
        self.mytriangle (self.c,60,100,"RX Main")
        self.mytriangle (self.c,180,70,"PGA")
        self.mytriangle (self.c,300,70,"TX Sum")
        self.mytriangle (self.c,180,200,"Computer")
        #self.myres(self.c,190,30,False)
        desc = self.c.create_text(5,30,text="Desc\n in",fill="green", anchor=W)
        rx = self.c.create_text(5,100,text="from\n RX",fill="green", anchor=W)
        tc = self.c.create_text(310,10,text="To Computer",fill="green", anchor=W)
        dci = self.c.create_line(30,30, 50,30,fill="white")
        #dco = self.c.create_line(150,30, 170,30,fill="white")
        l = self.c.create_line(30,100, 60,100,fill="white")
        l2 = self.c.create_line(160,100, 170,100, 170,10, 310,10, fill="white")
        l2a = self.c.create_line(170,70, 180,70, fill="white")
        l3 = self.c.create_line(280,70, 300,70, fill="white")
        #l3a = self.c.create_line(200,70,270,70, fill="white", arrow=FIRST)
        l4 = self.c.create_line(400,70, 420,70, fill="white")
        l5 = self.c.create_line(280,200, 290,200, 290,70, fill="white")
        tx = self.c.create_text(420,70,text="to\nTX",fill="green", anchor=W)
        tx = self.c.create_text(420,220,text="CTCSS\nTX",fill="green", anchor=W)
        self.rA = Scale(self.tk,from_=0, to=256, orient=HORIZONTAL, command=self.rAcb)
        self.rA.place(x=40,y=150,height=40,width=120)
        self.rB = Scale(self.tk,from_=0, to=256, orient=HORIZONTAL, command=self.rBcb)
        self.rB.place(x=40,y=10,height=40,width=120)
        self.rC = Scale(self.tk,from_=0, to=256, orient=HORIZONTAL, command=self.rCcb)
        self.rC.place(x=170,y=250,height=40,width=120)
        self.rD = Scale(self.tk,from_=0, to=256, orient=HORIZONTAL, command=self.rDcb)
        self.rD.place(x=295,y=120,height=40,width=120)
        self.rE = Scale(self.tk,from_=0, to=256, orient=HORIZONTAL, command=self.rEcb)
        self.rE.place(x=295,y=200,height=40,width=120)
        self.ps = Spinbox(self.tk,values=('port1','port2'), command=self.portSelect, wrap=True)
        self.ps.place(x=400,y=30,width=50)
        self.portSelect()
        co = self.c.create_text(5,200,text="From Computer", anchor=W, fill="green")
        l6 = self.c.create_line(105,200, 180,200,fill="white")
        self.c.create_text(35,300,text="COR",fill="green")
        self.c.create_text(85,300,text="CTCSS",fill="green")
        self.c.create_text(515,300,text="TX",fill="green")
        self.ref['cor1'] = self.c.create_oval(20,310, 50,340, fill="grey")
        self.ref['ctcss1'] = self.c.create_oval(70,310, 100,340, fill="grey")
        self.ref['tx1'] = self.c.create_oval(500,310, 530,340, fill="grey")
        self.ref['cor2'] = self.c.create_oval(20,360, 50,390, fill="grey")
        self.ref['ctcss2'] = self.c.create_oval(70,360, 100,390, fill="grey")
        self.ref['tx2'] = self.c.create_oval(500,360, 530,390, fill="grey")
        x=140
        y1=310
        y2=360
        tone = ["77.0", "88.5", "103.5", "110.9",
                "114.8", "123.0", "146.2", "165.5" ]
        self.ref['softCtcss1'] = []
        self.ref['softCtcss2'] = []
        for i in range (8) :
            self.c.create_text(x+15,300,text=tone[i],fill="green")
            t=self.c.create_oval(x,y1,x+30,y1+30, fill="grey")
            self.ref['softCtcss1'].append(t)
            t=self.c.create_oval(x,y2,x+30,y2+30, fill="grey")
            self.ref['softCtcss2'].append(t)
            x=x+40
        SaveButton = Button(self.tk,text="Save",command=self.guiSave)
        SaveButton.place(x=20,y=240, height = 30, width = 40)


    def updateItem(self,name,value,color=None):
        if(self.gui) :
            if(value) :
                if(color == None):
                    self.c.itemconfig(self.ref[name], fill="green")
                else :
                    self.c.itemconfig(self.ref[name], fill=color)
            else :
                self.c.itemconfig(self.ref[name], fill="grey")

    def updateArray(self,name,value):
        if(self.gui) :
            for i in range (8) :
                if (value[i]) :
                    self.c.itemconfig(self.ref[name][i], fill="green")
                else:
                    self.c.itemconfig(self.ref[name][i], fill="grey")

    def run(self) :
        if(self.gui) :
            self.tk.mainloop()

