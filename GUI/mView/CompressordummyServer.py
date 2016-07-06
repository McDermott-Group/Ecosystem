from labrad.server import LabradServer, setting
from twisted.internet.defer import inlineCallbacks, returnValue
import random
class MyServer(LabradServer):
    name = "My Server"    # Will be labrad name of server
    lastRandom=100;
    deltaRandom = 5;

    @setting(10, returns='w')
    def Temperature(self, c):
        return random.randrange(self.lastRandom-self.deltaRandom, self.lastRandom+self.deltaRandom);
    
    @setting(11, returns = 'w')
    def Pressure(self, c, data):
         return random.randrange(self.lastRandom-self.deltaRandom, self.lastRandom+self.deltaRandom);
    
    def somethingElse(self):
        print("something Else")
        
__server__ = MyServer()

if __name__ == '__main__':
    from labrad import util
    util.runServer(__server__)
