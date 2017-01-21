import time
import numpy as np
import matplotlib.pyplot as plt

import labrad
import labrad.units as units
from labrad.units import V, ns, s, MS


def test_ats_configuration(input_range=4*V,
                           sampling_rate=500*MS/s,
                           trigger_delay=0*ns,
                           samples_per_record=16382*ns,
                           number_of_records=10000):
    """
    This is an example on how to configure an ATS board for a data
    acquisition. No actual data is taken since it requires an external
    trigger pulse.
    """
    print('Testing the basic board functionality.')

    # Select a board assuming there exists only one.
    cxn = labrad.connect()
    ats = cxn.ats_waveform_digitizer
    ats.select_device()
    
    # Turning the board LED on and off. In an actual experiment this
    # step should be skept.
    print('\nTurning the LED on for 1 sec.')
    ats.set_led_state(1)
    time.sleep(1)
    print('Turning the LED off.')
    ats.set_led_state(0)
    
    # Configure the board for an acquisition. 
    print('Configuring the boards...')
    ats.configure_inputs(input_range)
    ats.sampling_rate(sampling_rate)
    ats.configure_trigger(trigger_delay)
    ats.samples_per_record(samples_per_record)
    ats.number_of_records(number_of_records)
    ats.configure_buffers()
    
    # Display some extra information. This is typically not required
    # during any actual measurements.
    print('\nAcquring the channel information...') 
    [samples_per_channel, bits_per_sample] = ats.get_channel_info()
    print('There are %d samples per channel, %d bits per sample.'
            %(samples_per_channel, bits_per_sample))
    print('Records to be acquired: %d.' %ats.number_of_records())
    bytes_per_sample = (bits_per_sample - 1) // 8 + 1
    sampling_rate = ats.sampling_rate()['S/s']
    if type(samples_per_record) == units.Value:
        samples_per_record = samples_per_record['s']
    samples_per_record = sampling_rate * samples_per_record
    memory = 2 * bytes_per_sample * samples_per_record * number_of_records
    print('Minimum memory required: %d bytes, which is about %.2f MB.'
            %(memory, float(memory) / (1024 * 1024)))
    
    # Check the board state.
    print('\nIs board busy?')
    print('%s.' %ats.busy())

def test_ats():
    """
    This is an example on how to configure an ATS board for a data
    acquisition and acquire some data. An external trigger pulse
    should be provided to the ATS board to properly run this example.
    """
    # Select a board with a specific name.
    cxn = labrad.connect()
    ats = cxn.ats_waveform_digitizer
    ats.select_device("ATS1::1")

    # Configure the board for an actual acquisition. 
    ats.configure_inputs(.1*V)
    ats.sampling_rate(10**9)
    ats.configure_trigger()
    ats.samples_per_record(512)
    ats.number_of_records(1)
    ats.configure_buffers()

    # Generate the demodulation weights.
    t = np.linspace(0, 255, 256)
    Omega = 2 * np.pi * 31.25e6
    WA = np.cos(Omega * t)
    WB = np.sin(Omega * t)

    # Acquire the data and get the results.
    start = time.time()
    ats.acquire_data()
    iqs = ats.get_iqs(WA, WB)
    data = ats.get_records()
    avg = ats.get_average()
    times = ats.get_times()
    stop = time.time()
    print('Execution time: %f seconds.' %(stop-start))

    # Plot the data.
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
    # test_ats()