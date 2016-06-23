# Copyright (C) 2015, 2016 Guilhem Ribeill
#               2016 Ivan Pechenezhskiy
#				2016 Noah Meltzer
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

from labrad.gpib import GPIBManagedServer, GPIBDeviceWrapper
from labrad.server import setting
import labrad.units as units

from utilities import sleep

class AgilentN5230ADeviceWrapper(GPIBDeviceWrapper):

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
		yield dev.write('*CLS')
	
	@inlineCallbacks
	def preset(self):
		"""Preset the network analyzer."""
		yield self.initialize()
	
	@inlineCallbacks
	def power_output(self, pow):
		'''Turn output power on or off'''
		if pow is None:
			resp = yield dev.query('OUTP?')
			pow = bool(int(resp))
		else:
			if pow:
				yield dev.write('OUTP ON')
			else:
				yield dev.write('OUTP OFF')
		returnValue(pow)
	
	@inlineCallbacks
	def center_frequency(self, cfreq):
		'''Set or get the sweep center frequency.'''
		if cfreq is None:
			resp = yield self.query('SENS1:FREQ:CENT?')
			creq = float(resp)*units.Hz
		else:
			yield self.write('SENS1:FREQ:CENT %I'%cfeq['Hz'])
		returnValue(cfreq)
	
	@inlineCallbacks	
	def frequency_span(self, span):
		if span is None:	
			resp = yield dev.query('SENS1:FREQ:SPAN?')
			span = float(resp)*units.Hz
		else:
			yield dev.write('SENS1:FREQ:SPAN %i'%span['Hz'])
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
			resp = yield self.quey('SENS1:FREQ:STOP?')
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
	def source_power(self, pow):
		if pow is None:
			resp = yield self.query('SOUR:POW?')
			pow = float(resp) * units.dBm
		else:
			yield self.write('SOUR:POW1 %f' %pow['dBm'])
		returnValue(pow)
	
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
	def measurement_setup(self, meas):
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

	@inlineCallbacks
	def get_trace(self):
		"""Get the active trace from the network analyzer."""
		  
		meas = yield self.query('SYST:ACT:MEAS?')
		yield self.write('CALC:PAR:SEL %s' %meas)   
		yield self.write('FORM ASC,0')
		
		avgMode = yield self.average_mode(c)
		if avgMode:
			avgCount = yield self.average_points(c)
			yield self.restart_averaging(c)
			yield self.write('SENS:SWE:GRO:COUN %i' %avgCount)
			yield self.write('ABORT;SENS:SWE:MODE GRO')
		else:
			# Stop the current sweep and immediately send a trigger. 
			yield self.write('ABORT;SENS:SWE:MODE SING')

		# Wait for the measurement to finish.
		yield self.query('*OPC?', timeout=24*units.h)
		ascii_data = yield self.query('CALC1:DATA? FDATA')

		data = numpy.array([x for x in ascii_data.split(',')],
				dtype=float) * units.dB
		returnValue(data)

	@inlineCallbacks
	def get_s2p(self, ports):
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
				
		S = (''.join(['S', str(ports[0]), str(ports[0])]),
			 ''.join(['S', str(ports[0]), str(ports[1])]),
			 ''.join(['S', str(ports[1]), str(ports[0])]),
			 ''.join(['S', str(ports[1]), str(ports[1])]))
		# Delete all measurements on the PNA.
		yield self.write('CALC:PAR:DEL:ALL')
		# Close window 1 if it already exists.
		if (yield self.query('DISP:WIND1:STATE?')) == '1':
			self.write('DISP:WIND1:STATE OFF')
		# Create window 1.
		yield self.write('DISP:WIND1:STATE ON')
		for k in range(4):
			yield self.write('CALC:PAR:DEF:EXT "s2p_%s",%s'
					%(S[k], S[k]))
			yield self.write('DISP:WIND1:TRAC%d:FEED "s2p_%s"'
					%(k + 1, S[k]))
			yield self.write('CALC:PAR:SEL "s2p_%s"' %S[k])
			yield self.write('SENS1:SWE:TIME:AUTO ON')
			yield self.write('TRIG:SOUR IMM')
  
		yield self.write('FORM ASC,0')
		
		avgMode = yield self.average_mode(c)
		if avgMode:
			avgCount = yield self.average_points(c)
			yield self.restart_averaging(c)
			yield self.write('SENS:SWE:GRO:COUN %i' %avgCount)
			yield self.write('ABORT;SENS:SWE:MODE GRO')
		else:
			# Stop the current sweep and immediately send a trigger. 
			yield self.write('ABORT;SENS:SWE:MODE SING')

		# Wait for the measurement to finish.
		yield self.query('*OPC?', timeout=24*units.h)
		ascii_data = yield self.query("CALC:DATA:SNP:PORT? '%i,%i'"
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
	
	@inlineCallbacks
	def get_s_parameters(self, S):
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
						
		# Delete all measurements on the PNA.
		yield self.write('CALC:PAR:DEL:ALL')
		# Close window 1 if it already exists.
		if (yield self.query('DISP:WIND1:STATE?')) == '1':
			self.write('DISP:WIND1:STATE OFF')
		# Create window 1.
		yield self.write('DISP:WIND1:STATE ON')
		for k, Sp in enumerate(S):
			yield self.write('CALC:PAR:DEF:EXT "Rxy_%s",%s'
					%(Sp, Sp))
			yield self.write('DISP:WIND1:TRAC%d:FEED "Rxy_%s"'
					%(2 * k + 1, Sp))
			yield self.write('CALC:PAR:DEF:EXT "Ixy_%s",%s'
					%(Sp, Sp))
			yield self.write('DISP:WIND1:TRAC%d:FEED "Ixy_%s"'
					%(2 * k + 2, Sp))
			yield self.write('CALC:PAR:SEL "Rxy_%s"' %Sp)
			yield self.write('CALC:FORM REAL')
			yield self.write('CALC:PAR:SEL "Ixy_%s"' %Sp)
			yield self.write('CALC:FORM IMAG')
			yield self.write('SENS1:SWE:TIME:AUTO ON')
			yield self.write('TRIG:SOUR IMM')
  
		yield self.write('FORM ASC,0')
		
		for k in range(len(S)):
			yield self.write('DISP:WIND1:TRAC%d:Y:AUTO'%(2 * k + 1))
			yield self.write('DISP:WIND1:TRAC%d:Y:AUTO'%(2 * k + 2))

		avgMode = yield self.average_mode(c)
		if avgMode:
			avgCount = yield self.average_points(c)
			yield self.restart_averaging(c)
			yield self.write('SENS:SWE:GRO:COUN %i' %avgCount)
			yield self.write('ABORT;SENS:SWE:MODE GRO')
		else:
			# Stop the current sweep and immediately send a trigger. 
			yield self.write('ABORT;SENS:SWE:MODE SING')

		# Wait for the measurement to finish.
		yield self.query('*OPC?', timeout=24*units.h)

		data = []
		for Sp in S:
			yield self.write('CALC:PAR:SEL "Rxy_%s"' %Sp)
			ascii_data = yield self.query('CALC:DATA? FDATA')
			real = numpy.array([x for x in ascii_data.split(',')],
				dtype=float)
			yield self.write('CALC:PAR:SEL "Ixy_%s"' %Sp)
			ascii_data = yield self.query('CALC:DATA? FDATA')
			imag = numpy.array([x for x in ascii_data.split(',')],
			dtype=float)
			data.append([real, imag])
				  
		returnValue(data)
	
	def display_format(self, fmt):
		raise NotImplementedError

class Agilent8720ETDeviceWrapper(AgilentN5230ADeviceWrapper):
	# Override the N5320A's method
	@inlineCallbacks
	def initialize(self):
		p = self._packet()
		p.write('OPC?;PRES')
		yield p.send()
		
	def clear_status(self):
		raise NotImplementedError

	def power_output(self, pow):
		raise NotImplementedError
	
	def center_frequency(self, cfreq):
		raise NotImplementedError
		
	def frequency_span(self, span):
		raise NotImplementedError
		
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
	
	def if_bandwidth(self, bw):
		raise NotImplementedError
	
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
	def source_power(self, pow):
		"""Set or get the sweep power level."""
		if pow is None:
			resp = yield self.query('POWE?')
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
			yield self.write('POWE%iDB' %pow['dBm'])
		returnValue(pow)
	
	def get_sweep_time(self):
		raise NotImplementedError
	
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
			"LINMAG" - real [linear units];
			"PHASE"  - real [deg];
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
		if fmt == 'LOGMAG':
			returnValue(real.astype(float) * units.dB)
		elif fmt == 'LINMAG':
			returnValue(real.astype(float))
		elif fmt == 'PHASE':
			returnValue(real.astype(float) * units.deg)
		elif fmt == 'REIM':
			imag = numpy.hstack((raw[2:-1:2], raw[-1]))
			returnValue(real.astype(float) + 1j * imag.astype(float))
	
	@inlineCallbacks
	def measurement_setup(self, mode):
		"""
		Set or get the measurement mode: transmission or reflection. 
		
		Following options are allowed (could be in any letter case):
			"S11", "REFL", 'R', 'REFLECTION' for the reflection mode;
			"S21", "TRAN", 'T', 'TRANSMISSION', 'TRANS' for the
			transmission mode.
		
		Output is either 'S11' or 'S21'.
		"""
		if mode is None:
			resp = yield self.query('RFLP?')
			if bool(int(resp)):
				returnValue('S11')
			else:
				returnValue('S21')
		else:
			if mode.upper() in ('S11', 'R', 'REFL', 'REFLECTION'):
				yield self.write('RFLP')
				returnValue('S11')
			if mode.upper() in ('S21', 'T', 'TRAN', 'TRANS',
					'TRANSMISSION'):
				yield self.write('TRAP')
				returnValue('S21')
			else:
				raise ValueError('Unknown measurement mode: %s.' %mode)
	
	def get_s2p(self, ports):
		raise NotImplementedError

	@inlineCallbacks
	def display_format(self, fmt):
		"""
		Set or get the display format. Following options are allowed:
			"LOGMAG" - log magnitude display;
			"LINMAG" - linear magnitude display;
			"PHASE"  - phase display;
			"REIM"   - real and imaginary display.
		"""
		if fmt is None:
			resp = yield self.query('LOGM?')
			if bool(int(resp)):
				returnValue('LOGMAG')
			resp = yield self.query('LINM?')
			if bool(int(resp)):
				returnValue('LINMAG')
			resp = yield self.query('PHAS?')
			if bool(int(resp)):
				returnValue('PHASE')
			resp = yield self.query('POLA?')
			if bool(int(resp)):
				returnValue('REIM')
		else:
			if fmt.upper() == 'LOGMAG': 
				yield self.write('LOGM')
			elif fmt.upper() == 'LINMAG': 
				yield self.write('LINM')
			elif fmt.upper() == 'PHASE': 
				yield self.write('PHAS')
			elif fmt.upper() == 'REIM': 
				yield self.write('POLA')
			else:
				raise ValueError('Unknown display format request: %s.'
					%fmt)
		returnValue(fmt)


class vnaServer(GPIBManagedServer):
	name = 'GPIB VNA'
	deviceWrappers = {'AGILENT N5230':AgilentN5230ADeviceWrapper,
					'AGILENT 8720ET':Agilent8720ETDeviceWrapper}
	
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
	def start_frequency(self,c,start = None):
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
	
	@setting(1500, 'Measurement Setup', meas='s', returns='s')
	def measurement_setup(self, c, meas='S21'):
		dev = self.selectedDevice(c)
		resp  = yield dev.measurement_setup(meas)
		returnValue(resp)
	
	@setting(1600, 'Get Trace', returns=['*v[dB]', '*v', '*v[deg]', '*c'])
	def get_trace(self, c):
		dev = self.selectedDevice(c)
		resp  = yield dev.get_trace()
		returnValue(resp)

	@setting(1700, 'Get S2P', ports='(w, w)', returns=('*(v[Hz], '
		'v[dB], v[deg], v[dB], v[deg], v[dB], v[deg], v[dB], '
		'v[deg])'))
	def get_s2p(self, c, ports=(1, 2)):
		dev = self.selectedDevice(c)
		resp  = yield dev.get_s2p(ports)
		returnValue(resp)

	@setting(1800, 'Display Format', fmt='s', returns='s')
	def display_format(self, c, fmt=None):
		dev = self.selectedDevice(c)
		resp  = yield dev.display_format(fmt)
		returnValue(resp)

	
__server__ = vnaServer()

if __name__ == '__main__':
	from labrad  import util
	util.runServer(__server__)
	
	