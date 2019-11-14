import keysightSD1 as key
import numpy as np

AWG_TYPE = 'M3202A'

PXI_BACKPLANE_TRIGGERS = {
    'PXI Trigger 0': 4000,
    'PXI Trigger 1': 4001,
    'PXI Trigger 2': 4002,
    'PXI Trigger 3': 4003,
    'PXI Trigger 4': 4004,
    'PXI Trigger 5': 4005,
    'PXI Trigger 6': 4006,
    'PXI Trigger 7': 4007,
}

PXI_TRIGGER_VALUES = { 
    'High' : 0, # why keysight has negated logic I have no idea
    'Low' : 1,
}

PXI_TRIGGER_TYPES = {
    'Active High' : 1,
    'Active Low' : 2,
    'Rising Edge' : 3,
    'Falling Edge' : 4
}

def create_awg_object(slot_number, chassis_number=0):
    awg = key.SD_AOU()
    open_error_code = awg.openWithSlot(AWG_TYPE, chassis_number, slot_number)
    if open_error_code < 0:  ## probably want to raise error instead
        print("\tWhile opening the AWG in slot number %i," % slot_number)
        print("\t the following error code was encountered: %i" % open_error_code)
        print("\tSee the SD_Error() class in location")
        print("\tC:\Program Files (x86)\Keysight\SD1\Libraries\Python\keysightSD1")
        print("\tfor more details.")
        raise Exception
    return awg
    
def flush_waveforms_from_awg(awg, slot_number):
    flushing_error_code = awg.waveformFlush()
    if slot_number not in [2, 3, 4, 5, 6, 7, 8, 9, 10]:
        raise Exception("The value of slot_number must be an integer >=2 and <= 10.")
    if flushing_error_code < 0: ## probably want to raise error instead
        print("\tWhile flushing waveforms from the AWG in slot %i," % slot_number)
        print("\tthe following error code was encountered: %i." % flushing_error_code)
        print("\tSee the SD_Error() class in location")
        print("\tC:\Program Files (x86)\Keysight\SD1\Libraries\Python\keysightSD1")
        print("\tfor more details.")
        raise Exception

def configure_awg_channel(awg, channel_number, output_mode = key.SD_Waveshapes.AOU_AWG):  # key.SD_Waveshapes.AOU_OFF
    if channel_number in [1, 2, 3, 4]:
        waveshape_error_code = awg.channelWaveShape(channel_number, key.SD_Waveshapes.AOU_AWG)
    else:
        raise Exception("Invalid Channel Number")
    if waveshape_error_code < 0:
        print("\tWhile configuring the waveshape for the AWG in slot %i,", slot_number)
        print("\twith channel number %i, the following error code" % channel_number)
        print("was encountered: %i." % waveshape_error_code)
        print("\tSee the SD_Error() class in location")
        print("\tC:\Program Files (x86)\Keysight\SD1\Libraries\Python\keysightSD1")
        print("\tfor more details.")
        raise Exception
        
def create_keysight_waveform_object(waveform, waveform_name):  # waveform is a 1D numpy array, waveformID is a unique identifier (within an AWG)
    keysight_waveform_object = key.SD_Wave()
    create_waveform_error_code = keysight_waveform_object.newFromArrayDouble(key.SD_WaveformTypes.WAVE_ANALOG,   ### why double
                                                                    waveform.tolist())
    if create_waveform_error_code < 0:
        print("\tWhile creating waveform with name %s," % waveform_name)
        print("\tthe following error code was encountered: %i." % create_waveform_error_code)
        print("\tSee the SD_Error() class in location")
        print("\tC:\Program Files (x86)\Keysight\SD1\Libraries\Python\keysightSD1")
        print("\tfor more details.")
        raise Exception
    return keysight_waveform_object

def load_waveform_onto_awg(awg, slot_number, keysight_waveform_object, waveform_id):  #waveform_id a unique ID within an AWG
    if slot_number not in [2, 3, 4, 5, 6, 7, 8, 9, 10]:
        raise Exception("The value of slot_number must be an integer >=2 and <= 10.")
    if not isinstance(waveform_id, int) or waveform_id < 0:
        raise Exception("The waveform_id must be an integer >= 0.")
    load_waveform_error_code = awg.waveformLoad(keysight_waveform_object, waveform_id)
    if load_waveform_error_code < 0:  ## probably want to raise error instead
        print("\tWhile loading waveform with waveform_id %i " % waveform_id)
        print("\tonto the AWG in slot number %i," % slot_number)
        print("\tthe following error code was encountered: %i." % load_waveform_error_code)
        print("\tSee the SD_Error() class in location")
        print("\tC:\Program Files (x86)\Keysight\SD1\Libraries\Python\keysightSD1")
        print("\tfor more details.")
        raise Exception
        
