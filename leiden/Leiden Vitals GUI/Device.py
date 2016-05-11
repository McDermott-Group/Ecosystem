# Copyright (C) 2016 Noah Meltzer
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

# Utilities libraries.


"""
### BEGIN NODE INFO
[info]
name = Device class
version = 1.0.1
description = References a device

### END NODE INFO
"""
from NFrame import NFrame
from PyQt4 import QtCore, QtGui
import labrad
import threading
class Device:
	name = None
	frame = None
	serverName = None
	settings=[]
	nicknames=[]
	settingNames = []
	deviceServer = None
	isDevice = False
	selectedDevice = None
	setDeviceCmd = None
	cxn = None
	def __init__(self, serverName, name, nicknames, settingNames, cxn, setDeviceCmd = None, selectedDevice = 0):
		print("making device")
		self.name = name
		self.nicknames = nicknames
	
		self.frame = NFrame(self.name, self.nicknames)
		self.cxn = cxn
		self.serverName = serverName
		self.settingNames = settingNames
		self.setDeviceCmd = setDeviceCmd
		self.selectedDevice = selectedDevice
		self.connect()
		self.Query()
		
		self.deviceThread = threading.Thread(target = self.Query, args=[])
		self.deviceThread.start()
		

	def connect(self):
		try:
			
			print("attempting connection "+str(self.isDevice))
			self.deviceServer = getattr(self.cxn, self.serverName)()
			if(self.setDeviceCmd is not None):
				getattr(self.deviceServer, self.setDeviceCmd)(0)
			print(self.settingNames)
			return True
		except:
			self.frame.raiseError("Could Not connect to "+self.name)
			print("Could not connect to "+self.name)
			return False
		#print(self.deviceServer.pressure())
		
	def getFrame(self):
		return self.frame
		
	def Query(self):
		if(not self.isDevice):
			if(self.connect() is not self.isDevice):
				print("Connected to "+self.name)
				self.isDevice = True
		else:
			try:
				#print("getting readings of " + self.name)
				readings = []
				units = []
				for i in range(0, len(self.settingNames)):
					reading = getattr(self.deviceServer, self.settingNames[i])()
					if isinstance(reading, labrad.units.Value):
						readings.append(reading._value)
						units.append(reading.units)
					else:
						readings.append(reading)
						units.append("")
				self.frame.setReadings(readings)
				self.frame.setUnits(units)
				#print(units)
				threading.Timer(2, self.Query).start()
				self.frame.retractError()
				#print(readings)
			except:
				self.frame.raiseError("Problem communicating with "+self.name)
				self.isDevice = False
				
			#print("problem communicating with "+self.name)
		return 