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
name = GPIB Network Analyzers
version = 1.6.0
description = Provides basic control for network analayzers.

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
import numpy as np
from twisted.internet.defer import inlineCallbacks, returnValue

from labrad import util
from labrad.gpib import GPIBManagedServer, GPIBDeviceWrapper
from labrad.server import setting
import labrad.units as units

if __file__ in [f for f in os.listdir('.') if os.path.isfile(f)]:
    SCRIPT_PATH = os.path.dirname(os.getcwd())
else:
    SCRIPT_PATH = os.path.dirname(__file__)
LOCAL_PATH = SCRIPT_PATH.rsplit('instruments', 1)[0]
INSTRUMENTS_PATH = os.path.join(LOCAL_PATH, 'instruments')
if INSTRUMENTS_PATH not in sys.path:
    sys.path.append(INSTRUMENTS_PATH)

from utilities.gpib_device_wrapper import ReadRawGPIBDeviceWrapper
from utilities.sleep import sleep


class AgilentN5230ADeviceWrapper(ReadRawGPIBDeviceWrapper):
    model = 'Agilent Technologies N5230'
    available_traces = ('S11', 'S12', 'S13', 'S14', 'S21', 'S22', 'S23',
            'S24', 'S31', 'S32', 'S33', 'S34', 'S41', 'S42', 'S43',
            'S44')
    nPorts = 4

    @inlineCallbacks
    def initialize(self):
        # Create a new packet.
        p = self._packet()
        # Write to the packet.
        # Run the system preset command.
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
    def power_output(self, output=None):
        """Turn the output power on or off."""
        if output is None:
            resp = yield self.query('OUTP?')
            output = bool(int(resp))
        else:
            if output:
                yield self.write('OUTP ON')
            else:
                yield self.write('OUTP OFF')
        returnValue(output)

    @inlineCallbacks
    def center_frequency(self, cfreq=None):
        """Set or get the sweep center frequency."""
        if cfreq is None:
            resp = yield self.query('SENS1:FREQ:CENT?')
            cfreq = float(resp) * units.Hz
        else:
            yield self.write('SENS1:FREQ:CENT %i'%cfreq['Hz'])
        returnValue(cfreq)

    @inlineCallbacks
    def frequency_span(self, span=None):
        """Set or get the sweep frequency span."""
        if span is None:
            resp = yield self.query('SENS1:FREQ:SPAN?')
            span = float(resp) * units.Hz
        else:
            yield self.write('SENS1:FREQ:SPAN %i'%span['Hz'])
        returnValue(span)

    @inlineCallbacks
    def start_frequency(self, start=None):
        """Set or get the sweep start frequency."""
        if start is None:
            resp = yield self.query('SENS1:FREQ:STAR?')
            start = float(resp) * units.Hz
        else:
            yield self.write('SENS1:FREQ:STAR %i' %start['Hz'])
        returnValue(start)

    @inlineCallbacks
    def stop_frequency(self, stop=None):
        """Set or get the sweep stop frequency."""
        if stop is None:
            resp = yield self.query('SENS1:FREQ:STOP?')
            stop = float(resp) * units.Hz
        else:
            yield self.write('SENS1:FREQ:STOP %i' %stop['Hz'])
        returnValue(stop)

    @inlineCallbacks
    def sweep_type(self, stype='LIN'):
        """
        Set or get the frequency sweep type. 
        
        Accepts:
            stype: 'LIN' - for linear sweep,
                   'CW' - for single frequency
                   (default: 'LIN').
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
    def if_bandwidth(self, bw=None):
        """Set or get the IF bandwidth."""
        if bw is None:
            resp = yield self.query('SENS1:BAND?')
            bw = float(resp) * units.Hz
        else:
            yield self.write('SENS1:BAND %i' %bw['Hz'])
        returnValue(bw)

    @inlineCallbacks
    def average_mode(self, avg=None):
        """Turn the sweep averaging on or off, or query the state."""
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
        """
        Clear and restart the trace averaging on the current sweep.
        """
        yield self.write('SENS1:AVER:CLE')

    @inlineCallbacks
    def average_points(self, avg_pts=None):
        """
        Set or get the number of measurements to combine for an average.
        """
        if avg_pts is None:
            resp = yield self.query('SENS1:AVER:COUN?')
            avg_pts = int(float(resp))
        else:
            yield self.write('SENS1:AVER:COUN %d' %avg_pts)
        returnValue(avg_pts)

    @inlineCallbacks
    def source_power(self, power=None):
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
        sweep_time = float(resp) * units.s
        returnValue(sweep_time)

    @inlineCallbacks
    def sweep_points(self, points=None):
        """Set or get the number of points in the sweep."""
        if points is None:
            resp = yield self.query('SENS1:SWE:POIN?')
            points = int(float(resp))
        else:
            yield self.write('SENS1:SWE:POIN %i' %points)
        returnValue(points)

    @inlineCallbacks
    def measurement_setup(self, s_params=['S11'], formats=['MP'],
            trigger='IMM'):
        """
        Setup the measurement.
        
        Accepts:
            s_params: list of strings of the form Sxy ['S21', 'S11',...]
                    (default: ['S11']).
            formats: list of strings composed of 'RI' or 'MP',
                    'RI' - for the real/imaginary returned data format,
                    'MP' - for the magnitude/phase display format
                    (default: ['MP']).
            trigger: 'IMM' - for immediate triggering,
                     'EXT' - for external triggering (default: 'IMM').
        """
        s_params = [S.upper() for S in s_params]

        for Sp in s_params:
            if Sp not in self.available_traces:
                raise ValueError('Illegal S-parameter: %s.'
                        %str(Sp))

        # Delete all measurements on the PNA.
        yield self.write('CALC:PAR:DEL:ALL')
        # Close window 1 if it already exists.
        if (yield self.query('DISP:WIND1:STATE?')) == '1':
            self.write('DISP:WIND1:STATE OFF')
        # Create window 1.
        yield self.write('DISP:WIND1:STATE ON')
        for k, Sp in enumerate(s_params):
            if formats[k] == 'RI':
                yield self.write('CALC:PAR:DEF:EXT "R_%s",%s' %(Sp, Sp))
                yield self.write('DISP:WIND1:TRAC%d:FEED "R_%s"'
                                                    %(2 * k + 1, Sp))
                yield self.write('CALC:PAR:DEF:EXT "I_%s",%s' %(Sp, Sp))
                yield self.write('DISP:WIND1:TRAC%d:FEED "I_%s"'
                                                    %(2 * k + 2, Sp))
                yield self.write('CALC:PAR:SEL "R_%s"' %Sp)
                yield self.write('CALC:FORM REAL')
                yield self.write('CALC:PAR:SEL "I_%s"' %Sp)
                yield self.write('CALC:FORM IMAG')
            elif formats[k] == 'MP':
                yield self.write('CALC:PAR:DEF:EXT "M_%s",%s' %(Sp, Sp))
                yield self.write('DISP:WIND1:TRAC%d:FEED "M_%s"'
                                                    %(2 * k + 1, Sp))
                yield self.write('CALC:PAR:DEF:EXT "P_%s",%s' %(Sp, Sp))
                yield self.write('DISP:WIND1:TRAC%d:FEED "P_%s"'
                                                    %(2 * k + 2, Sp))
                yield self.write('CALC:PAR:SEL "M_%s"' %Sp)
                yield self.write('CALC:FORM MLOG')
                yield self.write('CALC:PAR:SEL "P_%s"' %Sp)
                yield self.write('CALC:FORM PHAS')
            yield self.write('DISP:WIND1:TRAC%d:Y:AUTO'%(2 * k + 1))
            yield self.write('DISP:WIND1:TRAC%d:Y:AUTO'%(2 * k + 2))
        
        yield self.write('SENS1:SWE:TIME:AUTO ON')
        
        if trigger == 'EXT':
            yield self.write('TRIG:SOUR EXT')
            yield self.write('TRIG:TYPE LEV')
        else:
            yield self.write('TRIG:SOUR IMM')

    @inlineCallbacks
    def get_data(self):
        """Get the active trace(s) from the network analyzer."""
        # Get list of traces in form "name, S21, name, S32,...".
        formats_s_params = yield self.query('CALC:PAR:CAT?')
        formats_s_params = formats_s_params.strip('"').split(',')

        # yield self.write('FORM REAL,64') # Do we need to add ',64'?
        yield self.write('FORM ASC,0')

        avg_mode = yield self.average_mode()
        if avg_mode:
            avgCount = yield self.average_points()
            yield self.restart_averaging()
            yield self.write('SENS:SWE:GRO:COUN %i' %avgCount)
            yield self.write('ABORT;SENS:SWE:MODE GRO')
        else:
            # Stop the current sweep and immediately send a trigger.
            yield self.write('ABORT;SENS:SWE:MODE SING')

        # Wait for the measurement to finish.
        # yield self.query('*OPC?', timeout=24*units.h) <-- old way, blocked GPIB chain entirely
        measurement_finished = False 
        yield self.write('*OPC') # will trigger bit in ESR when measurement finished
        while measurement_finished == False:
            yield sleep(0.05) # polling rate = 20Hz 
            opc_bit = yield self.query('*ESR?') # poll ESR for measurement completion
            opc_bit = int(opc_bit) & 0x1
            if (opc_bit == 1):
                measurement_finished = True
        
        # Pull the data.
        data = ()
        pair = ()
        unit_multipliers = {'R': 1, 'I': 1,
                'M': units.dB, 'P': units.deg}
        # The data will come in with a header in the form
        # '#[single char][number of data points][data]'.
        for idx, meas in enumerate(formats_s_params[::2]):
            yield self.write('CALC:PAR:SEL "%s"' %meas)
            data_string = yield self.query('CALC:DATA? FDATA')
            d = np.array(data_string.split(','), dtype=float)
            pair += (d * unit_multipliers[meas[0]]),
            if idx % 2:
                data += (pair),
                pair = ()
        returnValue(data)


class KeysightN5242ADeviceWrapper(AgilentN5230ADeviceWrapper):
    model = 'Keysight Technologies N5242A'
    available_traces = ('S11', 'S12', 'S21', 'S22')
    nPorts = 2


class KeysightE5063ADeviceWrapper(AgilentN5230ADeviceWrapper):
    model = 'Keysight Technologies E5063A'
    available_traces = ('S11', 'S12', 'S21', 'S22')
    nPorts = 2

    @inlineCallbacks
    def measurement_setup(self, s_params=['S11'], formats=['MP'],
            trigger='IMM'):
        """
        Setup the measurement.
        
        Accepts:
            s_params: list of strings of the form Sxy ['S21', 'S11',...]
                    (default: ['S11']).
            formats: list of strings composed of 'RI' or 'MP',
                    'RI' - for the real/imaginary returned data format,
                    'MP' - for the magnitude/phase display format
                    (default: ['MP']).
            trigger: 'IMM' - for immediate triggering,
                     'EXT' - for external triggering (default: 'IMM').
        """
        s_params = [S.upper() for S in s_params]

        for Sp in s_params:
            if Sp not in self.available_traces:
                raise ValueError('Illegal S-parameter: %s.'
                        %str(Sp))

        num_params = len(s_params)
        if num_params == 1:
            layout = 'D1_2'
        elif num_params == 2:
            layout = 'D1_2_3_4'          
        else:
            raise ValueError('Only one or two S-parameters are allowed '
                    'by the server implementation.')
         
        yield self.write('DISP:SPL D1')
        # Set the number of traces.
        yield self.write('CALC1:PAR:COUNT %d' %(2 * num_params))
        # Set the graph layout.
        yield self.write('DISP:WIND1:SPL %s' %layout)
        # Make window 1 (channel 1) active.
        yield self.write('DISP:WIND1:ACT')

        for k, Sp in enumerate(s_params):
            if formats[k] == 'RI':
                # Set the measurement parameter.
                yield self.write('CALC1:PAR%d:DEF %s' %((2 * k + 1), Sp))
                # Make the trace active.
                yield self.write('CALC1:PAR%d:SEL' %(2 * k + 1))
                # Select the format.
                yield self.write('CALC1:FORM REAL')
                # Set the measurement parameter.
                yield self.write('CALC1:PAR%d:DEF %s' %((2 * k + 2), Sp))
                # Make the trace active.
                yield self.write('CALC1:PAR%d:SEL' %(2 * k + 2))
                # Select the format.
                yield self.write('CALC1:FORM IMAG')
            elif formats[k] == 'MP':
                # Set the measurement parameter.
                yield self.write('CALC1:PAR%d:DEF %s' %((2 * k + 1), Sp))
                # Make the trace active.
                yield self.write('CALC1:PAR%d:SEL' %(2 * k + 1))
                # Select the format.
                yield self.write('CALC1:FORM MLOG')
                # Set the measurement parameter.
                yield self.write('CALC1:PAR%d:DEF %s' %((2 * k + 2), Sp))
                # Make the trace active.
                yield self.write('CALC1:PAR%d:SEL' %(2 * k + 2))
                # Select the format.
                yield self.write('CALC1:FORM PHAS')
            yield self.write('DISP:WIND1:TRAC%d:Y:AUTO'%(2 * k + 1))
            yield self.write('DISP:WIND1:TRAC%d:Y:AUTO'%(2 * k + 2))
        
        yield self.write('SENS1:SWE:TIME:AUTO 1')
        
        if trigger == 'EXT':
            yield self.write('TRIG:SOUR EXT')
        else:
            yield self.write('TRIG:SOUR INT')
    
    @inlineCallbacks
    def get_data(self):
        """Get the active trace(s) from the network analyzer."""
        avg_mode = yield self.average_mode()
        if avg_mode:
            yield self.write('TRIG:AVER 1')
        
        # Start the measurement.
        yield self.write('INIT1:CONT 0')
        yield self.write('ABOR')
        yield self.write('INIT1')

        # Wait for the measurement to finish.
        sweep_time = yield self.get_sweep_time()
        yield sleep(sweep_time)

        # Wait for the measurement to finish.
        yield self.query('*OPC?', timeout=24*units.h)

        # Pull the data.
        yield self.write('FORM:DATA ASC')
        data = ()
        pair = ()
        unit_multipliers = {'REAL': 1, 'IMAG': 1,
                 'MLOG': units.dB, 'PHAS': units.deg}
        num_params = yield self.query('CALC1:PAR:COUNT?')
        for k in range(int(num_params)):
            yield self.write('CALC1:PAR%d:SEL' %(k + 1))     
            format = (yield self.query('CALC1:FORM?'))
            data_string = (yield self.query('CALC1:DATA:FDAT?'))
            d = np.array(data_string.split(','), dtype=float)
            # Select only every other element.
            d = d[::2]
            pair += (d * unit_multipliers[format]),
            if k % 2:
                data += (pair),
                pair = ()
        returnValue(data)


class Agilent8720ETDeviceWrapper(ReadRawGPIBDeviceWrapper):
    model = 'Agilent Technologies 8720ET'
    available_traces = ('S11', 'S21')
    nPorts = 2
        
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
    def power_output(self, output=None):
        """Turn the output power on or off."""
        if output is None:
            resp = yield dev.query('POWT?')
            output = bool(int(resp))
        else:
            if output:
                yield dev.write('POWTON')
            else:
                yield dev.write('POWTOFF')
        returnValue(output)

    @inlineCallbacks
    def center_frequency(self, cfreq=None):
        """Set or get the sweep center frequency."""
        if cfreq is None:
            resp = yield self.query('CENT?')
            cfreq = float(resp) * units.Hz
        else:
            yield self.write('CENT%i' %freq['Hz'])
        returnVlaue(cfreq)

    @inlineCallbacks
    def frequency_span(self, span=None):
        """Set or get the sweep frequency span."""
        if span is None:
            resp = yield self.query('SPAN?')
            span = float(resp) * units.Hz
        else:
            yield self.write('SPAN%i' %freq['Hz'])
        returnVlaue(span)

    @inlineCallbacks
    def start_frequency(self, start=None):
        """Set or get the sweep start frequency."""
        if start is None:
            resp = yield self.query('STAR?')
            start = float(resp) * units.Hz
        else:
            yield self.write('STAR%i' %freq['Hz'])
        returnVlaue(start)

    @inlineCallbacks
    def stop_frequency(self, stop=None):
        """Set or get the sweep stop frequency."""
        dev = self.selectedDevice(c)
        if stop is None:
            resp = yield self.query('STOP?')
            stop = float(resp) * units.Hz
        else:
            yield self.write('STOP%i' %freq['Hz'])
        returnValue(stop)

    def sweep_type(self, stype=None):
        raise NotImplementedError

    @inlineCallbacks
    def if_bandwidth(self, bw=None):
        """Set or get the IF bandwidth."""
        if bw is None:
            resp = yield self.query('IFBW?')
            bw = float(resp) * units.Hz
        else:
            yield self.write('IFBW%i' %freq['Hz'])
        returnVlaue(bw)

    @inlineCallbacks
    def average_mode(self, avg=None):
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
        """Restart the trace averaging."""
        yield self.write('AVERREST')

    @inlineCallbacks
    def average_points(self, avg_pts=None):
        """Set or get number of points in average (in 0-999 range)."""
        if avg_pts is None:
            N = yield self.query('AVERFACT?')
            avg_pts = int(float(N))
        else:
            yield self.write('AVERFACT%i' %avg_pts)
        returnValue(avg_pts)

    @inlineCallbacks
    def source_power(self, power=None):
        """Set or get the sweep power level."""
        if power is None:
            resp = yield self.query('POWE?')
            power = float(resp) * units.dBm
        else:
            if power['dBm'] < -100:
                power = -100 * units.dBm
                print('Minimum power level for %s is %s.'
                        %(self.model, power))
            if power['dBm'] > 10:
                power = 10 * units.dBm
                print('Maximum power level for %s is %s.'
                        %(self.model, power))
            yield self.write('POWE%iDB' %power['dBm'])
        returnValue(power)

    @inlineCallbacks
    def get_sweep_time(self):
        """Get the time to complete a sweep."""
        resp = yield self.query('SWET?')
        sweep_time = float(resp) * units.s
        returnValue(sweep_time)

    @inlineCallbacks
    def sweep_points(self, sweep_pts=None):
        """
        Set or get number of points in a sweep. The number will be
        automatically coarsen to 3, 11, 21, 26, 51, 101, 201, 401, 801,
        or 1601 by the network analyzer.
        """
        if sweep_pts is not None:
            yield self.write('POIN%i' %sweep_pts)
            t = yield self.query('SWET?')
            yield sleep(2 * float(t)) # Be sure to wait for two sweep
                                      # times as required in the docs.
        resp = yield self.query('POIN?')
        sweep_pts = int(float(resp))
        returnValue(sweep_pts)

    @inlineCallbacks
    def measurement_setup(self, s_params=['S11'], formats=['MP'],
            trigger='IMM'):
        """
        Setup the measurement.

        Accepts:
            s_params: either ['S11'] for the reflection data or ['S21']
                    for the transmission (default: ['S11']).
            formats: list of strings composed of 'RI' or 'MP',
                    'RI' - for the real/imaginary returned data format,
                    'MP' - for the magnitude/phase display format
                    (default: ['MP']).
            trigger: 'IMM' - for immediate triggering (default: 'IMM').
        """
        if len(s_params) != 1:
            raise IndexError('This VNA only takes a single trace.')
        
        # Given a list but this VNA can only take one S-parameter.
        mode = s_params[0].uppper()
        if mode == 'S11':
            yield self.write('RFLP')
        elif mode == 'S21':
            yield self.write('TRAP')
        else:
            raise ValueError('Illegal S-parameter: %s.' %mode)

        fmt = formats[0]
        self.form = fmt.upper()
        if fmt.upper() == 'MP':
            yield self.write('LOGM')
        elif fmt.upper() == 'RI':
            yield self.write('POLA')
        else:
            raise ValueError('Unknown display format request: %s.'
                    %fmt)

        if trigger.upper() != 'IMM':
            raise ValueError('Only immediate ("IMM") triggering is '
                          'implemented for this network analyzer.')

    @inlineCallbacks
    def get_data(self):
        """
        Get network analyzer trace. The output depends on the display
        format.
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
        raw = np.fromstring(dataBuffer, dtype=np.float32)
        data = np.empty((raw.shape[-1] - 1) / 2)
        real = raw[1:-1:2]
        imag = np.hstack((raw[2:-1:2], raw[-1]))
        
        if self.form == 'MP':
            data = (real.astype(float) * units.dB,
                    imag.astype(float) * units.deg),
        elif self.form == 'RI':
            data = (real.astype(float), imag.astype(float)),
        returnValue(data)


