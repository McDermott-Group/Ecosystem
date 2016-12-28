import time
import numpy as np
import matplotlib.pyplot as plt

import labrad
from labrad.units import V

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