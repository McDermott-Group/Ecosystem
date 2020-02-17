import time
import general.waveforms as wf
from labrad.units import us, ns, V, MHz, MS, s, deg
import agilent_arbitrary_waveform_generator as awg


ExptVars = {
            'R0 Drive Amplitude': 0.1 * V,
            'R0 Drive SB Frequency': 30.0 * MHz, 
            'R0 Drive Time': 1000 * ns, 
            'Total Time': 0.0 * us,
            
            'Dwell Amplitude': 0.5 * V,
            'Dwell Amplitude 2': 0.1 * V,
            'Dwell Time': 10 * ns, #+ 15.0 * us,
            'Dwell Time 2': 6 * ns,

            'Reps':5000,
           }
           
RO_I, RO_Q = wf.Harmonic(amplitude = ExptVars['R0 Drive Amplitude'],
                         frequency = ExptVars['R0 Drive SB Frequency'],
                         start     = ExptVars['Total Time'],
                         duration  = ExptVars['R0 Drive Time'])  
                         
DWELL = wf.DC(amplitude = ExptVars['Dwell Amplitude'],
            start   = RO_I.end,
            duration  = ExptVars['Dwell Time'])
DWELL2 = wf.DC(amplitude = ExptVars['Dwell Amplitude 2'],
            start   = DWELL.end,
            duration  = ExptVars['Dwell Time 2'])  
                              
original_waveforms_dict = wf.wfs_dict(wf.Waveform('RO_I', RO_I),
                  wf.Waveform('RO_Q', RO_Q),
                  wf.Waveform('DWELL', [DWELL, DWELL2]))
    
keysight_waveforms_list = [
    awg.KeysightWaveform(slot_number = 4, channel_number = 1, waveform_name = 'RO_I'),
    awg.KeysightWaveform(slot_number = 4, channel_number = 2, waveform_name = 'RO_Q'),
    awg.KeysightWaveform(slot_number = 4, channel_number = 3, waveform_name = 'DWELL'),
    awg.KeysightWaveform(slot_number = 4, channel_number = 4, waveform_name = 'RO_I'), #'ATS_Trigger'
    awg.KeysightWaveform(slot_number = 3, channel_number = 1, waveform_name = 'RO_Q'),
    awg.KeysightWaveform(slot_number = 3, channel_number = 2, waveform_name = 'DWELL'),
    awg.KeysightWaveform(slot_number = 3, channel_number = 3, waveform_name = 'RO_I'),
    awg.KeysightWaveform(slot_number = 3, channel_number = 4, waveform_name = 'RO_Q'),
    awg.KeysightWaveform(slot_number = 2, channel_number = 1, waveform_name = 'RO_Q'),
    awg.KeysightWaveform(slot_number = 2, channel_number = 2, waveform_name = 'DWELL'),
    awg.KeysightWaveform(slot_number = 2, channel_number = 3, waveform_name = 'RO_I'),
    awg.KeysightWaveform(slot_number = 2, channel_number = 4, waveform_name = 'RO_Q'),
]

for ii in range(0, 1000):
    awgs = []
    demodulation_time = ExptVars['R0 Drive Time']['s']
    n_reps = ExptVars['Reps']
    wait_time = 2.0 * n_reps * demodulation_time
    awgs = awg.load_awgs(keysight_waveforms_list, original_waveforms_dict, n_reps, awgs)
    time.sleep(wait_time)
    awg.trigger_awgs(awgs)
    time.sleep(wait_time) # make sure AWGs are finished firing waveforms
    awg.close_awgs(awgs)
    time.sleep(wait_time)
