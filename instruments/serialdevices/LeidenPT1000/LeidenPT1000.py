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
name = Goldstein's PT1000 Temperature Monitor
version = 1.2.0
description = Monitors temperature of PT1000

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
"""

import os
import traceback
import numpy as np
from twisted.internet.defer import inlineCallbacks, returnValue

from labrad.devices import DeviceServer, DeviceWrapper
from labrad.server import setting
import labrad.units as units
from labrad import util

from utilities import sleep


class goldsteinsPT1000TemperatureMonitorWrapper(DeviceWrapper):
    @inlineCallbacks
    def connect(self, server, port):
        print('Connecting to {0} on port {1}...'.format(server.name, port))
        self.server = server
        self.ctx = server.context()
        self.port = port
        p = self.packet()
        p.open(port)
        p.baudrate(9600L)
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
    deviceName = "Goldstein's PT1000 Temperature Monitor"
    name = "Goldstein's PT1000 Temperature Monitor"
    deviceWrapper = goldsteinsPT1000TemperatureMonitorWrapper
    
    @inlineCallbacks
    def initServer(self): 
        self.reg = self.client.registry()
        yield self.loadConfigInfo()
        yield DeviceServer.initServer(self)

    @setting(100, 'Get Resistances', returns='*v[Ohm]')
    def getResistances(self, ctx):
        readings = []
        self.dev = self.selectedDevice(ctx)

        for i in range(2):
            yield self.dev.write_line(str(i+1))
            yield sleep(0.2)
            reading = yield self.dev.read_line()
           
            readings.append(reading)
            readings[i] = reading.strip()
            if(reading == "OL\r\n"):
                readings[i] = np.nan
            elif len(reading) is 0:
                readings[i] = np.nan
            else:
                readings[i] = reading.strip()
        try:
            readings = [float(readings[0]) * units.Ohm,
                        float(readings[1]) * units.Ohm]
        except:
            traceback.print_exc()
        returnValue(readings)
        
    def _pt1000_res2temp(self, resistance):
        R = resistance['Ohm']
        
        # PT1000 room temperature resistance.
        R0 = 1000 # Ohm
        
        # ITS-90 calibration coefficients.
        A = 3.9083e-3
        B = -5.7750e-7

        temp = -R0 * A + np.sqrt((R0 * A)**2 - 4 * R0 * B * (R0 - R))
        temp /= 2 * R0 * B
        temp += 273.15 # K
        
        # Extra correction.
        p1 = 6.0933e-17
        p2 = -3.2865e-13
        p3 = 6.8074e-10
        p4 = -6.8275e-07
        p5 = 0.00033726
        p6 = -0.070257
        p7 = 2.7358
        temp -= (p1 * R**6 + p2 * R**5 + p3 * R**4 + p4 * R**3 +
                 p5 * R**2 + p6 * R + p7)
        return temp
    
    @setting(110, 'Get Temperatures', returns='*v[K]')
    def getTemperatures(self, ctx):
        resistances = yield self.getResistances(ctx)
        readings = [self._pt1000_res2temp(resistances[0]) * units.K,
                    self._pt1000_res2temp(resistances[1]) * units.K]
        returnValue(readings)

    @setting(200, 'Get Device Info', returns='s')
    def getInfo(self, ctx):
        self.dev = self.selectedDevice(ctx)
        yield self.dev.write_line('?')
        yield sleep(0.05)
        reading = yield self.dev.read_line()
    
        returnValue(reading)
    
    @inlineCallbacks
    def loadConfigInfo(self):
        reg = self.reg
        yield reg.cd(['', 'Servers','PT1000TemperatureMonitor',
                'Links'], True)
        dirs, keys = yield reg.dir()
        p = reg.packet()
        for k in keys:
            p.get(k, key = k)
        ans = yield p.send()
        self.serialLinks = dict((k, ans[k]) for k in keys)
    
    @inlineCallbacks
    def findDevices(self):
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

        
__server__ = goldsteinsPT1000TemperatureMonitorServer()


if __name__=='__main__':
    util.runServer(__server__)