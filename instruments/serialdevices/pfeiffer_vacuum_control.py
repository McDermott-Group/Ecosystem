
# Copyright (C) 2016 Noah Meltzer, Alexander Opremcak
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

"""
### BEGIN NODE INFO
[info]
name = Pfeiffer Vacuum Control Unit
version = 1.0.14
description = Monitors and Controls Vacuum System

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
"""
# The LoopingCall function allows a function to be called periodically
# on a time interval.
from twisted.internet.task import LoopingCall
from twisted.internet.reactor import callLater
from twisted.internet.defer import inlineCallbacks, returnValue

from labrad.devices import DeviceServer, DeviceWrapper
from labrad.server import setting
import labrad.units as units
from labrad import util
import time

class PfeifferVacuumControlWrapper(DeviceWrapper):
    @inlineCallbacks
    def connect(self, server, port):
        """Connect to an Pfeiffer Vacuum Control Unit."""
        print('Connecting to "%s" on port "%s"...' %(server.name, port))
        self.server = server
        self.ctx = server.context()
        self.port = port
        p = self.packet()
        p.open(port)
        # The following parameters match the default configuration of the
        # serial device.
        p.baudrate(9600L)
        p.stopbits(1L)
        p.bytesize(8L)
        p.parity('N')
        p.rts(False)
        p.timeout(2 * units.s)
        # Clear out the read buffer. This is necessary for some devices.
        p.read_line()
        yield p.send()
        
    def packet(self):
        """Create a packet in our private context."""
        return self.server.packet(context=self.ctx)
    
    def shutdown(self):
        """Disconnect from the serial port when we shut down."""
        return self.packet().close().send()
    
    @inlineCallbacks
    def write_line(self, code):
        """Write data value to the rate monitor."""
        yield self.server.write_line(code, context = self.ctx)

    @inlineCallbacks
    def write(self, code):
        """Write data value to the rate monitor."""
        yield self.server.write(code, context = self.ctx)
        
    @inlineCallbacks
    def read_line(self):
        """Read data value from the rate monitor."""
        ans = yield self.server.read(context = self.ctx)
        print "ans=", ans
        returnValue(ans)

    @inlineCallbacks
    def read(self):
        """Write data value to the rate monitor."""
        ans =  yield self.server.read(context = self.ctx)
        returnValue(ans)

class OmegaRatemeterServer(DeviceServer):
    deviceName = 'Pfeiffer Vacuum Control Unit'
    name = 'Pfeiffer Vacuum Control Unit'
    deviceWrapper = PfeifferVacuumControlWrapper
    
    @inlineCallbacks
    def initServer(self):
        """Initializes the server"""
        print "Server Initializing"        
        self.reg = self.client.registry()
        yield self.loadConfigInfo()
        yield DeviceServer.initServer(self)
    
    def startRefreshing(self):
        """
        Start periodically refreshing the list of devices.
        The start call returns a deferred which we save for later.
        When the refresh loop is shutdown, we will wait for this
        deferred to fire to indicate that it has terminated.
        """
        self.refresher = LoopingCall(self.checkMeasurements)
        self.refresherDone = self.refresher.start(5, now=True)

    @inlineCallbacks
    def stopServer(self):
        """Kill the device refresh loop and wait for it to terminate."""
        if hasattr(self, 'refresher'):
            self.refresher.stop()
            yield self.refresherDone
      
    @setting(9, 'Start Server', returns='b')
    def startServer(self, c):
        """
        starts server. Initializes the repeated flow rate measurement.
        """
        self.dev = self.selectedDevice(c)
        i =1
        callLater(0.1, self.startRefreshing)
        return(True)
    
    @inlineCallbacks
    def getPressures(self, dev):
        # Iterate through sensors 1 to 6
        for i in range(1, 7):
            # The serial command 'PRx' tells the device that we are
            # talking about sensor x.
            yield self.dev.write("PR"+str(i)+"\r\n")
            # Give the device time to receive and process the request
            time.sleep(0.05)
            # The device responds with an acknowledge, discard it.
            yield self.dev.read()
            time.sleep(0.05)
            # Write the 'enquire' code to the serial bus. This tells the
            # device that we want a reading
            yield self.dev.write("\x05\r\n")
            time.sleep(0.05)
            response = yield self.dev.read()
            # The reading is formatted in the following way:
            # 'status,measurement.'
            # Separate the status code from the reading
            response = response.rsplit(',')
            pressure = response[1]
            status = response[0]
            # A status code of 5 means that no sensor is connected
            if(status == '5'):
                print("sensor "+str(i)+": Not Connected")
            else:
                # Using rstrip(), strip whitespace and escape characters
                # off the end of the reading
                print("sensor "+str(i)+": "+pressure.rstrip())
        
           
                
            
        returnValue(None)
        
    @inlineCallbacks
    def checkMeasurements(self):
        """Make sure the flow rate is within range."""
        output = yield self.getPressures(self.dev)

    @inlineCallbacks
    def loadConfigInfo(self):
        """Load configuration information from the registry."""
        reg = self.reg
        yield reg.cd(['', 'Servers', 'Leiden Vacuum Monitor', 'Links'], True)
        dirs, keys = yield reg.dir()
        p = reg.packet()
        for k in keys:
            p.get(k, key=k)
        ans = yield p.send()
        self.serialLinks = dict((k, ans[k]) for k in keys)

    def sendAlert(self):
        raise NotImpementedError('An email alert will be sent in future.')

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

__server__ = OmegaRatemeterServer()


if __name__ == '__main__':
    util.runServer(__server__)

