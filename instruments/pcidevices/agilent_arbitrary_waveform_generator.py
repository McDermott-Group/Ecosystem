# Use at your own risk - A. Opremcak
import keysightSD1 as keySD
import numpy as np

AWG_TYPE = 'M3202A'
KEYSIGHT_LIBRARY_PATH = "C:\\Program Files (x86)\\Keysight" \
                        "\\SD1\\Libraries\\Python\\keysightSD1"
TRIGGER_SOURCES = {
    'Trigger 0': 4000,
    'Trigger 1': 4001,
    'Trigger 2': 4002,
    'Trigger 3': 4003,
    'Trigger 4': 4004,
    'Trigger 5': 4005,
    'Trigger 6': 4006,
    'Trigger 7': 4007,
}
TRIGGER_VALUES = {
    'High': 0,
    'Low': 1,
}
TRIGGER_SYNC_MODE ={
    'Nearest CLK Edge': 1,
    'Immediate': 0,
}
TRIGGER_BEHAVIORS = {
    'Active High': 1,
    'Active Low': 2,
    'Rising Edge': 3,
    'Falling Edge': 4
}


def create_awg_object(slot_number, chassis_number=0):
    """Creates a Keysight arbitrary waveform generator (AWG) object.

    Args:
        slot_number (int): The physical slot number on the PXIe Chassis.
            Note that slot_number 1 is reserved for the M9022A PXIe system
            module. Slot numbers 2 through 10 may be used for M3202A AWGs.
        chassis_number (int, optional): The chassis number containing
            the awg you are attempting to communicate with. Defaults
            to zero as we currently only have one.

    Returns:
        SD_AOU object: A Keysight module identifier object initialized
        for the specified (slot_number, chassis_number) pair.

    """
    if isinstance(slot_number, int) and slot_number in range(2, 11):
        awg = keySD.SD_AOU()
        open_error_code = awg.openWithSlot(AWG_TYPE, chassis_number,
                                           slot_number)
        if open_error_code < 0:
            raise Exception("While opening the AWG in slot number %i,"
                            % slot_number + " error code %i was encountered."
                            % open_error_code + " See the SD_Error() class in"
                            " location: " + KEYSIGHT_LIBRARY_PATH +
                            " for more details.")
        return awg
    else:
        raise Exception("slot_number must be an integer from 2 to 10.")


def flush_waveforms_from_awg(awg):
    """Deletes all waveforms from the AWGs onboard RAM.

    Args:
        awg (SD_AOU object): A properly initialized Keysight module
            identifier object returned by create_awg_object().

    """
    flushing_error_code = awg.waveformFlush()
    if flushing_error_code < 0:
        slot_number = awg.getSlot()
        raise Exception("While flushing waveforms from the AWG in"
                        " slot number %i," % slot_number + " error code %i"
                        " was encountered." % flushing_error_code +
                        " See the SD_Error() class in location: " +
                        KEYSIGHT_LIBRARY_PATH + " for more details.")


def configure_awg_channel(awg, channel_number,
                          output_mode=keySD.SD_Waveshapes.AOU_AWG):
    """Sets the waveshape type for a given AWG channel number.

    Args:
        awg (SD_AOU object): A Keysight module identifier object.
        channel_number (int): The channel number of the AWG that
            will be configured.
        output_mode (int, optional)): A Keysight defined constant
            specifying the desired waveshape for the channel number
            of interest. Defaults to keySD.SD_Waveshapes.AOU_AWG
            indicating the channel will be used in AWG mode.

    """
    if channel_number in [1, 2, 3, 4]:
        waveshape_error_code = awg.channelWaveShape(channel_number,
                                                    output_mode)
        if waveshape_error_code < 0:
            slot_number = awg.getSlot()
            raise Exception("While configuring the wave shape for the AWG in"
                            " slot number %i" % slot_number + ' with channel'
                            ' number %i, ' % channel_number + "error code %i"
                            " was encountered." % waveshape_error_code +
                            " See the SD_Error() class in location: " +
                            KEYSIGHT_LIBRARY_PATH + " for more details.")
    else:
        raise Exception("channel_number must be an integer from 1 to 4.")


