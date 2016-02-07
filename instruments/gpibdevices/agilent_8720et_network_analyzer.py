# Copyright (C) 2015, 2016 Guilhem Ribeill
#               2016 Ivan Pechenezhskiy
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
name = Agilent 8720ET Network Analyzer
version = 1.2.0
description = Two channel 8720ET network analyzer server

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 5
### END NODE INFO
"""

import numpy
from twisted.internet.defer import inlineCallbacks, returnValue

from labrad.gpib import GPIBManagedServer
from labrad.server import setting
import labrad.units as units

from gpib_device_wrapper import ReadRawGPIBDeviceWrapper
from utilities import sleep


class Agilent8720ETDeviceWrapper(ReadRawGPIBDeviceWrapper):
    @inlineCallbacks
    def initialize(self):
        p = self._packet()
        p.write('OPC?;PRES')
        yield p.send()


class Agilent8720ETServer(GPIBManagedServer):
    name = 'Agilent 8720ET Network Analyzer'
    deviceName = 'HEWLETT PACKARD 8720ET'
    deviceWrapper = Agilent8720ETDeviceWrapper
    
    @setting(431, 'Preset')
    def preset(self, c):
        """Preset the network analyzer."""
        dev = self.selectedDevice(c)
        yield dev.initialize()

    @setting(432, 'Start Frequency', freq='v[Hz]', returns='v[Hz]')
    def start_frequency(self, c, freq=None):
        """Set or get the start frequency of the sweep."""
        dev = self.selectedDevice(c)
        if freq is None:
            resp = yield dev.query('STAR?')
            freq = float(resp) * units.Hz
        else:
            yield dev.write('STAR%i' %freq['Hz'])
        returnValue(freq)
    
    @setting(433, 'Stop Frequency', freq='v[Hz]', returns='v[Hz]')
    def stop_frequency(self, c, freq=None):
        """Set or get the stop frequency of the sweep."""
        dev = self.selectedDevice(c)
        if freq is None:
            resp = yield dev.query('STOP?')
            freq = float(resp) * units.Hz
        else:
            yield dev.write('STOP%i' %freq['Hz'])
        returnValue(freq)
        
    @setting(435, 'Measurement Setup', mode='s', returns='s')
    def measurement_setup(self, c, mode=None):
        """
        Set or get the measurement mode: transmission or reflection. 
        
        Following options are allowed (could be in any letter case):
            "S11", "REFL", 'R', 'REFLECTION' for the reflection mode;
            "S21", "TRAN", 'T', 'TRANSMISSION', 'TRANS' for the
            transmission mode.
        
        Output is either 'S11' or 'S21'.
        """
        dev = self.selectedDevice(c)
        if mode is None:
            resp = yield dev.query('RFLP?')
            if bool(int(resp)):
                returnValue('S11')
            else:
                returnValue('S21')
        else:
            if mode.upper() in ('S11', 'R', 'REFL', 'REFLECTION'):
                yield dev.write('RFLP')
                returnValue('S11')
            if mode.upper() in ('S21', 'T', 'TRAN', 'TRANS',
                    'TRANSMISSION'):
                yield dev.write('TRAP')
                returnValue('S21')
            else:
                raise ValueError('Unknown measurement mode: %s.' %mode)

    @setting(436, 'Sweep Points', pn='w', returns='w')
    def sweep_points(self, c, pn=None):
        """
        Set or get number of points in a sweep. The number will be 
        automatically coarsen to 3, 11, 21, 26, 51, 101, 201, 401, 801,
        or 1601 by the network analyzer.
        """
        dev = self.selectedDevice(c)
        if pn is not None:
            yield dev.write('POIN%i' %pn)
            t = yield dev.query('SWET?')
            yield sleep(2 * float(t)) # Be sure to wait for two sweep
                                      # times as required in the docs.
        resp = yield dev.query('POIN?')
        pn = int(float(resp))
        returnValue(pn)   
    
    @setting(437, 'Average Mode', avg='b', returns='b')
    def average_mode(self, c, avg=None):
        """Set or get average state."""
        dev = self.selectedDevice(c)
        if avg is None:
            resp = yield dev.query('AVERO?')
            avg = bool(int(resp))
        else:
            if avg:
                yield dev.write('AVEROON')
            else:
                yield dev.write('AVEROOFF')
        returnValue(avg)
        
    @setting(438, 'Average Points', aN='w', returns='w')
    def average_points(self, c, aN=None):
        """Set or get number of points in average (in 0-999 range)."""
        dev = self.selectedDevice(c)
        if aN is None:
            N = yield dev.query('AVERFACT?')
            aN = int(float(N))
        else:
            yield dev.write('AVERFACT%i' %aN)
        returnValue(aN)
        
    @setting(439, 'Restart Averaging')
    def restart_averaging(self, c):
        """Restart trace averaging."""
        dev = self.selectedDevice(c)
        yield dev.write('AVERREST')

    @setting(445, 'Source Power', pow='v[dBm]', returns='v[dBm]')
    def source_power(self, c, pow=None):
        """Set or get the sweep power level."""
        dev = self.selectedDevice(c)
        if pow is None:
            resp = yield dev.query('POWE?')
            pow = float(resp) * units.dBm
        else:
            if pow['dBm'] < -100:
                pow = -100 * units.dBm
                print('Minimum power level for Agilent 8720ET is %s.'
                        %pow)
            if pow['dBm'] > 10:
                pow = 10 * units.dBm
                print('Maximum power level for Agilent 8720ER is %s.'
                        %pow)
            yield dev.write('POWE%iDB' %pow['dBm'])
        returnValue(pow)
        
    @setting(450, 'Get Trace', returns=['*v[dB]', '*v', '*v[deg]', '*c'])
    def get_trace(self, c):
        """
        Get network analyzer trace. The output depends on the display
        format:
            "LOGMAG" - real [dB];
            "LINMAG" - real [linear units];
            "PHASE"  - real [deg];
            "REIM"   - complex [linear units].
        """
        dev = self.selectedDevice(c)
        # PC-DOS 32-bit floating-point format with 4 bytes-per-number,
        # 8 bytes-per-data point.
        yield dev.write('FORM5')
        avgOn = yield self.average_mode(c)

        if avgOn:
            numAvg = yield self.average_points(c)
            yield dev.write('AVERREST')
            yield dev.query('OPC?;NUMG%i' %numAvg, timeout=12*units.h)
        else:
            yield dev.query('OPC?;SING')

        yield dev.write('OUTPFORM')
        dataBuffer = yield dev.read_raw()

        fmt = yield self.display_format(c)
        raw = numpy.fromstring(dataBuffer, dtype=numpy.float32)
        data = numpy.empty((raw.shape[-1] - 1) / 2)
        real = raw[1:-1:2]
        if fmt == 'LOGMAG':
            returnValue(real.astype(float) * units.dB)
        elif fmt == 'LINMAG':
            returnValue(real.astype(float))
        elif fmt == 'PHASE':
            returnValue(real.astype(float) * units.deg)
        elif fmt == 'REIM':
            imag = numpy.hstack((raw[2:-1:2], raw[-1]))
            returnValue(real.astype(float) + 1j * imag.astype(float))
        
    @setting(451, 'Display Format', fmt='s', returns='s')
    def display_format(self, c, fmt=None):
        """
        Set or get the display format. Following options are allowed:
            "LOGMAG" - log magnitude display;
            "LINMAG" - linear magnitude display;
            "PHASE"  - phase display;
            "REIM"   - real and imaginary display.
        """
        dev = self.selectedDevice(c)
        if fmt is None:
            resp = yield dev.query('LOGM?')
            if bool(int(resp)):
                returnValue('LOGMAG')
            resp = yield dev.query('LINM?')
            if bool(int(resp)):
                returnValue('LINMAG')
            resp = yield dev.query('PHAS?')
            if bool(int(resp)):
                returnValue('PHASE')
            resp = yield dev.query('POLA?')
            if bool(int(resp)):
                returnValue('REIM')
        else:
            if fmt.upper() == 'LOGMAG': 
                yield dev.write('LOGM')
            elif fmt.upper() == 'LINMAG': 
                yield dev.write('LINM')
            elif fmt.upper() == 'PHASE': 
                yield dev.write('PHAS')
            elif fmt.upper() == 'REIM': 
                yield dev.write('POLA')
            else:
                raise ValueError('Unknown display format request: %s.'
                    %fmt)
        returnValue(fmt)


__server__ = Agilent8720ETServer()


if __name__ == '__main__':
    from labrad import util
    util.runServer(__server__)