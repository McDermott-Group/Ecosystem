# Copyright (C) 2016 Noah Meltzer
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
### BEGIN NODE INFO
[info]
name = Lakeshore RuOx
version = 2.6.1
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

			
class LakeshoreRuOxServer(GPIBManagedServer):
	name = 'Lakeshore RuOx'
	deviceName = 'LSCI MODEL370'
	#deviceWrapper = RuOxWrapper


	@setting(10, 'Temperatures', returns='v[K]')
	def temperatures(self, c):
		"""Read channel temperatures.
		Returns a ValueList of the channel temperatures in Kelvin.
		"""
		dev = self.selectedDevice(c)
		temps = yield dev.query("RDGK?")
		temps = float(temps)*units.K
		returnValue(temps)
	
	
__server__ = LakeshoreRuOxServer()

if __name__ == '__main__':
	from labrad import util
	util.runServer(__server__)
