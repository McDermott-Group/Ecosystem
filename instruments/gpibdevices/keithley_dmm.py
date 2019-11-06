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
name = Keithley DMM
version = 1.0.0
description = 
  
[startup]
cmdline = %PYTHON% %FILE%
timeout = 20
  
[shutdown]
message = 987654321
timeout = 5
### END NODE INFO
"""

import math
import numpy
from twisted.internet.defer import inlineCallbacks, returnValue

from labrad.server import setting
from labrad.gpib import GPIBManagedServer
from labrad import units


class KeithleyServer(GPIBManagedServer):
    name = 'Keithley DMM' # Server name
    deviceName = ['KEITHLEY INSTRUMENTS INC. MODEL 2000', 'KEITHLEY INSTRUMENTS INC. MODEL 2100']
    #deviceWrapper = KeithleyWrapper
    @setting(99, 'set_fw_range', input_range='v[Ohm]')
    def set_fw_range(self, c, input_range):
        """Aquires the DMM's four wire resistance range and returns it."""
        dev = self.selectedDevice(c)
        resistance_range = yield dev.write('CONF:FRES '+str(input_range['Ohm']))
    
    @setting(83, 'set_frequency_input_range_and_resolution', input_range='v[V]')
    def set_frequency_input_range_and_resolution(self, c, input_range=100e-3 * units.V):
        """Sets the voltage input range and digits of precision
           for a frequency measurement."""
        dev = self.selectedDevice(c)
        yield dev.write('CONF:FREQ '+ str(input_range['V']) + ",MAX")
        
    @setting(84, 'get_frequency', returns = 'v[Hz]')
    def get_frequency(self, c):
        """Aquires new value for frequency and returns it."""
        dev = self.selectedDevice(c)
        frequency = yield dev.query('MEAS:FREQ?')
        frequency = float(frequency.split(',')[0].strip('ABCDEFGHIJKLMNOPQRSTUVWXYZ'))
        returnValue(frequency * units.Hz)
    
    @setting(85, 'set_ac_range', input_range = 'v[V]')
    def set_ac_range(self, c, input_range = 100e-3 * units.V):
        """Sets the voltage input range for an AC voltage measurement."""
        dev = self.selectedDevice(c)
        yield dev.write('CONF:VOLT:AC '+ str(input_range['V']) + ",MAX") 
        
    @setting(86, 'Set Digital Filter Paramters', avg_type = 's', state ='s', count='i')
    def set_digital_filter_paramters(self, c, avg_type = "REPEAT", state = "ON", count=10):
        """Sets the digital filtering parameters for an AC voltage measurement."""
        dev = self.selectedDevice(c)
        if avg_type in ['REPEAT', 'MOVING']:
            yield dev.write('SENS:AVER:TCON '+ avg_type) 
        if state in ["ON", "OFF"]:
            yield dev.write('SENS:AVER:STATE '+ state)
        count = '%.1E' % count
        yield dev.write('SENS:AVER:COUNT ' + count)

    @setting(87, 'Get AC Volts', returns = 'v[V]')
    def get_ac_volts(self, c):
        """Aquires new value for AC Voltage and returns it."""
        dev = self.selectedDevice(c)
        voltage = yield dev.query('MEAS:VOLT:AC?')
        voltage = float(voltage.split(',')[0].strip('ABCDEFGHIJKLMNOPQRSTUVWXYZ'))
        returnValue(voltage * units.V)
  
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
        auto = yield self.get_auto_range_status(c)
        if not int(auto):
            range = yield self.get_fw_range(c)
        else:
            range = ''
        yield dev.write('TRIGger:SOURce IMMediate')
        resistance = yield dev.query('MEAS:FRES? '+str(range))
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
        resistance_range = yield dev.query('SENS:FRES:RANGe?')
        resistance_range = float(resistance_range.split(',')[0].strip('ABCDEFGHIJKLMNOPQRSTUVWXYZ'))
        returnValue(resistance_range * units.Ohm)

    @setting(23, 'Return To Local', returns = '')
    def return_to_local(self, c):
        """Returns the DMM's front panel to local after interfacing remotely."""
        dev = self.selectedDevice(c)
        yield dev.write('SYSTem:LOCal')

    @setting(24, 'Return To Remote', returns = '')
    def return_to_remote(self, c):
        """Returns the DMM's front panel to remote."""
        dev = self.selectedDevice(c)
        yield dev.write('SYSTem:REMote')
        
    @setting(25, 'Get Auto Range Status', returns = 's')
    def get_auto_range_status(self, c):
        """Returns the DMM's front panel to remote."""
        dev = self.selectedDevice(c)
        auto_range_status = yield dev.query('SENSe:FRESistance:RANGe:AUTO?')
        returnValue(auto_range_status)
        
    @setting(26, 'Set Auto Range Status', auto='b')
    def set_auto_range_status(self, c, auto):
        """Sets the DMM's auto range."""
        dev = self.selectedDevice(c)
        if auto:
            autoStr = 'ON'
        else:
            autoStr = 'OFF'
        yield dev.write('SENSe:FRESistance:RANGe:AUTO '+autoStr)
        
    @setting(27, 'Get DMM Mode', returns = 's')
    def get_dmm_mode(self, c):
        """Returns the DMM's front panel to remote."""
        dev = self.selectedDevice(c)
        dmm_mode = yield dev.query('SENSe:FUNCtion?')
        returnValue(dmm_mode)
        
    
  
__server__ = KeithleyServer()
  
if __name__ == '__main__':
    from labrad import util
    util.runServer(__server__)
