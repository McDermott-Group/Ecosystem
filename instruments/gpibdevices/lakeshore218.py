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
### BEGIN NODE INFO
[info]
name =  LakeShore 218
version = 1.0.1
description =

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
"""

from datetime import datetime
import math

from twisted.python import log
from twisted.internet.defer import inlineCallbacks, returnValue

from labrad import types as T, util, units as U
from labrad.server import setting
from labrad.gpib import GPIBManagedServer, GPIBDeviceWrapper
import labrad.units as units
import numpy as np

#class LakeShore218Wrapper(GPIBDeviceWrapper):
	
class Lakeshore218Server(GPIBManagedServer):
	name = 'LakeShore 218'
	deviceName = 'LSCI MODEL218S'
	#deviceWrapper = LakeShore218Wrapper
	@setting(10, 'Get Instrument Name', returns='s')
	def getInstrumentName(self, c):
		"""Return the instrument name."""
		dev = self.selectedDevice(c)
		instrumentName = yield dev.query('*IDN?')
		print "getting name"
		returnValue(instrumentName)
	# @inlineCallbacks
	# def getTemperature(self, c, input):
		# # To get just one temperature, enter a number 1-8, to get all, enter 0.
		# print "selecting device"
		# dev = self.selectedDevice(c)
		# print "querying device"
		# result = yield dev.query('CRDG? 1')
		# print "Got result"
		# print result
		# returnValue(result)
		  
	# def configureAllForDT670(self):
		# '''Configure all inputs for DT-670'''
		# for i in range(1, 9):
			# result = yield self.query('INCRV '+str(i)+'6')
		# returnValue(True)
		  
	@setting(100, 'get_single_temperature', input = 'i', returns = 'v[degC]')
	def getSingleTemperature(self, c, input):
		'''Get the temperature for a specific input'''
		dev = self.selectedDevice(c)
		result = yield dev.query('CRDG? '+str(input))
		result = result.split()
		result = float(result[0])
		result = result *units.degC
		returnValue(result)

	@setting(200, 'get_all_temperatures', returns = '*v[degC]')
	def getAllTemperatures(self, c):
		'''Get the temperature for a specific input'''
		dev = self.selectedDevice(c)
		results = []
		for i in range(1, 8):
		
			result = yield dev.query('CRDG? '+str(i))
			result = result.split()
			result = float(result[0])
			result = result * units.degC
			results.append(result)
		returnValue(results)

	# @setting(300, 'configure_for_DT670', returns = 'b')
	# def configureForDT670(self, c):
		# '''Configure all inputs for DT670'''
		# dev = self.selectedDevice(c)
		# result = yield dev.configureAllForDT670()
		# returnValue(result)
		
		
__server__ = Lakeshore218Server()

if __name__ == '__main__':
    from labrad import util
    util.runServer(__server__)

