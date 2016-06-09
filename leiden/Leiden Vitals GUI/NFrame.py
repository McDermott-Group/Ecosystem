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
name = NFrame class
version = 1.0.1
description = Organizes information returned by servers

### END NODE INFO
"""

class NFrame:
	serverTitle = None
	nicknames = None
	serverSettings = None
	serverUnits = None
	readings = None
	error = False
	errmsg = None
	units = []
	buttons = [[]]
	buttonInd = None
	buttonPushed = False
	def __init__(self, title, nicknames):
		self.serverTitle = title
		self.nicknames = nicknames
	def setTitle(self, title):
		self.serverTitle = title
	def getTitle(self):
		return self.serverTitle
	def getNicknames(self):
		return self.nicknames
	def setReadings(self, readings):
		self.readings = readings
	def getReadings(self):
		return self.readings
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
		