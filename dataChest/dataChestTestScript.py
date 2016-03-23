from dataChest import *
import numpy as np
histLen = 100000
d = dataChest()

#create histogram data
mu, sigma = 1, 0.1
gaussian = mu + sigma*np.random.randn(histLen)
d.createDataset("Histogram", [("indepName1", [histLen], "float64", "Seconds")], [("depName1", [histLen], "float64", "Volts")])
data = []
for ii in range(0, histLen):
    data.append(float(ii))
d.addData([[data,gaussian]]) #single row

d.addParameter("X Label", "Time")
d.addParameter("Y Label", "Digitizer Noise")
d.addParameter("Plot Title", "Gaussian Noise Generator")

#create damped sinusoid
t1 = np.arange(0.0, 2.0, 0.00001)
d.createDataset("DampedOscillations", [("time", [len(t1)], "float64", "Seconds")],
                [("Oscillatory", [len(t1)], "float64", "Volts"),
                 ("Underdamped", [len(t1)], "float64", "Volts"),
                 ("Envelope", [len(t1)], "float64", "Volts")])
d.addParameter("X Label", "Time")
d.addParameter("Y Label", "Voltage")
d.addParameter("Plot Title", "Damped Oscillations")
d.addData([[t1, np.sin(2 * np.pi * t1),
            np.exp(-t1) * np.sin(2 * np.pi * t1),
            np.exp(-t1)]])