def queue_waveform(awg, slot_number, channel_number, waveform_id, 
                   trigger_mode = key.SD_TriggerModes.EXTTRIG,
                   start_delay = 0, cycles = 1, prescalar = 0): #waveform must be loaded
    cycles = int(cycles)
    if cycles > 65535:
        raise Exception("Number of cycles must be <65535 = 2**16-1.")
    if channel_number in [1, 2, 3, 4]:
        # print("cycles=", cycles)
        queue_waveform_error_code = awg.AWGqueueWaveform(channel_number, waveform_id, trigger_mode,
                                                         start_delay, cycles, prescalar)
        if queue_waveform_error_code < 0:  ## probably want to raise error instead
            print("\tWhile queueing the waveform with id # %i " % waveform_id)
            print("\tonto the AWG in slot number %i, the following error" % slot_number)
            print("\tcode was encountered: %i." % queue_waveform_error_code)
            print("\tSee the SD_Error() class in location")
            print("\tC:\Program Files (x86)\Keysight\SD1\Libraries\Python\keysightSD1")
            print("\tfor more details.")
            raise Exception
    else:
        print("invalid channel number.")
        
def configure_synchronization_mode(awg, slot_number, channel_number, syncMode = 1):
    sync_mode_error_code = awg.AWGqueueSyncMode(channel_number, syncMode)
    if sync_mode_error_code < 0:
        print("\tWhile configuring the synchronization mode for the AWG in slot %i," % slot_number)
        print("\tthe following error code was encountered: %i." % sync_mode_error_code)
        print("\tSee the SD_Error() class in location")
        print("\tC:\Program Files (x86)\Keysight\SD1\Libraries\Python\keysightSD1")
        print("\tfor more details.")
        raise Exception

def set_channel_amplitude(awg, slot_number, channel_number, amplitude_in_volts = 1.5):
    # if np.abs(amplitude_in_volts) > 1.5:
        # raise Exception("amplitude_in_volts must be < 1.5 in absolute value.")
    set_amplitude_error_code = awg.channelAmplitude(channel_number, amplitude_in_volts)
    if set_amplitude_error_code < 0:  ## probably want to raise error instead
        print("\tWhile setting the amplitude of channel %i " %  channel_number)
        print("\tonto the AWG in slot number %i, the following error", slot_number)
        print("\tcode was encountered: %i.", set_amplitude_error_code)
        print("\tSee the SD_Error() class in location")
        print("\tC:\Program Files (x86)\Keysight\SD1\Libraries\Python\keysightSD1")
        print("\tfor more details.")
        raise Exception
        
def start_awg(awg, slot_number, channel_number):
    start_awg_error_code = awg.AWGstart(channel_number)
    if channel_number not in [1, 2, 3, 4]:
        raise Exception("Invalid Channel Number")
    if start_awg_error_code < 0:
        print("\tWhile starting the AWG in slot %i," % slot_number)
        print("\tthe following error code was encountered: %i." % start_awg_error_code)
        print("\tSee the SD_Error() class in location")
        print("\tC:\Program Files (x86)\Keysight\SD1\Libraries\Python\keysightSD1")
        print("\tfor more details.")
        raise Exception
        
def send_backplane_trigger_awg(awg, trigger_value, pxi_trigger_number = PXI_BACKPLANE_TRIGGERS['PXI Trigger 0']):
    if trigger_value not in PXI_TRIGGER_VALUES.values():
        raise Exception("Invalid Trigger Level.")
    if pxi_trigger_number not in PXI_BACKPLANE_TRIGGERS.values():
        raise Exception("Invalid PXI Trigger Number")
    trigger_error_code = awg.PXItriggerWrite(pxi_trigger_number, trigger_value) #should be a dictionary for EZ lookup
    if trigger_error_code < 0:
        print("\tWhile starting the AWG in slot %i," % slot_number)
        print("\tthe following error code was encountered: %i." % start_awg_error_code)
        print("\tSee the SD_Error() class in location")
        print("\tC:\Program Files (x86)\Keysight\SD1\Libraries\Python\keysightSD1")
        print("\tfor more details.")
        raise Exception
        
def configure_pxi_backplane_trigger(awg, channel_number, pxi_trigger_number = PXI_BACKPLANE_TRIGGERS['PXI Trigger 0'], #should be a dictionary for EZ lookup
                                    trigger_type = PXI_TRIGGER_TYPES['Rising Edge']):  #should be a dictionary for EZ lookup
    if channel_number not in [1, 2, 3, 4]:
        raise Exception("Invalid Channel Number")
    if pxi_trigger_number not in PXI_BACKPLANE_TRIGGERS.values():
        raise Exception("Invalid PXI Trigger Number")
    configure_pxi_trigger_error_code = awg.AWGtriggerExternalConfig(channel_number,
                                                                    pxi_trigger_number,
                                                                    trigger_type)
    if configure_pxi_trigger_error_code < 0:
        print("negative error code for trigger")
        
