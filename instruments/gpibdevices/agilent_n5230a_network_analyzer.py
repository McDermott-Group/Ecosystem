# Copyright (C) 2015 Guilhem Ribeill
#               2015, 2016 Ivan Pechenezhskiy
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
name = Agilent N5230A Network Analyzer
version = 1.2.1
description = Four channel 5230A PNA-L network analyzer server

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

from utilities import sleep


class AgilentN5230ADeviceWrapper(GPIBDeviceWrapper):
    @inlineCallbacks
    def initialize(self):
        p = self._packet()
        p.write('SYST:PRES')
        yield p.send()
        yield sleep(0.1)


class AgilentN5230AServer(GPIBManagedServer):
    name = 'Agilent N5230A Network Analyzer'
    deviceName = 'AGILENT TECHNOLOGIES N5230A'
    deviceWrapper = AgilentN5230ADeviceWrapper
    
    @setting(598, 'Clear Status')
    def clear_status(self, c):
    	"""
        Clear the instrument status byte by emptying the error queue and
        clearing all event registers. Also cancel any preceding *OPC
        command or query.
        """
    	dev = self.selectedDevice(c)
    	yield dev.write('*CLS')
        
    @setting(599, 'Preset')
    def preset(self, c):
    	"""Preset the network analyzer."""
    	dev = self.selectedDevice(c)
    	yield dev.initialize()
    
    @setting(601, 'Power Output', pow='b', returns='b')
    def power_output(self, c, pow=None):
    	"""Turn output power on or off, or query state."""
    	dev = self.selectedDevice(c)
    	if pow is None:
    		resp = yield dev.query('OUTP?')
    		pow = bool(int(resp))
    	else:
    		if pow:
    			yield dev.write('OUTP ON')
    		else:
    			yield dev.write('OUTP OFF')
    	returnValue(pow)
    	
	@setting(602, 'Center Frequency', cfreq='v[Hz]', returns='v[Hz]')
	def center_frequency(self, c, cfreq=None):
		"""Set or get the sweep center frequency."""
		dev = self.selectedDevice(c)
		if cfreq is None:
			resp = yield dev.query('SENS1:FREQ:CENT?')
			cfreq = float(resp) * units.Hz
		else:
			yield dev.write('SENS1:FREQ:CENT %i' %cfreq['Hz'])
		returnValue(cfreq)
	
	@setting(603, 'Frequency Span', span='v[Hz]', returns='v[Hz]')
	def frequency_span(self, c, span=None):
		"""Set or get the sweep center frequency."""
		dev = self.selectedDevice(c)
		if span is None:
			resp = yield dev.query('SENS1:FREQ:SPAN?')
			span = float(resp) * units.Hz
		else:
			yield dev.write('SENS1:FREQ:SPAN %i' %span['Hz'])
		returnValue(cfreq)
    	
    @setting(604, 'Start Frequency', start='v[Hz]', returns='v[Hz]')
    def start_frequency(self, c, start=None):
    	"""Set or get sweep start frequency."""
    	dev = self.selectedDevice(c)
    	if start is None:
    		resp = yield dev.query('SENS1:FREQ:STAR?')
    		start = float(resp) * units.Hz
    	else:
    		yield dev.write('SENS1:FREQ:STAR %i' %start['Hz'])
    	returnValue(start)
    	
    @setting(605, 'Stop Frequency', stop='v[Hz]', returns='v[Hz]')
    def stop_frequency(self, c, stop=None):
    	"""Set or get sweep stop frequency."""
    	dev = self.selectedDevice(c)
    	if stop is None:
    		resp = yield dev.query('SENS1:FREQ:STOP?')
    		stop = float(resp) * units.Hz
    	else:
    		yield dev.write('SENS1:FREQ:STOP %i' %stop['Hz'])
    	returnValue(stop)
    	
    @setting(606, 'Sweep Type', stype='s', returns='s')
    def sweep_type(self, c, stype=None):
    	"""
        Set or get the frequency sweep type. 'LIN' - for linear,
        'CW' - for single frequency.
        """
    	dev = self.selectedDevice(c)
    	if stype is None:
            stype = yield dev.query('SENS1:SWE:TYPE?')
        else:
    		if stype.upper() != 'CW' and stype.upper() != 'LIN':
    			raise ValueError('Unknown sweep type: %s. ' +
                        'Please use "LIN" or "CW".' %stype)
    		else:
    			yield dev.write('SENS1:SWE:TYPE %s' %stype)
    	returnValue(stype)
    
    @setting(607, 'IF Bandwidth', bw='v[Hz]', returns='v[Hz]')
    def if_bandwidth(self, c, bw=None):
    	"""Set or get the IF bandwidth."""
    	dev = self.selectedDevice(c)
    	if bw is None:
    		resp = yield dev.query('SENS1:BAND?')
    		bw = float(resp) * units.Hz
    	else:
    		yield dev.write('SENS1:BAND %i' %bw['Hz'])
    	returnValue(bw)
    
    @setting(608, 'Average Mode', avg='b', returns='b')
    def average_mode(self, c, avg=None):
    	"""Turn sweep averaging on or off, or query state."""
    	dev = self.selectedDevice(c)
    	if avg is None:
    		resp = yield dev.query('SENS1:AVER?')
    		avg = bool(int(resp))
    	else:
    		if avg:
    			yield dev.write('SENS1:AVER ON')
    		else:
    			yield dev.write('SENS1:AVER OFF')
    	returnValue(avg)
    	
    @setting(609, 'Restart Averaging')
    def restart_averaging(self, c):
    	"""Clears and restarts trace averaging on the current sweep."""
    	dev = self.selectedDevice(c)
    	yield dev.write('SENS1:AVER:CLE')
    
    @setting(610, 'Average Points', count='w', returns='w')
    def average_points(self, c, count=None):
    	"""
        Set or get the number of measurements to combine for an average.
        """
    	dev = self.selectedDevice(c)
    	if count is None:
    		resp = yield dev.query('SENS1:AVER:COUN?')
    		count = int(float(resp))
    	else:
    		yield dev.write('SENS1:AVER:COUN %d' %count)
    	returnValue(count)
    
    @setting(611, 'Source Power', pow='v[dBm]', returns='v[dBm]')
    def source_power(self, c, pow=None):
    	"""Set or get source RF power."""
    	dev = self.selectedDevice(c)
    	if pow is None:
    		resp = yield dev.query('SOUR:POW?')
    		pow = float(resp) * units.dBm
    	else:
    		yield dev.write('SOUR:POW1 %f' %pow['dBm'])
    	returnValue(pow)
    	
    @setting(612, 'Get Sweep Time', returns='v[s]')
    def get_sweep_time(self, c):
    	"""Get the time to complete a sweep."""
    	dev = self.selectedDevice(c)
       	resp = yield dev.query('SENS1:SWE:TIME?')
    	swpTime = float(resp) * units.s
    	returnValue(swpTime)
    
    @setting(613, 'Sweep Points', points='w', returns='w')
    def sweep_points(self, c, points=None):
    	"""Set or get the number of points in the sweep."""
    	dev = self.selectedDevice(c)
    	if points is None:
    		resp = yield dev.query('SENS1:SWE:POIN?')
    		points = int(float(resp))
    	else:
    		yield dev.write('SENS1:SWE:POIN %i' %points)
    	returnValue(points)
    		    	
    @setting(614, 'Measurement Setup', meas='s')
    def measurement_setup(self, c, meas='S21'):
    	"""
        Set the measurement parameters. Use a string of the form Sxx
        (S21, S11...) for the measurement type.
    	"""
    	if meas not in ('S11', 'S12', 'S13', 'S14', 'S21', 'S22', 'S23', 
                'S24', 'S31', 'S32', 'S33', 'S34', 'S41', 'S42', 'S43',
                'S44'):
    		raise ValueError('Illegal measurment definition: %s.'
                    %str(meas))

        dev = self.selectedDevice(c)
        # Delete all measurements on the PNA.
    	yield dev.write('CALC:PAR:DEL:ALL')
        # Close window 1 if it already exists.
        if (yield dev.query('DISP:WIND1:STATE?')) == '1':
            dev.write('DISP:WIND1:STATE OFF')
        # Create window 1.
        yield dev.write('DISP:WIND1:STATE ON')
    	yield dev.write('CALC:PAR:DEF:EXT "%s",%s' %(meas, meas))
    	yield dev.write('DISP:WIND1:TRAC1:FEED "%s"' %meas)
    	yield dev.write('CALC:PAR:SEL "%s"' %meas)
        yield dev.write('SENS1:SWE:TIME:AUTO ON')
        yield dev.write('TRIG:SOUR IMM')
    
    @setting(615, 'Get Trace', returns='*v[dB]')
    def get_trace(self, c):
    	"""Get the active trace from the network analyzer."""
    	dev = self.selectedDevice(c)    	
        
    	meas = yield dev.query('SYST:ACT:MEAS?')
    	yield dev.write('CALC:PAR:SEL %s' %meas)   
    	yield dev.write('FORM ASC,0')
        
        avgMode = yield self.average_mode(c)
        if avgMode:
            avgCount = yield self.average_points(c)
            yield self.restart_averaging(c)
            yield dev.write('SENS:SWE:GRO:COUN %i' %avgCount)
            yield dev.write('ABORT;SENS:SWE:MODE GRO')
        else:
            # Stop the current sweep and immediately send a trigger. 
            yield dev.write('ABORT;SENS:SWE:MODE SING')

        # Wait for the measurement to finish.
        yield dev.query('*OPC?', timeout=24*units.h)
        ascii_data = yield dev.query('CALC1:DATA? FDATA')

    	data = numpy.array([x for x in ascii_data.split(',')],
                dtype=float) * units.dB
    	returnValue(data)

    @setting(616, 'Get S2P', ports='(w, w)', returns=('*(v[Hz], '
            'v[dB], v[deg], v[dB], v[deg], v[dB], v[deg], v[dB], '
            'v[deg])'))
    def get_s2p(self, c, ports=(1, 2)):
    	"""
        Get the scattering parameters from the network analyzer
        in the S2P format. The input parameter should be a tuple that
        specifies two network analyzer ports, e.g. (1, 2).
        Available ports are 1, 2, 3, and 4. The data are returned as 
        a list of tuples in the following format:
            *(frequency,
            S[ports[0], ports[0]], Phase[ports[0], ports[0]],
            S[ports[1], ports[0]], Phase[ports[1], ports[0]],
            S[ports[0], ports[1]], Phase[ports[0], ports[1]],
            S[ports[1], ports[1]], Phase[ports[0], ports[1]]).
        """
        if len(ports) != 2:
            raise Exception("Two and only two ports should be "
                    "specified.")
        for port in ports:
            if port < 1 or port > 4:
                raise Exception("Port number could be only '1', '2', "
                        "'3', or '4'.")
        if ports[0] == ports[1]:
            raise Exception("Port numbers should not be equal.")
        
    	dev = self.selectedDevice(c)    	
        
        S = (''.join(['S', str(ports[0]), str(ports[0])]),
             ''.join(['S', str(ports[0]), str(ports[1])]),
             ''.join(['S', str(ports[1]), str(ports[0])]),
             ''.join(['S', str(ports[1]), str(ports[1])]))
        # Delete all measurements on the PNA.
        yield dev.write('CALC:PAR:DEL:ALL')
        # Close window 1 if it already exists.
        if (yield dev.query('DISP:WIND1:STATE?')) == '1':
            dev.write('DISP:WIND1:STATE OFF')
        # Create window 1.
        yield dev.write('DISP:WIND1:STATE ON')
        for k in range(4):
            yield dev.write('CALC:PAR:DEF:EXT "s2p_%s",%s'
                    %(S[k], S[k]))
            yield dev.write('DISP:WIND1:TRAC%d:FEED "s2p_%s"'
                    %(k + 1, S[k]))
            yield dev.write('CALC:PAR:SEL "s2p_%s"' %S[k])
            yield dev.write('SENS1:SWE:TIME:AUTO ON')
            yield dev.write('TRIG:SOUR IMM')
  
    	yield dev.write('FORM ASC,0')
        
        avgMode = yield self.average_mode(c)
        if avgMode:
            avgCount = yield self.average_points(c)
            yield self.restart_averaging(c)
            yield dev.write('SENS:SWE:GRO:COUN %i' %avgCount)
            yield dev.write('ABORT;SENS:SWE:MODE GRO')
        else:
            # Stop the current sweep and immediately send a trigger. 
            yield dev.write('ABORT;SENS:SWE:MODE SING')

        # Set the units to dB and deg.
        yield dev.write('MMEM:STOR:TRAC:FORM:SNP DB')
            
        # Wait for the measurement to finish.
        yield dev.query('*OPC?', timeout=24*units.h)
        ascii_data = yield dev.query("CALC:DATA:SNP:PORT? '%i,%i'"
                %ports)
    	data = numpy.array([x for x in ascii_data.split(',')],
            dtype=float)
        length = numpy.size(data) / 9
        data = data.reshape(9, length)
        data = [(data[0, k] * units.Hz,
                 data[1, k] * units.dB, data[2, k] * units.deg,
                 data[3, k] * units.dB, data[4, k] * units.deg,
                 data[5, k] * units.dB, data[6, k] * units.deg,
                 data[7, k] * units.dB, data[8, k] * units.deg)
                 for k in range(length)]               
    	returnValue(data)

    @setting(617, 'Get S Parameters', S='*s', returns='*(*v[], *v[])')
    def get_s_parameters(self, c, S=['S43']):
    	"""
        Get a set of scattering parameters from the network analyzer. 
		The input parameter should be a list of strings in the format 
		['S21','S43','S34',...] where Smn is the S-parameter connecting 
		port n to port m. Available ports are 1, 2, 3, and 4. The data
		is returned as a list *[*Re(Sxy), *Im(Sxy)]. The values are
        unitless. To obtain the magnitude in dB use the following
        equation: 20 * log10(Re(Sxy)^2 + Im(Sxy)^2).
        """
        S = [x.capitalize() for x in S]
        # Remove duplicates.
        S = list(set(S))

        # Match to strings of format "Sxy" only.
        for Sp in S:
            if Sp not in ('S11', 'S12', 'S13', 'S14', 'S21', 'S22', 
                    'S23', 'S24', 'S31', 'S32', 'S33', 'S34', 'S41',
                    'S42', 'S43', 'S44'):
                raise ValueError('Illegal measurment definition: %s.'
                        %str(Sp))
                        
        dev = self.selectedDevice(c)
        # Delete all measurements on the PNA.
        yield dev.write('CALC:PAR:DEL:ALL')
        # Close window 1 if it already exists.
        if (yield dev.query('DISP:WIND1:STATE?')) == '1':
            dev.write('DISP:WIND1:STATE OFF')
        # Create window 1.
        yield dev.write('DISP:WIND1:STATE ON')
        for k, Sp in enumerate(S):
            yield dev.write('CALC:PAR:DEF:EXT "Rxy_%s",%s'
                    %(Sp, Sp))
            yield dev.write('DISP:WIND1:TRAC%d:FEED "Rxy_%s"'
                    %(2 * k + 1, Sp))
            yield dev.write('CALC:PAR:DEF:EXT "Ixy_%s",%s'
                    %(Sp, Sp))
            yield dev.write('DISP:WIND1:TRAC%d:FEED "Ixy_%s"'
                    %(2 * k + 2, Sp))
            yield dev.write('CALC:PAR:SEL "Rxy_%s"' %Sp)
            yield dev.write('CALC:FORM REAL')
            yield dev.write('CALC:PAR:SEL "Ixy_%s"' %Sp)
            yield dev.write('CALC:FORM IMAG')
            yield dev.write('SENS1:SWE:TIME:AUTO ON')
            yield dev.write('TRIG:SOUR IMM')
  
        yield dev.write('FORM ASC,0')
        
        for k in range(len(S)):
            yield dev.write('DISP:WIND1:TRAC%d:Y:AUTO'%(2 * k + 1))
            yield dev.write('DISP:WIND1:TRAC%d:Y:AUTO'%(2 * k + 2))

        avgMode = yield self.average_mode(c)
        if avgMode:
            avgCount = yield self.average_points(c)
            yield self.restart_averaging(c)
            yield dev.write('SENS:SWE:GRO:COUN %i' %avgCount)
            yield dev.write('ABORT;SENS:SWE:MODE GRO')
        else:
            # Stop the current sweep and immediately send a trigger. 
            yield dev.write('ABORT;SENS:SWE:MODE SING')

        # Wait for the measurement to finish.
        yield dev.query('*OPC?', timeout=24*units.h)

        data = []
        for Sp in S:
            yield dev.write('CALC:PAR:SEL "Rxy_%s"' %Sp)
            ascii_data = yield dev.query('CALC:DATA? FDATA')
            real = numpy.array([x for x in ascii_data.split(',')],
                dtype=float)
            yield dev.write('CALC:PAR:SEL "Ixy_%s"' %Sp)
            ascii_data = yield dev.query('CALC:DATA? FDATA')
            imag = numpy.array([x for x in ascii_data.split(',')],
            dtype=float)
            data.append([real, imag])
                  
        returnValue(data)		


__server__ = AgilentN5230AServer()


if __name__ == '__main__':
    from labrad import util
    util.runServer(__server__)