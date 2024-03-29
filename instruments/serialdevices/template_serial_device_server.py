# Copyright (C) 2019 Chuanhong (Vincent) Liu
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


# This is a server template for serial device in Robert McDermott's lab.

"""
### BEGIN NODE INFO
[info]
name = SR560
version = 1.0.0
description = Remote control the front panel of sr560 low-noise preamplifier

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
from twisted.internet.task import LoopingCall
from twisted.internet.reactor import callLater
from twisted.internet.defer import inlineCallbacks, returnValue

from labrad.devices import DeviceServer, DeviceWrapper
from labrad.server import setting
import labrad.units as units
from labrad import util


class SR560Wrapper(DeviceWrapper):
    @inlineCallbacks
    def connect(self, server, port):
        """Connect to an SR560 Amplifier."""
        print(('Connecting to "%s" on port "%s"...' % (server.name, port)))
        self.server = server
        self.ctx = server.context()
        self.port = port
        p = self.packet()
        p.open(port)
        # The following parameters match the default configuration of
        # the SR560 unit. You should go to the instrument menu and change
        # the settings below.
        p.baudrate(9600)
        p.stopbits(2)
        p.bytesize(8)
        p.parity("N")
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
    def write(self, code):
        """Write data value to the SR560 unit."""
        yield self.server.write(code, context=self.ctx)

    @inlineCallbacks
    def read(self):
        """Read data value from the SR560 unit."""
        ans = yield self.server.read(context=self.ctx)
        returnValue(ans)


class SR560Server(DeviceServer):
    """Provides direct access to serial devices."""

    deviceName = "SR560"
    name = "SR560"
    deviceWrapper = SR560Wrapper

    @inlineCallbacks
    def initServer(self):
        self.mydevices = {}
        yield self.loadConfigInfo()
        yield DeviceServer.initServer(self)
        # start refreshing only after we have started serving
        # this ensures that we are added to the list of available
        # servers before we start sending messages

    @inlineCallbacks
    def loadConfigInfo(self):
        """Load configuration information from the registry."""
        reg = self.client.registry()
        yield reg.cd(["", "Servers", "SR560", "Links"], True)
        dirs, keys = yield reg.dir()
        p = reg.packet()
        for k in keys:
            p.get(k, key=k)
        ans = yield p.send()
        self.serialLinks = {k: ans[k] for k in keys}
        print(self.serialLinks)

    @inlineCallbacks
    def findDevices(self):
        """Find available devices from a list stored in the registry."""
        devs = []
        for name, (server, port) in list(self.serialLinks.items()):
            if server not in self.client.servers:
                continue
            server = self.client[server]
            ports = yield server.list_serial_ports()
            if port not in ports:
                continue
            devName = "{} - {}".format(server, port)
            devs += [(name, (server, port))]
        returnValue(devs)

    @setting(9, "set_input_coupling", coupling="s", returns="s")
    def set_input_coupling(self, c, coupling=None):
        coupling_dict = {"GND": 0, "DC": 1, "AC": 2}
        coupling_number = coupling_dict[coupling]
        dev = self.selectedDevice(c)
        yield dev.write("LISN 3\r\n")
        yield dev.write("CPLG {}\r\n".format(coupling_number))
        returnValue("Input coupling has been set to {}".format(coupling))

    @setting(100, "reset", returns="s")
    def reset(self, c):
        """Recalls default settings."""
        dev = self.selectedDevice(c)
        yield dev.write("LISN 3\r\n")
        yield dev.write("*RST")
        returnValue("Recalls default settings")


__server__ = SR560Server()


if __name__ == "__main__":
    util.runServer(__server__)
