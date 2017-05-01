class SpiDev:
    def __init__(self,*a,**kw):
        pass
    def open(self,*a,**kw):
        print("spi open",a,kw)
    def xfer2(self,*a,**kw):
        print("spi xfer2",a,kw)
        return [0]
    def close(self):
        pass
