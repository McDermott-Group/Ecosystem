import time
import numpy as np
import matplotlib.pyplot as plt

import labrad
from labrad.units import V, ns, s, MS

# API_SUCCESS = 512


def test_ats_configuration(input_range=4*V,
                           sampling_rate=500*MS/s,
                           trigger_delay=0*ns,
                           samples_per_record=16382*ns,
                           number_of_records=10000):
    print('Testing the basic board functionality.')

    cxn = labrad.connect()
    ats = cxn.ats_waveform_digitizer
    ats.select_device()
    
    print('\nTurning the LED on for 1 sec.')
    ats.set_led_state(1)
    time.sleep(1)
    print('Turning the LED off.')
    ats.set_led_state(0)
    
    print('Configuring the boards...')
    ats.configure_inputs(input_range)
    ats.sampling_rate(sampling_rate)
    ats.configure_trigger(trigger_delay)
    ats.samples_per_record(samples_per_record)
    ats.number_of_records(number_of_records)
    ats.configure_buffers()
    
    print('\nAcquring the channel information...') 
    [samples_per_channel, bits_per_sample] = ats.get_channel_info()
    print('There are %d samples per channel, %d bits per sample.'
            %(samples_per_channel, bits_per_sample))
    print('Records to be acquired: %d.' %ats.number_of_records())
    
    print('\nIs board busy?')
    print('%s.' %ats.busy())
    
def test_ats():
    cxn = labrad.connect()
    digitizer = cxn.ats_waveform_digitizer
    digitizer.select_device("ATS1::1")
    digitizer.configure_clock_reference()
    digitizer.configure_trigger()

    digitizer.configure_inputs(.1*V)
    digitizer.samples_per_record(512)
    digitizer.records_per_buffer(1)
    digitizer.number_of_records(1)
    digitizer.configure_buffers()

    t = np.linspace(0, 255, 256)
    Omega = 2 * np.pi * 31.25e6
    WA = np.cos(Omega * t)
    WB = np.sin(Omega * t)

    start = time.time()
    digitizer.acquire_data()
    iqs = digitizer.get_iqs(WA, WB)
    data = digitizer.get_records()
    avg = digitizer.get_average()
    times = digitizer.get_times()

    stop = time.time()
    print('Execution time: %f seconds.' %(stop-start))

    I = avg[0]
    Q = avg[1]
    plt.plot(times['ns'], I['mV'], 'g', times['ns'], Q['mV'], 'b')
    plt.xlabel('Time (ns)')
    plt.ylabel('Voltage (mV)')
    plt.legend(['I', 'Q'])
    plt.xlim([times[0]['ns'], times[-1]['ns']])
    plt.show()
    
 
 
if __name__ == '__main__':
    test_ats_configuration()