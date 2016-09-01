from labrad.server import LabradServer, setting
from twisted.internet.defer import inlineCallbacks, returnValue
import random
import numpy as np
import time as t

class MyServer(LabradServer):
    name = "My Server"    # Will be labrad name of server

    start = t.time() 
    @setting(10, returns='v')
    def Temperature(self, c):
        
        #return np.sin((t.time()-self.start)/2)
        return 1 + random.random()
    @setting(11, returns = 'v')
    def Pressure(self, c, data):
          #return np.sin((t.time()-self.start)/1.5)
          return 2+ random.random()
    def somethingElse(self):
        print("something Else")
        
__server__ = MyServer()

if __name__ == '__main__':
    from labrad import util
    util.runServer(__server__)
