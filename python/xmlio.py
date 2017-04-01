from xml.etree import ElementTree as XML
from xml.dom import minidom
# at some point some effort should be make to name the xml file something specific to the node

def dumpXml() :
    generated_on = str(datetime.datetime.now())
    config = XML.Element('config')
    comment = XML.Comment("configuration dumped on " + generated_on)
    config.append(comment)
    for v in xmlvars :
        ve = XML.SubElement(config,v)
        vv = eval(v)
        ve.text=str(vv)
    for p in ('port1', 'port2') :
        portvars = eval(p + ".xmlvars")
        port = XML.SubElement(config, p)
        for pi in portvars :
            pe = XML.SubElement(port,pi)
            pev = eval(p + "." + pi)
            pe.text = str(pev)
        for tr in ('tx', 'rx') :
            tre = XML.SubElement(port,tr)
            trl = eval(p + "." + tr + ".xmlvars")
            for tri in trl :
                triv = XML.SubElement(tre,tri)
                trv = eval(p + "." + tr + "." + tri)
                triv.text = str(trv)
                

    f = open("config.xml", "w")
    f.write(minidom.parseString(XML.tostring(config)).toprettyxml(indent = "  "))
    f.close()
    
def isInt_str(v):
    return v=='0' or (v if v.find('..') > -1 else v.lstrip('-+').rstrip('0').rstrip('.')).isdigit()

def isBool_str(v):
    return v=='True' or v=='False'

def isList_str(v):
    return v.startswith('[') and v.endswith(']')

def isFloat_str(v) :
    return v.replace('.','',1).isdigit()

def isOK(v):
    v = str(v).strip()
    if(isInt_str(v)) :
        #print "Int"
        return True
    elif (isFloat_str(v)) :
        #print "Float"
        return True
    elif (isBool_str(v)) :
        #print "Bool"
        return True
    elif (isList_str(v)) :
        #print "List"
        return True
    else :
        return False

def processList(root,hierarchy) :
    for child in root :
        if ( list(child) ) :
            processList (child, hierarchy + child.tag + ".")
        else :
            val = child.text.strip()
            if (not isOK(val) ) :
                val =  "'"+val+"'"
            #print hierarchy + child.tag + " = " + val
            exec(hierarchy + child.tag + " = " + val)
            


def loadXml(fileName) :
    rf = open(fileName, "rt")
    rt = XML.ElementTree.Parse(rf)
    rf.close()
    root = rt.getroot()
    processList(root, "")

    
