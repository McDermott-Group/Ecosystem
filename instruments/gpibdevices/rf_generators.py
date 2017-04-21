# Copyright (C) 2015 Ivan Pechenezhskiy
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
name = GPIB RF Generators
version = 1.0.2
description = Provides basic control for microwave generators.

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 5
### END NODE INFO
"""

import os
import sys
import string
from twisted.internet.defer import inlineCallbacks, returnValue

from labrad import util
from labrad.server import setting
from labrad.units import Hz, dBm
from labrad.gpib import GPIBManagedServer, GPIBDeviceWrapper

if __file__ in [f for f in os.listdir('.') if os.path.isfile(f)]:
    SCRIPT_PATH = os.path.dirname(os.getcwd())
else:
    SCRIPT_PATH = os.path.dirname(__file__)
LOCAL_PATH = SCRIPT_PATH.rsplit('instruments', 1)[0]
INSTRUMENTS_PATH = os.path.join(LOCAL_PATH, 'instruments')
if INSTRUMENTS_PATH not in sys.path:
    sys.path.append(INSTRUMENTS_PATH)

from utilities.gpib_device_wrapper import ReadRawGPIBDeviceWrapper


class HP83712BWrapper(GPIBDeviceWrapper):
    @inlineCallbacks
    def initialize(self):
        self.frequency = yield self.getFrequency()
        self.power = yield self.getPower()
        self.output = yield self.getOutput()

    @inlineCallbacks
    def reset(self):
        yield self.write('*CLS;*RST')
        yield self.initialize()

    @inlineCallbacks
    def getFrequency(self):
        freq = yield self.query('FREQ?').addCallback(float)
        self.frequency = freq * Hz
        returnValue(self.frequency)

    @inlineCallbacks
    def getPower(self):
        self.power = (yield self.query('POW?').addCallback(float)) * dBm
        returnValue(self.power)

    @inlineCallbacks
    def getOutput(self):
        output = yield self.query('OUTP?')
        self.output = bool(float(output))
        returnValue(self.output)

    @inlineCallbacks
    def setFrequency(self, freq):
        if self.frequency != freq:
            yield self.write('FREQ %s' % str(freq['Hz']))
            # Ensure that the frequency is set properly.
            self.frequency = yield self.getFrequency()

    @inlineCallbacks
    def setPower(self, pwr):
        if self.power != pwr:
            yield self.write('POW %s' % str(pwr['dBm']))
            # Ensure that the power is set properly.
            self.power = yield self.getPower()

    @inlineCallbacks
    def setOutput(self, out):
        if self.output != bool(out):
            yield self.write('OUTP %s' % str(int(out)))
            # Ensure that the output is set properly.
            self.output = yield self.getOutput()


class HP83620AWrapper(HP83712BWrapper):
    @inlineCallbacks
    def getOutput(self):
        output = yield self.query('POW:STAT?')
        self.output = bool(float(output))
        returnValue(self.output)

    @inlineCallbacks
    def setOutput(self, out):
        if self.output != bool(out):
            yield self.write('POW:STAT %s' % str(int(out)))
            # Ensure that the output is set properly.
            self.output = yield self.getOutput()


class HP8341BWrapper(ReadRawGPIBDeviceWrapper):
    @inlineCallbacks
    def initialize(self):
        self.frequency = yield self.getFrequency()
        self.power = yield self.getPower()
        self.output = yield self.getOutput()

    @inlineCallbacks
    def reset(self):
        yield self.write('CS')
        yield self.initialize()

    @inlineCallbacks
    def getFrequency(self):
        freq = yield self.query('OK').addCallback(float)
        self.frequency = freq * Hz
        returnValue(self.frequency)

    @inlineCallbacks
    def getPower(self):
        self.power = (yield self.query('OR').addCallback(float)) * dBm
        returnValue(self.power)

    @inlineCallbacks
    def getOutput(self):
        yield self.write('OM')
        status = yield self.read_raw()
        self.output = bool(ord(status[6]) & 32)
        returnValue(self.output)

    @inlineCallbacks
    def setFrequency(self, freq):
        if self.frequency != freq:
            yield self.write('CW%sGZ' % str(freq['GHz']))
            # Ensure that the frequency is set properly.
            self.frequency = yield self.getFrequency()

    @inlineCallbacks
    def setPower(self, pwr):
        if self.power != pwr:
            yield self.write('PL%sDB' % str(pwr['dBm']))
            # Ensure that the power is set properly.
            self.power = yield self.getPower()

    @inlineCallbacks
    def setOutput(self, out):
        if self.output != bool(out):
            yield self.write('RF%s' % str(int(out)))
            # Ensure that the output is set properly.
            self.output = yield self.getOutput()


class HP8673EWrapper(HP8341BWrapper):
    @inlineCallbacks
    def getFrequency(self):
        freq = yield self.query('OK')
        self.frequency = float(freq.strip(string.ascii_letters)) * Hz
        returnValue(self.frequency)

    @inlineCallbacks
    def getPower(self):
        pwr = yield self.query('LEOA')
        self.power = float(pwr.strip(string.ascii_letters)) * dBm
        returnValue(self.power)

    @inlineCallbacks
    def setPower(self, pwr):
        if self.power != pwr:
            yield self.write('LE%sDB' % str(pwr['dBm']))
            # Ensure that the power is set properly.
            self.power = yield self.getPower()

    @inlineCallbacks
    def reset(self):
        HP8341BWrapper.reset(self)
        yield self.write('RF0')

    @inlineCallbacks
    def initialize(self):
        HP8341BWrapper.initialize(self)
        yield self.write('RF0')


class RFGeneratorServer(GPIBManagedServer):
    """This server provides basic control for microwave generators."""
    name = 'GPIB RF Generators'
    deviceWrappers = {'HEWLETT-PACKARD 83620A': HP83620AWrapper,
                      'HEWLETT-PACKARD 83711B': HP83712BWrapper,
                      'HEWLETT-PACKARD 83712B': HP83712BWrapper,
                      'HEWLETT-PACKARD 8340B': HP8341BWrapper,
                      'HEWLETT-PACKARD 8341B': HP8341BWrapper,
                      'HEWLETT-PACKARD 8673E': HP8673EWrapper}

    @setting(9, 'Reset')
    def reset(self, c):
        """Reset the RF generator."""
        yield self.selectedDevice(c).reset()

    @setting(10, 'Frequency', freq='v[Hz]', returns='v[Hz]')
    def frequency(self, c, freq=None):
        """Get or set the CW frequency."""
        dev = self.selectedDevice(c)
        if freq is not None:
            yield dev.setFrequency(freq)
        returnValue(dev.frequency)

    @setting(11, 'Power', pwr='v[dBm]', returns='v[dBm]')
    def power(self, c, pwr=None):
        """Get or set the CW power."""
        dev = self.selectedDevice(c)
        if pwr is not None:
            yield dev.setPower(pwr)
        returnValue(dev.power)

    @setting(12, 'Output', on='b', returns='b')
    def output(self, c, on=None):
        """Get or set the RF generator output state (on/off)."""
        dev = self.selectedDevice(c)
        if on is not None:
            yield dev.setOutput(on)
        returnValue(dev.output)


__server__ = RFGeneratorServer()


if __name__ == '__main__':
    util.runServer(__server__)
