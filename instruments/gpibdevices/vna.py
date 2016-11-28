# Copyright (C) 2015, 2016 Guilhem Ribeill
#               2016 Ivan Pechenezhskiy
#               2016 Noah Meltzer
#               2016 Chris Wilen
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
name = Network Analyzers
version = 1.2.0
description = Network analyzer server

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

from labrad.gpib import GPIBManagedServer, GPIBDeviceWrapper
from labrad.server import setting
import labrad.units as units
from gpib_device_wrapper import ReadRawGPIBDeviceWrapper

from utilities import sleep

class AgilentN5230ADeviceWrapper(ReadRawGPIBDeviceWrapper):

    availableTraces = ('S11', 'S12', 'S13', 'S14', 'S21', 'S22', 'S23',
            'S24', 'S31', 'S32', 'S33', 'S34', 'S41', 'S42', 'S43',
            'S44')
    nPorts = 4

    @inlineCallbacks
    def initialize(self):
        # Create a new packet
        p = self._packet()
        # Write to the packet
        # This is the system->preset command
        p.write('SYST:PRES')
        yield p.send()
        yield sleep(0.1)

    @inlineCallbacks
    def clear_status(self):
        """
        Clear the instrument status byte by emptying the error queue and
        clearing all event registers. Also cancel any preceding *OPC
        command or query.
        """
        yield self.write('*CLS')

    @inlineCallbacks
    def preset(self):
        """Preset the network analyzer."""
        yield self.initialize()

    @inlineCallbacks
    def power_output(self, powOn):
        '''Turn output power on or off'''
        if powOn is None:
            resp = yield self.query('OUTP?')
            powOn = bool(int(resp))
        else:
            if powOn:
                yield self.write('OUTP ON')
            else:
                yield self.write('OUTP OFF')
        returnValue(powOn)

    @inlineCallbacks
    def center_frequency(self, cfreq):
        '''Set or get the sweep center frequency.'''
        if cfreq is None:
            resp = yield self.query('SENS1:FREQ:CENT?')
            cfreq = float(resp)*units.Hz
        else:
            yield self.write('SENS1:FREQ:CENT %i'%cfreq['Hz'])
        returnValue(cfreq)

    @inlineCallbacks
    def frequency_span(self, span):
        if span is None:
            resp = yield self.query('SENS1:FREQ:SPAN?')
            span = float(resp)*units.Hz
        else:
            yield self.write('SENS1:FREQ:SPAN %i'%span['Hz'])
        returnValue (span) # THis didnt look right, so I changed iter

    @inlineCallbacks
    def start_frequency(self, start):
        if start is None:
            resp = yield self.query('SENS1:FREQ:STAR?')
            start = float(resp)*units.Hz
        else:
            yield self.write('SENS1:FREQ:SPAN %i' %span['Hz'])
        returnValue(start) #This didnt look right either, so I channged it

    @inlineCallbacks
    def stop_frequency(self, stop):
        '''Set or get sweep stop frequency.'''
        if stop is None:
            resp = yield self.query('SENS1:FREQ:STOP?')
            stop = float(resp)*units.Hz
        else:
            yield self.write('SENS1:FREQ:STOP %i' %stop['Hz'])
        returnValue(stop)

    @inlineCallbacks
    def sweep_type(self, stype):
        """
        Set or get the frequency sweep type. 'LIN' - for linear,
        'CW' - for single frequency.
        """
        if stype is None:
            stype = yield self.query('SENS1:SWE:TYPE?')
        else:
            if stype.upper() != 'CW' and stype.upper() != 'LIN':
                raise ValueError('Unknown sweep type: %s. ' +
                        'Please use "LIN" or "CW".' %stype)
            else:
                yield self.write('SENS1:SWE:TYPE %s' %stype)
        returnValue(stype)

    @inlineCallbacks
    def if_bandwidth(self, bw):
        """Set or get the IF bandwidth."""
        if bw is None:
            resp = yield self.query('SENS1:BAND?')
            bw = float(resp) * units.Hz
        else:
            yield self.write('SENS1:BAND %i' %bw['Hz'])
        returnValue(bw)

    @inlineCallbacks
    def average_mode(self, avg):
        """Turn sweep averaging on or off, or query state."""
        if avg is None:
            resp = yield self.query('SENS1:AVER?')
            avg = bool(int(resp))
        else:
            if avg:
                yield self.write('SENS1:AVER ON')
            else:
                yield self.write('SENS1:AVER OFF')
        returnValue(avg)

    @inlineCallbacks
    def restart_averaging(self):
        """Clears and restarts trace averaging on the current sweep."""
        yield self.write('SENS1:AVER:CLE')

    @inlineCallbacks
    def average_points(self, count):
        """
        Set or get the number of measurements to combine for an average.
        """
        if count is None:
            resp = yield self.query('SENS1:AVER:COUN?')
            count = int(float(resp))
        else:
            yield self.write('SENS1:AVER:COUN %d' %count)
        returnValue(count)

    @inlineCallbacks
    def source_power(self, power):
        if power is None:
            resp = yield self.query('SOUR:POW?')
            power = float(resp) * units.dBm
        else:
            yield self.write('SOUR:POW1 %f' %power['dBm'])
        returnValue(power)

    @inlineCallbacks
    def get_sweep_time(self):
        """Get the time to complete a sweep."""
        resp = yield self.query('SENS1:SWE:TIME?')
        swpTime = float(resp) * units.s
        returnValue(swpTime)

    @inlineCallbacks
    def sweep_points(self, points):
        """Set or get the number of points in the sweep."""
        if points is None:
            resp = yield self.query('SENS1:SWE:POIN?')
            points = int(float(resp))
        else:
            yield self.write('SENS1:SWE:POIN %i' %points)
        returnValue(points)

    @inlineCallbacks
    def measurement_setup(self, SList, formList, triggerType):
        """
        Set the measurement parameters. Use a list of strings of the form Sxx
        (S21, S11...) for the measurement type.  The form list can be either
        'IQ' or 'MP' for mag/phase.
        """
        SList = [S.upper() for S in SList]

        for Sp in SList:
            if Sp not in self.availableTraces:
                raise ValueError('Illegal measurment definition: %s.' %str(Sp))

        # Delete all measurements on the PNA.
        yield self.write('CALC:PAR:DEL:ALL')
        # Close window 1 if it already exists.
        if (yield self.query('DISP:WIND1:STATE?')) == '1':
            self.write('DISP:WIND1:STATE OFF')
        # Create window 1.
        yield self.write('DISP:WIND1:STATE ON')
        for k, Sp in enumerate(SList):
            if formList[k] == 'IQ':
                yield self.write('CALC:PAR:DEF:EXT "R_%s",%s' %(Sp, Sp))
                yield self.write('DISP:WIND1:TRAC%d:FEED "R_%s"' %(2 * k + 1, Sp))
                yield self.write('CALC:PAR:DEF:EXT "I_%s",%s' %(Sp, Sp))
                yield self.write('DISP:WIND1:TRAC%d:FEED "I_%s"' %(2 * k + 2, Sp))
                yield self.write('CALC:PAR:SEL "R_%s"' %Sp)
                yield self.write('CALC:FORM REAL')
                yield self.write('CALC:PAR:SEL "I_%s"' %Sp)
                yield self.write('CALC:FORM IMAG')
            if formList[k] == 'MP':
                yield self.write('CALC:PAR:DEF:EXT "M_%s",%s' %(Sp, Sp))
                yield self.write('DISP:WIND1:TRAC%d:FEED "M_%s"' %(2 * k + 1, Sp))
                yield self.write('CALC:PAR:DEF:EXT "P_%s",%s' %(Sp, Sp))
                yield self.write('DISP:WIND1:TRAC%d:FEED "P_%s"' %(2 * k + 2, Sp))
                yield self.write('CALC:PAR:SEL "M_%s"' %Sp)
                yield self.write('CALC:FORM MLOG')
                yield self.write('CALC:PAR:SEL "P_%s"' %Sp)
                yield self.write('CALC:FORM PHAS')
            yield self.write('DISP:WIND1:TRAC%d:Y:AUTO'%(2 * k + 1))
            yield self.write('DISP:WIND1:TRAC%d:Y:AUTO'%(2 * k + 2))
            yield self.write('SENS1:SWE:TIME:AUTO ON')
        
        if triggerType == 'EXT':
            yield self.write('TRIG:SOUR EXT')
            yield self.write('TRIG:TYPE LEV')
        else:
            yield self.write('TRIG:SOUR IMM')

    @inlineCallbacks
    def get_trace(self):
        """Get the active trace from the network analyzer."""

        # get list of traces in form "name, S21, name, S32,..."
        measList = yield self.query('CALC:PAR:CAT?')
        measList = measList.strip('"').split(',')

        # yield self.write('FORM REAL,64') # do we need to add ',64'
        yield self.write('FORM ASC,0')

        avgMode = yield self.average_mode(None)
        if avgMode:
            avgCount = yield self.average_points(None)
            yield self.restart_averaging()
            yield self.write('SENS:SWE:GRO:COUN %i' %avgCount)
            yield self.write('ABORT;SENS:SWE:MODE GRO')
        else:
            # Stop the current sweep and immediately send a trigger.
            yield self.write('ABORT;SENS:SWE:MODE SING')

        # Wait for the measurement to finish.
        yield self.query('*OPC?', timeout=24*units.h)

        # pull data
        data = []
        unitMultiplier = {'I':1, 'Q':1, 'P':units.deg, 'M':units.dB}
        # the data will come in with a header in the form '#[single char][number of data points][data]'
        for meas in measList[::2]:
            yield self.write('CALC:PAR:SEL "%s"' %meas)
            yield self.write('CALC:DATA? FDATA')
            data_string = yield self.read()
            # data_string = yield self.read_raw()
            # data_string = data_string[len(data_string)%8:] # remove header
            # d = numpy.fromstring(data_string, dtype=numpy.float64) # * unitMultiplier[meas[0]]
            d = numpy.array([x for x in data_string.split(',')], dtype=float)# * unitMultiplier[meas[0]]
            data.append(d)

        returnValue(data)

