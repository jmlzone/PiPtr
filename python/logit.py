import datetime
import sys

def logit(msg) :
    dt = datetime.datetime.now()
    ds = dt.strftime("%B %d, %Y %I:%M:%S%p")
    print(ds + " - " + msg)
    sys.stdout.flush()

