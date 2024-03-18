#!/usr/bin/env python3
def getModel ():
    """ Model from cat /proc/cpuinfo | grep Model
        ie: Model		: Raspberry Pi 4 Model B Rev 1.4
        or: Model		: Raspberry Pi Zero W Rev 1.1 """

    model = 'unknown'
    submod = 'unknown'
    rev = 'unknown'
    try:
        with open('/proc/cpuinfo', 'r', encoding='UTF-8') as file:
            while line := file.readline():
                if('Model' in line) :
                    words = line.split()
        model = words[4]
        if(words[5]) == 'Model' :
            submod = words[6]
        else:
            submod = words[5]
            
        rev = words[-1]
        file.close()
    except:
        pass
    return((model,submod,rev))

def getMemGB() :
    """memory from: cat /proc/meminfo | grep Total
       ie: MemTotal:        7998784 kB"""
    KB = '0'
    try:
        with open('/proc/meminfo', 'r', encoding='UTF-8') as file:
            while line := file.readline():
                if('MemTotal' in line) :
                    words = line.split()
        KB = words[1]
        file.close()
    except:
        pass
    MB = int(KB) / 1024
    GB = MB/1024.0
    return(GB)

if(__name__ == '__main__') :
    (model,submod,rev) = getModel()
    GB = getMemGB()
    print("This is a %s, %s rev %s with %f GB of memory" %  (model,submod,rev, GB))
