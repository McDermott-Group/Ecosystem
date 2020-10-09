# Use at your own risk -A. Opremcak
import atsapi as ats
import ctypes
import numpy as np
from labrad.units import GS, MS, s, mV, V, ns
import time

# some useful lists and mappings to AlazarTech defined constants
INPUT_VOLTAGE_RANGES = [ats.INPUT_RANGE_PM_4_V,
                        ats.INPUT_RANGE_PM_2_V,
                        ats.INPUT_RANGE_PM_1_V,
                        ats.INPUT_RANGE_PM_400_MV,
                        ats.INPUT_RANGE_PM_200_MV,
                        ats.INPUT_RANGE_PM_100_MV,
                        ats.INPUT_RANGE_PM_40_MV]
INPUT_COUPLINGS = {'DC Coupled': ats.DC_COUPLING,
                   'AC Coupled': ats.AC_COUPLING}
CHANNEL_IDS = [ats.CHANNEL_A, ats.CHANNEL_B]
DISABLE_BW_LIMIT = 0
BANDWIDTH_FLAGS = {'Enable BW Limit': 1,
                   'Disable BW Limit': 0}
CLOCK_SOURCE_IDS = [ats.INTERNAL_CLOCK, ats.SLOW_EXTERNAL_CLOCK,
                    ats.EXTERNAL_CLOCK_AC, ats.EXTERNAL_CLOCK_10MHz_REF]
MINIMUM_NUMBER_OF_SAMPLES = 256
BITS_PER_SAMPLE = 8  # 8-bit digitizer
BYTES_PER_SAMPLE = 1
MAXIMUM_BUFFER_SIZE = 64 * 2**20  # 64 MB
NUMBER_OF_CHANNELS = 2
ADC_INPUT_IMPEDANCE = ats.IMPEDANCE_50_OHM
MAX_SAMPLING_RATE = 1 * GS/s
NUMBER_OF_PRE_TRIGGER_SAMPLES = 0  # ==> NPT asynch AutoDMA mode
CHANNEL_LOGIC_FOR_A_AND_B = 3  # acquire data on both channels (A & B)


