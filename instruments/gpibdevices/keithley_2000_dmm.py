# Copyright (C) 2011 Dylan Gorman
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
# along with this program.  If not, see <http://www.gnu.org/licenses/>
  
"""
### BEGIN NODE INFO
[info]
name = Keithley 2000 DMM
version = 1.0
description = 
  
[startup]
cmdline = %PYTHON% %FILE%
timeout = 20
  
[shutdown]
message = 987654321
timeout = 5
### END NODE INFO
"""
  
from labrad.server import setting
from labrad.gpib import GPIBManagedServer
from labrad import units
from twisted.internet.defer import inlineCallbacks, returnValue
import numpy
import math
  
class KeithleyServer(GPIBManagedServer):
    name = 'Keithley 2000 DMM' # Server name
    deviceName = ['KEITHLEY INSTRUMENTS INC. MODEL 2000', 'KEITHLEY INSTRUMENTS INC. MODEL 2100']
    #deviceWrapper = KeithleyWrapper
  
    @setting(11, 'Get DC Volts', returns = 'v[V]')
    def get_dc_volts(self, c):
        """Aquires new value for DC Voltage and returns it."""
        dev = self.selectedDevice(c)
        voltage = yield dev.query('MEAS:VOLT:DC?')
        voltage = float(voltage.split(',')[0].strip('ABCDEFGHIJKLMNOPQRSTUVWXYZ'))
        returnValue(voltage * units.V)
  
    @setting(12, 'Get Resistance', returns = 'v[Ohm]')
    def get_resistance(self, c):
        """Aquires resistance and returns it."""
        dev = self.selectedDevice(c)
        resistance = yield dev.query('MEAS:RES?')
        resistance = float(resistance.split(',')[0].strip('ABCDEFGHIJKLMNOPQRSTUVWXYZ'))
        returnValue(resistance * units.Ohm)
  
    @setting(13, 'Get FW Resistance', returns = 'v[Ohm]')
    def get_fw_resistance(self, c):
        """Aquires resistance using four-wire measurement and returns it."""
        dev = self.selectedDevice(c)
        resistance = yield dev.query('MEAS:FRES?')
        resistance = float(resistance.split(',')[0].strip('ABCDEFGHIJKLMNOPQRSTUVWXYZ'))
        returnValue(resistance * units.Ohm)
        
    @setting(20, 'Get Ruox Temperature', returns=['v[K]'])
    def get_ruox_temperature(self, c):
        """Get the temperatures of the Ruox Thermometer for the ADR fridge.  All RuOx readers of every kind must have this method to work with the ADR control program."""
        reg = self.client.registry
        reg.cd(c['adr settings path'])
        RCal = yield reg.get('RCal')
        dev = self.selectedDevice(c)
        
        V = yield self.get_dc_volts(c)
        R = RCal*1000*V['V']
        try: T = pow((2.85/math.log((R-652)/100)),4)*units.K
        except ValueError: T = numpy.nan*units.K
        returnValue(T)
    
    @setting(21,'Set ADR Settings Path',path=['*s'])
    def set_adr_settings_path(self,c,path):
        c['adr settings path'] = path

    @setting(22, 'Get FW Range', returns = 'v[Ohm]')
    def get_fw_range(self, c):
        """Aquires the DMM's four wire resistance range and returns it."""
        dev = self.selectedDevice(c)
        resistanceRange = yield dev.query('SENS:FRES:RANGe?')
        resistanceRange = float(resistanceRange.split(',')[0].strip('ABCDEFGHIJKLMNOPQRSTUVWXYZ'))
        returnValue(resistanceRange * units.Ohm)

    @setting(23, 'Return To Local', returns = '')
    def return_to_local(self, c):
        """Returns the DMM's front panel to local after interfacing remotely."""
        dev = self.selectedDevice(c)
        resistanceRange = yield dev.write('SYSTem:LOCal')

    @setting(24, 'Return To Remote', returns = '')
    def return_to_remote(self, c):
        """Returns the DMM's front panel to remote."""
        dev = self.selectedDevice(c)
        resistanceRange = yield dev.write('SYSTem:REMote')
  
__server__ = KeithleyServer()
  
if __name__ == '__main__':
    from labrad import util
    util.runServer(__server__)
