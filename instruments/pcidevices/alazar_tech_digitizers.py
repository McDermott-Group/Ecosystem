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
#LabRAD settings use underscores for self consistency
#with our servers.

from twisted.internet.defer import inlineCallbacks, returnvalue
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
        
    @setting(5, 'Set Capture Clock', sourceID='w', 
            sampleRateIdOrvalue='w', edgeID='w', decimation='w', 
            returns='')
    def set_capture_clock(self, c, sourceID, sampleRateIdOrvalue, 
            edgeID, decimation):
        boardHandle = self.boardHandles[c['devName']]
        boardHandle.setCaptureClock(sourceID, sampleRateIdOrvalue,
                edgeID, decimation)
       
    @setting(6, 'Input Control', channelID=['w', 's'],
            couplingID=['w', 's'], rangeID=['w', 'v[mV]'],
            impedanceID='w', returns='')
    def input_control(self, c, channelID, couplingID, rangeID,
            impedanceID=ats.IMPEDANCE_50_OHM):
        boardHandle = self.boardHandles[c['devName']]
        
        if type(channelID) == str:
            if channelID.upper() == "A":
                channelID = ats.CHANNEL_A
            elif channelID.upper() == "B":
                channelID = ats.CHANNEL_B
            else: 
                raise Exception("Acceptable string values for "
                        + "channelID are 'A' and 'B'.")
                
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

        boardHandle.inputControlEx(channelID, couplingID, rangeID,
                impedanceID)

    @setting(7, 'Set BW Limit', channelID=['w', 's'], flag='w', returns='')
    def set_bw_limit(self, c, channelID, flag):
        if type(channelID) == str:
            if channelID.upper() == "A":
                channelID = ats.CHANNEL_A
            elif channelID.upper() == "B":
                channelID = ats.CHANNEL_B
            else: 
                raise Exception("Acceptable string values for "
                        + "channelID are 'A' and 'B'.")
        boardHandle = self.boardHandles[c['devName']]
        boardHandle.setBWLimit(channelID, flag)
        
    @setting(8, 'Set Trigger Operation', triggerOperation='w', 
            triggerEngineID1='w', sourceID1='w', 
            slopeID1='w', level1='w', 
            triggerEngineID2='w', sourceID2='w', 
            slopeID2='w', level2='w',  returns='')
    def set_trigger_operation(self, c, triggerOperation, 
            triggerEngineID1, sourceID1, slopeID1, level1, 
            triggerEngineID2, sourceID2, slopeID2, level2):
        boardHandle = self.boardHandles[c['devName']]
        boardHandle.settriggerOperation(triggerOperation,
                triggerEngineID1, sourceID1, slopeID1, level1,
                triggerEngineID2, sourceID2, slopeID2, level2)
   
    @setting(9, 'Set External Trigger', couplingID='w', rangeID='w',
            returns='')
    def set_external_trigger(self, c, couplingID, rangeID):
        boardHandle = self.boardHandles[c['devName']]
        boardHandle.setExternalTrigger(couplingID, rangeID)

    @setting(10, 'Set Trigger Delay', value='w', returns='')
    def set_trigger_delay(self, c, value):
        boardHandle = self.boardHandles[c['devName']]
        boardHandle.setTriggerDelay(value)

    @setting(11, 'Set Trigger Time Out', timeoutTicks='w',
            returns='')     
    def set_trigger_time_out(self, c, timeoutTicks):
        boardHandle = self.boardHandles[c['devName']]
        boardHandle.setTriggerTimeOut(timeoutTicks)
   
    @setting(12, 'Set Record Size', preTriggerSamples='w',
            postTriggerSamples='w', returns='')
    def set_record_size(self, c, preTriggerSamples, postTriggerSamples):
        boardHandle = self.boardHandles[c['devName']]
        boardHandle.setRecordSize(preTriggerSamples,
                postTriggerSamples)
 
    @setting(13, 'Set Record Count', recordsPerCapture='w', returns='')
    def set_record_count(self, c, recordsPerCapture):
        boardHandle = self.boardHandles[c['devName']]
        boardHandle.setRecordCount(recordsPerCapture)
 
    @setting(14, 'Get Channel Info', returns='*w')
    def get_channel_info(self, c):
        boardHandle = self.boardHandles[c['devName']]
        memorySizeInSamplesPerChannel, bitsPerSample = boardHandle.getChannelInfo()
        return [memorySizeInSamplesPerChannel.value, bitsPerSample.value]

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
    def set_records_per_buffer(self, c, recordsPerBuffer):
        c['recordsPerBuffer'] = recordsPerBuffer
        
    @setting(19, 'Get Records Per Buffer', returns='w')
    def get_records_per_buffer(self, c):
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
            samplesAboveRequiredMin = samplesPerRecord - 256
            if samplesAboveRequiredMin%64!=0:
                div64 = float(samplesAboveRequiredMin) / 64.0
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
        #should be chosen such that 1 MB < bytesPerBuffer < 64 MB
        #recordsPerBuffer = 10 
        recordsPerBuffer = c['recordsPerBuffer']
        c['samplesPerRecord'] = samplesPerRecord
        c['numberOfRecords'] = numberOfRecords
        
        if numberOfRecords < recordsPerBuffer or numberOfRecords%recordsPerBuffer!=0:
            raise Exception("The number of records must be a positive "
                    + "integer multiple of records per buffer.")

        # TODO: Select the number of buffers per acquisition.
        buffersPerAcquisition = numberOfRecords/recordsPerBuffer
        c['buffersPerAcquisition'] = buffersPerAcquisition
        
        # # TODO: Select the active channels.
        channels = ats.CHANNEL_A | ats.CHANNEL_B
        channelCount = 0

        for ch in ats.channels:
            channelCount += (ch & channels == ch)

        # Compute the number of bytes per record and per buffer
        chan_info = self.get_channel_info(c)
        #memorySizeInSamplesPerChannel = chan_info[0]
        bitsPerSample = chan_info[1]
        c['bitsPerSample'] = bitsPerSample
        bytesPerSample = (bitsPerSample + 7) // 8
        
        bytesPerRecord = bytesPerSample * samplesPerRecord
        bytesPerBuffer = bytesPerRecord * recordsPerBuffer * channelCount

        # TODO: Select number of DMA buffers to allocate
        bufferCount = 4

        # Allocate DMA buffers
        sampleType = ctypes.c_uint8
        if bytesPerSample > 1:
            sampleType = ctypes.c_uint16
            
        c['buffers'] = []
        #buffers = []
        for i in range(bufferCount):
            c['buffers'].append(ats.DMABuffer(sampleType, bytesPerBuffer))
        
        #Current implementation is NPT Mode = No Pre Trigger Samples 
        preTriggerSamples = 0 
        self.set_record_size(c, preTriggerSamples, samplesPerRecord)
        
        #Configure the board to make an NPT AutoDMA acquisition
        boardHandle.beforeAsyncRead(channels,
                -preTriggerSamples,
                samplesPerRecord,
                recordsPerBuffer,
                numberOfRecords,
                ats.ADMA_EXTERNAL_STARTCAPTURE | ats.ADMA_NPT)
        
        #Post DMA buffers to board
        for buffer in c['buffers']:
            boardHandle.postAsyncBuffer(buffer.addr, buffer.size_bytes)
            
        #must allocate these first otherwise takes up too much time during acquisition
        c['recordsBuffer'] = np.zeros(2*numberOfRecords*samplesPerRecord, dtype=np.uint8)

    @setting(54, 'Add Demod Weights', chA_weight='*v', chB_weight='*v', demodName ='s',  returns='')
    def add_demod_weights(self, c, chA_weight, chB_weight, demodName):
        samplesPerRecord = c['samplesPerRecord']
        numberOfRecords = c['numberOfRecords']
        numChannels = 2
        if len(chA_weight) != samplesPerRecord or len(chB_weight) != samplesPerRecord:
            raise Exception("The chA_weight and chB_weight arrays "
                    +"must have a length which matches the number "
                    +"of samples per record, namely " + str(samplesPerRecord))
        else:
            c['demodWeightsDict'][demodName] = [chA_weight, chB_weight]
            c['iqBuffers'][demodName] = np.zeros((numberOfRecords, numChannels))
 
    @setting(55, 'Acquire Data', returns='')
    def acquire_data(self, c):
        boardHandle = self.boardHandles[c['devName']]

        buffersCompleted = 0
        bytesTransferred = 0

        recordsPerBuffer = c['recordsPerBuffer']
        samplesPerRecord = c['samplesPerRecord']
        
        recordsBuffer = c['recordsBuffer'] 
        
        bufferSize = 2 * recordsPerBuffer * samplesPerRecord

        boardHandle.startCapture() 
        while (buffersCompleted < c['buffersPerAcquisition']):
            buffer = c['buffers'][buffersCompleted % len(c['buffers'])]
            boardHandle.waitAsyncBufferComplete(buffer.addr, timeout_ms=5000)
            boardHandle.postAsyncBuffer(buffer.addr, buffer.size_bytes) 
            bufferPosition = bufferSize * buffersCompleted
            recordsBuffer[bufferPosition:bufferPosition + bufferSize] = \
                    buffer.buffer
            buffersCompleted += 1
        boardHandle.abortAsyncRead()
        
    @setting(56, 'Get Records', returns='?')
    def get_records(self, c):
        recordsBuffer = c['recordsBuffer'] 
        samplesPerRecord = c['samplesPerRecord']
        numberOfRecords = c['numberOfRecords']
        vFullScale = float(c['input_range_mv'])/1e3 #convert to volts
        bitsPerSample = c['bitsPerSample']
        numChannels = 2
        dV = 2 * vFullScale / ((2**bitsPerSample) - 1)
        #Note that Fortran style indexing is used on 2nd reshaping
        timeSeries = recordsBuffer.reshape((numChannels*numberOfRecords, 
                                              samplesPerRecord)).\
                                     reshape((numberOfRecords,
                                              numChannels,
                                              samplesPerRecord), order="F")
        #0 ==> -VFullScale, 2^(N-1) ==> ~0, (2**N)-1 ==> +VFullScale
        timeSeries = -vFullScale + timeSeries * dV
        return timeSeries
        
    @setting(57, 'Get IQS', demodName = 's', returns='?')
    def get_iqs(self, c, demodName):
        recordsBuffer = c['recordsBuffer'] 
        samplesPerRecord = c['samplesPerRecord']
        numberOfRecords = c['numberOfRecords']
        
        vFullScale = float(c['input_range_mv'])/1e3 #convert to volts
        bitsPerSample = c['bitsPerSample']
        numChannels = 2 #think about how to do this in multi-channel case
        dV = 2*vFullScale/((2**bitsPerSample)-1)
        
        recordsPerBuffer = c['recordsPerBuffer']
        numRecords = (len(recordsBuffer)/samplesPerRecord)/2
        numBuffers = numRecords/recordsPerBuffer
        samplesPerBuffer = samplesPerRecord * recordsPerBuffer
       
        wA = c['demodWeightsDict'][demodName][0]
        wB = c['demodWeightsDict'][demodName][1]
        iq_buffer = c['iqBuffers'][demodName]
        for ii in range(0, numBuffers):
            #Note that Fortran style indexing is used on 2nd reshaping
            timeSeriesChunk = recordsBuffer.reshape((numChannels*numberOfRecords, 
                                              samplesPerRecord)).\
                                    reshape((numberOfRecords,
                                              numChannels,
                                              samplesPerRecord), order="F")[ii*recordsPerBuffer:(ii+1)*recordsPerBuffer]
            timeSeriesChunk = -vFullScale + timeSeriesChunk * dV
            #demod array shaped like [[I1,Q1], [I2,Q2], ..., [Im, Qm]] where m = num recs per buf
            iq_buffer[ii*recordsPerBuffer:(ii+1)*recordsPerBuffer] = self.demodulate_buffered_data(wA, wB, timeSeriesChunk) 
            
        return iq_buffer
        
    def demodulate_buffered_data(self, wA, wB, timeSeriesChunk):
        demodVals = []
        for ii in range(0, len(timeSeriesChunk)):
            vA = timeSeriesChunk[ii][0]
            vB = timeSeriesChunk[ii][1]
            I = np.mean(wA*vA - wB*vB) #check that these are legit
            Q = np.mean(wA*vA + wB*vB) #check that these are legit
            demodVals.append([I,Q])
        return np.asarray(demodVals)
            
__server__ = AlazarTechServer()

if __name__ == '__main__':
    util.runServer(__server__)