class KeysightDeviceWrapper(AgilentN5230ADeviceWrapper):

        availableTraces = ('S11', 'S12', 'S21', 'S22')
        nPorts = 2

class Agilent8720ETDeviceWrapper(ReadRawGPIBDeviceWrapper):

    @inlineCallbacks
    def initialize(self):
        p = self._packet()
        p.write('OPC?;PRES')
        yield p.send()

    @inlineCallbacks
    def clear_status(self):
        """
        Clear the instrument status byte by emptying the error queue and
        clearing all event registers. Also cancel any preceding *OPC
        command or query.
        """
        yield dev.write('*CLS')

    @inlineCallbacks
    def preset(self):
        """Preset the network analyzer."""
        yield self.initialize()

    @inlineCallbacks
    def power_output(self, powOn):
        '''Turn output power on or off'''
        if powOn is None:
            resp = yield dev.query('POWT?')
            powOn = bool(int(resp))
        else:
            if powOn:
                yield dev.write('POWTON')
            else:
                yield dev.write('POWTOFF')
        returnValue(powOn)

    @inlineCallbacks
    def center_frequency(self, cfreq):
        if cfreq is None:
            resp = yield self.query('CENT?')
            cfreq = float(resp)*units.Hz
        else:
            yield self.write('CENT%i' %freq['Hz'])
        returnVlaue(cfreq)

    @inlineCallbacks
    def frequency_span(self, span):
        if span is None:
            resp = yield self.query('SPAN?')
            span = float(resp)*units.Hz
        else:
            yield self.write('SPAN%i' %freq['Hz'])
        returnVlaue(span)

    @inlineCallbacks
    def start_frequency(self, start):
        if start is None:
            resp = yield self.query('STAR?')
            start = float(resp)*units.Hz
        else:
            yield self.write('STAR%i' %freq['Hz'])
        returnVlaue(start)

    @inlineCallbacks
    def stop_frequency(self, stop):
        """Set or get the stop frequency of the sweep."""
        dev = self.selectedDevice(c)
        if stop is None:
            resp = yield self.query('STOP?')
            stop = float(resp) * units.Hz
        else:
            yield self.write('STOP%i' %freq['Hz'])
        returnValue(stop)

    def sweep_type(self, stype):
        raise NotImplementedError

    @inlineCallbacks
    def if_bandwidth(self, bw):
        if bw is None:
            resp = yield self.query('IFBW?')
            bw = float(resp)*units.Hz
        else:
            yield self.write('IFBW%i' %freq['Hz'])
        returnVlaue(bw)

    @inlineCallbacks
    def average_mode(self, avg):
        """Set or get average state."""
        if avg is None:
            resp = yield self.query('AVERO?')
            avg = bool(int(resp))
        else:
            if avg:
                yield self.write('AVEROON')
            else:
                yield self.write('AVEROOFF')
        returnValue(avg)

    @inlineCallbacks
    def restart_averaging(self):
        """Restart trace averaging."""
        yield self.write('AVERREST')

    @inlineCallbacks
    def average_points(self, aN):
        """Set or get number of points in average (in 0-999 range)."""
        if aN is None:
            N = yield self.query('AVERFACT?')
            aN = int(float(N))
        else:
            yield self.write('AVERFACT%i' %aN)
        returnValue(aN)

    @inlineCallbacks
    def source_power(self, power):
        """Set or get the sweep power level."""
        if power is None:
            resp = yield self.query('POWE?')
            power = float(resp) * units.dBm
        else:
            if power['dBm'] < -100:
                power = -100 * units.dBm
                print('Minimum power level for Agilent 8720ET is %s.'
                        %power)
            if power['dBm'] > 10:
                power = 10 * units.dBm
                print('Maximum power level for Agilent 8720ER is %s.'
                        %power)
            yield self.write('POWE%iDB' %power['dBm'])
        returnValue(power)

    @inlineCallbacks
    def get_sweep_time(self):
        """Get the time to complete a sweep."""
        resp = yield self.query('SWET?')
        swpTime = float(resp) * units.s
        returnValue(swpTime)

    @inlineCallbacks
    def sweep_points(self, pn):
        """
        Set or get number of points in a sweep. The number will be
        automatically coarsen to 3, 11, 21, 26, 51, 101, 201, 401, 801,
        or 1601 by the network analyzer.
        """
        if pn is not None:
            yield self.write('POIN%i' %pn)
            t = yield self.query('SWET?')
            yield sleep(2 * float(t)) # Be sure to wait for two sweep
                                      # times as required in the docs.
        resp = yield self.query('POIN?')
        pn = int(float(resp))
        returnValue(pn)

    @inlineCallbacks
    def get_trace(self):
        """
        Get network analyzer trace. The output depends on the display
        format:
            "LOGMAG" - real [dB];
            "REIM"   - complex [linear units].
        """
        # PC-DOS 32-bit floating-point format with 4 bytes-per-number,
        # 8 bytes-per-data point.
        yield self.write('FORM5')
        avgOn = yield self.average_mode(c)

        if avgOn:
            numAvg = yield self.average_points(c)
            yield self.write('AVERREST')
            yield self.query('OPC?;NUMG%i' %numAvg, timeout=12*units.h)
        else:
            yield self.query('OPC?;SING')

        yield self.write('OUTPFORM')
        dataBuffer = yield self.read_raw()

        fmt = yield self.display_format(c)
        raw = numpy.fromstring(dataBuffer, dtype=numpy.float32)
        data = numpy.empty((raw.shape[-1] - 1) / 2)
        real = raw[1:-1:2]
        if self.form == 'MP':
            # &&& is every other entry in the dataset the phase for this???
            returnValue([real.astype(float)])
        elif self.form == 'IQ':
            imag = numpy.hstack((raw[2:-1:2], raw[-1]))
            returnValue([real.astype(float) + 1j * imag.astype(float)])

    @inlineCallbacks
    def measurement_setup(self, SList, formList, triggerType):
        """
        Set or get the measurement mode: transmission or reflection.

        Following options are allowed (could be in any letter case):
            "S11", "REFL", 'R', 'REFLECTION' for the reflection mode;
            "S21", "TRAN", 'T', 'TRANSMISSION', 'TRANS' for the
            transmission mode.

        formList sets the display format. Following options are allowed:
            "MP" - log magnitude display;
            "IQ"   - real and imaginary display.
        """
        if SList is not None:
            if len(SList) != 1:
                raise IndexError('This VNA only takes a single trace')
            mode = SList[0] # given a list but this VNA can only take one
            if mode.upper() in ('S11', 'R', 'REFL', 'REFLECTION'):
                yield self.write('RFLP')
            if mode.upper() in ('S21', 'T', 'TRAN', 'TRANS', 'TRANSMISSION'):
                yield self.write('TRAP')
            else:
                raise ValueError('Unknown measurement mode: %s.' %mode)

        if formList is not None:
            fmt = formList[0]
            self.form = fmt.upper()
            if fmt.upper() == 'MP':
                yield self.write('LOGM')
            elif fmt.upper() == 'IQ':
                yield self.write('POLA')
            else:
                raise ValueError('Unknown display format request: %s.' %fmt)
        else:
            self.form = None

        if triggerType is not 'IMM':
            raise Warning('Only immediate ("IMM") triggering is implemented for this VNA.')