def initialize_awg(slot_number,
                   channel_numbers=[1, 2, 3, 4],
                   chassis_number=0):
    """Creates an initialized AWG object with flushed waveforms and
    configured channels.

    Args:
        slot_number (int): The physical slot number on the PXIe Chassis
            that the AWG is in.
        channel_numbers (list, optional): A list of channel numbers for
            the AWG in slot_number that should be initialized. Default
            is to initialize all channels.
        chassis_number (int, optional): The chassis number containing
            the awg you are attempting to communicate with. Defaults
            to zero as we currently only have one.

    Returns:
        SD_AOU object: A Keysight module identifier object initialized
        for the specified (slot_number, chassis_number) pair with
        flushed waveforms and configured channels.

    """
    awg = create_awg_object(slot_number, chassis_number)
    flush_waveforms_from_awg(awg)
    for channel_number in channel_numbers:
        configure_awg_channel(awg, channel_number,
                              output_mode=keySD.SD_Waveshapes.AOU_AWG)
    return awg


def create_keysight_waveform_object(waveform_data, waveform_name):
    """Creates a Keysight waveform object from a 1D numpy.ndarray.

    Args:
        waveform_data(numpy.ndarray): Waveform data in the form of
            a one dimensional numpy.ndarray.
        waveform_name(str): The waveform alias used in the
            general.waveforms.wfs_dict to build your waveforms.

    Returns:
        SD_Wave object with waveform_data loaded onto it. This SD_Wave
        object is subsequently loaded onto the AWG of interest using
        the mapping provided by the 'Keysight Waveforms List' from
        the Resources list in our ordinary experimental framework.

    """
    if isinstance(waveform_data, np.ndarray) and \
            len(waveform_data.shape) == 1:
        keysight_waveform_object = keySD.SD_Wave()
        create_waveform_error_code = \
            keysight_waveform_object.newFromArrayDouble(
                keySD.SD_WaveformTypes.WAVE_ANALOG,
                waveform_data.tolist())
        if create_waveform_error_code < 0:
            raise Exception("While creating the waveform with name %s,"
                            % waveform_name + " error code %i was"
                            " encountered." % create_waveform_error_code +
                            " See the SD_Error() class in location: " +
                            KEYSIGHT_LIBRARY_PATH + " for more details.")
        return keysight_waveform_object
    else:
        raise Exception("waveform_data must be of a 1D numpy.ndarray.")


def load_waveform_onto_awg(awg, keysight_waveform_object,
                           waveform_id):
    """Loads a Keysight waveform object onto the onboard RAM of an AWG.

    Note: Within a given AWG, all waveform_id's must be unique!!!

    Args:
        awg (SD_AOU object): A Keysight module identifier object.
        keysight_waveform_object (SD_Wave object): A Keysight waveform
            object with waveform data loaded onto it.
        waveform_id (int): A waveform ID used for mapping an SD_Wave
            onto an integer. This number cannot be used to refer to
            multiple waveforms and will be used later for waveform
            queueing.

    """
    if not isinstance(waveform_id, int) or waveform_id < 0:
        raise Exception("waveform_id must be an integer >= 0.")
    load_waveform_error_code = awg.waveformLoad(keysight_waveform_object,
                                                waveform_id)
    if load_waveform_error_code < 0:
        slot_number = awg.getSlot()
        raise Exception("While loading the waveform with waveform ID %i"
                        % waveform_id + " onto the AWG in slot number %i,"
                        % slot_number + " error code %i was encountered."
                        % load_waveform_error_code + " See the SD_Error() "
                        "class in location: " + KEYSIGHT_LIBRARY_PATH +
                        " for more details.")

