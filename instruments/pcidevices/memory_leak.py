import numpy as np
import time
import keysightSD1 as keySD
AWG_TYPE = 'M3202A'
UNIQUE_SLOT_NUMBERS = [2, 3, 4]
CHASSIS_NUMBER=0
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

t = np.arange(0, 1000, 0.1)
waveform1 = np.sin(2.0*np.pi*t) #map to CH1
waveform2 = np.cos(2.0*np.pi*t) #map to CH2
waveform3 = -np.sin(2.0*np.pi*t) #map to CH3
waveform4 = -np.cos(2.0*np.pi*t) #map to CH4



def initialize_awg(slot_number, channel_numbers=[1, 2, 3, 4], chassis_number=0):
    awg = keySD.SD_AOU()
    open_error_code = awg.openWithSlot(AWG_TYPE, CHASSIS_NUMBER, slot_number)
    if open_error_code < 0:
        print("open_error_code=", open_error_code)
    flushing_error_code = awg.waveformFlush()
    if flushing_error_code < 0:
        print("flushing_error_code=", flushing_error_code)
    for channel_number in channel_numbers:
        waveshape_error_code = awg.channelWaveShape(channel_number,
                                                    keySD.SD_Waveshapes.AOU_AWG)
        if waveshape_error_code < 0:
            print("waveshape_error_code=", waveshape_error_code)
    return awg
    
    
def create_keysight_waveform_objects():
    keysight_waveform_object1 = keySD.SD_Wave()
    keysight_waveform_object2 = keySD.SD_Wave()
    keysight_waveform_object3 = keySD.SD_Wave()
    keysight_waveform_object4 = keySD.SD_Wave()
    
    create_waveform_error_code = \
        keysight_waveform_object1.newFromArrayDouble(
                keySD.SD_WaveformTypes.WAVE_ANALOG,
                waveform1.tolist())
    if create_waveform_error_code < 0:
        print("create_waveform_error_code1=", create_waveform_error_code)
    create_waveform_error_code = \
        keysight_waveform_object2.newFromArrayDouble(
                keySD.SD_WaveformTypes.WAVE_ANALOG,
                waveform2.tolist())
    if create_waveform_error_code < 0:
        print("create_waveform_error_code2=", create_waveform_error_code)
    create_waveform_error_code = \
        keysight_waveform_object3.newFromArrayDouble(
                keySD.SD_WaveformTypes.WAVE_ANALOG,
                waveform3.tolist())
    if create_waveform_error_code < 0:
        print("create_waveform_error_code3=", create_waveform_error_code)
    create_waveform_error_code = \
        keysight_waveform_object4.newFromArrayDouble(
                keySD.SD_WaveformTypes.WAVE_ANALOG,
                waveform4.tolist())
    if create_waveform_error_code < 0:
        print("create_waveform_error_code4=", create_waveform_error_code)
    return keysight_waveform_object1, keysight_waveform_object2, \
           keysight_waveform_object3, keysight_waveform_object4
           
def load_waveforms_onto_awg(awg, waveforms):
    for ii in range(0, len(waveforms)):
        keysight_waveform_object = waveforms[ii]
        load_waveform_error_code = awg.waveformLoad(keysight_waveform_object, ii+1)
        if load_waveform_error_code < 0:
            print("load_waveform_error_code=", load_waveform_error_code)
            
def queue_waveforms(awg, channel_numbers=[1, 2, 3, 4],
                   trigger_mode=keySD.SD_TriggerModes.EXTTRIG,
                   start_delay=0, cycles=5000, prescalar=0):
    for channel_number in channel_numbers:
        queue_waveform_error_code = awg.AWGqueueWaveform(channel_number,
                                                         channel_number,
                                                         trigger_mode,
                                                         start_delay, cycles,
                                                         prescalar)
        if queue_waveform_error_code < 0:
            print("queue_waveform_error_code=", queue_waveform_error_code)
            
def configure_awg(awg, channel_numbers=[1, 2, 3, 4]):
    """Configures an AWG with waveforms loaded onto it to look for
    a trigger.

    Args:
        awg (SD_AOU object): A Keysight module identifier object.
        channel_numbers (list, optional): A list of channel numbers for
            the AWG that should be configured. Default
            is to initialize all channels.

    """
    sync_mode = 1
    for channel_number in channel_numbers:
        sync_mode_error_code = awg.AWGqueueSyncMode(channel_number, sync_mode)
        if sync_mode_error_code < 0:
            print("sync_mode_error_code=", sync_mode_error_code)
    for channel_number in channel_numbers:
        configure_trigger_error_code = awg.AWGtriggerExternalConfig(
        channel_number,
        TRIGGER_SOURCES['Trigger 0'],
        TRIGGER_BEHAVIORS['Rising Edge'],
        TRIGGER_SYNC_MODE['Nearest CLK Edge'])
        if configure_trigger_error_code < 0:
            print("configure_trigger_error_code=", configure_trigger_error_code)
    for channel_number in channel_numbers:
        set_amplitude_error_code = awg.channelAmplitude(channel_number, 1.5)
        if set_amplitude_error_code < 0:
            print("set_amplitude_error_code=", set_amplitude_error_code)
    for channel_number in channel_numbers:
        start_awg_error_code = awg.AWGstart(channel_number)
        if start_awg_error_code < 0:
            print("start_awg_error_code=", start_awg_error_code)
            
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
    if trigger_value not in TRIGGER_VALUES.values():
        raise Exception("Invalid trigger_value. See the TRIGGER_VALUES"
                        " dictionary for a complete set of options.")
    if trigger_source not in TRIGGER_SOURCES.values():
        raise Exception("Invalid trigger_number. See the "
                        "TRIGGER_SOURCES dictionary"
                        " for a complete set of options.")
    trigger_error_code = awg.PXItriggerWrite(trigger_source,
                                             trigger_value)
    if trigger_error_code < 0:
        slot_number = awg.getSlot()
        raise Exception("While sending a backplane trigger to the AWG"
                        " in slot number %i," % slot_number + "error code %i"
                        " was encountered." % trigger_error_code)
            
            
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
    """Closes all AWGs after waveform generation to free resources.

    Args:
        awgs (list[SD_AOU object]): A list of Keysight AWG objects
        configured for triggering.

    """
    for awg in awgs:
        close_error_code = awg.close()
        if close_error_code < 0:
            print("close_error_code=", close_error_code)
            

for ii in range(0, 10000):     
    t0 = time.time()
    awg2 = initialize_awg(2)
    waveforms_for_awgs2 = create_keysight_waveform_objects() # all the same here but could in principle be different
    load_waveforms_onto_awg(awg2, waveforms_for_awgs2)
    queue_waveforms(awg2)

    awg3 = initialize_awg(3)
    waveforms_for_awgs3 = create_keysight_waveform_objects() # all the same here but could in principle be different
    load_waveforms_onto_awg(awg3, waveforms_for_awgs3)
    queue_waveforms(awg3)

    awg4 = initialize_awg(4)
    waveforms_for_awgs4 = create_keysight_waveform_objects() # all the same here but could in principle be different
    load_waveforms_onto_awg(awg4, waveforms_for_awgs4)
    queue_waveforms(awg4)

    configure_awg(awg2)
    configure_awg(awg3)
    configure_awg(awg4)
    awgs = [awg2, awg3, awg4]

    trigger_awgs(awgs)
    time.sleep(2.0*5000*len(t)*1e-9)
    close_awgs(awgs)
    tf = time.time()
    print("tf-t0=", tf-t0)
    print("ii=", ii)
    
    