class VNAServer(GPIBManagedServer):
    name = 'GPIB Network Analyzers'
    
    # Note: while N5242A and E5063A are from Keysight, *IDN? returns
    # Agilent as the manufacturer, hence the changes between Keysight
    # and Agilent in the device names and wrappers. Similarly, 8720ET is
    # from Agilent but HP is listed as its manufacturer.
    deviceWrappers = {'AGILENT TECHNOLOGIES N5230A': AgilentN5230ADeviceWrapper,
                      'AGILENT TECHNOLOGIES N5242A': KeysightN5242ADeviceWrapper,
                      'AGILENT TECHNOLOGIES E5063A': KeysightE5063ADeviceWrapper,
                      'HEWLETT PACKARD 8720ET': Agilent8720ETDeviceWrapper}

    @setting(100, 'Clear Status')
    def clear_status(self, c):
        """
        Clear the instrument status byte by emptying the error queue and
        clearing all event registers. Also cancel any preceding *OPC
        command or query.
        """
        dev = self.selectedDevice(c)
        dev.clear_status()

    @setting(150, 'Preset')
    def preset(self, c):
        """Preset the network analyzer."""
        dev = self.selectedDevice(c)
        dev.preset()

    @setting(200, 'Power Output', power='b', returns='b')
    def power_output(self, c, power=None):
        """Turn output power on or off, or query state."""
        dev = self.selectedDevice(c)
        power = yield dev.power_output(power)
        returnValue(power)

    @setting(300, 'Center Frequency', cfreq='v[Hz]', returns='v[Hz]')
    def center_frequency(self, c, cfreq=None):
        """Set or get the sweep center frequency."""
        dev = self.selectedDevice(c)
        cfreq = yield dev.center_frequency(cfreq)
        returnValue(cfreq)

    @setting(400, 'Frequency Span', span='v[Hz]', returns='v[Hz]')
    def frequency_span(self, c, span=None):
        """Set or get the sweep frequency span."""
        dev = self.selectedDevice(c)
        span = yield dev.frequency_span(span)
        returnValue(span)

    @setting(500, 'Start Frequency', start='v[Hz]', returns='v[Hz]')
    def start_frequency(self, c, start=None):
        """Set or get the sweep start frequency."""
        dev = self.selectedDevice(c)
        span = yield dev.start_frequency(start)
        returnValue(span)

    @setting(600, 'Stop Frequency', stop='v[Hz]', returns='v[Hz]')
    def stop_frequency(self, c, stop=None):
        """Set or get the sweep stop frequency."""
        dev = self.selectedDevice(c)
        resp = yield dev.stop_frequency(stop)
        returnValue(resp)

    @setting(700, 'Sweep Type', stype='s', returns='s')
    def sweep_type(self, c, stype=None):
        dev = self.selectedDevice(c)
        resp = yield dev.sweep_type(stype)
        returnValue(resp)

    @setting(800, 'IF Bandwidth', bw='v[Hz]', returns='v[Hz]')
    def if_bandwidth(self, c, bw=None):
        dev = self.selectedDevice(c)
        resp = yield dev.if_bandwidth(bw)
        returnValue(resp)

    @setting(900, 'Average Mode', avg='b', returns='b')
    def average_mode(self, c, avg=None):
        dev = self.selectedDevice(c)
        resp = yield dev.average_mode(avg)
        returnValue(resp)

    @setting(1000, 'Restart Averaging')
    def restart_averaging(self, c):
        dev = self.selectedDevice(c)
        dev.restart_averaging()

    @setting(1100, 'Average Points', avg_pts='w', returns='w')
    def average_points(self, c, avg_pts=None):
        dev = self.selectedDevice(c)
        resp = yield dev.average_points(avg_pts)
        returnValue(resp)

    @setting(1200, 'Source Power', power='v[dBm]', returns='v[dBm]')
    def source_power(self, c, power=None):
        dev = self.selectedDevice(c)
        resp = yield dev.source_power(power)
        returnValue(resp)

    @setting(1300, 'Get Sweep Time', returns='v[s]')
    def get_sweep_time(self, c):
        dev = self.selectedDevice(c)
        resp = yield dev.get_sweep_time()
        returnValue(resp)

    @setting(1400, 'Sweep Points', points='w', returns='w')
    def sweep_points(self, c, points=None):
        dev = self.selectedDevice(c)
        resp = yield dev.sweep_points(points)
        returnValue(resp)

    @setting(1500, 'Measurement Setup', s_params='*s', formats='*s',
            trigger='s')
    def measurement_setup(self, c, s_params=['S21'], formats=['MP'],
            trigger='IMM'):
        """
        Setup the measurement.

        Accepts:
            s_params: list of strings of the form Sxy ['S21', 'S11',...]
                    (default: ['S21']).
            formats: list of strings composed of 'RI' or 'MP',
                    'RI' - for the real/imaginary returned data format,
                    'MP' - for the magnitude/phase display format
                    (default: all traces are 'MP').
            trigger: 'IMM' - for immediate triggering,
                    'EXT' - for external triggering
                    (default: 'IMM').
        """
        if formats is not None:
            if len(formats) is not len(s_params):
                raise IndexError('s_params and formats are not the same '
                        'length.')
            for form in formats:
                if form not in ('RI', 'MP'):
                    raise ValueError('Illegal measurment definition: '
                            '%s.' %str(form))
        else:
            formats = ['MP'] * len(s_params)

        dev = self.selectedDevice(c)
        yield dev.measurement_setup(s_params, formats, trigger)

    @setting(1600, 'Get Data', returns='?')
    def get_data(self, c):
        """
        Get the network analyzer trace. The output depends on
        the display format. The returned data is a 3D-tuple. The first
        index defines an S-parameter in the dataset (specified by
        argument s_params in 'Measurement Setup' setting), the second
        index always runs from 0 to 1 and corresponds to either
        real/imaginary or magnitude/phase S-parameter values
        (which are set by agrument formats in 'Measurement Setup'), and
        the third dimension corresponds to the sweep frequencies.
        """
        dev = self.selectedDevice(c)
        resp = yield dev.get_data()
        returnValue(resp)

    @setting(1700, 'Get Frequencies', returns='*v[Hz]')
    def get_frequencies(self, c):
        """Get the trace frequencies."""
        dev = self.selectedDevice(c)
        start = yield dev.start_frequency()
        stop = yield dev.stop_frequency()
        pts = yield dev.sweep_points()
        freqs = np.linspace(start['Hz'], stop['Hz'], pts) * units.Hz
        returnValue(freqs)
        
    @setting(1800, 'Get Model', returns='s')
    def get_model(self, c):
        """Get the network analyzer model."""
        dev = self.selectedDevice(c)
        return dev.model


__server__ = VNAServer()


if __name__ == '__main__':
    util.runServer(__server__)