### the prescalar is changed from 0 to 1 for longer time measurement.
### the topological project will change it back after the measurement.
### Please double check if this is not changed back.
def queue_waveform(awg, channel_number, waveform_id,
                   trigger_mode=keySD.SD_TriggerModes.EXTTRIG,
                   start_delay=0, cycles=1, prescalar=0):
    """Queues the specified waveform onto one of AWGs channels.

    Note 1: At this stage, the waveform data has already been loaded
    onto the AWG and has been mapped onto a necessarily unique
    waveform identifier.

    Note 2: In general, all AWGs within the chassis should be configured
    to 'fire' on a common PXI backplane trigger. For more information,
    refer to Keysight's documentation.

    Args:
        awg (SD_AOU object): A Keysight module identifier object.
        channel_number (int): The AWG channel number that the
            waveform will be queued onto.
        waveform_id (int): A waveform identifier that uniquely
            identifies previously loaded waveform data.
        trigger_mode (int, optional): A Keysight defined constant
            that specifies the type of trigger that the AWG channel
            should respond to.
        start_delay(int, optional): The delay between the trigger
            and waveform launch in implicit multiples of 10 * ns.
            The maximum delay is (2**16-1) * (10 * ns) ~ 655.35 * us.
            Defaults to 0
        cycles (int, optional): The number of times the waveform is
            repeated once launched; i.e., triggered. Zero specifies
            an infinite number of cycles.
        prescalar (int, optional): The waveform prescalar used to
            reduce the effective sampling rate in implicit multiples
            of five; i.e. output rate --> output rate/(5 * prescalar).
            Defaults to 0 ==> 1 GS/s.

    """
    cycles = int(cycles)
    if cycles > 65535:
        raise Exception("The number of cycles must be < 65535 = 2**16-1.")
    if cycles < 0:
        raise Exception("A negative number of cycles does not make sense.")
    if channel_number in [1, 2, 3, 4]:
        queue_waveform_error_code = awg.AWGqueueWaveform(channel_number,
                                                         waveform_id,
                                                         trigger_mode,
                                                         start_delay, cycles,
                                                         prescalar)
        if queue_waveform_error_code < 0:
            slot_number = awg.getSlot()
            raise Exception("While queueing the waveform with ID # %i"
                            % waveform_id + " onto the AWG in slot number %i,"
                            % slot_number + " error code %i was encountered."
                            % queue_waveform_error_code + " See the SD_Error()"
                            " class in location: " + KEYSIGHT_LIBRARY_PATH +
                            " for more details.")
    else:
        raise Exception("channel_number must be an integer from 1 to 4.")


def configure_synchronization_mode(awg, channel_number, sync_mode=1):
    """Configures the synchronization mode for the channel's queue.

    Args:
        awg (SD_AOU object): A Keysight module identifier object.
        channel_number (int): The AWG channel number whose
            synchronization mode you would like to configure.
        sync_mode (int, optional): An integer indicating the
            synchronization mode type. Defaults to 1 ==>
            synchronized to 10 MHz reference clock.

    """
    sync_mode_error_code = awg.AWGqueueSyncMode(channel_number, sync_mode)
    if sync_mode_error_code < 0:
        slot_number = awg.getSlot()
        raise Exception("While configuring the synchronization mode for the "
                        "AWG in slot number %i," % slot_number +
                        " error code %i was encountered."
                        % sync_mode_error_code + " See the SD_Error()"
                        " class in location: " + KEYSIGHT_LIBRARY_PATH +
                        " for more details.")


def set_channel_amplitude(awg, channel_number, amplitude_in_volts=1.5):
    """Sets the full scale range of a given channel.

    Note: This specified amplitude assumes a matched 50 Ohm load
    resistor; i.e. an open circuit voltage of 2 * amplitude_in_volts.

    Args:
        awg (SD_AOU object): A Keysight module identifier object.
        channel_number (int): The AWG channel number whose
            synchronization mode you would like to configure.
        amplitude_in_volts (float, optional): The amplitude in volts
            that you will measure across of 50 Ohm scope (e.g. the
            Joe-Scope) for waveform_data with value 1.0. ##### work out units as this is cludgy.

    """
    if np.abs(amplitude_in_volts) > 1.5:
        raise Exception("amplitude_in_volts must be < 1.5 in absolute value.")
    if not isinstance(amplitude_in_volts, float):
        raise Exception("amplitude_in_volts must be a float.")
    set_amplitude_error_code = awg.channelAmplitude(channel_number,
                                                    amplitude_in_volts)
    if set_amplitude_error_code < 0:
        slot_number = awg.getSlot()
        raise Exception("While setting the amplitude for the AWG in"
                        " slot number %i" % slot_number + ' with channel'
                        ' number %i, ' % channel_number + "error code %i"
                        " was encountered." % set_amplitude_error_code +
                        " See the SD_Error() class in location: " +
                        KEYSIGHT_LIBRARY_PATH + " for more details.")


