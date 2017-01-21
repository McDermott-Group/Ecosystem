import time
import numpy as np
import matplotlib.pyplot as plt

import labrad
import labrad.units as units

def single_value_setting_test(vna, setting, value):
    print("\nAttempting to set '%s' setting to %s." %(setting, value))
    vna[setting](value)
    value = vna[setting](value)
    print("'%s' setting is set to %s." %(setting, value))

def vna_test(device_id=0, s_params=['S21'], formats=['RI'], trigger='IMM',
        single_value_settings={'Source Power':    -10*units.dBm,
                               'Start Frequency':   1*units.GHz,
                               'Stop Frequency':   10*units.GHz,
                               'IF Bandwidth':      1*units.kHz,
                               'Sweep Points':    2001,
                               'Average Points':   10},
        plot_magnitude=True, plot_phase=False):
    print('Running single trace VNA test...')

    # Connect to the server.
    cxn = labrad.connect()
    vna = cxn.gpib_network_analyzers()
    
    # Select a network analyzer.
    vnas = vna.list_devices()
    if not vnas:
        print('No network analyzer is found.')
        return
    print('\nFound devices: %s.' %vnas)
    print('Selecting device: %s.' %vnas[device_id][1])
    vna.select_device(vnas[device_id][1])
    
    # Print the network analyzer model.
    model = vna.get_model()
    print('Device model: %s.' %model)
    
    # Test single value settings.
    for setting, value in single_value_settings.items():
        single_value_setting_test(vna, setting, value)

    # Setup the measurement.
    vna.measurement_setup(s_params, formats, trigger)
    
    # Get the data.
    start = time.time()
    data = vna.get_data()
    freqs = vna.get_frequencies()
    stop = time.time()
    print('\nShape of the returned dataset: %s.' %str(np.shape(data)))
    print('Number of S-paremeters: %d.' %len(data))
    print('Number of frequency points: %d.' %np.size(freqs))
    print('Execution time: %f seconds.' %(stop-start))

    # Plot the data.
    if plot_magnitude or plot_phase:
        for idx in range(len(data)):
            if formats[idx] == 'RI':
                Sxy = data[idx][0] + 1j * data[idx][1]
                mag = 20 * np.log10(np.abs(Sxy))
                phs = np.angle(Sxy, deg=True)
            else:
                mag = data[idx][0]['dB']
                phs = data[idx][1]['deg']
        
            if plot_magnitude:
                plt.figure(2 * device_id)
                plt.plot(freqs['GHz'], mag)
                plt.xlabel('Frequency (GHz)')
                plt.ylabel('Magnitude (dB)')
                plt.legend(s_params)
                plt.xlim([freqs[0]['GHz'], freqs[-1]['GHz']])
            
            if plot_phase:
                plt.figure(2 * device_id + 1)
                plt.plot(freqs['GHz'], phs)
                plt.xlabel('Frequency (GHz)')
                plt.ylabel('Phase (deg)')
                plt.legend(s_params)
                plt.xlim([freqs[0]['GHz'], freqs[-1]['GHz']])
            
        plt.show()
 
 
if __name__ == '__main__':
    # vna_test(s_params=['S11', 'S12', 'S21', 'S22'],
             # formats=['RI', 'RI', 'MP', 'MP'])
             
    vna_test(s_params=['S11', 'S11'], formats=['RI', 'MP'],
            plot_phase=True)