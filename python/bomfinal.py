#!/usr/bin/python
import os
import re
import string
import sys
import csv
ifile = sys.argv[1]
ofile = sys.argv[2]
csvi = os.path.expandvars(os.path.expanduser(ifile))
csvo = os.path.expandvars(os.path.expanduser(ofile))
fo = open(csvo ,"w")
foWriter=csv.writer(fo, lineterminator='\n')
foWriter.writerow(["Designator","Manufacturer Part Number","Quantity"])
Header = False

fi=open(csvi)
fiReader = csv.reader(fi)
#for line in fi:
for row in fiReader:
    if(not Header) :
        Header = True
    else :
        #fulltext = line.strip()
        #fields = fulltext.split(',')
        fields = row
        count=fields[2]
        mpn=fields[3]
        seeedSku= fields[4]
        refs=fields[6]
        if(seeedSku != '') :
            pn = seeedSku
        else :
            pn = mpn
        des=','.join(refs.split(' '))
        if(pn != '') :
            foWriter.writerow([des,pn,count])
fi.close()
fo.close()
