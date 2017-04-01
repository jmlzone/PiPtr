# This file is the "user level commands" and the mapping from the
# touch tone codes to the functions.

# user functions or "marcos" below are some examples.
# the commands here work on both ports.
# for commands that should work on the port where they came in...
# a command can affect the other port....

def test123():
    print "test123"
    port0.tx.tailBeepWav = './sounds/Tink.wav'
    sys.stdout.flush()

def test456():
    print "test456"
    port0.tx.tailBeepWav = './sounds/Submarine.wav'
    sys.stdout.flush()

def test789():
    print "test789"
    port0.tx.tailBeepWav = './sounds/Glass.wav'
    sys.stdout.flush()

def cmdWithArg(arg):
    print "command got %d" %arg
    sys.stdout.flush()

def beepMethod(arg):
    port0.tx.beepMethod = arg
    print "Tail Method Set to %d" %arg
    sys.stdout.flush()

def rptDown():
    global p0
    print "Shutting down"
    tx0.down()
    GPIO.cleanup()
    p0.terminate()
    exit(-1)


def talkingClock(prefix = 'its'):
    dt = datetime.datetime.now()
    ds = dt.strftime("%I %M %p, %A %B %_d")
    myTime = prefix + " "+ ds
    os.environ['ALSA_CARD'] = 'Device'
    subprocess.call(['/usr/bin/espeak', myTime], shell=False)


# command table.
# the command table can be in the format of the long list or you can add things like shown at the end.
#
cmdlist =[("123$",test123), # the $ at the end forces an exact match
          ("456",test456),
          ("789",test789)]
cmdlist = cmdlist + [("123(\d+)", cmdWithArg)] # rexexp type argument needed 1 or more decimal digits.
cmdlist = cmdlist + [("DDDDD", rptDown)]
cmdlist = cmdlist + [("2337(\d)", beepMethod)]
