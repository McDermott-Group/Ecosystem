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
name = PT1000 Thermometer
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
import time
from twisted.internet.defer import inlineCallbacks, returnValue

from labrad.devices import DeviceServer, DeviceWrapper
from labrad.server import setting
import labrad.units as units
from labrad import util

class goldsteinsPT1000TemperatureMonitorWrapper(DeviceWrapper):
	@inlineCallbacks
	def connect(self, server, port):
		print('Connecting to {0} on port {1} ...'.format(server.name, port))
		self.server = server
		self.ctx = server.context()
		self.port = port
		p = self.packet()
		p.open(port)
		p.baudrate(9600L)
		p.timeout(0.1*units.s)
		p.read_line()
		yield p.send()
		
	def packet(self):
		return self.server.packet(context = self.ctx)
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
	deviceName = "Goldstein's PT1000 Temperature Monitor Server"
	name = "Goldstein's PT1000 Temperature Monitor Server"
	deviceWrapper = goldsteinsPT1000TemperatureMonitorWrapper
	
	@inlineCallbacks
	def initServer(self):
		print "Server Initializing"
		self.reg = self.client.registry()
		yield self.loadConfigInfo()
		yield DeviceServer.initServer(self)
	@setting(100, 'Get Temperature', returns = '?')
	def getTemperature(self, ctx):
		self.dev = self.selectedDevice(ctx)
		yield self.dev.write_line('1')
		yield time.sleep(1)
		reading = yield self.dev.read_line()
		print "reading1: ", reading
		time.sleep(2)
		if not reading:
			returnValue(None)
		else:
			print("HERE1")
			reading*units.K
			print("HERE2")
			returnValue(reading)
			
	@setting(200, 'Get Device Info', returns = 's')
	def getInfo(self, ctx):
		self.dev = self.selectedDevice(ctx)
		yield self.dev.write_line('?')
		yield time.sleep(1)
		reading = yield self.dev.read_line()
		if not reading:
			returnValue(None)
		else:
			reading*units.K
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