def close_awg(awg):
    close_error = awg.close()
    if close_error < 0:
        print("close_error was negative.")
        
def initialize_awg(slot_number, channel_numbers=[1, 2, 3, 4], chassis_number=0):
    awg = create_awg_object(slot_number, chassis_number)
    flush_waveforms_from_awg(awg, slot_number)
    for channel_number in channel_numbers:
        configure_awg_channel(awg, channel_number, output_mode = key.SD_Waveshapes.AOU_AWG) # turn off unused channels in separate step
    return awg
    
def load_waveforms_onto_awg(awg, slot_number, waveform_dict, n_reps, waveform_id):
    channel_number_channel_id_pairs = []
    for key in sorted(waveform_dict.keys()):
        waveform_name = key
        waveform_tuple = waveform_dict[waveform_name]
        waveform_slot_number = waveform_tuple[0]
        waveform_channel_number = waveform_tuple[1]
        waveform = waveform_tuple[2]
        # waveform_id = 0
        if waveform_slot_number == slot_number: #cycles
            keysight_waveform_object = create_keysight_waveform_object(waveform, waveform_name)
            load_waveform_onto_awg(awg, slot_number, keysight_waveform_object, waveform_id)
            channel_number_channel_id_pairs.append([waveform_channel_number, waveform_id])
            waveform_id += 1
    for pair in channel_number_channel_id_pairs:
        channel_number = pair[0]
        waveform_id = pair[1]
        queue_waveform(awg, slot_number, channel_number, waveform_id, cycles = n_reps)
        
            
def configure_awg(awg, slot_number, channel_numbers = [1, 2, 3, 4]):
    for channel_number in channel_numbers:
        configure_synchronization_mode(awg, slot_number, channel_number)
    for channel_number in channel_numbers:
        configure_pxi_backplane_trigger(awg, channel_number)
    for channel_number in channel_numbers:
        set_channel_amplitude(awg, slot_number, channel_number)
    for channel_number in channel_numbers:
        start_awg(awg, slot_number, channel_number)


        

# waveform1 = np.zeros(4000) # Create array of zeros with 1000 elements
# waveform1[0] = 0.0 # Initialize element 0 as -0.5
# for i in range(0, len(waveform1)): # This for..loop will increment from -0.5
    # waveform1[i] = 0.9 * np.sin(2.0*np.pi*0.01*float(i)) * np.exp(-float(i)/1000.)
# keysight_waveform_object1 = create_keysight_waveform_object(waveform1, waveform_name="decaying")

# waveform2 = np.zeros(4000) # Create array of zeros with 1000 elements
# waveform2[0] = 0.0 # Initialize element 0 as -0.5
# for i in range(0, len(waveform2)): # This for..loop will increment from -0.5
    # waveform2[i] = 0.9 * np.cos(2.0*np.pi*0.01*float(0))
# keysight_waveform_object2 = create_keysight_waveform_object(waveform2, waveform_name="non-decaying")
    
# waveform_dict = {
    # 'RO_I1': (4, 1, waveform1),
    # 'RO_I2': (4, 2, waveform1),
    # 'RO_I3': (4, 3, waveform1),
    # 'RO_I4': (4, 4, waveform1),
    # 'RO_Q1': (3, 1, waveform2),
    # 'RO_Q2': (3, 2, waveform2),
    # 'RO_Q3': (3, 3, waveform2),
    # 'RO_Q4': (3, 4, waveform2),
# }

# slot_number=4
# waveform_id = 0

# awg1 = create_awg_object(slot_number, chassis_number=0)
# flush_waveforms_from_awg(awg1, slot_number)
# configure_awg_channel(awg1, channel_number = 1, output_mode = key.SD_Waveshapes.AOU_AWG)
# configure_awg_channel(awg1, channel_number = 2, output_mode = key.SD_Waveshapes.AOU_AWG)
# configure_awg_channel(awg1, channel_number = 3, output_mode = key.SD_Waveshapes.AOU_AWG)
# configure_awg_channel(awg1, channel_number = 4, output_mode = key.SD_Waveshapes.AOU_AWG)

# load_waveform_onto_awg(awg1, slot_number, keysight_waveform_object1, 0)
# load_waveform_onto_awg(awg1, slot_number, keysight_waveform_object1, 1)
# load_waveform_onto_awg(awg1, slot_number, keysight_waveform_object1, 2)
# load_waveform_onto_awg(awg1, slot_number, keysight_waveform_object1, 3)

# queue_waveform(awg1, slot_number, 1, 0) #invalid waveform id doesn't raise an issue
# queue_waveform(awg1, slot_number, 2, 1)
# queue_waveform(awg1, slot_number, 3, 2)
# queue_waveform(awg1, slot_number, 4, 3)

