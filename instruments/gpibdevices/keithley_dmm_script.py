import labrad
from labrad.units import mV, V
import labrad.units as U
import time
import numpy as np

from matplotlib import pyplot as plt

def compute_effective_capacitance(Vs, Vc, R_s, f_wavetek, Vc_gain=1):
    Vc = Vc/Vc_gain
    omega = 2.0 * np.pi * f_wavetek
    C = np.sqrt((Vs/Vc)**2-1)/(omega * R_s)
    return C
    
def compute_capacitance_of_interest(C_1, C_2, C_3):
    return np.sqrt(C_1 * C_2 - C_2 * C_3)
    
Vs = 109.37e-3
R_series = 3e6
Vc_gain = 50.
f_wavetek = 217.77

cxn = labrad.connect()

dmm = cxn.keithley_2000_dmm
dmm.select_device(0)

V_t = []
F_t = []
for ii in range(0, 10):
    dmm.set_ac_range(10.0 * V)
    dmm.set_digital_filter_paramters("REPEAT", "ON", 10)
    v = dmm.get_ac_volts()
    time.sleep(1.5)
    dmm.set_frequency_input_range_and_resolution(10.0 * V)
    f = dmm.get_frequency()
    V_t.append(v['V'])
    F_t.append(f['Hz'])
    time.sleep(1.5)
    print(v)
    print(f)
    
dmm.gpib_query('SYST:ERR?')
    
print(np.asarray(V_t).mean())
# print(np.asarray(F_t).mean())
plt.plot(V_t)
plt.ylabel("Voltage (V)")
plt.xlabel("Some Notion of Time")
plt.show()

    
    
    
