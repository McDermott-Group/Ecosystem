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
name = Goldstein's Laser Endpoint Monitor
version = 1.0.1
description = Laser endpoint monitor

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
import numpy as np
from twisted.internet.defer import inlineCallbacks, returnValue

from labrad.devices import DeviceServer, DeviceWrapper
from labrad.server import setting
import labrad.units as units
from labrad import util
import csv

if __file__ in [f for f in os.listdir('.') if os.path.isfile(f)]:
    SCRIPT_PATH = os.path.dirname(os.getcwd())
else:
    SCRIPT_PATH = os.path.dirname(__file__)
LOCAL_PATH = SCRIPT_PATH.rsplit('instruments', 1)[0]
INSTRUMENTS_PATH = os.path.join(LOCAL_PATH, 'instruments')
if INSTRUMENTS_PATH not in sys.path:
    sys.path.append(INSTRUMENTS_PATH)

from utilities.sleep import sleep


class goldsteinsLaserEndpointMonitorWrapper(DeviceWrapper):
    @inlineCallbacks
    def connect(self, server, port):
        print(('Connecting to {0} on port {1}...'.format(server.name, port)))
        self.server = server
        self.ctx = server.context()
        self.port = port
        p = self.packet()
        p.open(port)
        p.baudrate(9600)
        p.timeout(1*units.s)
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
        ans = yield self.server.read(context=self.ctx)
        returnValue(ans)


class goldsteinsPT1000TemperatureMonitorServer(DeviceServer):
    deviceName = "Goldstein's Laser Endpoint Monitor"
    name = "Goldstein's Laser Endpoint Monitor"
    deviceWrapper =  goldsteinsLaserEndpointMonitorWrapper
    
    @inlineCallbacks
    def initServer(self):
        print("Server Initializing")
        self.reg = self.client.registry()
        yield self.loadConfigInfo()
        yield DeviceServer.initServer(self)

    @setting(100, 'Get Reading', returns = '?')
    def getReading(self, ctx):
        self.dev = self.selectedDevice(ctx)
        yield self.dev.write_line("1")
        yield sleep(0.1)
        reading = yield self.dev.read_line()
        reading = reading.strip()
        reading = float(reading)
        reading = reading*units.V
        returnValue(reading)
            
    @setting(200, 'Get Device Info', returns = 's')
    def getInfo(self, ctx):
        self.dev = self.selectedDevice(ctx)
        yield self.dev.write_line('?')
        yield sleep(0.05)
        reading = yield self.dev.read_line()
    
        returnValue(reading)
    
    @inlineCallbacks
    def loadConfigInfo(self):
        reg = self.reg
        yield reg.cd(['', 'Servers','LaserEndpointMonitor', 'Links'], True)
        dirs, keys = yield reg.dir()
        p = reg.packet()
        for k in keys:
            p.get(k, key = k)
        ans = yield p.send()
        self.serialLinks = dict((k, ans[k]) for k in keys)
    
    @inlineCallbacks
    def findDevices(self):
        devs = []
        for name, (server, port) in list(self.serialLinks.items()):
            if server not in self.client.servers:
                continue
            server = self.client[server]
            ports = yield server.list_serial_ports()
            if port not in ports:
                continue
            devName = '{} - {}'.format(server, port)
            devs += [(name, (server, port))]
        returnValue(devs)
        
__server__ = goldsteinsPT1000TemperatureMonitorServer()

if __name__=='__main__':
    util.runServer(__server__)