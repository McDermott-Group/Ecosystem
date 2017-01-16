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
    zip = 10
    @setting(10, returns='v[degF]')
    def Temperature(self, c):
      
        return random.random()*self.zip*units.degF
       # return 0.5
    @setting(11, zip = 'i')
    def changeLocation(self, ctx, zip):
        self.zip = zip
    def somethingElse(self):
        print("something Else")
        
__server__ = MyServer2()

if __name__ == '__main__':
    from labrad import util
    util.runServer(__server__)