class ADC(object):

    """A class for interacting with the AlazarTech ATS9870 PCIe digitizer (ADC)

    This class assumes you are working with the ADC in no pre-trigger
    (NPT) asynchronous AutoDMA mode (DMA == Direct Memory Access), with
    an externally provided 10 MHz reference clock. In addition we assume
    that an external trigger (that goes from low-to-high) will be supplied
    at the TRIG IN port of the ADC each time a triggered reading is desired.
    For official documentation please see the pdf files in location:
            C:\Repositories\area51\instruments\alazartech
    Of particular interest are the:
        (i) ATS-SDK-Guide.pdf (programming manual)
        (ii) ATS9870_datasheet.pdf (generic but useful hardware info)
        (iii) ATS9870_user_manual.pdf (exhaustive description of the ADC)

    Attributes:
        number_of_triggers (int): The actual number of triggers the digitizer
            will look for after rounding up to a full DMA buffer.
        demodulation_time (labrad.units.Value): The actual demodulation time
            that the digitizer will sample for after a trigger is provided.
            See Table 9 on pg. 249 of the ATS-SDK-Guide.pdf for requirements
            on the number of samples.
        input_voltage_range (labrad.units.Value): The actual input voltage
            range that will be used on channels A & B of the digitizer.
            Note that +/- 40 * mV the input bandwidth (BW) drops is 200 MHz.
            For all remaining options input voltage ranges the input BW is
            450 MHz.
        sampling_rate (labrad.units.Value): The sampling rate in GS/s, MS/s,
            or S/s. Note that the effective clock decimation defined as
            ( (1 GS/s) / (sampling_rate) ) must be 1, 2, 4, or any multiple of
            10.
        trigger_delay (labrad.units.Value): The time delay between when the
            trigger is received and when data acquisition begins.
    """
    def __init__(self, number_of_triggers, demodulation_time,
                 input_voltage_range, sampling_rate, trigger_level,
                 trigger_delay):
        """Configure an adc_board_handle with user specified settings.

        Note that this object can be re-used to avoid the timing overhead
        associated with configuring the ATS9870 for NPT AutoDMA mode.
        Specifically we want to avoid calling configure_adc_sampling_rate
        every time we want to use the digitizer within a constant set of
        configuration settings.


        Args:
            number_of_triggers (int): The desired number of triggers the
                digitizer should look for before data acquisition is complete.
                In reality, this number is rounded slightly in order to fill
                an integer number of Direct Memory Access (DMA) buffers. Call self.number_of_triggers
                to get actual value after rounding.
            demodulation_time (labrad.units.Value): The desired demodulation
                time that the digitizer will acquire samples for after a
                trigger is received. This number is also round to meet the
                digitizers Samples per Record Alignment Requirements.
            input_voltage_range (labrad.units.Value): The desired input
                voltage range that will be used on channels A & B of the
                digitizer. See manufacturer provided datasheet for a list
                of options.  &&& list options
            sampling_rate (labrad.units.Value): The desired sampling rate.
                Acceptable values are 1 GS/s, 500 MS/s, 250 MS/s, or 1 GS/s
                divided by any multiple of 10.
            trigger_level (labrad.units.Value): The trigger level that
                will be used to start data acquisition. An externally provided
                trigger (@ the TRIG IN port of the digitizer) which crosses
                from below this value to above it will force the digitizer to
                start a single acquisition after the amount of time specified
                by the user provided trigger_delay. Note that trigger_delay
                will be rounded to an integer multiple of 1/sampling_rate.
            trigger_delay (labrad.units.Value): The time delay between when
                the trigger is received and when data acquisition begins.
        """
        self.adc_board_handle = self.create_adc_board_handle()
        self.sampling_rate = \
            self.configure_adc_sampling_rate(sampling_rate)
        self.input_voltage_range = \
            self.configure_adc_input_settings(input_voltage_range)
        self.trigger_delay = \
            self.configure_adc_trigger_settings(trigger_level, trigger_delay)
        (self.number_of_triggers, self.number_of_samples_per_trigger,
         self.number_of_triggers_per_buffer, self.number_of_recycled_buffers) \
            = self.compute_adc_memory_requirements(number_of_triggers,
                                                   demodulation_time)
        self.records_buffer, self.dma_buffers, self.iq_buffers = \
            self.configure_adc_buffers()
        self.reshaped_records_buffer = None

    def create_adc_board_handle(self):
        """Creates an ADC board handle to communicate with a single ATS9870.

        Returns:
            Handle object: An board handle that allows for subsequent
                communication with the ATS9870 installed in the computer.

        """
        number_of_board_systems = ats.numOfSystems()
        if number_of_board_systems > 1:
            raise Exception('This library was written assuming one'
                            'ADC per computer. Use with multiple ADCs'
                            '(with or without SyncBoards) will require '
                            'changes.')
        number_of_adcs_in_board_system = \
            ats.boardsInSystemBySystemID(number_of_board_systems)
        if number_of_adcs_in_board_system > 1:
            raise Exception('This library was written assuming one'
                            'ADC per computer. Use with multiple ADCs'
                            '(with or without SyncBoards) will require '
                            'significant changes to this library.')
        adc_board_handle = ats.Board(systemId=1L, boardId=1L)
        board_type = ats.boardNames[adc_board_handle.type]
        if board_type != 'ATS9870':
            raise Exception("Only ATS9870 board types are supported"
                            "by this library.")
        return adc_board_handle

    def configure_adc_sampling_rate(self, sampling_rate):
        """Configures the ADCs sampling rate.

        Note that we assume an external 10 MHz reference clock is provided
        in the form of a sine wave that drops +/- 200 mV across the 50 Ohm
        input impedance of the ECLK port on the front panel of the digitizer.

        Args:
            sampling_rate (labrad.units.Value): The desired sampling rate in
            labrad units of S/s (or compatible units).

        Returns:
            labrad.units.Value: The sampling rate after verifying that the
            decimation factor is compatible with the external 10 MHz PLL mode
            (i.e. a decimation factor in {1, 2, 4, or any multiple of 10}).
            See pp. 202-203 of the ATS-SDK-Guide.pdf for more information on
            this topic.

        """
        if sampling_rate['S/s'] in [250e6, 500e6, 1e9] or \
                not ((MAX_SAMPLING_RATE['GS/s']/sampling_rate['GS/s']) % 10):
            decimation_factor = \
                int(np.ceil(MAX_SAMPLING_RATE['MS/s']/sampling_rate['MS/s']))
            print("decimation_factor=", decimation_factor)   
            decimation_factor = 1
        else:
            raise Exception("Please use a sampling rate that is 1 GS/s, "
                            "500 MS/s, 250 MS/s or 1 GS/s divided by any "
                            "multiple of 10.")
        self.adc_board_handle.setCaptureClock(ats.EXTERNAL_CLOCK_10MHz_REF,
                                              sampling_rate['S/s'], #MAX_SAMPLING_RATE['S/s'],
                                              ats.CLOCK_EDGE_RISING,
                                              decimation_factor)
        return sampling_rate

    def configure_adc_input_settings(self, input_voltage_range,
                                     input_coupling=ats.DC_COUPLING,
                                     bandwidth_limit_flag=DISABLE_BW_LIMIT):
        """Configures the input BW, voltage range, and impedance of the ADC.

        Note 1: we generally operate the ADC with both channels DC coupled.
        Note 2: if the bandwidth bandwidth_limit_flag == 1 (i.e. BW limit is
        enabled, then the input bandwidth of the ADC reduces to ~ 20 MHz. We
        typically work with intermediate frequencies (what goes into the I
        and Q ports of the mixer) ~ 30-100 MHz, meaning that this feature
        should almost always be disabled, opening up to bandwidth to 200-450
        MHz depending on the selected input_voltage_range.

        Args:
            input_voltage_range (labrad.units.Value): See class docstring
                for more info on this parameter.
            input_coupling (int, optional): An ats_api recognized constant
                that determines whether channels A & B are AC or DC coupled.
            bandwidth_limit_flag (int, optional): An ats_api recognized
                constant that determines whether or not the input bandwidth
                is reduced to ~ 20 MHz.

        Returns:
            labrad.units.Value: The input voltage range after rounding to
            the smallest available option that is less than or equal to
            input_voltage_range specified by the user.

        """
        if input_voltage_range['mV'] > 4000:
            raise Exception("Maximum input voltage range is 4 Volts.")
        elif input_voltage_range['mV'] < 40:
            raise Exception("Minimum input voltage range is 40 milliVolts.")
        else:
            available_ranges_in_milli_volts = \
                [4000, 2000, 1000, 400, 200, 100, 40]

            def find_min_position(array, offset):
                plus_array = [elem for elem in array if elem-offset >= 0]
                min_elem = min(plus_array)
                return min_elem, array.index(min_elem)

            min_positive_value, min_positive_index = \
                find_min_position(available_ranges_in_milli_volts,
                                  input_voltage_range['mV'])
            input_voltage_range_as_ats_constant = \
                INPUT_VOLTAGE_RANGES[min_positive_index]
            input_voltage_range = \
                available_ranges_in_milli_volts[min_positive_index] * mV
        if input_voltage_range_as_ats_constant not in INPUT_VOLTAGE_RANGES:
            raise Exception("input_range must be in INPUT_VOLTAGE_RANGES." +
                            str(input_voltage_range))
        if input_coupling not in [ats.DC_COUPLING, ats.AC_COUPLING]:
            raise Exception("input_coupling must be either AC or DC coupled.")
        if bandwidth_limit_flag not in [0, 1]:
            raise Exception("Acceptable values for the bandwidth_limit_flag "
                            "are: (i) 0 ==> Disabled or (ii) 1 ==> enabled.")

        for channel_id in CHANNEL_IDS:
            self.adc_board_handle.inputControlEx(
                channel_id,
                input_coupling,
                input_voltage_range_as_ats_constant,
                ADC_INPUT_IMPEDANCE)
            self.adc_board_handle.setBWLimit(channel_id, bandwidth_limit_flag)
        return input_voltage_range

    def configure_adc_trigger_settings(self,
                                       trigger_level,
                                       trigger_delay,
                                       timeout_ticks=0):
        """Configures the trigger level, delay, logic, and timeout settings.

        Note: we implicitly assume a single-engine rising edge trigger, i.e.
        the ADC will trigger when the voltage across the TRIG IN port goes
        from below trigger_level to above it after waiting by the amount of
        time specified by trigger_delay.

        Args:
            trigger_level (labrad.units.Value): see the __init__ docstring
                for details. See pp. 218 of the ATS-SDK-Guide.pdf for more
                info.
            trigger_delay (labrad.units.Value): see the __init__ docstring
                or pp. 217 of the ATS-SDK-Guide.pdf for more details.
            timeout_ticks (int, optional): The time to wait (in implicit units
                of 10 microseconds) for a trigger event before automatically
                generating a trigger event. Defaults to 0 ==> wait forever
                for a trigger event. See pp. 230 of the ATS-SDK-Guide.pdf
                for more info.

        Returns:
            (labrad.units.Value): the trigger_delay in units of time after
            rounding to the nearest integer number of 1/sampling_rate.

        """
        # 0 ==> wait forever for a trigger event see pg. 223
        if trigger_level['V'] > 5.0:
            raise Exception("The trigger level must be between 0 and 5 Volts.")
        trigger_level = 128 + int(127. * trigger_level['V']/5.) # see pg. 220
        # see AlazarSetTriggerOperation on pg. 218 of SDK
        trigger_delay_in_samples = \
            int(trigger_delay['s'] * self.sampling_rate['S/s'])
        trigger_delay = (trigger_delay_in_samples/self.sampling_rate['S/s']) \
            * s
        if trigger_delay_in_samples < 0 or trigger_delay_in_samples > 9999999:
            raise Exception("The trigger delay in units of ADC samples must "
                            "be >= 0 and <= 9,999,999.")
        e1 = self.adc_board_handle.setTriggerOperation(
            ats.TRIG_ENGINE_OP_J,
            ats.TRIG_ENGINE_J,
            ats.TRIG_EXTERNAL,
            ats.TRIGGER_SLOPE_POSITIVE,
            trigger_level,
            ats.TRIG_ENGINE_K,
            ats.TRIG_DISABLE, # using single trigger (enginer J) that triggers on on low-to-high logic
            ats.TRIGGER_SLOPE_POSITIVE,
            trigger_level)
        self.adc_board_handle.setExternalTrigger(ats.DC_COUPLING, ats.ETR_5V) # only option is 5V entire range for ATS9870
        self.adc_board_handle.setTriggerDelay(trigger_delay_in_samples)
        self.adc_board_handle.setTriggerTimeOut(timeout_ticks)
        return trigger_delay

    def compute_adc_memory_requirements(self, number_of_triggers,
                                        demodulation_time):
        """Computes the actual number of triggers based on ADC requirements.

        Note 1: the number_of_triggers must be rounded in order to fill an
        integer number of DMA buffers. This is particularly important when
        either the number_of_triggers or the demodulation_time is large since
        all of the data can no longer fit in a single DMA buffer. In this case
        the number of triggers is rounded up, meaning that the DACs need to
        fire more triggers than the number specified by the user!
        Note 2: the demodulation_time must have a minimum of 256 samples and
        must be an integer multiple of 64 samples.

        Args:
            number_of_triggers (int): see the __init__ docstring for more
                details.
            demodulation_time (labrad.units.Value): see the __init__
                docstring for more details.

        Returns:
            tuple[int]: (the actual number of triggers the ADC needs to
            fill its buffers, the actual number of samples per trigger
            after rounding to the nearest multiple of 64, the number of
            triggered readings that fit into each buffer, and the number of
            recycled buffers).

        """

        number_of_triggers = int(number_of_triggers)
        if number_of_triggers > 65.5e3:
            raise Exception("The number of cycles must be < 65535 = 2**16-1.")

        number_of_samples_per_trigger = int(demodulation_time['s'] *
                                            self.sampling_rate['S/s'])
        if number_of_samples_per_trigger < MINIMUM_NUMBER_OF_SAMPLES:
            number_of_samples_per_trigger = MINIMUM_NUMBER_OF_SAMPLES
        else:
            samples_above_required_minimum = \
                number_of_samples_per_trigger - MINIMUM_NUMBER_OF_SAMPLES
            if samples_above_required_minimum % 64:
                div_64 = samples_above_required_minimum // 64 + 1
                number_of_samples_per_trigger = 256 + 64 * div_64

        if not isinstance(number_of_triggers, int):
            raise Exception('The number_of_records must be an integer.')
        if number_of_triggers < 1:
            raise Exception('The number_of_records must be at least one.')

        bytes_per_trigger = number_of_samples_per_trigger * BYTES_PER_SAMPLE
        memory_size = NUMBER_OF_CHANNELS * bytes_per_trigger * \
            number_of_triggers
        if memory_size < MAXIMUM_BUFFER_SIZE/20:
            number_of_triggers_per_buffer = number_of_triggers
            number_of_recycled_buffers = 1
        else:
            optimal_buffer_size = MAXIMUM_BUFFER_SIZE / 10
            number_of_triggers_per_buffer = optimal_buffer_size / \
                (NUMBER_OF_CHANNELS * bytes_per_trigger)
            buffers_per_acquisition = \
                (number_of_triggers - 1) // number_of_triggers_per_buffer + 1
            number_of_triggers = buffers_per_acquisition * \
                number_of_triggers_per_buffer
            number_of_recycled_buffers = 3

        return (number_of_triggers, number_of_samples_per_trigger,
                number_of_triggers_per_buffer, number_of_recycled_buffers)

    def configure_adc_buffers(self):
        """Creates the necessary buffers for NPT AutoDMA acquisition.

        Note: both the records_buffer and dma_buffers can be reused in
        order to cut down on memory leaks. However, a new object must be
        created if the number_of_triggers, demodulation_time,
        input_voltage_range, sampling_rate, trigger_level, or trigger_delay
        are changed.

        Returns:
            tuple(numpy.ndarray, list[ats_api.DMABuffer]): a tuple containing
            a records_buffer and a list of DMA buffers to be used in the
            acquire_data method.

        """
        total_number_of_samples = NUMBER_OF_CHANNELS * \
                                  self.number_of_triggers * \
                                  self.number_of_samples_per_trigger
        records_buffer = np.empty(total_number_of_samples, dtype=np.uint8)

        bytes_per_trigger = self.number_of_samples_per_trigger * \
                            BYTES_PER_SAMPLE
        bytes_per_buffer = bytes_per_trigger * \
                           self.number_of_triggers_per_buffer * \
                           NUMBER_OF_CHANNELS

        sample_data_type = ctypes.c_uint8
        dma_buffers = []
        for ii in range(0, self.number_of_recycled_buffers):
            dma_buffers.append(
                ats.DMABuffer(sample_data_type, bytes_per_buffer))

        self.adc_board_handle.setRecordSize(NUMBER_OF_PRE_TRIGGER_SAMPLES,
                                            self.number_of_samples_per_trigger)
                                            
        iq_buffers = np.empty((self.number_of_triggers, 2), dtype=np.float32)
        print(type(dma_buffers[0]))
        return records_buffer, dma_buffers, iq_buffers

    def acquire_data(self):
        """

        Returns:

        """
        self.adc_board_handle.beforeAsyncRead(
            CHANNEL_LOGIC_FOR_A_AND_B,
            NUMBER_OF_PRE_TRIGGER_SAMPLES,
            self.number_of_samples_per_trigger,
            self.number_of_triggers_per_buffer,
            self.number_of_triggers,
            ats.ADMA_EXTERNAL_STARTCAPTURE |
            ats.ADMA_NPT)
        # post dma buffers to ADC
        for dma_buffer in self.dma_buffers:
            self.adc_board_handle.postAsyncBuffer(dma_buffer.addr,
                                                  dma_buffer.size_bytes)
        number_of_buffers_acquired = 0
        buffer_size = NUMBER_OF_CHANNELS * \
            self.number_of_triggers_per_buffer * \
            self.number_of_samples_per_trigger
        self.adc_board_handle.startCapture()
        total_number_of_buffers_to_fill = self.number_of_triggers \
            / self.number_of_triggers_per_buffer
        try:
            while number_of_buffers_acquired < \
                    total_number_of_buffers_to_fill:
                dma_buffer = self.dma_buffers[number_of_buffers_acquired %
                                              self.number_of_recycled_buffers]
                self.adc_board_handle.waitAsyncBufferComplete(dma_buffer.addr,
                                                              timeout_ms=10000)

                buffer_position = buffer_size * number_of_buffers_acquired
                self.records_buffer[
                    buffer_position:buffer_position + buffer_size] \
                    = dma_buffer.buffer
                self.adc_board_handle.postAsyncBuffer(dma_buffer.addr,
                                                      dma_buffer.size_bytes)
                number_of_buffers_acquired += 1
        except BaseException:
            raise
        finally:
            self.adc_board_handle.abortAsyncRead()
        t1 = time.time()
        records_buffer_view = self.records_buffer.view()
        records_buffer_view.shape = (total_number_of_buffers_to_fill,
                                     NUMBER_OF_CHANNELS,
                                     self.number_of_triggers_per_buffer,
                                     self.number_of_samples_per_trigger)
        records_buffer_view = np.rollaxis(records_buffer_view, 2, 1).\
            reshape(self.number_of_triggers,
                    NUMBER_OF_CHANNELS,
                    self.number_of_samples_per_trigger)

        self.reshaped_records_buffer = \
            records_buffer_view.astype(np.float32, copy=False)
        code_zero = float(1 << (BITS_PER_SAMPLE - 1)) - 0.5
        code_range = float(1 << (BITS_PER_SAMPLE - 1)) - 0.5
        self.reshaped_records_buffer -= code_zero
        self.reshaped_records_buffer *= (self.input_voltage_range['V'] / code_range)
        
    def get_records(self, trigger_number=0, number_of_triggers=1):
        return self.reshaped_records_buffer[trigger_number::number_of_triggers] * V
        
    def get_average(self, trigger_number=0, number_of_triggers=1):
        return np.mean(self.reshaped_records_buffer[trigger_number::number_of_triggers], axis=0) * V
        
    def get_times(self):
        n = self.number_of_samples_per_trigger
        f_s = self.sampling_rate['GS/s']
        t = np.linspace(0, n - 1, n)
        return (t / f_s) * ns
        
    def get_iqs(self, ch_a_weight, ch_b_weight):
        n_samples_per_trigger = self.number_of_samples_per_trigger
        n_triggers = self.number_of_triggers
        
        ch_a = ch_a_weight['']
        ch_b = ch_b_weight['']
        
        ch_a_len = len(ch_a)
        if ch_a_len > n_samples_per_trigger:
            ch_a = ch_a[:n_samples_per_trigger]
        elif ch_a_len < n_samples_per_trigger:
            ch_a = np.hstack([ch_a, np.zeros(n_samples_per_trigger - ch_a_len)])

        ch_b_len = len(ch_b)
        if ch_b_len > n_samples_per_trigger:
            ch_b = ch_b[:n_samples_per_trigger]
        elif ch_b_len < n_samples_per_trigger:
            ch_b = np.hstack([ch_b, np.zeros(n_samples_per_trigger - ch_b_len)])
            
        chs = np.stack([np.hstack([ch_a, ch_b]).T,
                        np.hstack([-ch_b, ch_a]).T], axis=1)
        
        try:
            np.dot(self.reshaped_records_buffer.reshape(n_triggers, -1), np.float32(chs),
                   self.iq_buffers)
        except Exception as e:
            # print(type(self.reshaped_records_buffer))
            # print 'n_triggers %d' % n_triggers
            # print 'reshaped_records_buffer.shape'
            # print self.reshaped_records_buffer.shape
            # print 'size of second dotted array %d' % len(np.float32(chs))
            print e
            
        self.iq_buffers /= n_samples_per_trigger

        return self.iq_buffers * V