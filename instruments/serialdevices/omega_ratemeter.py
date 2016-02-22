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
name = Omega Ratemeter Server
version = 1.0.15
description = Monitors flow

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


class OmegaRatemeterWrapper(DeviceWrapper):
    @inlineCallbacks
    def connect(self, server, port):
        """Connect to an Omega rate monitor."""
        print('Connecting to "%s" on port "%s"...' %(server.name, port))
        self.server = server
        self.ctx = server.context()
        self.port = port
        p = self.packet()
        p.open(port)
        # Where are these parameters coming from?
        p.baudrate(9600L)
        p.stopbits(1L)
        p.bytesize(7L)
        p.parity('E')
        p.rts(False)
        p.timeout(1 * units.s)
        p.read_line() # Clear out the read buffer.
        yield p.send()
        
    def packet(self):
        """Create a packet in our private context."""
        return self.server.packet(context=self.ctx)
    
    def shutdown(self):
        """Disconnect from the serial port when we shut down."""
        return self.packet().close().send()
    
    @inlineCallbacks
    def write_line(self, code):
        """Write a command to the rate monitor."""
        p = self.packet()
        p.write_line(code)
        yield p.send()

    @inlineCallbacks
    def read_line(self):
        """Read a line from the rate monitor."""
        p = self.packet()
        p.read_line()
        returnValue(yield p.send())


class OmegaRatemeterServer(DeviceServer):
    deviceName = 'Omega Ratemeter Server'
    name = 'Omega Ratemeter Server'
    deviceWrapper = OmegaRatemeterWrapper
    
    @inlineCallbacks
    def initServer(self):
        """Initialize the server."""
        print("Server initializing...")  
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
        self.refresherDone = self.refresher.start(5.0, now=True)

    @inlineCallbacks
    def stopServer(self):
        """Kill the device refresh loop and wait for it to terminate."""
        if hasattr(self, 'refresher'):
            self.refresher.stop()
            yield self.refresherDone
      
    @setting(9, 'Start Server', returns='')
    def start_server(self, c):
        """
        Start server and initialize the repeated flow rate measurement.
        """
        self.dev = self.selectedDevice(c)
        callLater(0.1, self.startRefreshing)
    
    @inlineCallbacks
    def getRate(self, dev):
        """Get flow rate."""
        # The crazy in the next line is because...
        yield dev.write_line("@U?V\r")
        reading = yield dev.read_line()
        # Get last number in string.
        reading.rsplit(None, 1)[-1]
        # Strip the 'L' off.
        reading = float(reading.lstrip("L"))
        # Convert it to correct units, the reading are in gpm.
        output = reading * units.galUS / units.min
        returnValue(output)

    @inlineCallbacks
    def checkMeasurements(self, dev):
        """Make sure the flow rate is within the range."""
        raise NotImpementedError('')
        rate = yield self.getRate(dev)
        
    @inlineCallbacks
    def loadConfigInfo(self):
        """Load configuration information from the registry."""
        reg = self.reg
        yield reg.cd(['', 'Servers', 'Omega Ratemeter', 'Links'], True)
        dirs, keys = yield reg.dir()
        p = reg.packet()
        for k in keys:
            p.get(k, key=k)
        ans = yield p.send()
        self.serialLinks = {k: ans[k] for k in keys}

    def sendAlert(self):
        raise NotImpementedError('An email alert will be sent in future.')
        
    @inlineCallbacks    
    def findDevices(self):
        """Find available devices from a list stored in the registry."""
        devs = []
        for name, (server, port) in self.serialLinks:
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