def start_awg(awg, channel_number):
    """Starts the selected AWG from the beginning of its queue.

    Note: For each AWG channel, our queues consist of a single
    waveform repeated n_reps times.

    Args:
        awg (SD_AOU object): A Keysight module identifier object
            ready to be started.
        channel_number (int): The channel number of the AWG
            that you would like to start.

    """
    if channel_number not in [1, 2, 3, 4]:
        raise Exception("channel_number must be an integer from 1 to 4.")
    start_awg_error_code = awg.AWGstart(channel_number)
    if start_awg_error_code < 0:
        slot_number = awg.getSlot()
        raise Exception("While starting the AWG in slot number %i"
                        % slot_number + ' with channel number %i, '
                        % channel_number + "error code %i"
                        " was encountered." % start_awg_error_code +
                        " See the SD_Error() class in location: " +
                        KEYSIGHT_LIBRARY_PATH + " for more details.")


def configure_pxi_backplane_trigger(
            awg, channel_number,
            trigger_source=TRIGGER_SOURCES['Trigger 0'],
            trigger_behavior=TRIGGER_BEHAVIORS['Rising Edge'],
            sync_mode=TRIGGER_SYNC_MODE['Nearest CLK Edge']):
    """Configures the PXIe chassis for backplane triggering.

    Note: This is how all AWGs within a chassis can be configured to
    fire waveforms on a single trigger. At present, this will only
    work for modules in slots 2-5 as the trigger backplance for slots
    6-10 are not yet tied together. Waiting for input from Keysight or
    to graduate, whichever comes sooner...

    Args:
        awg (SD_AOU object): A Keysight module identifier object
            ready to be started.
        channel_number (int): The channel number of the AWG
            that you would like to configure for backplane
            triggering.
        trigger_source (int, optional): A Keysight defined constant
            used for specifying the trigger source that the AWG
            should look for. Defaults to PXIe backplane 'Trigger 0'.
        trigger_behavior (int, optional): A Keysight defined constant
            used for specifying the type of trigger event that will
            fire the AWG; e.g. 'High', 'Low', 'Rise', or 'Fall'.

    """
    if channel_number not in [1, 2, 3, 4]:
        raise Exception("channel_number must be an integer from 1 to 4.")
    if trigger_source not in list(TRIGGER_SOURCES.values()):
        raise Exception("Invalid trigger_number. See the "
                        "TRIGGER_SOURCES dictionary"
                        " for a complete set of options.")
    if trigger_behavior not in list(TRIGGER_BEHAVIORS.values()):
        raise Exception("Invalid trigger_behavior. See the "
                        "TRIGGER_BEHAVIORS dictionary"
                        " for a complete set of options.")
    configure_trigger_error_code = awg.AWGtriggerExternalConfig(
        channel_number,
        trigger_source,
        trigger_behavior,
        sync_mode)
    if configure_trigger_error_code < 0:
        slot_number = awg.getSlot()
        raise Exception("While configuring the backplane trigger for the AWG"
                        " in slot number %i," % slot_number + " error code %i"
                        " was encountered." % configure_trigger_error_code +
                        " See the SD_Error() class in location: " +
                        KEYSIGHT_LIBRARY_PATH + " for more details.")


def send_backplane_trigger_awg(awg, trigger_value,
                               trigger_source=TRIGGER_SOURCES['Trigger 0']):
    """Sets the digital value of a PXI trigger on backplane of PXIe Chassis.

    Note: The PXI triggers on slots 1-5 and on slot 6-10 are not
    tied together by default. This will need to be modified if more
    AWGs are purchased so that AWGs in slots 1-5 will trigger at the
    same time as AWGs in slots 6-10.

    Args:
        awg (SD_AOU object): A Keysight module identifier object
            used for specifying the trigger. Note
        trigger_value (int): 0 ==> ON, 1 ==> OFF. Yes there logic
            is negated. This isn't a typo.
        trigger_source (int, optional): A Keysight defined constant
            used for specifying the PXI Trigger number that should be
            set to the logic level defined by trigger_value.

    """
    if trigger_value not in list(TRIGGER_VALUES.values()):
        raise Exception("Invalid trigger_value. See the TRIGGER_VALUES"
                        " dictionary for a complete set of options.")
    if trigger_source not in list(TRIGGER_SOURCES.values()):
        raise Exception("Invalid trigger_number. See the "
                        "TRIGGER_SOURCES dictionary"
                        " for a complete set of options.")
    trigger_error_code = awg.PXItriggerWrite(trigger_source,
                                             trigger_value)
    if trigger_error_code < 0:
        slot_number = awg.getSlot()
        raise Exception("While sending a backplane trigger to the AWG"
                        " in slot number %i," % slot_number + "error code %i"
                        " was encountered." % trigger_error_code +
                        " See the SD_Error() class in location: " +
                        KEYSIGHT_LIBRARY_PATH + " for more details.")


