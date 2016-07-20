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
version = 1.0.1
description = Monitors temperature of PT1000

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
"""

from twisted.internet.defer import inlineCallbacks, returnValue
import numpy as np

from labrad.devices import DeviceServer, DeviceWrapper
from labrad.server import setting
import labrad.units as units
from labrad import util
import csv

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
        print "Server Initializing"
        self.reg = self.client.registry()
        yield self.loadConfigInfo()
        yield DeviceServer.initServer(self)
    
    def resToTemp(self, R):
        R = R / 10 # Because the curve we use is for the PT100.
        f = open('PT100Table.csv', 'rb')

        reader = csv.reader(f)
        
        curr = [0,0]
        prevRow = [0]
        for i, row in enumerate(reader):
            for y, cell in enumerate(row[1::]):
                prev = curr[:]
                try:
                    curr[0] = float(cell)
                    if(float(prevRow[0])>0):
                        curr[1]=(float(row[0])+y)
                        sign = 1
                    else:
                        curr[1]=(float(row[0])-y)
                        sign = -1
                except:
                    continue
                if(float(prev[0]*sign)<=R*sign<float(curr[0]*sign)):
                    fac = (curr[0]-R)/(curr[0]-prev[0])
                    return curr[1]*(1-fac)+prev[1]*fac
            prevRow = row    
        return np.nan

    @setting(100, 'Get Temperatures', returns = '*?')
    def getTemperatures(self, ctx):
        readings = []
        self.dev = self.selectedDevice(ctx)
        for i in range(2):
            yield self.dev.write_line(str(i+1))
            yield sleep(0.1)
            reading = yield self.dev.read_line()
            reading = reading.strip()
            if(reading == "OL"):
                readings.append(np.nan)
            elif len(reading) is 0:
                readings.append(np.nan)
            else:
                readings.append(self.resToTemp(float(reading))+273.15)
        
        readings = readings*units.K
        returnValue(readings)
            
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
        yield reg.cd(['', 'Servers','PT1000TemperatureMonitor', 'Links'], True)
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