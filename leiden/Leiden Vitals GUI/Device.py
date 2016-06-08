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
# Import nGui tools
from NFrame import NFrame
import NPopUp

import labrad

import threading
import sys, traceback

# The device class handles a labrad device

class Device:
	name = None				# Name of device
	frame = None 			# Device's frame
	serverName = None		# The device's labrad server
	settings=[]				# List of settings that the user wants run on their device
	nicknames=[]			# Nicknames of settings (the ones that show up on th Gui)
	settingNames = []		# The actual names of the settings
	deviceServer = None	# Stores the actual reference to the labrad server
	isDevice = False			# True if device is functioning correctly
	selectedDevice = None	# Used for device.select_device(selectedDevice) setting
	setDeviceCmd = None	# stores the setting to select device (almost always 'select_device')
	buttonNames = []		# List that stores the names of buttons
	buttonSettings = []		# Names of the settings that each button triggers
	buttonMessages = []		# If a popup alert message is specified, it is stored here
	buttons = [[]]				# Stores the buttons along with their parameters
	settingArgs = []			# Arguments that should be passed to settings if necessary
	
	cxn = None
	def __init__(self, serverName, name, nicknames, settingNames, settingArgs, cxn, buttonNames, buttonSettings, buttonMessages,  buttonArgs, setDeviceCmd = None, selectedDevice = 0):
		#print("making device")
		# Get all the stuff from the constructor.
		self.name = name
		self.nicknames = nicknames
		self.frame = NFrame(self.name, self.nicknames)
		self.cxn = cxn
		self.serverName = serverName
		self.settingNames = settingNames
		self.setDeviceCmd = setDeviceCmd
		self.selectedDevice = selectedDevice
		self.settingArgs = settingArgs
		
		# Determine which buttons get messages
		if(buttonMessages is not None):
			self.buttonMessages = buttonMessages
		# Setup all buttons
		if(buttonNames is not None):
			self.buttonNames = buttonNames
			self.buttonSettings = buttonSettings
			#print(buttonArgs)
			for i in range(0, len(self.buttonNames)):
				#print(self.name)
				#print()
				#print(i)
				if(i is not 0):
					self.buttons.append([])
				self.buttons[i].append(self.buttonNames[i])
				self.buttons[i].append(self.buttonSettings[i])
				self.buttons[i].append(self.buttonMessages[i])
				self.buttons[i].append(buttonArgs[i])
			self.frame.setButtons(self.buttons)
		# Connect to the device's server
		self.connect()
		# Each device NEEDS to run on a different thread than the main thread (which ALWAYS runs the gui)
		# This thread is responsible for querying the devices
		self.deviceThread = threading.Thread(target = self.Query, args=[])
		# If the main thread stops, stop the child thread
		self.deviceThread.daemon = True
		# Start the thread
		self.deviceThread.start()
		

	def connect(self):	
		'''Connect to the device'''
		try:
			# Attempt to connect to the server given the connection and the server name.
			self.deviceServer = getattr(self.cxn, self.serverName)()
			# If the select device command is not none, run it.
			if(self.setDeviceCmd is not None):
				getattr(self.deviceServer, self.setDeviceCmd)(self.selectedDevice)
			# True means successfully connected
			return True
		except:
			# The nFrame class can pass an error along with a message
			self.frame.raiseError("")
			return False
		
	def getFrame(self):
		'''Return the device's frame'''
		return self.frame
		
	def prompt(self, button):
		'''If a button is clicked, handle it.'''
		try:
			#print("Device: "+self.name+", Button: "+self.frame.getButtons()[button][0])
			# if the button has a warning message attatched
			if(self.frame.getButtons()[button][2] is not None):
				# Create a new popup
				self.warning = NPopUp.PopUp(self.frame.getButtons()[button][2])
				# Stop the main gui thread and run the popup
				self.warning.exec_()
				# If and only if the 'ok' button is pressed
				if(self.warning.consent):
					# If the setting associated with the button also has an argument for the setting
					if(self.frame.getButtons()[button][3] is not None):
						getattr(self.deviceServer, self.frame.getButtons()[button][1])(self.frame.getButtons()[button][4])
					# If just the setting needs to be run
					else:
						getattr(self.deviceServer, self.frame.getButtons()[button][1])
			# Otherwise if there is no warning message, do not make a popup
			else:
				# If there is an argument that must be passed to the setting
				if(self.frame.getButtons()[button][3] is not None):
					getattr(self.deviceServer, self.frame.getButtons()[button][1])(self.frame.getButtons()[button][4])
				# If not.
				else:
					getattr(self.deviceServer, self.frame.getButtons()[button][1])
		except:
			#print("Device not connected.")
			return
	def Query(self):
		'''Ask the device for readings'''
		# If the device is attatched.
		if(not self.isDevice):
			# Try to connect again, if the value changes, then we know that the device has connected.
			if(self.connect() is not self.isDevice):
				#print("Connected to "+self.name)
				self.isDevice = True
		# Otherwise, if the device is already connected
		else:
			try:
				readings = []	# Stores the readings
				units = []		# Stores the units
				for i in range(0, len(self.settingNames)):
					# If the setting needs to be passed arguments
					if(self.settingArgs[i] is not None):
						reading = getattr(self.deviceServer, self.settingNames[i])(self.settingArgs[i])
					else:
						reading = getattr(self.deviceServer, self.settingNames[i])()
					# If the reading has a value and units
					if isinstance(reading, labrad.units.Value):
						readings.append(reading._value)
						units.append(reading.units)
					# If the reading is an array of values and units
					elif(isinstance(reading, labrad.units.ValueArray)):
						# loop through the array
						for i in range(0, len(reading)):
							if isinstance(reading[i], labrad.units.Value):
								readings.append(reading[i]._value)
								units.append(reading[i].units)
								
							else:
								readings.append(reading[i])
								units.append("")
					elif(type(reading) is list):
						for i in range(0, len(reading)):
							readings.append(reading[i])
							units.append("")
					else:
						try:
							readings.append(reading)
							units.append("")
						except:
							print("Problem with readings, type/n"+type(reading)+"\ncannot be displayed")
				# Pass the readings and units to the frame
				self.frame.setReadings(readings)
				self.frame.setUnits(units)
				# If there was an error, retract it.
				self.frame.retractError()
			except:
				#exc_type, exc_value, exc_traceback = sys.exc_info()
				#traceback.print_tb(exc_traceback)
				self.frame.raiseError("Problem communicating with "+self.name)
				self.frame.setReadings(None)
				self.isDevice = False
		# Query calls itself again, this keeps the thread alive.
		threading.Timer(1, self.Query).start()
		return 