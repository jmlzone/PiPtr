#!/usr/bin/python
import threading
import time
from Tkinter import *
tk=Tk()
#w = Label(tk,text="Hello Tkinter")
c = Canvas(tk,bg="black",height = 350, width = 550)
c.place(x=0, y=0, height = 350, width = 550)

def mytriangle (canvas,x,y,text) :
    """ draw a horizontal triangle centered starting at startxy """
    incr=100
    t=canvas.create_polygon(x,y-(incr/2),x,y+(incr/2),x+incr,y,x,y-(incr/2), fill="grey")
    canvas.pack()
    tx=canvas.create_text(x + ((incr/2) -10),y, text=text)

def myres(canvas,startx,starty,hv) :
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

mytriangle (c,60,70,"RX Main")
mytriangle (c,270,70,"PGA")
mytriangle (c,390,70,"TX Sum")
mytriangle (c,270,200,"Computer")
myres(c,190,30,False)

rx = c.create_text(5,70,text="from\n RX",fill="green", anchor=W)
tc = c.create_text(400,10,text="To Computer",fill="green", anchor=W)
l = c.create_line(30,70, 60,70,fill="white")
l2 = c.create_line(160,70, 170,70, 170,10, 400,10, fill="white")
l2a = c.create_line(190,30, 190,10, fill="white")
l3 = c.create_line(370,70, 390,70, fill="white")
l3a = c.create_line(200,70,270,70, fill="white", arrow=FIRST)
l4 = c.create_line(490,70, 510,70, fill="white")
l5 = c.create_line(370,200, 380,200, 380,70, fill="white")
rx = c.create_text(510,70,text="to\nTX",fill="green", anchor=W)
r0 = Scale(tk,from_=0, to=256, orient=HORIZONTAL)
r0.place(x=50,y=120,height=40,width=120)
r1 = Scale(tk,from_=256, to=0)
r1.place(x=210,y=20,height=120,width=40)
r3 = Scale(tk,from_=0, to=256, orient=HORIZONTAL)
r3.place(x=385,y=120,height=40,width=120)
r2 = Scale(tk,from_=0, to=256, orient=HORIZONTAL)
r2.place(x=260,y=250,height=40,width=120)
R0 = 150
R1 = 2
R2 = 50
R3 = 20
r0.set(R0)
r1.set(R1)
r2.set(R2)
r3.set(R3)
co = c.create_text(5,200,text="From Computer", anchor=W, fill="green")
l6 = c.create_line(105,200, 270,200,fill="white")
c.create_text(35,300,text="COR",fill="green")
c.create_text(85,300,text="CTCSS",fill="green")
c.create_text(515,300,text="TX",fill="green")
corLed = c.create_oval(20,310, 50,340, fill="grey")
ctcssLed = c.create_oval(70,310, 100,340, fill="grey")
txLed = c.create_oval(500,310, 530,340, fill="grey")
