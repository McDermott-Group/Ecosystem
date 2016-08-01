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
name = MKS PDR2000
version = 1.0.15
description = Monitors vacuum system

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
"""
import time
from labrad.devices import DeviceServer, DeviceWrapper
from labrad.server import setting
import labrad.units as units
from labrad import util
import numpy as np
from twisted.internet.defer import inlineCallbacks, returnValue

class MKSPDR2000Wrapper(DeviceWrapper):
	@inlineCallbacks
	def connect(self, server, port):
		'''Connect to the MKS PDR2000'''
		print('Connecting to "%s" on port "%s"...' %(server.name, port))

		self.server = server
		self.ctx = server.context()
		self.port = port
		p = self.packet()
		p.open(port)
		# The following parameters were obtained from the MKS PDR2000 manual.
		p.baudrate(9600L)
		p.stopbits(1L)
		p.bytesize(8L)
		p.parity('N')
		p.timeout(0.1 * units.s)
		# Clear out the Rx buffer. This is necessary for some devices.
		yield p.send()
	
	def packet(self):
		'''Create a new packet in our private context'''
		return self.server.packet(context=self.ctx)

	def shutdown(self):
		'''Disconnect from teh serial port when we shut down.'''
		return self.packet().close().send()

	@inlineCallbacks
	def write_line(self, code):
		'''Write data to the device.'''
		yield self.server.write_line(code, context=self.ctx)
	@inlineCallbacks
	def read_line(self):
		'''Read a data value from the device.'''
		ans = yield self.server.read(context=self.ctx)
		returnValue(ans)
	@inlineCallbacks
	def getUnits(self):
		yield self.write_line('u')
		time.sleep(0.5)
		ans = yield self.read_line()
		returnValue(ans)


class MKSPDR2000Server(DeviceServer):
	deviceName = 'MKS PDR2000 Server'
	name = 'MKS PDR2000 Server'
	deviceWrapper = MKSPDR2000Wrapper
	 
	@inlineCallbacks
	def initServer(self):
		'''Initialize the MKSPDR2000 server.'''
		print "Server Initializing"
		self.reg = self.client.registry()
		yield self.loadConfigInfo()
		yield DeviceServer.initServer(self)
		  
	@setting(100, 'get_pressure', returns='*v[torr]')
	def getPressure(self, ctx):
		print "setting dev"
		self.dev = self.selectedDevice(ctx)
		print "writing"
		yield self.dev.write_line("p")
		print "sleeping"
		time.sleep(1)
		print "getting reading"
		reading = yield self.dev.read_line()
		print reading
		print "getting units"
		yield self.dev.write_line('u')
		print "sleeping"
		time.sleep(1)
		print "reading units"
		unit = yield self.dev.read_line()
		unit = unit.strip()
		print unit
		print reading
		# Just in case there is an error and nothing is returned 
        # (RS232 is finicky).
		if not reading:
			returnValue(None)
		else:
			# Get last number in string.
			reading = reading.split(" ")
			reading[0]=reading[0].strip()
			reading[1]=reading[1].strip()
			#print reading
			if reading [0] == 'Off':
				#print ("0 is off")
				reading [0] = np.nan
			if reading [1] == 'Off':
				#print ("1 is off")
				reading [1] = np.nan
			#print reading
			if unit == 'Torr':
				#print "units of torr"
				reading[0] = float(reading[0]) 
				#print reading [0]
				reading[1] = float(reading[1])
				#print reading [1]
			elif unit == 'mTorr':
				reading[0] = (float(reading[0])/1000) 
				reading[1] = (float(reading[1])/1000) 
			reading = reading * units.torr
			#print type(reading[1])
			#print reading[1] is "Off"
		print reading
			#print "done"
			# Add correct units.
		returnValue(reading)
		
	@inlineCallbacks
	def loadConfigInfo(self):
		"""Load configuration information from the registry."""
		reg = self.reg
		yield reg.cd(['', 'Servers', 'MKSPDR2000',
				'Links'], True)
		dirs, keys = yield reg.dir()
		p = reg.packet()
		for k in keys:
			p.get(k, key=k)
		ans = yield p.send()
		self.serialLinks = dict((k, ans[k]) for k in keys)

	@inlineCallbacks       
	def findDevices(self):
		"""Find available devices from list stored in the registry."""
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


__server__ = MKSPDR2000Server()


if __name__ == '__main__':
	from labrad import util
	util.runServer(__server__)