class VNAServer(GPIBManagedServer):
    name = 'GPIB VNA'
    deviceWrappers = {'AGILENT TECHNOLOGIES N5230A': AgilentN5230ADeviceWrapper,
                    # Note: while this device is from Keysight, *IDN? returns Agilent as
                    # the manufacturer, hence the change between Keysight and Agilent in
                    # name and deviceName.
                      'AGILENT TECHNOLOGIES N5242A': KeysightDeviceWrapper,
                      'KEYSIGHT TECHNOLOGIES E5063A': KeysightDeviceWrapper,
                      'HEWLETT PACKARD 8720ET': Agilent8720ETDeviceWrapper}

    @setting(100, 'Clear Status')
    def clear_status(self, c):
        """ Clear the instrument status byte by emptying the error queue and
        clearing all event registers. Also cancel any preceding *OPC
        command or query. """
        dev = self.selectedDevice(c)
        dev.clear_status()

    @setting(150, 'Preset')
    def preset(self, c):
        """Preset the network analyzer."""
        dev = self.selectedDevice(c)
        dev.preset()

    @setting(200, 'Power Output', pow='b', returns = 'b')
    def power_output(self, c, pow = None):
        '''Turn output power on or off, or query state.'''
        dev = self.selectedDevice(c)
        pow = yield dev.power_output(pow)
        returnValue(pow)

    @setting(300, 'Center Frequency', cfreq = 'v[Hz]', returns = 'v[Hz]')
    def center_frequency(self, c, cfreq = None):
        """Set or get the sweep center frequency"""
        dev = self.selectedDevice(c)
        cfreq = yield dev.center_frequency(cfreq)
        returnValue(cfreq)

    @setting(400, 'Frequency Span', span = 'v[Hz]', returns = 'v[Hz]')
    def frequency_span(self, c, span = None):
        dev = self.selectedDevice(c)
        span = yield dev.frequency_span(span)
        returnValue(span)

    @setting(500, 'Start Frequency', start = 'v[Hz]', returns = 'v[Hz]')
    def start_frequency(self, c, start = None):
        dev = self.selectedDevice(c)
        span = yield dev.start_frequency(start)
        returnValue(span)

    @setting(600, 'Stop Frequency', stop = 'v[Hz]', returns = 'v[Hz]')
    def stop_frequency(self, c, stop = None):
        dev = self.selectedDevice(c)
        resp  = yield dev.stop_frequency(stop)
        returnValue(resp)

    @setting(700, 'Sweep Type', stype = 's', returns = 's')
    def sweep_type(self, c, stype = None):
        dev = self.selectedDevice(c)
        resp  = yield dev.sweep_type(stype)
        returnValue(resp)

    @setting(800, 'IF Bandwidth',bw='v[Hz]', returns='v[Hz]')
    def if_bandwidth(self, c, bw = None):
        dev = self.selectedDevice(c)
        resp  = yield dev.if_bandwidth(bw)
        returnValue(resp)

    @setting(900, 'Average Mode',  avg='b', returns='b')
    def average_mode(self, c, avg = None):
        dev = self.selectedDevice(c)
        resp  = yield dev.average_mode(avg)
        returnValue(resp)

    @setting(1000, 'Restart Averaging')
    def restart_averaging(self, c):
        dev = self.selectedDevice(c)
        dev.restart_averaging()

    @setting(1100, 'Average Points', count = 'w', returns = 'w')
    def average_points(self, c, count = None):
        dev = self.selectedDevice(c)
        resp  = yield dev.average_points(count)
        returnValue(resp)

    @setting(1200, 'Source Power',pow='v[dBm]', returns='v[dBm]')
    def source_power(self, c, pow = None):
        dev = self.selectedDevice(c)
        resp  = yield dev.source_power(pow)
        returnValue(resp)

    @setting(1300, 'Get Sweep Time', returns = 'v[s]')
    def get_sweep_time(self, c):
        dev = self.selectedDevice(c)
        resp  = yield dev.get_sweep_time(pow)
        returnValue(resp)

    @setting(1400, 'Sweep Points', points='w', returns='w')
    def sweep_points(self, c, points = None):
        dev = self.selectedDevice(c)
        resp  = yield dev.sweep_points(points)
        returnValue(resp)

    @setting(1500, 'Measurement Setup', SList='*s', formList='?', triggerType='s')
    def measurement_setup(self, c, SList=['S21'], formList=['MP'], triggerType='IMM'):
        """
        Set the measurement parameters. Use a list of strings of the form Sxx
        (S21, S11...) for the measurement type.  The form list can be either
        'IQ' or 'MP' for mag/phase.
        """
        if formList is not None:
            if len(formList) is not len(SList):
                raise IndexError('S List and Form List are not the same length.')
            for form in formList:
                if form not in ('IQ','MP'):
                    raise ValueError('Illegal measurment definition: %s.' %str(form))
        else:
            formList = ['MP']*len(SList)

        dev = self.selectedDevice(c)
        yield dev.measurement_setup(SList, formList, triggerType)

    @setting(1600, 'Get Trace', returns='*2v')#'(*v[dB],*v[deg],*v[dB],*v[deg])')#['*2v[dB]', '*2v', '*2v[deg]', '*2c', '?'])
    def get_trace(self, c):
        """
        Get network analyzer trace. The output depends on the display
        format:
            "LOGMAG" - real [dB];
            "PHASE"  - real [deg];
            "REIM"   - complex [linear units].
        """
        dev = self.selectedDevice(c)
        resp  = yield dev.get_trace()
        returnValue(resp)


__server__ = VNAServer()

if __name__ == '__main__':
    from labrad  import util
    util.runServer(__server__)
