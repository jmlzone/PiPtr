#!/usr/bin/python
import threading
import time
from Tkinter import *
class gui :
    def __init__(self) :
        self.tk=Tk()
        self.c = Canvas(self.tk,bg="black",height = 350, width = 550)
        self.c.place(x=0, y=0, height = 350, width = 550)
        self.c.pack() # extends window to fit.

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

    def init(self) :
        self.mytriangle (self.c,60,70,"RX Main")
        self.mytriangle (self.c,270,70,"PGA")
        self.mytriangle (self.c,390,70,"TX Sum")
        self.mytriangle (self.c,270,200,"Computer")
        self.myres(self.c,190,30,False)
        rx = self.c.create_text(5,70,text="from\n RX",fill="green", anchor=W)
        tc = self.c.create_text(400,10,text="To Computer",fill="green", anchor=W)
        l = self.c.create_line(30,70, 60,70,fill="white")
        l2 = self.c.create_line(160,70, 170,70, 170,10, 400,10, fill="white")
        l2a = self.c.create_line(190,30, 190,10, fill="white")
        l3 = self.c.create_line(370,70, 390,70, fill="white")
        l3a = self.c.create_line(200,70,270,70, fill="white", arrow=FIRST)
        l4 = self.c.create_line(490,70, 510,70, fill="white")
        l5 = self.c.create_line(370,200, 380,200, 380,70, fill="white")
        rx = self.c.create_text(510,70,text="to\nTX",fill="green", anchor=W)
        r0 = Scale(self.tk,from_=0, to=256, orient=HORIZONTAL)
        r0.place(x=50,y=120,height=40,width=120)
        r1 = Scale(self.tk,from_=256, to=0)
        r1.place(x=210,y=20,height=120,width=40)
        r3 = Scale(self.tk,from_=0, to=256, orient=HORIZONTAL)
        r3.place(x=385,y=120,height=40,width=120)
        r2 = Scale(self.tk,from_=0, to=256, orient=HORIZONTAL)
        r2.place(x=260,y=250,height=40,width=120)
        R0 = 150
        R1 = 2
        R2 = 50
        R3 = 20
        r0.set(R0)
        r1.set(R1)
        r2.set(R2)
        r3.set(R3)
        co = self.c.create_text(5,200,text="From Computer", anchor=W, fill="green")
        l6 = self.c.create_line(105,200, 270,200,fill="white")
        self.c.create_text(35,300,text="COR",fill="green")
        self.c.create_text(85,300,text="CTCSS",fill="green")
        self.c.create_text(515,300,text="TX",fill="green")
        self.corLed = self.c.create_oval(20,310, 50,340, fill="grey")
        self.ctcssLed = self.c.create_oval(70,310, 100,340, fill="grey")
        self.txLed = self.c.create_oval(500,310, 530,340, fill="grey")
        x=140
        y=310
        self.softArr = []
        for i in range (8) :
            t=self.c.create_oval(x,y,x+30,y+30, fill="grey")
            self.softArr.append(t)
            x=x+40

    def updateRxGui(self, port,cor,ctcss,softCtcss) :
        if(cor) :
            self.c.itemconfig(self.corLed, fill="green")
        else:
            self.c.itemconfig(self.corLed, fill="grey")
        if(ctcss) :
            self.c.itemconfig(self.ctcssLed, fill="green")
        else:
            self.c.itemconfig(self.ctcssLed, fill="grey")

        for i in range (8) :
            if (softCtcss[i]) :
                self.c.itemconfig(self.softArr[i], fill="green")
            else:
                self.c.itemconfig(self.softArr[i], fill="grey")
            
    def updateTxGui(self,port,tx) :
        if(tx) :
            self.c.itemconfig(self.txLed, fill="red")
        else:
            self.c.itemconfig(self.txLed, fill="grey")

    def run(self) :
        self.tk.mainloop()