def close_awg(awg):
    """Releases all resources there were allocated to an AWG.

    Note: This must always be called before exiting an application
    on all used AWGs.

    Args:
        awg (SD_AOU object): A Keysight AWG objects that needs
            to be closed.

    """
    close_error_code = awg.close()
    if close_error_code < 0:
        slot_number = awg.getSlot()
        raise Exception("While closing the AWG in slot number %i,"
                        % slot_number + " error code %i was encountered."
                        % close_error_code + " See the SD_Error() class"
                        " in location: " + KEYSIGHT_LIBRARY_PATH +
                        " for more details.")


def load_waveforms_onto_awg(awg, keysight_waveforms_list,
                            original_waveforms_dict, n_reps, waveform_id=0):
    """Loads waveforms onto a properly initialized AWG.

    Args:
        awg (SD_AOU object): A Keysight module identifier object
            corresponding to the AWG you would like to load waveforms
            onto.
        keysight_waveforms_list (list[KeysightWaveform]): A list of
            Keysight objects (see Class definition below) containing a
            mapping between the waveforms dictionary and a (slot_number,
            channel_number) pair.
        original_waveforms_dict (general.waveforms.wfs_dict): The usual
            dictionary of waveforms built in our experimental framework.
        n_reps (int): The number of times the waveform should be
            replayed after a trigger.
        waveform_id:

    Returns:

    """
    slot_number = awg.getSlot()
    channel_number_channel_id_pairs = []
    channel_slot_pairs = []
    for waveform_obect in keysight_waveforms_list:
        waveform_slot_number = waveform_obect.slot_number
        waveform_channel_number = waveform_obect.channel_number
        waveform_name = waveform_obect.waveform_name
        waveform_data = np.asarray(original_waveforms_dict[waveform_name])
        channel_slot_pairs.append(
            (waveform_slot_number, waveform_channel_number))
        if waveform_slot_number == slot_number:  # cycles
            keysight_waveform_object = create_keysight_waveform_object(
                waveform_data, waveform_name)
            load_waveform_onto_awg(awg, keysight_waveform_object, waveform_id)
            channel_number_channel_id_pairs.append(
                [waveform_channel_number, waveform_id])
            waveform_id += 1
    duplicate_pairs = find_duplicate_slot_channel_pairs(
        channel_slot_pairs)
    if len(duplicate_pairs) != 0:
        raise Exception("The following (slot_number, channel_number) pairs"
                        " are duplicated %s", str(duplicate_pairs) +
                        "All (slot_number, channel_number) pairs must be"
                        " otherwise unique waveform to DAC assignments are"
                        " ambiguous.")
    for pair in channel_number_channel_id_pairs:
        channel_number = pair[0]
        waveform_id = pair[1]
        queue_waveform(awg, channel_number, waveform_id, cycles=n_reps)


def find_duplicate_slot_channel_pairs(slot_number_channel_number_pairs):
    """Finds duplicate (slot_number, channel_number) pairs to avoid
    ambiguity in assigning waveform data to an AWG channel.

    Args:
        channel_number_slot_number_pairs(list(tuple)): A list of
            (slot_number, channel_number) pairs to be checked for
            duplicate entries.

    Returns:
        list[tuple]: A list of duplicated (slot_number, channel_number)
        pairs.

    """
    n_elements = len(slot_number_channel_number_pairs)
    duplicates = []
    for ii in range(0, n_elements):
        for jj in range(ii + 1, n_elements):
            if slot_number_channel_number_pairs[ii] == \
                    slot_number_channel_number_pairs[jj]:
                duplicates.append(slot_number_channel_number_pairs[ii])
    return duplicates


