"""
### BEGIN NODE INFO
[info]
name = AVS47 Resistance Bridge
version = 1.0.0
description = Monitors DR temperatures

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
"""

import os
import sys
import time
# The LoopingCall function allows a function to be called periodically
# on a time interval.
from twisted.internet.task import LoopingCall
from twisted.internet.reactor import callLater
from twisted.internet.defer import inlineCallbacks, returnValue

from labrad.devices import DeviceServer, DeviceWrapper
from labrad.server import setting
import labrad.units as units
from labrad import util

if __file__ in [f for f in os.listdir('.') if os.path.isfile(f)]:
    SCRIPT_PATH = os.path.dirname(os.getcwd())
else:
    SCRIPT_PATH = os.path.dirname(__file__)
LOCAL_PATH = SCRIPT_PATH.rsplit('instruments', 1)[0]
INSTRUMENTS_PATH = os.path.join(LOCAL_PATH, 'instruments')
if INSTRUMENTS_PATH not in sys.path:
    sys.path.append(INSTRUMENTS_PATH)

from utilities.gpib_device_wrapper import ReadRawGPIBDeviceWrapper
from utilities.sleep import sleep


class AVS47ResistanceBridgeWrapper(DeviceWrapper):

    @inlineCallbacks
    def connect(self, server, port):
        print('Connecting to "%s" on port "%s"...' %(server.name, port))
        self.server = server
        self.ctx = server.context()
        self.port = port
        p = self.packet()
        p.open(port)
        p.baudrate(9600L)
        p.stopbits(1L)
        p.bytesize(8L)
        p.parity('N')
        p.rts(False)
        p.dtr(False)
        p.timeout(5 * units.s)
        p.read_line()
        yield p.send()
    
    def packet(self):
        return self.server.packet(context=self.ctx)
    
    def shutdown(self):
        return self.packet().close().send()
     
    @inlineCallbacks
    def write_line(self, code):
        yield self.server.write_line(code, context=self.ctx)
        
    @inlineCallbacks    
    def read_line(self):
        ans = yield self.server.read(context = self.ctx)
        returnValue(ans)
        
        
class AVS47ResistanceBridgeServer(DeviceServer):
    deviceName = 'AVS47 Resistance Bridge'
    name = 'AVS47 Resistance Bridge'
    deviceWrapper = AVS47ResistanceBridgeWrapper
    
    @inlineCallbacks
    def initServer(self):
        print('Server initializing...')
        self.reg = self.client.registry()
        yield self.loadConfigInfo()
        yield DeviceServer.initServer(self)
        print self.serialLinks
        
    @setting(9, 'Start Server', returns='b')
    def startServer(self, c):
        self.dev = self.selectedDevice(c)
        callLater(0.1, self.startRefreshing)
        return True
        
    @setting(10, 'Identify', returns='s')
    def identify(self, c):
        self.dev = self.selectedDevice(c)
        yield self.dev.write_line("*IDN?")
        yield sleep(0.5)
        reading = yield self.dev.read_line()
        reading = yield str(reading.rstrip("\r\n"))
        returnValue(reading)
        
    @inlineCallbacks
    def loadConfigInfo(self):
        """Load configuration information from the registry."""
        reg = self.reg
        yield reg.cd(['', 'Servers', 'AVS47 Resistance Bridge', 'Links'], True)
        dirs, keys = yield reg.dir()
        p = reg.packet()
        for k in keys:
            p.get(k, key=k)
        ans = yield p.send()
        self.serialLinks = dict((k, ans[k]) for k in keys) 

    @inlineCallbacks    
    def findDevices(self):
        """Find available devices from a list stored in the registry."""
        devs = []
        for name, (server, port) in self.serialLinks.items():
            if server not in self.client.servers:
                continue
            server = self.client[server]
            ports = yield server.list_serial_ports()
            if port not in ports:
                continue
            devName = '{} - {}'.format(server, port)
            devs += [(name, (server, port))]
        returnValue(devs)

    def startRefreshing(self):
        """
        Start periodically refreshing the list of devices.
        The start call returns a deferred which we save for later.
        When the refresh loop is shutdown, we will wait for this
        deferred to fire to indicate that it has terminated.
        """
        self.refresher = LoopingCall(self.checkMeasurements)
        self.refresherDone = self.refresher.start(5.0, now=True)    
        
__server__ = AVS47ResistanceBridgeServer()


if __name__ == '__main__':
    util.runServer(__server__)