# configure_synchronization_mode(awg1, slot_number, channel_number=1, syncMode = 1)
# configure_synchronization_mode(awg1, slot_number, channel_number=2, syncMode = 1)
# configure_synchronization_mode(awg1, slot_number, channel_number=3, syncMode = 1)
# configure_synchronization_mode(awg1, slot_number, channel_number=4, syncMode = 1)

# configure_pxi_backplane_trigger(awg1, channel_number=1)
# configure_pxi_backplane_trigger(awg1, channel_number=2)
# configure_pxi_backplane_trigger(awg1, channel_number=3)
# configure_pxi_backplane_trigger(awg1, channel_number=4)

# set_channel_amplitude(awg1, slot_number, channel_number = 1, amplitude_in_volts = 1.5) # doesn't error for amplitudes > 1.5
# set_channel_amplitude(awg1, slot_number, channel_number = 2, amplitude_in_volts = 1.5)
# set_channel_amplitude(awg1, slot_number, channel_number = 3, amplitude_in_volts = 1.5)
# set_channel_amplitude(awg1, slot_number, channel_number = 4, amplitude_in_volts = 1.5)

# start_awg(awg1, slot_number, channel_number = 1)
# start_awg(awg1, slot_number, channel_number = 2)
# start_awg(awg1, slot_number, channel_number = 3)
# start_awg(awg1, slot_number, channel_number = 4)

# # send_backplane_trigger_awg(awg, trigger_value = PXI_TRIGGER_VALUES['Low'])
# # send_backplane_trigger_awg(awg, trigger_value = PXI_TRIGGER_VALUES['High'])


# slot_number=3
# waveform_id_2 = 1
# awg2 = create_awg_object(slot_number, chassis_number=0)
# flush_waveforms_from_awg(awg2, slot_number)
# configure_awg_channel(awg2, channel_number = 1, output_mode = key.SD_Waveshapes.AOU_AWG)
# configure_awg_channel(awg2, channel_number = 2, output_mode = key.SD_Waveshapes.AOU_AWG)
# configure_awg_channel(awg2, channel_number = 3, output_mode = key.SD_Waveshapes.AOU_AWG)
# configure_awg_channel(awg2, channel_number = 4, output_mode = key.SD_Waveshapes.AOU_AWG)
    
# load_waveform_onto_awg(awg2, slot_number, keysight_waveform_object2, 0)
# load_waveform_onto_awg(awg2, slot_number, keysight_waveform_object2, 1)
# load_waveform_onto_awg(awg2, slot_number, keysight_waveform_object2, 2)
# load_waveform_onto_awg(awg2, slot_number, keysight_waveform_object2, 3)

# queue_waveform(awg2, slot_number, 1, 0) #invalid waveform id doesn't raise an issue
# queue_waveform(awg2, slot_number, 2, 1)
# queue_waveform(awg2, slot_number, 3, 2)
# queue_waveform(awg2, slot_number, 4, 3)

# configure_synchronization_mode(awg2, slot_number, channel_number=1, syncMode = 1)
# configure_synchronization_mode(awg2, slot_number, channel_number=2, syncMode = 1)
# configure_synchronization_mode(awg2, slot_number, channel_number=3, syncMode = 1)
# configure_synchronization_mode(awg2, slot_number, channel_number=4, syncMode = 1)

# configure_pxi_backplane_trigger(awg2, channel_number=1)
# configure_pxi_backplane_trigger(awg2, channel_number=2)
# configure_pxi_backplane_trigger(awg2, channel_number=3)
# configure_pxi_backplane_trigger(awg2, channel_number=4)

# set_channel_amplitude(awg2, slot_number, channel_number = 1, amplitude_in_volts = 1.5) # doesn't error for amplitudes > 1.5
# set_channel_amplitude(awg2, slot_number, channel_number = 2, amplitude_in_volts = 1.5)
# set_channel_amplitude(awg2, slot_number, channel_number = 3, amplitude_in_volts = 1.5)
# set_channel_amplitude(awg2, slot_number, channel_number = 4, amplitude_in_volts = 1.5)

# start_awg(awg2, slot_number, channel_number = 1)
# start_awg(awg2, slot_number, channel_number = 2)
# start_awg(awg2, slot_number, channel_number = 3)
# start_awg(awg2, slot_number, channel_number = 4)

# send_backplane_trigger_awg(awg2, trigger_value = PXI_TRIGGER_VALUES['Low'])
# send_backplane_trigger_awg(awg2, trigger_value = PXI_TRIGGER_VALUES['High'])
# # send_backplane_trigger_awg(awg2, trigger_value = PXI_TRIGGER_VALUES['Low'])
# # send_backplane_trigger_awg(awg2, trigger_value = PXI_TRIGGER_VALUES['High'])

# close_awg(awg1)
# close_awg(awg2)