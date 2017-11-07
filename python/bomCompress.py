#!/usr/bin/python
import os
import re
import string
import sys

ifile = sys.argv[1]
ofile = sys.argv[2]
matchFootPrintOnly = ["J"]
ignoreRef  = r'^TP*'
ignoreValue = ["TESTPOINT", "SPARE", "MOUNTING_HOLE"]

csvi = os.path.expandvars(os.path.expanduser(ifile))

groups = []
def newGroup(ref,val,foorptint) :
    groups.append([val,footprint,[ref],ref[0]])
def addToGroup(g,ref,val,footprint):
    groups[g][2].append(ref)
def fits(g,ref,val,footprint) :
    if(footprint == groups[g][1]) :
        if( (val == groups[g][0] and ref[0] == groups[g][3]) or (ref[0] in matchFootPrintOnly)) :
            #print ("fit val %s fp %s" % (val,footprint))
            return True
        else :
            #print("no fit for val fp = %s v1 %s V2 %s" %(footprint, groups[g][0],val))
            return False
    else :
        #print("no fit fp %s %s" %(groups[g][0], footprint))
        return False
        

Header = False
fi=open(csvi)
for line in fi:
    fulltext = line.strip()
    if(not Header) :
        Header = True
    else :
        fields = fulltext.split(',')
        ref = re.sub(r'^"|"$', '', str(fields[0]))
        val = re.sub(r'^"|"$', '',str(fields[1]))
        footprint = re.sub(r'^"|"$', '',str(fields[2]))
        matchRef = re.search(ignoreRef,ref)
        if((not val in ignoreValue) and (not matchRef)) :
            found = False
            for g in range(len(groups)) :
                if( not found and fits(g, ref, val, footprint) ) :
                    found = True
                    addToGroup(g,ref,val,footprint)
            if(not found) :
                newGroup(ref,val,footprint)
fi.close()
print("created  %d groups" % len(groups))
csvo = os.path.expandvars(os.path.expanduser(ofile))
fo = open(csvo ,"w")
fo.write("type,val,count,footprint,refs\n")
for g in range(len(groups)) :
  fo.write ("%s,%s,%d,%s,%s\n" %(groups[g][3],groups[g][0],len(groups[g][2]),groups[g][1], ' '.join(groups[g][2])))
fo.close()