def configure_awg(awg, channel_numbers=[1, 2, 3, 4]):
    """Configures an AWG with waveforms loaded onto it to look for
    a trigger.

    Args:
        awg (SD_AOU object): A Keysight module identifier object.
        channel_numbers (list, optional): A list of channel numbers for
            the AWG that should be configured. Default
            is to initialize all channels.

    """
    for channel_number in channel_numbers:
        configure_synchronization_mode(awg, channel_number)
    for channel_number in channel_numbers:
        configure_pxi_backplane_trigger(awg, channel_number)
    for channel_number in channel_numbers:
        set_channel_amplitude(awg, channel_number)
    for channel_number in channel_numbers:
        start_awg(awg, channel_number)


def load_awgs(keysight_waveforms_list, original_waveforms_dict, n_reps,
              awgs=[]):
    """Prepares the AWGs for triggering, including initialization,
    waveform loading, synchronization settings.

    Args:
        keysight_waveforms_list (list[KeysightWaveform]): A list of
            Keysight objects (see Class definition below) containing a
            mapping between the waveforms dictionary and a (slot_number,
            channel_number) pair.
        original_waveforms_dict (general.waveforms.wfs_dict): The usual
            dictionary of waveforms built in our experimental framework.
        n_reps (int): The number of times the waveform should be
            replayed after a trigger.

    Returns:
        list[SD_AOU object]: A list of Keysight AWG objects with loaded
        waveforms, ready to be triggered.

    """
    unique_slot_numbers = []
    for keysight_waveform in keysight_waveforms_list:
        unique_slot_numbers.append(keysight_waveform.slot_number)
    unique_slot_numbers = list(set(unique_slot_numbers))
    for slot_number in unique_slot_numbers:
        awg = initialize_awg(slot_number)
        load_waveforms_onto_awg(awg, keysight_waveforms_list,
                                original_waveforms_dict, n_reps)
        awgs.append(awg)
    for awg in awgs:
        configure_awg(awg)
    if len(awgs) == 0:
        raise Exception("AWGs list is empty. A minimal experiment will"
                        " require at least an ADC trigger.")
    return awgs


def trigger_awgs(awgs):
    """Triggers all AWGs configured to fire on a common backplane trigger.

    Args:
        awgs (list[SD_AOU object]): A list of Keysight AWG objects
        configured for triggering.

    """
    awg = awgs[0]
    send_backplane_trigger_awg(awg, trigger_value=TRIGGER_VALUES['Low'])
    send_backplane_trigger_awg(awg, trigger_value=TRIGGER_VALUES['High'])
    send_backplane_trigger_awg(awg, trigger_value=TRIGGER_VALUES['Low'])
    send_backplane_trigger_awg(awg, trigger_value=TRIGGER_VALUES['High'])
    send_backplane_trigger_awg(awg, trigger_value=TRIGGER_VALUES['Low'])


def close_awgs(awgs):
    """Closes all AWGs after waveform generation to avoid a memory leak.

    Args:
        awgs (list[SD_AOU object]): A list of Keysight AWG objects
        configured for triggering.

    """
    for awg in awgs:
        close_awg(awg)


class KeysightWaveform:
    def __init__(self, slot_number, channel_number, waveform_name):
        """A named tuple with some basic type checking.

        Args:
            slot_number (int): An integer from 2 to 10 indicating
                which slot the AWG is located in within the PXIe
                Chassis.
            channel_number (int): An integer from 1 to 4 indicating
                which channel of the AWG in slot_number you would
                like to assign a waveform_name to.
            waveform_name (str): A str corresponding to a key from
            general.waveforms.wfs_dict corresponding to a collection
            of waveform data.
        """
        if isinstance(slot_number, int) and slot_number in range(2, 11):
            self.slot_number = slot_number
        else:
            raise Exception("slot_number must be an integer from 2 to 10.")
        if isinstance(channel_number, int) and channel_number in range(1, 5):
            self.channel_number = channel_number
        else:
            raise Exception("channel_number must be an integer from 1 to 4.")
        if isinstance(waveform_name, str):
            self.waveform_name = waveform_name
        else:
            raise Exception("waveform_name must be a string.")