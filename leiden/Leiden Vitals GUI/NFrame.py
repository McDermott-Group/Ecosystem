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
version = 1.5.1
description = Organizes information returned by servers
"""

class NFrame:
	'''This class acts as the interface between the devices and all classes
	which use the device or any of its parameters'''
	# Name of device's server
	serverTitle = None
	# Parameter names to be displayed on GUI
	nicknames = None
	# Settings which are called by the GUI
	serverSettings = None
	# Device readings
	readings = None
	# Errors
	error = False
	# Error messages
	errmsg = None
	# Label on the y axis of the datachest dataplot
	yLabel = ""
	# Units used for each parameter
	units = []
	# Buttons on the GUI used to control the device
	buttons = [[]]
	# Stores an index of a certain button
	buttonInd = None
	# Is a specified button pushed
	buttonPushed = False
	# Store the plots
	plot = False
	# Just in case the user wants to label their NGui plot with
	# custom units (note these are only the units displayed onscreen,
	# not the units that the data is logged with)
	custUnits = ''
	
	def __init__(self):
		print("New Frame")
	def setTitle(self, title):
		self.serverTitle = title
	def getTitle(self):
		return self.serverTitle
	def getNicknames(self):
		return self.nicknames
	def setNicknames(self, nicknames):
		self.nicknames = nicknames
	def setReadings(self, readings):
		self.readings = readings
	def getReadings(self):
		return self.readings
	def setReadingIndices(self, index):
		self.readingIndices = index
	def getReadingIndices(self):
		return self.readingIndices
	def raiseError(self, msg):
		self.error = True
		self.errmsg = msg
	def retractError(self):
		self.error = False
		self.errmsg = None
	def isError(self):
		return self.error
	def errorMsg(self):
		return self.errmsg
	def setUnits(self, units):
		self.units = units
	def getUnits(self):
		return self.units
	def getCustomUnits(self):
		return self.custUnits
	def getButtons(self):
		return self.buttons
	def setButtons(self, buttons):
		self.buttons = buttons
	def buttonPressed(self, buttonInd):
		self.buttonInd = buttonInd
		self.buttonPushed = True
	def getButtonPressed(self):
		self.buttonPushed = False
		return self.buttonInd
	def isButtonPressed(self):
		return self.buttonPushed
	def setYLabel(self, y, custUnits=''):
		self.custUnits = custUnits
		self.yLabel = y
	def getYLabel(self):
		return self.yLabel
	def addPlot(self):
		self.plot=True
	def getPlot(self):
		return self.plot