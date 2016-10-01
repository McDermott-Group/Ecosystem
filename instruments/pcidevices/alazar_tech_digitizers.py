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

#This file uses lowerCamelCase for compatibility with 
#ATS provided coding examples and atsapi library. 

from twisted.internet.defer import inlineCallbacks, returnValue
import atsapi as ats
import numpy as np
import ctypes

from labrad.server import LabradServer, setting
from labrad.errors import Error
import labrad.units as units
from labrad import util


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
        """Return list of ATS digitizer boards."""
        return self.devs
    
    def findDevices(self):
        """Find available devices from ..."""
        self.devs = []
        self.numSystems = ats.numOfSystems()
        if self.numSystems > 1:
            print("More than one board system is currently not supported.")
        self.numBoardsInSystem = ats.boardsInSystemBySystemID(self.numSystems)
        for systemNum in range(1, self.numSystems+1):
            numBoardsInSystem = ats.boardsInSystemBySystemID(systemNum)
            for boardNum in range(1, numBoardsInSystem+1):
                    devName = 'ATS%d::%d' % (systemNum, boardNum)
                    self.boardHandles[devName] = \
                            ats.Board(systemId=systemNum, boardId=boardNum)
                    self.devs += [devName]
        return(self.devs)
   
    @setting(3, 'Select Device', devName='s', returns='')
    def select_device(self, c, devName):
        """"""
        if devName in self.devs:
            c['devName'] = devName
            c['demodWeightsDict'] = {}
            c['iqBuffers'] = {}
            c['recordsPerBuffer'] = 10
        else:
            print("Device " + devName + " was not found.")
            
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
        boardHandle.setCaptureClock(SourceId, SampleRateIdOrValue,
                EdgeId, Decimation)
       
    @setting(6, 'Input Control', ChannelId=['w', 's'],
            couplingID=['w', 's'], rangeID=['w', 'v[mV]'],
            ImpedanceId='w', returns='')
    def input_control(self, c, ChannelId, couplingID, rangeID,
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
                
        if type(couplingID) == str:
            if couplingID.upper() == "DC":
                couplingID = ats.DC_COUPLING
            elif couplingID.upper() == "AC":
                couplingID = ats.AC_COUPLING
            else:
                raise Exception("Acceptable string values for "
                        + "couplingID are 'DC' and 'AC'.")
                
        if type(rangeID) != long:
            if rangeID.units == "mV":
                if rangeID['mV'] == 4000:
                    rangeID = ats.INPUT_RANGE_PM_4_V
                elif rangeID['mV'] == 2000:
                    rangeID = ats.INPUT_RANGE_PM_2_V
                elif rangeID['mV'] == 1000:
                    rangeID = ats.INPUT_RANGE_PM_1_V
                elif rangeID['mV'] == 400:
                    rangeID = ats.INPUT_RANGE_PM_400_MV
                elif rangeID['mV'] == 200:
                    rangeID = ats.INPUT_RANGE_PM_200_MV
                elif rangeID['mV'] == 100:
                    rangeID = ats.INPUT_RANGE_PM_100_MV
                elif rangeID['mV'] == 40:
                    rangeID = ats.INPUT_RANGE_PM_40_MV
                else:
                    raise Exception("Invalid rangeID provided.")

        boardHandle.inputControlEx(ChannelId, couplingID, rangeID,
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
    def set_trigger_operation(self, c, TriggerOperation, 
            TriggerEngineId1, SourceId1, SlopeId1, Level1, 
            TriggerEngineId2, SourceId2, SlopeId2, Level2):
        boardHandle = self.boardHandles[c['devName']]
        boardHandle.setTriggerOperation(TriggerOperation,
                TriggerEngineId1, SourceId1, SlopeId1, Level1,
                TriggerEngineId2, SourceId2, SlopeId2, Level2)
   
    @setting(9, 'Set External Trigger', couplingID='w', rangeID='w',
            returns='')
    def set_external_trigger(self, c, couplingID, rangeID):
        boardHandle = self.boardHandles[c['devName']]
        boardHandle.setExternalTrigger(couplingID, rangeID)

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
        
    @setting(18, 'Set Records Per Buffer', recordsPerBuffer='w',
            returns='')
    def set_recordsPerBuffer(self, c, recordsPerBuffer):
        c['recordsPerBuffer'] = recordsPerBuffer
        
    @setting(19, 'Get Records Per Buffer', returns='w')
    def get_recordsPerBuffer(self, c):
        recordsPerBuffer = c['recordsPerBuffer']
        return recordsPerBuffer

    @setting(50, 'Configure External Clocking', returns='')
    def configure_external_clocking(self, c):
        #assumes 10 MHz Reference clock and a sampling rate of 1 GS/s
        c['samplingRate'] = 1000000000
        self.set_capture_clock(c, ats.EXTERNAL_CLOCK_10MHz_REF,
                c['samplingRate'], ats.CLOCK_EDGE_RISING, 1)
 
    @setting(51, 'Congfigure Inputs', rangeID=['w', 'v[mV]'],
            couplingID=['w', 's'], returns='')
    def congfigure_inputs(self, c, rangeID, couplingID="DC"):
        chanIDs = ["A", "B"] #treated identically
        for chanID in chanIDs:
            #Both channels DC coupled by default
            self.input_control(c, chanID, couplingID, rangeID)
            #0 ==> Full Input Bandwidth, 1 ==> 20 MHz input bandwidth
            self.set_bw_limit(c, chanID, 0) 
        c['input_range_mv'] = rangeID['mV']
        
    @setting(52, 'Set Trigger', triggerDelay='w', returns='')
    def set_trigger(self, c, triggerDelay):
        trigLevel = 150 # do something about this such that voltage is acceptable
        self.set_trigger_operation(c,
                ats.TRIG_ENGINE_OP_J,
                ats.TRIG_ENGINE_J,
                ats.TRIG_EXTERNAL,
                ats.TRIGGER_SLOPE_POSITIVE,
                150,
                ats.TRIG_ENGINE_K,
                ats.TRIG_DISABLE,
                ats.TRIGGER_SLOPE_POSITIVE,
                128)
                                  
        self.set_external_trigger(c, ats.DC_COUPLING, ats.ETR_5V)                  
        self.set_trigger_delay(c, triggerDelay)
        self.set_trigger_time_out(c, 0)
       
    @setting(53, 'Configure Buffers', samplesPerRecord='w',
            numberOfRecords='w', returns='')
    def configure_buffers(self, c, samplesPerRecord, numberOfRecords):
        boardHandle = self.boardHandles[c['devName']]
        
        if samplesPerRecord < 256:
            raise Exception("ATS9870 digitizers require a minimum "
                    +"of 256 samples per record.")
        else:
            samples_above_required_min = samplesPerRecord - 256
            if samples_above_required_min%64!=0:
                div64 = float(samples_above_required_min) / 64.0
                recommendedMin = 256 + 64 * np.floor(div64)
                recommendedMax = 256 + 64 * np.ceil(div64)
                raise Exception("ATS9870 digitizers require the "
                        "number of sample per record to be of "
                        "the form: 256 + 64*n where "
                        "n = {0, 1, 2, ...}. The closest two "
                        "numbers of samples per record are: "
                        str(recommendedMin) + " and " 
                        str(recommendedMax) + ".")

        # TODO: Select the number of records per DMA buffer.
        #should be chosen such that 1 MB < bytes_per_buffer < 64 MB
        #recordsPerBuffer = 10 
        recordsPerBuffer = c['recordsPerBuffer']
        c['samplesPerRecord'] = samplesPerRecord
        c['numberOfRecords'] = numberOfRecords
        
        if numberOfRecords < recordsPerBuffer or numberOfRecords%recordsPerBuffer!=0:
            raise Exception("The number of records must be a positive "
                    + "integer multiple of records per buffer.")

        # TODO: Select the number of buffers per acquisition.
        buffers_per_acquisition = numberOfRecords/recordsPerBuffer
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
        
        bytes_per_record = bytes_per_sample * samplesPerRecord
        bytes_per_buffer = bytes_per_record * recordsPerBuffer * channel_count

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
        self.set_record_size(c, pre_trigger_samples, samplesPerRecord)
        
        #Configure the board to make an NPT AutoDMA acquisition
        boardHandle.beforeAsyncRead(channels,
                -pre_trigger_samples,
                samplesPerRecord,
                recordsPerBuffer,
                numberOfRecords,
                ats.ADMA_EXTERNAL_STARTCAPTURE | ats.ADMA_NPT)
        
        #Post DMA buffers to board
        for buffer in c['buffers']:
            boardHandle.postAsyncBuffer(buffer.addr, buffer.size_bytes)
            
        #must allocate these first otherwise takes up too much time during acquisition
        c['records_buffer'] = np.zeros(2*numberOfRecords*samplesPerRecord, dtype=np.uint8)

    @setting(54, 'Add Demod Weights', chA_weight='*v', chB_weight='*v', demod_name ='s',  returns='')
    def add_demod_weights(self, c, chA_weight, chB_weight, demod_name):
        samplesPerRecord = c['samplesPerRecord']
        numberOfRecords = c['numberOfRecords']
        num_channels = 2
        if len(chA_weight) != samplesPerRecord or len(chB_weight) != samplesPerRecord:
            raise Exception("The chA_weight and chB_weight arrays "
                    +"must have a length which matches the number "
                    +"of samples per record, namely " + str(samplesPerRecord))
        else:
            c['demodWeightsDict'][demod_name] = [chA_weight, chB_weight]
            c['iqBuffers'][demod_name] = np.zeros((numberOfRecords, num_channels))
 
    @setting(55, 'Acquire Data', returns='')
    def acquire_data(self, c):
        boardHandle = self.boardHandles[c['devName']]

        buffersCompleted = 0
        bytes_transferred = 0

        recordsPerBuffer = c['recordsPerBuffer']
        samplesPerRecord = c['samplesPerRecord']
        
        records_buffer = c['records_buffer'] 
        
        bufferSize = 2 * recordsPerBuffer * samplesPerRecord

        boardHandle.startCapture() 
        while (buffersCompleted < c['buffers_per_acquisition']):
            buffer = c['buffers'][buffersCompleted % len(c['buffers'])]
            boardHandle.waitAsyncBufferComplete(buffer.addr, timeout_ms=5000)
            boardHandle.postAsyncBuffer(buffer.addr, buffer.size_bytes) 
            bufferPosition = bufferSize * buffersCompleted
            records_buffer[bufferPosition:bufferPosition + bufferSize] = \
                    buffer.buffer
            buffersCompleted += 1
        boardHandle.abortAsyncRead()
        
    @setting(56, 'Get Records', returns='?')
    def get_records(self, c):
        records_buffer = c['records_buffer'] 
        samplesPerRecord = c['samplesPerRecord']
        numberOfRecords = c['numberOfRecords']
        v_full_scale = float(c['input_range_mv'])/1e3 #convert to volts
        bits_per_sample = c['bits_per_sample']
        num_channels = 2
        dV = 2 * v_full_scale / ((2**bits_per_sample) - 1)
        #Note that Fortran style indexing is used on 2nd reshaping
        time_series = records_buffer.reshape((num_channels*numberOfRecords, 
                                              samplesPerRecord)).\
                                     reshape((numberOfRecords,
                                              num_channels,
                                              samplesPerRecord), order="F")
        #0 ==> -VFullScale, 2^(N-1) ==> ~0, (2**N)-1 ==> +VFullScale
        time_series = -v_full_scale + time_series * dV
        return time_series
        
    @setting(57, 'Get IQS', demod_name = 's', returns='?')
    def get_iqs(self, c, demod_name):
        records_buffer = c['records_buffer'] 
        samplesPerRecord = c['samplesPerRecord']
        numberOfRecords = c['numberOfRecords']
        
        v_full_scale = float(c['input_range_mv'])/1e3 #convert to volts
        bits_per_sample = c['bits_per_sample']
        num_channels = 2 #think about how to do this in multi-channel case
        dV = 2*v_full_scale/((2**bits_per_sample)-1)
        
        recordsPerBuffer = c['recordsPerBuffer']
        num_records = (len(records_buffer)/samplesPerRecord)/2
        num_buffers = num_records/recordsPerBuffer
        samples_per_buffer = samplesPerRecord * recordsPerBuffer
       
        wA = c['demodWeightsDict'][demod_name][0]
        wB = c['demodWeightsDict'][demod_name][1]
        iq_buffer = c['iqBuffers'][demod_name]
        for ii in range(0, num_buffers):
            #Note that Fortran style indexing is used on 2nd reshaping
            time_series_chunk = records_buffer.reshape((num_channels*numberOfRecords, 
                                              samplesPerRecord)).\
                                    reshape((numberOfRecords,
                                              num_channels,
                                              samplesPerRecord), order="F")[ii*recordsPerBuffer:(ii+1)*recordsPerBuffer]
            time_series_chunk = -v_full_scale + time_series_chunk * dV
            #demod array shaped like [[I1,Q1], [I2,Q2], ..., [Im, Qm]] where m = num recs per buf
            iq_buffer[ii*recordsPerBuffer:(ii+1)*recordsPerBuffer] = self.demodulate_buffered_data(wA, wB, time_series_chunk) 
            
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