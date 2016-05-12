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
import NPopUp
import sys, traceback
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
	buttonNames = []
	buttonSettings = []
	buttonMessages = []
	buttons = [[]]
	cxn = None
	def __init__(self, serverName, name, nicknames, settingNames, cxn, buttonNames, buttonSettings, buttonMessages,  setDeviceCmd = None, selectedDevice = 0):
		print("making device")
		self.name = name
		self.nicknames = nicknames
	
		self.frame = NFrame(self.name, self.nicknames)
		self.cxn = cxn
		self.serverName = serverName
		self.settingNames = settingNames
		self.setDeviceCmd = setDeviceCmd
		self.selectedDevice = selectedDevice
		
		if(buttonMessages is not None):
			self.buttonMessages = buttonMessages
		if(buttonNames is not None):
			self.buttonNames = buttonNames
			self.buttonSettings = buttonSettings
			
			for i in range(0, len(self.buttonNames)):
				if(i is not 0):
					self.buttons.append([])
				self.buttons[i].append(self.buttonNames[i])
				self.buttons[i].append(self.buttonSettings[i])
				self.buttons[i].append(self.buttonMessages[i])
				
			self.frame.setButtons(self.buttons)
			
		self.connect()
		self.Query()
		
		self.deviceThread = threading.Thread(target = self.Query, args=[])
		self.deviceThread.daemon = True
		self.deviceThread.start()
		

	def connect(self):			
		try:
			
			#print("attempting connection to "+str(self.isDevice))
			#print(self.serverName)
			self.deviceServer = getattr(self.cxn, self.serverName)()
			if(self.setDeviceCmd is not None):
				getattr(self.deviceServer, self.setDeviceCmd)(self.selectedDevice)
			print(self.settingNames)
			return True
		except:
			self.frame.raiseError("")
			#print("Could not connect to "+self.name)
			return False
		#print(self.deviceServer.pressure())
		
	def getFrame(self):
		return self.frame
	def prompt(self, button):
		try:
			print("Device: "+self.name+", Button: "+self.frame.getButtons()[button][0])
			if(self.frame.getButtons()[button][2] is not None):
				self.warning = NPopUp.PopUp(self.frame.getButtons()[button][2])
				self.warning.exec_()
				if(self.warning.consent):
					getattr(self.deviceServer, self.frame.getButtons()[button][1])
			else:
				getattr(self.deviceServer, self.frame.getButtons()[button][1])
		except:
			print("Device not connected.")
			return
	def Query(self):
		#print("Querying")
		if(not self.isDevice):
			if(self.connect() is not self.isDevice):
				print("Connected to "+self.name)
				self.isDevice = True
		else:
			#try:
			readings = []
			units = []
			for i in range(0, len(self.settingNames)):
				#print("HERE A")
				reading = getattr(self.deviceServer, self.settingNames[i])()
				#print(reading)
				#print(type(reading))
				if isinstance(reading, labrad.units.Value):
					#print("HERE B")
					readings.append(reading._value)
					units.append(reading.units)
				elif(isinstance(reading, labrad.units.ValueArray)):
					#print("HERE C")
					for i in range(0, len(reading)):
						if isinstance(reading[i], labrad.units.Value):
							readings.append(reading[i]._value)
							units.append(reading[i].units)
							
						else:
							readings.append(reading[i]._value)
							units.append("")
							
				else:
					#print("HERE D")
					readings.append(reading[i])
					units.append("")
			#print("HERE E")
			self.frame.setReadings(readings)
			self.frame.setUnits(units)
			#print(units)
			#print(readings)
			self.frame.retractError()
				#print(readings)
			# except:
				# exc_type, exc_value, exc_traceback = sys.exc_info()
				# traceback.print_tb(exc_traceback)
				# self.frame.raiseError("Problem communicating with "+self.name)
				# self.isDevice = False
		if(any((i.name == "MainThread") and i.is_alive() for i in threading.enumerate())):
			threading.Timer(2, self.Query).start()
			#print("problem communicating with "+self.name)
		return 