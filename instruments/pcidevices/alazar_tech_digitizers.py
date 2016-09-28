# Copyright (C) 2016  Alexander Opremcak
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
name = ATS Waveform Digitizer
version = 1.1
description = Communicates with AlazarTech Digitizers over PCIe interface.

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
"""

from twisted.internet.defer import inlineCallbacks, returnValue
import atsapi as ats

from labrad.server import LabradServer, setting
from labrad.errors import Error
import labrad.units as units
from labrad import util
import numpy as np

import ctypes


TIMEOUT = 1 * units.s

  
class AlazarTechServer(LabradServer):
    deviceName = 'ATS Digitizer Server'
    name = 'ATS Digitizer Server'

    def initServer(self):
        print('Loading config info...')
        self.boardHandles = {}
        return self.findDevices()

    @setting(2, 'List Devices', returns='*s')
    def list_devices(self, c):
        """Return list of attenuator serial numbers."""
        return self.devs
    
    def findDevices(self):
        """Find available devices from list stored in the registry."""
        self.devs = []
        self.numSystems = ats.numOfSystems()
        if self.numSystems > 1:
            print "More than one board system is currently not supported."
        self.numBoardsInSystem = ats.boardsInSystemBySystemID(self.numSystems)
        print 'done.'
        for systemNum in range(1, self.numSystems+1):
            numBoardsInSystem = ats.boardsInSystemBySystemID(systemNum)
            for boardNum in range(1, numBoardsInSystem+1):
                    devName = 'ATS%d::%d' % (systemNum, boardNum)
                    self.boardHandles[devName] = \
                            ats.Board(systemId=systemNum, boardId=boardNum)
                    print "devName=", devName
                    self.devs += [devName]
        return(self.devs)
   
    @setting(3, 'Select Device', devName='s', returns='')
    def select_device(self, c, devName):
        """
        Select RF generator by its serial number. Since the serial 
        numbers are unique by definition, no extra information is 
        necessary to select a device.
        """
        if devName in self.devs:
            c['devName'] = devName
            c['demod_weights_dict'] = {}
            c['iq_buffers'] = {}
            c['records_per_buffer'] = 10
        else:
            print "Device not found"
            
    @setting(4, 'Set LED State', ledState='i', returns='')     
    def set_led_state(self, c, ledState):
        boardHandle = self.boardHandles[c['devName']]
        boardHandle.setLED(ledState)
        
    @setting(5, 'Set Capture Clock', SourceId='w', 
            SampleRateIdOrValue='w', EdgeId='w', Decimation='w', 
            returns='')     
    def set_capture_clock(self, c, SourceId, SampleRateIdOrValue, 
            EdgeId, Decimation):
        boardHandle = self.boardHandles[c['devName']]
        boardHandle.setCaptureClock(SourceId, SampleRateIdOrValue, EdgeId,
                Decimation)
       
    @setting(6, 'Input Control', ChannelId=['w', 's'], CouplingId=['w', 's'],
            RangeId=['w', 'v[mV]'], ImpedanceId='w', returns='')     
    def input_control(self, c, ChannelId, CouplingId, RangeId,
            ImpedanceId=ats.IMPEDANCE_50_OHM):
        boardHandle = self.boardHandles[c['devName']]
        
        if type(ChannelId) == str:
            if ChannelId.upper() == "A":
                ChannelId = ats.CHANNEL_A
            elif ChannelId.upper() == "B":
                ChannelId = ats.CHANNEL_B
            else: 
                raise Exception("Acceptable string values for "
                        + "ChannelId are 'A' and 'B'.")
                
        if type(CouplingId) == str:
            if CouplingId.upper() == "DC":
                CouplingId = ats.DC_COUPLING
            elif CouplingId.upper() == "AC":
                CouplingId = ats.AC_COUPLING
            else:
                raise Exception("Acceptable string values for "
                        + "CouplingId are 'DC' and 'AC'.")
                
        if type(RangeId) != long:
            if RangeId.units == "mV":
                if RangeId['mV'] == 4000:
                    RangeId = ats.INPUT_RANGE_PM_4_V
                elif RangeId['mV'] == 2000:
                    RangeId = ats.INPUT_RANGE_PM_2_V
                elif RangeId['mV'] == 1000:
                    RangeId = ats.INPUT_RANGE_PM_1_V
                elif RangeId['mV'] == 400:
                    RangeId = ats.INPUT_RANGE_PM_400_MV
                elif RangeId['mV'] == 200:
                    RangeId = ats.INPUT_RANGE_PM_200_MV
                elif RangeId['mV'] == 100:
                    RangeId = ats.INPUT_RANGE_PM_100_MV
                elif RangeId['mV'] == 40:
                    RangeId = ats.INPUT_RANGE_PM_40_MV
                else:
                    raise Exception("Invalid RangeId provided.")
                    
        boardHandle.inputControlEx(ChannelId, CouplingId, RangeId,
                ImpedanceId)

    @setting(7, 'Set BW Limit', ChannelId=['w', 's'], Flag='w', returns='')     
    def set_bw_limit(self, c, ChannelId, Flag):
        if type(ChannelId) == str:
            if ChannelId.upper() == "A":
                ChannelId = ats.CHANNEL_A
            elif ChannelId.upper() == "B":
                ChannelId = ats.CHANNEL_B
            else: 
                raise Exception("Acceptable string values for "
                        + "ChannelId are 'A' and 'B'.")
        boardHandle = self.boardHandles[c['devName']]
        boardHandle.setBWLimit(ChannelId, Flag)
        
    @setting(8, 'Set Trigger Operation', TriggerOperation='w', 
            TriggerEngineId1='w', SourceId1='w', 
            SlopeId1='w', Level1='w', 
            TriggerEngineId2='w', SourceId2='w', 
            SlopeId2='w', Level2='w',  returns='')     
    def set_trigger_operation(self, c, TriggerOperation='w', 
            TriggerEngineId1='w', SourceId1='w', 
            SlopeId1='w', Level1='w', 
            TriggerEngineId2='w', SourceId2='w', 
            SlopeId2='w', Level2='w'):
        boardHandle = self.boardHandles[c['devName']]
        boardHandle.setTriggerOperation(TriggerOperation,
                TriggerEngineId1, SourceId1, SlopeId1, Level1,
                TriggerEngineId2, SourceId2, SlopeId2, Level2)
   
    @setting(9, 'Set External Trigger', CouplingId='w', RangeId='w',
            returns='')     
    def set_external_trigger(self, c, CouplingId, RangeId):
        boardHandle = self.boardHandles[c['devName']]
        boardHandle.setExternalTrigger(CouplingId, RangeId)

    @setting(10, 'Set Trigger Delay', Value='w', returns='')     
    def set_trigger_delay(self, c, Value):
        boardHandle = self.boardHandles[c['devName']]
        boardHandle.setTriggerDelay(Value)

    @setting(11, 'Set Trigger Time Out', TimeoutTicks='w',
            returns='')     
    def set_trigger_time_out(self, c, TimeoutTicks):
        boardHandle = self.boardHandles[c['devName']]
        boardHandle.setTriggerTimeOut(TimeoutTicks)
   
    @setting(12, 'Set Record Size', PreTriggerSamples='w',
            PostTriggerSamples='w', returns='')     
    def set_record_size(self, c, PreTriggerSamples, PostTriggerSamples):
        boardHandle = self.boardHandles[c['devName']]
        boardHandle.setRecordSize(PreTriggerSamples,
                PostTriggerSamples)
 
    @setting(13, 'Set Record Count', RecordsPerCapture='w', returns='')     
    def set_record_count(self, c, RecordsPerCapture):
        boardHandle = self.boardHandles[c['devName']]
        boardHandle.setRecordCount(RecordsPerCapture)
 
    @setting(14, 'Get Channel Info', returns='*w')     
    def get_channel_info(self, c):
        boardHandle = self.boardHandles[c['devName']]
        memorySize_samples, bitsPerSample = boardHandle.getChannelInfo()
        return [memorySize_samples.value, bitsPerSample.value]

    @setting(15, 'Start Capture', returns='')     
    def start_capture(self, c):
        boardHandle = self.boardHandles[c['devName']]
        boardHandle.startCapture()
        
    @setting(16, 'Abort Capture', returns='')     
    def abort_capture(self, c):
        boardHandle = self.boardHandles[c['devName']]
        boardHandle.abortCapture()
        
    @setting(17, 'Busy', returns='')     
    def busy(self, c):
        boardHandle = self.boardHandles[c['devName']]
        busyState = boardHandle.busy()
        return busyState
        
    @setting(18, 'Set Records Per Buffer', records_per_buffer='w', returns='')     
    def set_records_per_buffer(self, c, records_per_buffer):
        c['records_per_buffer'] = records_per_buffer
        
    @setting(19, 'Get Records Per Buffer', returns='w')     
    def get_records_per_buffer(self, c):
        records_per_buffer = c['records_per_buffer']
        return records_per_buffer

    @setting(50, 'Configure External Clocking', returns='')     
    def configure_external_clocking(self, c):
        #assumes 10 MHz Reference clock and a sampling rate of 1 GS/s
        c['samplingRate'] = 1000000000
        self.set_capture_clock(c, ats.EXTERNAL_CLOCK_10MHz_REF,
                1000000000,
                ats.CLOCK_EDGE_RISING,
                1)
 
    @setting(51, 'Congfigure Inputs', RangeId=['w', 'v[mV]'], CouplingId=['w', 's'], returns='')     
    def congfigure_inputs(self, c, RangeId, CouplingId="DC"):
        chanIDs = ["A", "B"] #treated identically
        for chanID in chanIDs:
            #Both channels DC coupled by default
            self.input_control(c, chanID,
                    CouplingId,
                    RangeId)
            #0 ==> Full Input Bandwidth, 1 ==> 20 MHz input bandwidth
            self.set_bw_limit(c, chanID, 0) 
        c['input_range_mv'] = RangeId['mV']
        
    @setting(52, 'Set Trigger', triggerDelay='w', returns='')     
    def set_trigger(self, c, triggerDelay):
        trigLevel = 150 # do something about this such that voltage is acceptable
        self.set_trigger_operation(c, ats.TRIG_ENGINE_OP_J,
                ats.TRIG_ENGINE_J,
                ats.TRIG_EXTERNAL,
                ats.TRIGGER_SLOPE_POSITIVE,
                150,
                ats.TRIG_ENGINE_K,
                ats.TRIG_DISABLE,
                ats.TRIGGER_SLOPE_POSITIVE,
                128)
                                  
        self.set_external_trigger(c, ats.DC_COUPLING,
                ats.ETR_5V)                  
        self.set_trigger_delay(c, triggerDelay)
        self.set_trigger_time_out(c, 0)
       
    @setting(53, 'Configure Buffers', samples_per_record='w', number_of_records='w', returns='')
    def configure_buffers(self, c, samples_per_record, number_of_records):
        boardHandle = self.boardHandles[c['devName']]
        
        if samples_per_record < 256:
            raise Exception("ATS9870 digitizers require a minimum "
                    +"of 256 samples per record.")
        else:
            samples_above_required_min = samples_per_record - 256
            if samples_above_required_min%64!=0:
                recommendedMin = 256 + math.floor(float(samples_above_required_min)/64.0)*64
                recommendedMax = 256 + math.ceil(float(samples_above_required_min)/64.0)*64
                raise Exception("ATS9870 digitizers require the "
                        + "number of sample per record to be of "
                        + "the form: 256 + 64*n where "
                        + "n = {0, 1, 2, ...}. The closest two "
                        + "numbers of samples per record are: "
                        + str(recommendedMin) +" and " 
                        + str(recommendedMax)+".")

        # TODO: Select the number of records per DMA buffer.
        #should be chosen such that 1 MB < bytes_per_buffer < 64 MB
        #records_per_buffer = 10 
        records_per_buffer = c['records_per_buffer']
        c['samples_per_record'] = samples_per_record
        c['number_of_records'] = number_of_records
        
        

        
        if number_of_records < records_per_buffer or number_of_records%records_per_buffer!=0:
            raise Exception("The number of records must be a positive "
                    + "integer multiple of records per buffer.")

        # TODO: Select the number of buffers per acquisition.
        buffers_per_acquisition = number_of_records/records_per_buffer
        c['buffers_per_acquisition'] = buffers_per_acquisition
        
        # # TODO: Select the active channels.
        channels = ats.CHANNEL_A | ats.CHANNEL_B
        channel_count = 0

        for ch in ats.channels:
            channel_count += (ch & channels == ch)
            

        
        # Compute the number of bytes per record and per buffer
        chan_info = self.get_channel_info(c)
        memorySize_samples = chan_info[0]
        bits_per_sample = chan_info[1]
        c['bits_per_sample'] = bits_per_sample
        bytes_per_sample = (bits_per_sample + 7) // 8
        
        bytes_per_record = bytes_per_sample * samples_per_record
        bytes_per_buffer = bytes_per_record * records_per_buffer * channel_count

        # TODO: Select number of DMA buffers to allocate
        buffer_count = 4

        # Allocate DMA buffers
        sample_type = ctypes.c_uint8
        if bytes_per_sample > 1:
            sample_type = ctypes.c_uint16
            
        c['buffers'] = []
        #buffers = []
        for i in range(buffer_count):
            c['buffers'].append(ats.DMABuffer(sample_type, bytes_per_buffer))
        
        # Set the record size
        pre_trigger_samples = 0 
        self.set_record_size(c, pre_trigger_samples, samples_per_record)
        
        #Configure the board to make an NPT AutoDMA acquisition
        boardHandle.beforeAsyncRead(channels,
                -pre_trigger_samples,
                samples_per_record,
                records_per_buffer,
                number_of_records,
                ats.ADMA_EXTERNAL_STARTCAPTURE | ats.ADMA_NPT)
        
        #Post DMA buffers to board
        for buffer in c['buffers']:
            boardHandle.postAsyncBuffer(buffer.addr, buffer.size_bytes)
            
        #must allocate these first otherwise takes up too much time during aquisition
        # c['ch_a_buffer'] = np.zeros((number_of_records, samples_per_record), dtype=np.uint8)
        # c['ch_b_buffer'] = np.zeros((number_of_records, samples_per_record), dtype=np.uint8)
        c['records_buffer'] = np.zeros(2*number_of_records*samples_per_record, dtype=np.uint8)
        
    
    @setting(54, 'Add Demod Weights', chA_weight='*v', chB_weight='*v', demod_name ='s',  returns='')     
    def add_demod_weights(self, c, chA_weight, chB_weight, demod_name):
        samples_per_record = c['samples_per_record']
        number_of_records = c['number_of_records']
        num_channels = 2
        if len(chA_weight) != samples_per_record or len(chB_weight) != samples_per_record:
            raise Exception("The chA_weight and chB_weight arrays "
                    +"must have a length which matches the number "
                    +"of samples per record, namely " + str(samples_per_record))
        else:
            c['demod_weights_dict'][demod_name] = [chA_weight, chB_weight]
            c['iq_buffers'][demod_name] = np.zeros((number_of_records, num_channels))
 
    @setting(55, 'Acquire Data', returns='')
    def acquire_data(self, c):
        boardHandle = self.boardHandles[c['devName']]

        buffers_completed = 0
        bytes_transferred = 0

        records_per_buffer = c['records_per_buffer']
        samples_per_record = c['samples_per_record']
        
        records_buffer = c['records_buffer'] 

        boardHandle.startCapture() 
        while (buffers_completed < c['buffers_per_acquisition']):

            buffer = c['buffers'][buffers_completed % len(c['buffers'])]
            boardHandle.waitAsyncBufferComplete(buffer.addr, timeout_ms=5000)
            boardHandle.postAsyncBuffer(buffer.addr, buffer.size_bytes) 
            records_buffer[2*records_per_buffer*samples_per_record*buffers_completed:2*records_per_buffer*samples_per_record*(buffers_completed+1)] = \
                    buffer.buffer

            buffers_completed += 1
        boardHandle.abortAsyncRead()
        
    @setting(56, 'Get Records', returns='?')     
    def get_records(self, c):
        records_buffer = c['records_buffer'] 
        samples_per_record = c['samples_per_record']
        number_of_records = c['number_of_records']
        v_full_scale = float(c['input_range_mv'])/1e3 #convert to volts
        bits_per_sample = c['bits_per_sample']
        num_channels = 2
        dV = 2*v_full_scale/((2**bits_per_sample)-1)
        #Note that Fortran style indexing is used on 2nd reshaping
        time_series = records_buffer.reshape((num_channels*number_of_records, 
                                              samples_per_record)).\
                                    reshape((number_of_records,
                                              num_channels,
                                              samples_per_record), order="F")
        #0==> -VFullScale, 2^(N-1) == > ~0, (2**N)-1 = +VFullScale
        time_series = -v_full_scale + time_series * dV
        return time_series
        
    @setting(57, 'Get IQS', demod_name = 's', returns='?')     
    def get_iqs(self, c, demod_name):
        records_buffer = c['records_buffer'] 
        samples_per_record = c['samples_per_record']
        number_of_records = c['number_of_records']
        v_full_scale = float(c['input_range_mv'])/1e3 #convert to volts
        bits_per_sample = c['bits_per_sample']
        num_channels = 2 #think about how to do this in multi-channel case
        dV = 2*v_full_scale/((2**bits_per_sample)-1)
        records_per_buffer = c['records_per_buffer']
        num_records = (len(records_buffer)/samples_per_record)/2
        num_buffers = num_records/records_per_buffer
        samples_per_buffer = samples_per_record * records_per_buffer
       
        wA = c['demod_weights_dict'][demod_name][0]
        wB = c['demod_weights_dict'][demod_name][1]
        iq_buffer = c['iq_buffers'][demod_name]
        for ii in range(0, num_buffers):
            #Note that Fortran style indexing is used on 2nd reshaping
            time_series_chunk = records_buffer.reshape((num_channels*number_of_records, 
                                              samples_per_record)).\
                                    reshape((number_of_records,
                                              num_channels,
                                              samples_per_record), order="F")[ii*records_per_buffer:(ii+1)*records_per_buffer]
            time_series_chunk = -v_full_scale + time_series_chunk * dV
            #demod array shaped like [[I1,Q1], [I2,Q2], ..., [Im, Qm]] where m = num recs per buf
            iq_buffer[ii*records_per_buffer:(ii+1)*records_per_buffer] = self.demodulate_buffered_data(wA, wB, time_series_chunk) 
            
        return iq_buffer
        
    def demodulate_buffered_data(self, wA, wB, time_series_chunk):
        demod_vals = []
        for ii in range(0, len(time_series_chunk)):
            vA = time_series_chunk[ii][0]
            vB = time_series_chunk[ii][1]
            I = np.mean(wA*vA - wB*vB) #check that these are legit
            Q = np.mean(wA*vA + wB*vB) #check that these are legit
            demod_vals.append([I,Q])
        return np.asarray(demod_vals)
            
__server__ = AlazarTechServer()

if __name__ == '__main__':
    util.runServer(__server__)