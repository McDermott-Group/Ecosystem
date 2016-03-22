from dataChest import *
import numpy as np
histLen = 100000
d = dataChest()

#create histogram data
mu, sigma = 1, 0.1
gaussian = mu + sigma*np.random.randn(histLen)
d.createDataset("Histogram", [("indepName1", [histLen], "float64", "seconds")], [("depName1", [histLen], "float64", "Voltage")])
data = []
for ii in range(0, histLen):
    data.append(float(ii))
d.addData([[data,gaussian]]) #single row

d.addParameter("xlabel", "Time")
d.addParameter("ylabel", "Digitizer Noise")
d.addParameter("PlotTitle", "Gaussian Noise Generator")
print "dunzo"
#create damped sinusoid
t1 = np.arange(0.0, 2.0, 0.00001)
d.createDataset("DampedOscillations", [("time", [len(t1)], "float64", "seconds")],
                [("Oscillatory", [len(t1)], "float64", "Voltage"),
                 ("Underdamped", [len(t1)], "float64", "Voltage"),
                 ("Envelope", [len(t1)], "float64", "Voltage")])
d.addParameter("xlabel", "Time")
d.addParameter("ylabel", "Voltage")
d.addParameter("PlotTitle", "Damped Oscillations")
print "hey"
d.addData([[t1, np.sin(2 * np.pi * t1),
            np.exp(-t1) * np.sin(2 * np.pi * t1),
            np.exp(-t1)]])
print "now"
