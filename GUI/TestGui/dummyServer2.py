from labrad.server import LabradServer, setting
import labrad.units as units
from twisted.internet.defer import inlineCallbacks, returnValue
import random
import numpy as np
import time as t
import urllib2
import json
import random

class MyServer2(LabradServer):
    name = "My Server2"    # Will be labrad name of server

    start = t.time() 
    zip = 100
    prev0 = 0 
    prev1 = 0
    prev2 = 0 
    @setting(10, returns='v[degF]')
    def Temperature(self, c):
        new =  self.prev2 + self.zip*(random.random()-0.5)
        self.prev2 = new
        return new*units.degF
       # return 0.5
    @setting(100, returns='v[bar]')
    def pressure(self, c):
       
        new =  self.prev1 + self.zip*(random.random()-0.5)
        self.prev1 = new
        return new*units.bar
    @setting(200, returns='v[g]')
    def moisture(self, c):
       
        new =  self.prev0 + self.zip*(random.random()-0.5)
        self.prev0 = new
        return new*units.g
    @setting(11, zip = 'i')
    def changeLocation(self, ctx, zip):
        self.zip = zip
    def somethingElse(self):
        print("something Else")
        
__server__ = MyServer2()

if __name__ == '__main__':
    from labrad import util
    util.runServer(__server__)
