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
version = 1.0.14
description = Monitors flow

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
"""

from labrad.devices import DeviceServer, DeviceWrapper
from labrad.server import setting
import labrad.units as units
from twisted.internet.defer import inlineCallbacks, returnValue
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
        """Write a data value to the rate monitor."""
        p = self.packet()
        p.write_line(code)
        yield p.send()

    @inlineCallbacks
    def read_line(self, code=None):
        """Read a data value to the rate monitor."""
        p = self.packet()
        if code is not None:
            p.read_line(code)
        else:
            p.read_line(code)
        ans = yield p.send()
        returnValue(ans.read_line)


class OmegaRatemeterServer(DeviceServer):
    deviceName = 'Omega Ratemeter Server'
    name = 'Omega Ratemeter Server'
    deviceWrapper = OmegaRatemeterWrapper

    @setting(10, 'Get Rate', returns='v[ml/min]')
    def getRate(self, c):
        """Get flow rate."""
        dev = self.selectedDevice(c)
        yield dev.write_line("@U?V\r")
        reading = yield dev.read_line()
        returnValue(float(reading) * units.galUS / units.min)

    @inlineCallbacks
    def initServer(self):
        self.reg = self.client.registry()
        yield self.loadConfigInfo()
        yield DeviceServer.initServer(self)
    
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


__server__ = OmegaRatemeterServer()


if __name__ == '__main__':
    util.runServer(__server__)
