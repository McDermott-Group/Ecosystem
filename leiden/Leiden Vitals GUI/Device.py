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


"""
version = 1.0.1
description = References a device
"""

# Import nGui tools
from NFrame import NFrame
import NPopUp

import labrad

import threading
import sys, traceback

# The device class handles a labrad device

class Device:

	
	def __init__(self, serverName, name, nicknames, settingNames, settingArgs, cxn, 
				buttonNames, buttonSettings, buttonMessages,  buttonArgs, 
				yLabel =None, setDeviceCmd = None, selectedDevice = 0):
		#print("making device")
		# Get all the stuff from the constructor.
		self.cxn = cxn
		self.name = name
		# Nicknames of settings (the ones that show up on th Gui)
		self.nicknames=nicknames			
		# Device's frame
		self.frame = NFrame(self.name, self.nicknames)	
		# The device's labrad server		
		self.serverName = serverName	
		# List of settings that the user wants run on their device
		settings=[]				
		# The actual names of the settings
		self.settingNames = settingNames	
		# Stores the actual reference to the labrad server		
		deviceServer = None	
		# True if device is functioning correctly
		self.isDevice = False			
		# Used for device.select_device(selectedDevice) setting
		self.selectedDevice = selectedDevice	
		# stores the setting to select device (almost always 'select_device')
		self.setDeviceCmd = setDeviceCmd	
		# Stores the buttons along with their parameters
		buttons = [[]]				
		# Arguments that should be passed to settings if necessary
		self.settingArgs = settingArgs		
		
		#print name, ":", yLabel
		self.frame.setYLabel(yLabel)
		#print "Now it is: ", self.frame.getYLabel()
		# Determine which buttons get messages
		if(buttonMessages is not None):
			self.buttonMessages = buttonMessages
		# Setup all buttons
		if(buttonNames is not None):
			self.buttonNames = buttonNames
			self.buttonSettings = buttonSettings
			#print(buttonArgs)
			self.buttons = []
			#print "buttons before:  ", self.buttons
			for i in range(0, len(self.buttonNames)):
				#print(self.name)
				#print()
				#print(i)
				#if(i is not 0):
				self.buttons.append([])
				#print(i)
				#print(len(self.buttons))
				self.buttons[i].append(self.buttonNames[i])
				self.buttons[i].append(self.buttonSettings[i])
				self.buttons[i].append(self.buttonMessages[i])
				self.buttons[i].append(buttonArgs[i])
			self.frame.setButtons(self.buttons)
			
			#print "Device: ", self.name
			
			#print "buttonNames: ", self.buttonNames
			#print "buttons: ", self.frame.getButtons()
		# Connect to the device's server
		self.connect()
		# Each device NEEDS to run on a different thread 
		# than the main thread (which ALWAYS runs the gui)
		# This thread is responsible for querying the devices
		self.deviceThread = threading.Thread(target = self.Query, args=[])
		# If the main thread stops, stop the child thread
		self.deviceThread.daemon = True
		# Start the thread
		self.deviceThread.start()
		
	def connect(self):	
		'''Connect to the device'''
		try:
			# Attempt to connect to the server given the connection 
			# and the server name.
			self.deviceServer = getattr(self.cxn, self.serverName)()
			# If the select device command is not none, run it.
			if(self.setDeviceCmd is not None):
				getattr(self.deviceServer, self.setDeviceCmd)(
					self.selectedDevice)
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
			# if the button has a warning message attatched
			if(self.frame.getButtons()[button][2] is not None):
				# Create a new popup
				self.warning = NPopUp.PopUp(self.frame.getButtons()
					[button][2])
				# Stop the main gui thread and run the popup
				self.warning.exec_()
				# If and only if the 'ok' button is pressed
				if(self.warning.consent):
					# If the setting associated with the button also 
					# has an argument for the setting
					if(self.frame.getButtons()[button][3] is not None):
						getattr(self.deviceServer, self.frame.getButtons()
							[button][1])(self.frame.getButtons()
							[button][4])
					# If just the setting needs to be run
					else:
						getattr(self.deviceServer, self.frame.getButtons()
							[button][1])
			# Otherwise if there is no warning message, do not make a popup
			else:
				# If there is an argument that must be passed to the setting
				if(self.frame.getButtons()[button][3] is not None):
					getattr(self.deviceServer, self.frame.getButtons()
						[button][1])(self.frame.getButtons()[button][4])
				# If not.
				else:
					getattr(self.deviceServer, self.frame.getButtons()
						[button][1])
		except:
			#print("Device not connected.")
			return
	def Query(self):
		'''Ask the device for readings'''
		# If the device is attatched.
		#print("Querying")
		if(not self.isDevice):
			# Try to connect again, if the value changes, then we know 
			# that the device has connected.
			if(self.connect() is not self.isDevice):
				#print("Connected to "+self.name)
				self.isDevice = True
		# Otherwise, if the device is already connected
		else:
			#print("Reading")
			try:
				readings = []	# Stores the readings
				units = []		# Stores the units
				for i in range(0, len(self.settingNames)):
					# If the setting needs to be passed arguments
					if(self.settingArgs[i] is not None):
						reading = getattr(self.deviceServer, self
							.settingNames[i])(self.settingArgs[i])
					else:
						reading = getattr(self.deviceServer, self
							.settingNames[i])()
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
							print("Problem with readings, type '"
								+type(reading)+"' cannot be displayed")
				# Pass the readings and units to the frame
				self.frame.setReadings(readings)
				self.frame.setUnits(units)
				# If there was an error, retract it.
				self.frame.retractError()
			except:
				#exc_type, exc_value, exc_traceback = sys.exc_info()
				#traceback.print_tb(exc_traceback)
				#print("Error")
				self.frame.raiseError("Problem communicating with "
					+self.name)
				self.frame.setReadings(None)
				self.isDevice = False
		# Query calls itself again, this keeps the thread alive.
		threading.Timer(1, self.Query).start()
		return 