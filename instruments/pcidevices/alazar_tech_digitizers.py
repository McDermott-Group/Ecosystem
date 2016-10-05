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
version = 1.2.0
description = Communicates with AlazarTech Digitizers over PCIe interface.

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
"""

# This file uses lowerCamelCase for compatibility with ATS provided
# coding examples and atsapi library. 
# LabRAD settings use underscores for self-consistency with our servers.

import ctypes
import numpy as np
import atsapi as ats
from twisted.internet.defer import inlineCallbacks, returnValue

from labrad.server import LabradServer, setting
import labrad.units as units
from labrad import util


class AlazarTechServer(LabradServer):
    deviceName = 'ATS Digitizer Server'
    name = 'ATS Digitizer Server'

    def initServer(self):
        self.boardHandles = {}
        self.devNames = []
        self.devTypes = {}
        self.findDevices()
    
    def findDevices(self):
        """Find available devices."""
        self.numSystems = ats.numOfSystems()
        for systemNum in range(1, self.numSystems+1):
            numBoardsInSystem = ats.boardsInSystemBySystemID(systemNum)
            for boardNum in range(1, numBoardsInSystem+1):
                devName = 'ATS%d::%d' %(systemNum, boardNum)
                handle = ats.Board(systemId=systemNum, boardId=boardNum)
                self.boardHandles[devName] = handle
                devType = ats.boardNames[handle.type]
                self.devTypes[devName] = devType
                self.devNames += [devName]
                print('Found %s Waveform Digitizer at %s'
                        %(devType, devName))
        
    @setting(2, 'List Devices', returns='*s')
    def list_devices(self, c):
        """Return list of ATS digitizer boards."""
        return self.devNames
   
    @setting(3, 'Select Device', devName='s', returns='')
    def select_device(self, c, devName):
        """"""
        if devName in self.devNames:
            c['devName'] = devName
        else:
            print("Device %s could not be found" %devName)
            
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
        devName = c['devName']
        boardHandle = self.boardHandles[devName]
        devType = self.devTypes[devName]
        
        supportedTypes = ('ATS9870')
        if devType not in supportedTypes:
            raise NotImplementedError('Board type %s is yet not '
                    'supported' %devType)
        
        if type(channelID) == str:
            if channelID.upper() == "A":
                channelID = ats.CHANNEL_A
            elif channelID.upper() == "B":
                channelID = ats.CHANNEL_B
            else: 
                raise Exception("Acceptable string values for "
                        "channelID are 'A' and 'B'.")
                
        if type(couplingID) == str:
            if couplingID.upper() == "DC":
                couplingID = ats.DC_COUPLING
            elif couplingID.upper() == "AC":
                couplingID = ats.AC_COUPLING
            else:
                raise Exception("Acceptable string values for "
                        "couplingID are 'DC' and 'AC'.")
        
        if type(rangeID) == units.Value:
            rangeIDs = [ats.INPUT_RANGE_PM_4_V,
                        ats.INPUT_RANGE_PM_2_V,
                        ats.INPUT_RANGE_PM_1_V,
                        ats.INPUT_RANGE_PM_400_MV,
                        ats.INPUT_RANGE_PM_200_MV,
                        ats.INPUT_RANGE_PM_100_MV,
                        ats.INPUT_RANGE_PM_40_MV]
            rangeMaxima = [4000, 2000, 1000, 400, 200, 100, 40]        
            if rangeID['mV'] > 4000:
                raise Exception("Invalid rangeID provided.")
            for key in rangeMaxima:
                if rangeID['mV'] <= key:
                    rangeID = rangeIDs[rangeMaxima.index(key)]
                    break
        c['rangeV'] = float(rangeMaxima[rangeIDs.index(rangeID)]) / 1e3

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
                        "channelID are 'A' and 'B'.")
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
        boardHandle.setTriggerOperation(triggerOperation,
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

    @setting(11, 'Set Trigger Time Out', timeoutTicks='w', returns='')
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
        memorySizeInSamplesPerChannel, bitsPerSample = \
                boardHandle.getChannelInfo()
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
        
    @setting(20, 'Set Samples Per Record', samplesPerRecord=['w', 'v[ns]'],
            returns='')
    def set_samples_per_record(self, c, samplesPerRecord):
        if type(samplesPerRecord) == units.Value:
            samplingRate = float(c['samplingRate'])
            samplesPerRecord = int(triggerDelay['s'] * samplingRate)
        
        if samplesPerRecord <= 256:
            samplesPerRecord = 256
        else:
            samplesAboveRequiredMin = samplesPerRecord - 256
            if samplesAboveRequiredMin % 64:
                div64 = float(samplesAboveRequiredMin) / 64.
                samplesPerRecord = 256 + 64 * int(np.round(div64))

        c['samplesPerRecord'] = samplesPerRecord
        
    @setting(21, 'Get Samples Per Record', returns='w')
    def get_samples_per_record(self, c):
        if 'samplesPerRecord' not in c:
            c['samplesPerRecord'] = 256
        return c['samplesPerRecord']
        
    @setting(22, 'Set Records Per Buffer', recordsPerBuffer='w',
            returns='')
    def set_records_per_buffer(self, c, recordsPerBuffer):
        numberOfRecords = self.get_number_of_records(c)
        c['recordsPerBuffer'] = recordsPerBuffer
        self.set_number_of_records(c, numberOfRecords)
        
    @setting(23, 'Get Records Per Buffer', returns='w')
    def get_records_per_buffer(self, c):
        if 'recordsPerBuffer' not in c:
            c['recordsPerBuffer'] = 10
        return c['recordsPerBuffer']
        
    @setting(24, 'Set Number of Records', numberOfRecords='w',
            returns='')
    def set_number_of_records(self, c, numberOfRecords='w'):
        recordsPerBuffer = self.get_records_per_buffer(c)
        buffersPerAcquisition = \
            (numberOfRecords + recordsPerBuffer - 1) / recordsPerBuffer        
        c['buffersPerAcquisition'] = buffersPerAcquisition
        numberOfRecords = buffersPerAcquisition * recordsPerBuffer
        c['numberOfRecords'] = numberOfRecords
        
    @setting(25, 'Get Number of Records', returns='w')
    def get_number_of_records(self, c):
        if 'numberOfRecords' not in c:
            c['numberOfRecords'] = 0
        return c['numberOfRecords']

    @setting(50, 'Configure External Clocking', returns='')
    def configure_external_clocking(self, c):
        # Assume 10 MHz reference clock and a sampling rate of 1 GS/s.
        c['samplingRate'] = 1000000000
        self.set_capture_clock(c, ats.EXTERNAL_CLOCK_10MHz_REF,
                c['samplingRate'], ats.CLOCK_EDGE_RISING, 1)
 
    @setting(51, 'Configure Inputs', rangeID=['w', 'v[mV]'],
            couplingID=['w', 's'], returns='')
    def configure_inputs(self, c, rangeID, couplingID="DC"):
        # Channels are treated identically.
        chanIDs = ["A", "B"]
        for chanID in chanIDs:
            # Both channels are DC coupled by default.
            self.input_control(c, chanID, couplingID, rangeID)
             #0 ==> Full Input Bandwidth, 1 ==> 20 MHz input bandwidth.
            self.set_bw_limit(c, chanID, 0)
        
    @setting(52, 'Configure Trigger', triggerDelay=['w', 'v[ns]'],
            triggerLevel=['w', 'v[V]'], returns='')
    def configure_trigger(self, c, triggerDelay=0, triggerLevel=150):
        if type(triggerDelay) == units.Value:
            samplingRate = float(c['samplingRate'])
            triggerDelay = int(triggerDelay['s'] * samplingRate)
        
        if type(triggerLevel) == units.Value:
            triggerLevel = 128 + int(127 * triggerLevel['V'] / 5)
        
        self.set_trigger_operation(c,
                ats.TRIG_ENGINE_OP_J,
                ats.TRIG_ENGINE_J,
                ats.TRIG_EXTERNAL,
                ats.TRIGGER_SLOPE_POSITIVE,
                triggerLevel,
                ats.TRIG_ENGINE_K,
                ats.TRIG_DISABLE,
                ats.TRIGGER_SLOPE_POSITIVE,
                128)
                 
        self.set_external_trigger(c, ats.DC_COUPLING, ats.ETR_5V)                  
        self.set_trigger_delay(c, triggerDelay)
        self.set_trigger_time_out(c, 0)
       
    @setting(53, 'Configure Buffers', returns='')
    def configure_buffers(self, c):
        boardHandle = self.boardHandles[c['devName']]

        # TODO: Select the number of records per DMA buffer.
        # should be chosen such that 1 MB < bytesPerBuffer < 64 MB
        recordsPerBuffer = self.get_records_per_buffer(c)
        samplesPerRecord = self.get_samples_per_record(c)
        numberOfRecords = self.get_number_of_records(c)
        
        # TODO: Select the active channels.
        channels = ats.CHANNEL_A | ats.CHANNEL_B
        channelCount = 0

        for ch in ats.channels:
            channelCount += (ch & channels == ch)

        # Compute the number of bytes per record and per buffer
        chan_info = self.get_channel_info(c)
        bitsPerSample = chan_info[1]
        c['bitsPerSample'] = bitsPerSample
        bytesPerSample = (bitsPerSample + 7) // 8
        
        bytesPerRecord = bytesPerSample * samplesPerRecord
        bytesPerBuffer = bytesPerRecord * recordsPerBuffer * channelCount

        # TODO: Select number of DMA buffers to allocate.
        bufferCount = 4

        # Allocate DMA buffers.
        sampleType = ctypes.c_uint8
        if bytesPerSample > 1:
            sampleType = ctypes.c_uint16
            
        c['buffers'] = []
        for i in range(bufferCount):
            c['buffers'].append(ats.DMABuffer(sampleType, bytesPerBuffer))
        
        # Current implementation is NPT Mode = No Pre Trigger Samples. 
        preTriggerSamples = 0 
        self.set_record_size(c, preTriggerSamples, samplesPerRecord)
        
        # Configure the board for an NPT AutoDMA acquisition.
        boardHandle.beforeAsyncRead(channels,
                -preTriggerSamples,
                samplesPerRecord,
                recordsPerBuffer,
                numberOfRecords,
                ats.ADMA_EXTERNAL_STARTCAPTURE | ats.ADMA_NPT)
        
        # Post DMA buffers to board.
        for buffer in c['buffers']:
            boardHandle.postAsyncBuffer(buffer.addr, buffer.size_bytes)
            
        # Must allocate these first, otherwise takes up too much time
        # during acquisition.
        c['recordsBuffer'] = np.zeros(2*numberOfRecords*samplesPerRecord,
                dtype=np.uint8)

    @setting(54, 'Add Demod Weights', chA_weight='*v', chB_weight='*v',
            demodName='s',  returns='')
    def add_demod_weights(self, c, chA_weight, chB_weight, demodName):
        samplesPerRecord = self.get_samples_per_record(c)
        numberOfRecords = self.get_number_of_records(c)
        
        chA_len = len(chA_weight)
        if chA_len > samplesPerRecord:
            chA_weight = chA[:samplesPerRecord]
        elif chA_len < samplesPerRecord:
            chA_weight = chA + [0] * (samplesPerRecord - chA_len)
        
        chB_len = len(chB_weight)
        if chB_len > samplesPerRecord:
            chB_weight = chB[:samplesPerRecord]
        elif chB_len < samplesPerRecord:
            chB_weight = chB + [0] * (samplesPerRecord - chB_len)

        if 'demodWeigthsDict' not in c:
            c['demodWeightsDict'] = {}
        c['demodWeightsDict'][demodName] = [chA_weight, chB_weight]
        
        if 'iqBuffers' not in c:
            c['iqBuffers'] = {}
        c['iqBuffers'][demodName] = np.zeros((numberOfRecords, 2))
 
    @setting(55, 'Acquire Data', returns='')
    def acquire_data(self, c):
        boardHandle = self.boardHandles[c['devName']]

        buffersCompleted = 0
        bytesTransferred = 0

        recordsPerBuffer = self.get_records_per_buffer(c)
        samplesPerRecord = self.get_samples_per_record(c)
        
        recordsBuffer = c['recordsBuffer']
        
        bufferSize = 2 * recordsPerBuffer * samplesPerRecord

        boardHandle.startCapture() 
        while (buffersCompleted < c['buffersPerAcquisition']):
            buffer = c['buffers'][buffersCompleted % len(c['buffers'])]
            boardHandle.waitAsyncBufferComplete(buffer.addr, timeout_ms=50000)
            boardHandle.postAsyncBuffer(buffer.addr, buffer.size_bytes) 
            bufferPosition = bufferSize * buffersCompleted
            recordsBuffer[bufferPosition:bufferPosition + bufferSize] = \
                    buffer.buffer
            buffersCompleted += 1
        boardHandle.abortAsyncRead()
        
    @setting(56, 'Get Records', returns='*3v[V]')
    def get_records(self, c):
        recordsBuffer = c['recordsBuffer']
        samplesPerRecord = self.get_samples_per_record(c)
        numberOfRecords = self.get_number_of_records(c)

        bitsPerSample = c['bitsPerSample']
        numChannels = 2
        vFullScale = c['rangeV']
        dV = 2 * vFullScale / ((2**bitsPerSample) - 1)
        # Note that Fortran style indexing is used on the 2nd reshaping.
        timeSeries = recordsBuffer.\
                reshape((numChannels*numberOfRecords, samplesPerRecord)).\
                reshape((numberOfRecords,
                         numChannels,
                         samplesPerRecord), order="F")
        # 0 ==> -VFullScale, 2^(N-1) ==> ~0, (2**N)-1 ==> +VFullScale
        timeSeries = (-vFullScale + timeSeries * dV) * units.V
        return timeSeries
        
    @setting(57, 'Get IQs', demodName='s', returns='*2v[V]')
    def get_iqs(self, c, demodName):
        recordsBuffer = c['recordsBuffer']
        recordsPerBuffer = self.get_records_per_buffer(c)
        samplesPerRecord = self.get_samples_per_record(c)
        numberOfRecords = self.get_number_of_records(c)

        bitsPerSample = c['bitsPerSample']
        numChannels = 2
        vFullScale = c['rangeV']
        dV = 2 * vFullScale / ((2**bitsPerSample) - 1)
  
        numOfBuffers = numberOfRecords / recordsPerBuffer
        samplesPerBuffer = samplesPerRecord * recordsPerBuffer

        wA = c['demodWeightsDict'][demodName][0]
        wB = c['demodWeightsDict'][demodName][1]
        iq_buffer = c['iqBuffers'][demodName]
        for ii in range(numOfBuffers):
            #N ote that Fortran style indexing is used on the 2nd reshaping.
            timeSeriesChunk = recordsBuffer.\
                    reshape((numChannels*numberOfRecords, samplesPerRecord)).\
                    reshape((numberOfRecords,
                             numChannels,
                             samplesPerRecord), order="F")[ii*recordsPerBuffer:(ii+1)*recordsPerBuffer]
            timeSeriesChunk = -vFullScale + timeSeriesChunk * dV
            # Demod array shaped like [[I1,Q1], [I2,Q2], ..., [Im, Qm]]
            # where m  is number of records per buffer.
            iq_buffer[ii*recordsPerBuffer:(ii+1)*recordsPerBuffer] = \
                    self.demodulate_buffered_data(wA, wB, timeSeriesChunk) 
            
        return iq_buffer * units.V
        
    def demodulate_buffered_data(self, wA, wB, timeSeriesChunk):
        demodVals = []
        for ii in range(len(timeSeriesChunk)):
            vA = timeSeriesChunk[ii][0]
            vB = timeSeriesChunk[ii][1]
            I = np.mean(wA * vA - wB * vB)
            Q = np.mean(wB * vA + wA * vB)
            demodVals.append([I,Q])
        return np.asarray(demodVals)

        
__server__ = AlazarTechServer()


if __name__ == '__main__':
    util.runServer(__server__)