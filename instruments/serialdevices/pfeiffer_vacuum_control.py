
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
## This entire program is not meant to be edited yet, it is very rough and doesn't do anything yet!
from labrad.devices import DeviceServer, DeviceWrapper
from labrad.server import setting
import labrad.units as units
from twisted.internet.defer import inlineCallbacks, returnValue
from labrad import util

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
        """Write a data value to the vacuum control unit."""
        p = self.packet()
        p.write_line(code)
        yield p.send()
        
    @inlineCallbacks
    def read_line(self):
        """Read a data value from the vacuum control unit."""
        p = self.packet()
        p.read_line()
        ans = yield p.send()
        returnValue(ans.read_line)

class OmegaRatemeterServer(DeviceServer):
    deviceName = 'Pfeiffer Vacuum Control Unit'
    name = 'Pfeiffer Vacuum Control Unit'
    deviceWrapper = OmegaRatemeterWrapper
    
    @inlineCallbacks
    def initServer(self):
        """Initializes the server"""
        print "Server Initializing"        
        self.reg = self.client.registry()
        yield self.loadConfigInfo()
        yield DeviceServer.initServer(self)
    
    def startRefreshing(self):
        """Start periodically refreshing the list of devices.
        The start call returns a deferred which we save for later.
        When the refresh loop is shutdown, we will wait for this
        deferred to fire to indicate that it has terminated.
        """
        dev = self.dev
        self.refresher = LoopingCall(self.refreshMe)
        self.refresherDone = \
                self.refresher.start(5.0,
                now=True)
