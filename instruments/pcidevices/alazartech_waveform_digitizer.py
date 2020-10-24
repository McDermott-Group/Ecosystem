# Copyright (C) 2016  Alexander Opremcak, Ivan Pechenezhskiy
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
version = 1.7.2
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
    deviceName = 'ATS Waveform Digitizer'
    name = 'ATS Waveform Digitizer'

    def initServer(self):
        self.boardHandles = {}
        self.boardNames = []
        self.boardTypes = {}
        self.findBoards()

    def findBoards(self):
        """Find available devices."""
        self.numSystems = ats.numOfSystems()
        for systemNum in range(1, self.numSystems + 1):
            numBoardsInSystem = ats.boardsInSystemBySystemID(systemNum)
            for boardNum in range(1, numBoardsInSystem + 1):
                boardName = 'ATS%d::%d' % (systemNum, boardNum)
                handle = ats.Board(systemId=systemNum, boardId=boardNum)
                self.boardHandles[boardName] = handle
                devType = ats.boardNames[handle.type]
                self.boardTypes[boardName] = devType
                self.boardNames += [boardName]
                print('Found %s Waveform Digitizer at %s'
                      % (devType, boardName))

    # Settings from 0 to 49 are basic server settings.
    @setting(10, 'List Devices', returns='*s')
    def list_devices(self, c):
        """Return a list of the ATS digitizer boards."""
        return self.boardNames

    @setting(20, 'Select Device', boardName=['s', '_'], returns='')
    def select_device(self, c, boardName):
        """
        Select an ATS board.

        Accepts:
            boardName: board name or None. If None is given and
                    there is only one board, this board will
                    be automatically selected.
        Returns:
            boardName: name of the selected board.
        """
        if boardName in self.boardNames:
            c['boardName'] = boardName
        elif len(self.boardNames) == 1:
            c['boardName'] = self.boardNames[0]
        else:
            raise ValueError("Device %s could not be found" % boardName)
        return boardName

    @setting(30, 'Deselect Device', returns='')
    def deselect_device(self, c):
        """Deselect the ATS board."""
        # Clear the context.
        if 'boardName' in c:
            c = []

    # Settings from 50 to 499 are basically wrappers around the atsapi
    # library functions and methods. See the AlazarTech SDK Programmer's
    # Guide for the proper documentation. The doc-strings are omitted
    # to avoid improper duplication of the information.
    @setting(50, 'Set LED State', ledState='i', returns='')
    def set_led_state(self, c, ledState):
        boardHandle = self.boardHandles[c['boardName']]
        boardHandle.setLED(ledState)

    @setting(70, 'Set Capture Clock', sourceID='w',
             sampleRateIDorValue='w', edgeID='w', decimation='w',
             returns='')
    def set_capture_clock(self, c, sourceID, sampleRateIDorValue,
                          edgeID=ats.CLOCK_EDGE_RISING, decimation=1):
        boardHandle = self.boardHandles[c['boardName']]
        boardHandle.setCaptureClock(sourceID, sampleRateIDorValue,
                                    edgeID, decimation)

    @setting(80, 'Input Control', channelID='w', couplingID='w',
             rangeID='w', impedanceID='w', returns='')
    def input_control(self, c, channelID=ats.CHANNEL_A,
                      couplingID=ats.DC_COUPLING,
                      rangeID=ats.INPUT_RANGE_PM_4_V,
                      impedanceID=ats.IMPEDANCE_50_OHM):
        boardHandle = self.boardHandles[c['boardName']]
        boardHandle.inputControlEx(channelID, couplingID, rangeID,
                                   impedanceID)

    @setting(90, 'Set BW Limit', channelID='w', flag='w', returns='')
    def set_bw_limit(self, c, channelID, flag=0):
        boardHandle = self.boardHandles[c['boardName']]
        boardHandle.setBWLimit(channelID, flag)

    @setting(100, 'Set Trigger Operation', triggerOperation='w',
             triggerEngineID1='w', sourceID1='w',
             slopeID1='w', level1='w',
             triggerEngineID2='w', sourceID2='w',
             slopeID2='w', level2='w', returns='')
    def set_trigger_operation(self, c, triggerOperation,
                              triggerEngineID1, sourceID1,
                              slopeID1, level1,
                              triggerEngineID2, sourceID2,
                              slopeID2, level2):
        boardHandle = self.boardHandles[c['boardName']]
        boardHandle.setTriggerOperation(triggerOperation,
                                        triggerEngineID1, sourceID1,
                                        slopeID1, level1,
                                        triggerEngineID2, sourceID2,
                                        slopeID2, level2)

    @setting(110, 'Set External Trigger', couplingID='w', rangeID='w',
             returns='')
    def set_external_trigger(self, c, couplingID, rangeID):
        boardHandle = self.boardHandles[c['boardName']]
        boardHandle.setExternalTrigger(couplingID, rangeID)

    @setting(120, 'Set Trigger Delay', triggerDelay='w', returns='')
    def set_trigger_delay(self, c, triggerDelay=0):
        boardHandle = self.boardHandles[c['boardName']]
        boardHandle.setTriggerDelay(triggerDelay)

    @setting(130, 'Set Trigger Time Out', timeoutTicks='w', returns='')
    def set_trigger_time_out(self, c, timeoutTicks=0):
        boardHandle = self.boardHandles[c['boardName']]
        boardHandle.setTriggerTimeOut(timeoutTicks)

    @setting(140, 'Set Record Size', preTriggerSamples='w',
             postTriggerSamples='w', returns='')
    def set_record_size(self, c, preTriggerSamples, postTriggerSamples):
        boardHandle = self.boardHandles[c['boardName']]
        boardHandle.setRecordSize(preTriggerSamples,
                                  postTriggerSamples)

    @setting(150, 'Set Record Count', recordsPerCapture='w', returns='')
    def set_record_count(self, c, recordsPerCapture):
        boardHandle = self.boardHandles[c['boardName']]
        boardHandle.setRecordCount(recordsPerCapture)

    @setting(160, 'Get Channel Info', returns='*w')
    def get_channel_info(self, c):
        boardHandle = self.boardHandles[c['boardName']]
        memorySizeInSamplesPerChannel, bitsPerSample = \
            boardHandle.getChannelInfo()
        return [memorySizeInSamplesPerChannel.value,
                bitsPerSample.value]

    @setting(170, 'Start Capture', returns='')
    def start_capture(self, c):
        boardHandle = self.boardHandles[c['boardName']]
        boardHandle.startCapture()

    @setting(180, 'Abort Capture', returns='')
    def abort_capture(self, c):
        boardHandle = self.boardHandles[c['boardName']]
        boardHandle.abortCapture()

    @setting(190, 'Busy', returns='b')
    def busy(self, c):
        boardHandle = self.boardHandles[c['boardName']]
        busyState = boardHandle.busy()
        return busyState

    @setting(200, 'Abort Async Read', returns='')
    def abort_async_read(self, c):
        boardHandle = self.boardHandles[c['boardName']]
        boardHandle.abortAsyncRead()

    # Settings from 500 to 699 are supposed to simplify the board
    # configuration overhead before acquring any data.
    @setting(500, 'Select All Channels', returns='')
    def select_all_channels(self, c):
        """Configure all channels present on the board."""
        boardName = c['boardName']
        boardHandle = self.boardHandles[boardName]
        boardType = self.boardTypes[boardName]

        boardTypes2Channels = {'ATS9870': [ats.CHANNEL_A,
                                           ats.CHANNEL_B]}
        if boardType not in boardTypes2Channels:
            raise NotImplementedError('Board type %s is not yet '
                                      'supported' % boardType)

        channelIDs = boardTypes2Channels[boardType]
        # Select all channels.
        channels = 0
        channelCount = 0
        for ch in channelIDs:
            channels |= ch
            channelCount += 1

        c['channels'] = channels
        c['channelIDs'] = channelIDs

    @setting(510, 'Configure Inputs', rangeID=['w', 'v[mV]'],
             couplingID=['w', 's'], bandwidth='w', returns='')
    def configure_inputs(self, c, rangeID, couplingID="DC",
                         bandwidth=0):
        """
        Configure the ATS digitizer inputs (all channels are treated
        identically).

        Accepts:
            rangeID: input voltage range in voltage units or as
                    the atsapi code.
            couplingID: either 'DC' or 'AC', or the corresponding
                    the atsapi code (default: 'DC').
            bandwidth: either 0 or 1 for no bandwidth limitation or
                    20 MHz input bandwidth, correspondingly
                    (default: 0).
        Returns:
            None.
        """
        if 'channels' not in c:
            self.select_all_channels(c)

        if isinstance(couplingID, str):
            if couplingID.upper() == "DC":
                couplingID = ats.DC_COUPLING
            elif couplingID.upper() == "AC":
                couplingID = ats.AC_COUPLING
            else:
                raise Exception("Acceptable string values for "
                                "couplingID are 'DC' and 'AC'.")

        if isinstance(rangeID, units.Value):
            rangeID = rangeID['mV']  # mV
            if rangeID > 4000:
                raise Exception("Invalid rangeID provided.")
            rangeIDs = [ats.INPUT_RANGE_PM_4_V,
                        ats.INPUT_RANGE_PM_2_V,
                        ats.INPUT_RANGE_PM_1_V,
                        ats.INPUT_RANGE_PM_400_MV,
                        ats.INPUT_RANGE_PM_200_MV,
                        ats.INPUT_RANGE_PM_100_MV,
                        ats.INPUT_RANGE_PM_40_MV]
            maxima = [4000, 2000, 1000, 400, 200, 100, 40]  # mV
            rangeID = min([key for key in maxima if rangeID <= key])
            rangeID = rangeIDs[maxima.index(rangeID)]
        c['inputRangeV'] = float(maxima[rangeIDs.index(rangeID)]) / 1e3

        for chanID in c['channelIDs']:
            # Both channels are DC coupled by default.
            self.input_control(c, chanID, couplingID, rangeID)
            # 0 ==> full input bandwidth, 1 ==> 20 MHz input bandwidth.
            self.set_bw_limit(c, chanID, bandwidth)

    @setting(520, 'Sampling Rate', samplingRate=['w', 'v[S/s]'],
             returns='v[S/s]')
    def sampling_rate(self, c, samplingRate=None):
        """
        Set or get the sampling rate.

        Accepts:
            samplingRate: sampling rate in samples per unit time, or
                    as a number assuming S/s units.
        Returns:
            samplingRate: sampling rate in samples per unit time.
        """
        if samplingRate is None:
            if 'samplingRate' not in c:
                # Assume a sampling rate of 1 GS/s.
                c['samplingRate'] = 1000000000
        else:
            if isinstance(samplingRate, units.Value):
                samplingRate = samplingRate['S/s']
            rates = (1000000000, 500000000, 250000000)
            samplingRate = max([rate for rate in rates
                                if samplingRate >= rate])
            c['samplingRate'] = samplingRate

        self.configure_clock_reference(c)
        return c['samplingRate'] * units.Unit('S/s')

    @setting(530, 'Configure Clock Reference', returns='')
    def configure_clock_reference(self, c):
        """
        Configure the clock reference. Only external 10 MHz clock
        references are yet supported.
        """
        # Assume a 10 MHz reference.
        self.set_capture_clock(c, ats.EXTERNAL_CLOCK_10MHz_REF,
                               c['samplingRate'], ats.CLOCK_EDGE_RISING, 1)

    @setting(540, 'Configure Trigger', triggerDelay=['w', 'v[ns]'],
             triggerLevel=['w', 'v[V]'], returns='')
    def configure_trigger(self, c, triggerDelay=0, triggerLevel=150):
        """
        Configure the board trigger.

        Accepts:
            triggerDelay: trigger delay in time units or as a number of
                    samples (default: 0).
            tiggerLevel: trigger level in voltage units or as the atsapi
                    code (default: 150).
        Returns:
            None.
        """
        if isinstance(triggerDelay, units.Value):
            samplingRate = float(c['samplingRate'])
            triggerDelay = int(triggerDelay['s'] * samplingRate + 0.5)

        if isinstance(triggerLevel, units.Value):
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

    @setting(600, 'Samples per Record', samplesPerRecord=['w', 'v[ns]'],
             returns='w')
    def samples_per_record(self, c, samplesPerRecord=None):
        """
        Set or get number of samples per record.

        Accepts:
            samplesPerRecord: samples per record as an integer number or
                    some value in time units (in the later case,
                    the sampling rate will be used to compute the actual
                    number of samples per record).
        Returns:
            samplesPerRecord: samples per record as an integer number.
        """
        if samplesPerRecord is None:
            if 'samplesPerRecord' not in c:
                c['samplesPerRecord'] = 256
                c['preTriggerSamples'] = 0
                self.number_of_records(c)
        else:
            if isinstance(samplesPerRecord, units.Value):
                samplingRate = float(c['samplingRate'])
                samplesPerRecord = int(samplesPerRecord['s'] * samplingRate)

            if samplesPerRecord <= 256:
                samplesPerRecord = 256
            else:
                samplesAboveRequiredMin = samplesPerRecord - 256
                if samplesAboveRequiredMin % 64:
                    div64 = samplesAboveRequiredMin // 64 + 1
                    samplesPerRecord = 256 + 64 * div64
            c['samplesPerRecord'] = samplesPerRecord
            c['preTriggerSamples'] = 0
            self.number_of_records(c)

        # Compute the number of bytes per record and per buffer.
        chan_info = self.get_channel_info(c)
        bitsPerSample = chan_info[1]
        c['bitsPerSample'] = bitsPerSample
        c['bytesPerSample'] = (bitsPerSample + 7) // 8
        c['bytesPerRecord'] = c['bytesPerSample'] * c['samplesPerRecord']

        return c['samplesPerRecord']

    @setting(610, 'Number of Records', numberOfRecords='w', returns='w')
    def number_of_records(self, c, numberOfRecords=None):
        """
        Set or get number of records.

        Accepts:
            numberOfRecords: number of records.
        Returns:
            numberOfRecords: number of records.
        """
        if numberOfRecords is None:
            if 'numberOfRecords' not in c:
                c['numberOfRecords'] = 1
                c['numberOfBuffers'] = 1
                c['recordsPerBuffer'] = 1
                c['buffersPerAcquisition'] = 1
        else:
            samplesPerRecord = self.samples_per_record(c)
            bytesPerRecord = c['bytesPerRecord']

            if 'channelIDs' not in c:
                self.select_all_channels(c)
            numberOfChannels = len(c['channelIDs'])

            boardName = c['boardName']
            boardHandle = self.boardHandles[boardName]
            boardType = self.boardTypes[boardName]

            bufferMaxSizes = {'ATS9870': 64 * 2**20}  # 64 MB.
            if boardType not in bufferMaxSizes:
                raise NotImplementedError('Board type %s is not yet'
                                          'supported' % boardType)
            bufferMaxSize = bufferMaxSizes[boardType]

            memorySize = numberOfChannels * bytesPerRecord * numberOfRecords
            if memorySize < bufferMaxSize:
                c['numberOfRecords'] = numberOfRecords
                c['recordsPerBuffer'] = numberOfRecords
                c['numberOfBuffers'] = 1
                c['buffersPerAcquisition'] = 1
            else:
                recordsPerBuffer = (bufferMaxSize /
                                    (4 * numberOfChannels * bytesPerRecord))
                buffersPerAcquisition = (
                    numberOfRecords - 1) // recordsPerBuffer + 1
                numberOfRecords = buffersPerAcquisition * recordsPerBuffer
                c['numberOfRecords'] = numberOfRecords
                c['recordsPerBuffer'] = recordsPerBuffer
                c['numberOfBuffers'] = 3
                c['buffersPerAcquisition'] = buffersPerAcquisition

        return c['numberOfRecords']

    @setting(620, 'Configure Buffers', returns='')
    def configure_buffers(self, c):
        """Configure the data buffers."""
        samplesPerRecord = self.samples_per_record(c)
        numberOfRecords = self.number_of_records(c)

        if 'channelIDs' not in c:
            self.select_all_channels(c)
        numberOfChannels = len(c['channelIDs'])

        # Reinitialize buffers only when the size of the buffers
        # actually should be changed.
        if 'reshapedRecordsBuffer' in c and \
                np.shape(c['reshapedRecordsBuffer']) == \
                (numberOfRecords, numberOfChannels, samplesPerRecord):
            return

        preTriggerSamples = c['preTriggerSamples']
        bytesPerSample = c['bytesPerSample']
        bytesPerRecord = c['bytesPerRecord']
        recordsPerBuffer = c['recordsPerBuffer']
        numberOfBuffers = c['numberOfBuffers']

        bytesPerBuffer = bytesPerRecord * recordsPerBuffer * numberOfChannels

        # Allocate DMA buffers.
        sampleType = ctypes.c_uint8
        if bytesPerSample > 1:
            sampleType = ctypes.c_uint16

        c['buffers'] = []
        for i in range(numberOfBuffers):
            c['buffers'].append(ats.DMABuffer(sampleType, bytesPerBuffer))

        # Current implementation is NPT Mode = No Pre Trigger Samples.
        self.set_record_size(c, preTriggerSamples, samplesPerRecord)

        # Must allocate these first, otherwise takes up too much time
        # during the acquisition.
        samples = numberOfChannels * numberOfRecords * samplesPerRecord
        if bytesPerSample == 1:
            c['recordsBuffer'] = np.empty(samples, dtype=np.uint8)
        elif bytesPerSample == 2:
            c['recordsBuffer'] = np.empty(samples, dtype=np.uint16)
        else:
            c['recordsBuffer'] = np.empty(samples, dtype=np.uint32)
        c['reshapedRecordsBuffer'] = np.empty((numberOfRecords,
                                               numberOfChannels,
                                               samplesPerRecord),
                                              dtype=np.float32)

        c['iqBuffers'] = np.empty((numberOfRecords, 2), dtype=np.float32)

    # Data acquisition settings start from setting 700.
    @setting(700, 'Acquire Data', timeout='v[s]', returns='')
    def acquire_data(self, c, timeout=120 * units.s):
        """
        Acquire the data from an ATS board.

        Accepts:
            timeout: temout in time units.
        Returns:
            None.
        """
        boardHandle = self.boardHandles[c['boardName']]

        samplesPerRecord = self.samples_per_record(c)
        numberOfRecords = self.number_of_records(c)

        if 'channelIDs' not in c:
            self.select_all_channels(c)
        numberOfChannels = len(c['channelIDs'])
        channels = c['channels']

        preTriggerSamples = c['preTriggerSamples']
        buffersPerAcquisition = c['buffersPerAcquisition']

        recordsPerBuffer = c['recordsPerBuffer']
        buffers = c['buffers']
        recordsBuffer = c['recordsBuffer']
        reshapedRecordsBuffer = c['reshapedRecordsBuffer']

        # Configure the board for an NPT AutoDMA acquisition.
        boardHandle.beforeAsyncRead(
            channels,
            -preTriggerSamples,
            samplesPerRecord,
            recordsPerBuffer,
            numberOfRecords,
            ats.ADMA_EXTERNAL_STARTCAPTURE | ats.ADMA_NPT)

        # Post DMA buffers to board.
        for buffer in buffers:
            boardHandle.postAsyncBuffer(buffer.addr, buffer.size_bytes)

        # Acquire the data.
        buffersCompleted = 0
        bufferSize = numberOfChannels * recordsPerBuffer * samplesPerRecord
        boardHandle.startCapture()
        try:
            while buffersCompleted < buffersPerAcquisition:
                buffer = buffers[buffersCompleted % len(buffers)]
                boardHandle.waitAsyncBufferComplete(
                    buffer.addr, timeout_ms=int(timeout['ms']))
                bufferPosition = bufferSize * buffersCompleted
                recordsBuffer[bufferPosition:bufferPosition + bufferSize] = \
                    buffer.buffer
                boardHandle.postAsyncBuffer(buffer.addr, buffer.size_bytes)
                buffersCompleted += 1
        except BaseException:
            raise
        finally:
            boardHandle.abortAsyncRead()

        # Post-process the acquired data.
        bitsPerSample = c['bitsPerSample']
        inputRangeV = c['inputRangeV']

        # This is the original data reshaping. For very large data
        # arrays it throughs MemoryError but the code should be kept
        # here for the future reference.
        # reshapedRecordsBuffer = \
        #     np.float32(recordsBuffer.reshape(buffersPerAcquisition,
        #     numberOfChannels, recordsPerBuffer,
        #     samplesPerRecord).swapaxes(1, 2).reshape(numberOfRecords,
        #     numberOfChannels, samplesPerRecord))

        # Reshape the view of the recordsBuffer. No extra memory is
        # is expected to be allocated here.
        recordsView = recordsBuffer.view()
        recordsView.shape = (buffersPerAcquisition, numberOfChannels,
                             recordsPerBuffer, samplesPerRecord)
        recordsView = np.rollaxis(recordsView, 2, 1).reshape(numberOfRecords,
                                                             numberOfChannels,
                                                             samplesPerRecord)

        reshapedRecordsBuffer = recordsView.astype(np.float32, copy=False)

        codeZero = float(1 << (bitsPerSample - 1)) - 0.5
        codeRange = float(1 << (bitsPerSample - 1)) - 0.5
        reshapedRecordsBuffer -= codeZero
        reshapedRecordsBuffer *= (inputRangeV / codeRange)
        c['reshapedRecordsBuffer'] = reshapedRecordsBuffer

    @setting(710, 'Get Records', returns='*3v[V]')
    def get_records(self, c):
        """
        Get acquired records.

        Accepts:
            None.
        Returns:
            records: 3D array where the first index defines the record
                    number, the second --- the channel, and
                    the third ---  the sample in the record.
        """
        return c['reshapedRecordsBuffer'] * units.V

    @setting(720, 'Get IQs', chA_weight='*v', chB_weight='*v',
             returns='*2v[V]')
    def get_iqs(self, c, chA_weight, chB_weight):
        """
        Get the demodulated values (Is and Qs).

        Accepts:
            chA_weights: channel A values to be used as the demodulation
                weights.
            chB_weights: channel B values to be used as the demodulation
                weights.
        Returns:
            records: 2D array where the first index defines the record
                    number, the second --- the quadrature component
                    (either I or Q).
        """
        samplesPerRecord = self.samples_per_record(c)
        numberOfRecords = self.number_of_records(c)

        # print('samplesPerRecord=', samplesPerRecord)  # LIU
        # print('numberOfRecords=', numberOfRecords)  # LIU

        # labrad.units.DimensionlessArray to numpy.ndarray conversion.
        chA = chA_weight['']
        chB = chB_weight['']

        chA_len = len(chA)
        # print('chA_len', chA_len)  # LIU
        if chA_len > samplesPerRecord:
            chA = chA[:samplesPerRecord]
        elif chA_len < samplesPerRecord:
            chA = np.hstack([chA, np.zeros(samplesPerRecord - chA_len)])

        chB_len = len(chB)
        if chB_len > samplesPerRecord:
            chB = chB[:samplesPerRecord]
        elif chB_len < samplesPerRecord:
            chB = np.hstack([chB, np.zeros(samplesPerRecord - chB_len)])

        iqBuffer = c['iqBuffers']
        timeSeries = c['reshapedRecordsBuffer']

        # This is the original data processing. Keep it for the future
        # reference.
        # for i in range(numberOfRecords):
        #     vA = timeSeries[i][0]
        #     vB = timeSeries[i][1]
        #     iqBuffer[i][0] = np.mean(chA * vA - chB * vB) # I
        #     iqBuffer[i][1] = np.mean(chB * vA + chA * vB) # Q

        chs = np.stack([np.hstack([chA, chB]).T,
                        np.hstack([-chB, chA]).T], axis=1)

        # print ('numerofRecords=', numberOfRecords)  #LIU

        try:
            np.dot(timeSeries.reshape(numberOfRecords, -1), np.float32(chs),
                   iqBuffer)
        except Exception as e:
            print 'numberOfRecords %d' % numberOfRecords
            print 'timeSeries shape'
            print timeSeries.shape
            # print 'size of first dotted array %d' % len(timeSeries.reshape(numberOfRecords, -1))
            print 'size of second dotted array %d' % len(np.float32(chs))
            print e

        iqBuffer /= samplesPerRecord
        return iqBuffer * units.V

    @setting(730, 'Get Average', returns='*2v[V]')
    def get_average(self, c):
        """
        Get the averaged time trace.

        Accepts:
            None.
        Returns:
            record: 2D array where the first index defines
                    the quadrature component and the second ---
                    the sample in the averaged record.
        """
        result = c['reshapedRecordsBuffer']
        return np.mean(result, axis=0) * units.V

    @setting(740, 'Get Times', returns='*v[ns]')
    def get_times(self, c):
        """
        Get the vector of time values that correspond to the acquired
        data records.

        Accepts:
            None.
        Returns:
            times: 1D array of the record times.
        """
        samplesPerRecord = self.samples_per_record(c)
        samplingRate = float(c['samplingRate']) / 1e9  # samples per ns
        t = np.linspace(0, samplesPerRecord - 1, samplesPerRecord)
        return (t / samplingRate) * units.ns


__server__ = AlazarTechServer()


if __name__ == '__main__':
    util.runServer(__server__)
