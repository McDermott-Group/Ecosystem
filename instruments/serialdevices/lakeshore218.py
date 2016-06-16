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
name =  Lakeshore 218 GPIB Server
version = 1.0.1
description = Lakeshore 218 GPIB Labrad interface 

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
"""

from labrad.server import setting
from labrad.gpib import GPIBManagedServer, GPIBDeviceWrapper
import labrad.units as units
from labrad import util

class LakeShore218Wrapper(GPIBDeviceWrapper):
     @inlineCallbacks
     
     def getTemperature(self, input):
          # To get just one temperature, enter a number 1-8, to get all, enter 0.
          result = yield self.query('CRDG? '+str(input))
          returnValue(result*units.degC)
          
     def configureAllForDT670(self):
          '''Configure all inputs for DT-670'''
          for i in range(1, 9):
               result = yield self.query('INCRV '+str(i)+'6')
          returnValue(True)
          
class LakeShore218Wrapper(GPIBManagedServer):
     name = 'LakeShore218'
     deviceName = "LAKESHORE 218"
     deviceWrapper = LakeShore218Wrapper
    
     @setting(100, 'get_single_temperature', input = 'i', returns = 'v[degC]')
     def getSingleTemperature(self, c, input):
          '''Get the temperature for a specific input'''
          dev = self.selectedDevice(c)
          result = yield dev.getTemperatre(input) 
          returnValue(result)
          
     @setting(200, 'get_all_temperatures', returns = '*v[degC]')
     def getAllTemperatures(self, c):
          '''Get the temperature for a specific input'''
          dev = self.selectedDevice(c)
          # You can enter 0 and get all temperatures as a string, this
          # server splits everyting into a labrad valueArray
          result = yield dev.getTemperature(0)
          result.split(',')
          result = result * units.degC
          returnValue(result)
          
     @setting(300, 'configure_for_DT670', returns = 'b')
     def configureForDT670(self, c):
          '''Configure all inputs for DT670'''
          dev = self.selectedDevice(c)
          result = yield dev.configureAllForDT670()
          returnValue(result)

		