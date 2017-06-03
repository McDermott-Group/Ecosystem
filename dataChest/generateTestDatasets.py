import numpy as np
from dataChest import dataChest
import time


def gaussian(x, mu, sig): # with noise
    return np.exp(-np.power(x - mu, 2.) / (2 * np.power(sig, 2.))) + np.random.rand()/5.

d = dataChest(['testProject','Test Datasets'])

# 1D: Arbitrary Type 1 plot over time
if False:
    d.createDataset("1D_ArbType1_MyFavoriteTimeSeries",
                    [("indepName1", [1], "float64", "s")],
                    [("depName1", [1], "float64", "V")]
                    )
    d.addParameter("X Label", "Time")
    d.addParameter("Y Label", "Digitizer Noise")
    d.addParameter("Plot Title", "Random Number Generator")
    for ii in range(0, 1000):
        d.addData([[float(ii),np.random.rand()]])
        time.sleep(.2)

# 1D: Arbitrary Type 1
if True:
    d.createDataset("1D_ArbType1_MyFavoriteTimeSeries",
                    [("indepName1", [1], "float64", "s")],
                    [("depName1", [1], "float64", "V")]
                    )
    d.addParameter("X Label", "Time")
    d.addParameter("Y Label", "Digitizer Noise")
    d.addParameter("Plot Title", "Random Number Generator")
    net = []
    for ii in range(0, 1000):
        net.append([float(ii),np.random.rand()])
    d.addData(net) #add 100 rows of data at once d.getData() #single row

# 1D: Arbitrary Type 2
if True:
    res = 0.1
    timeAxis = np.arange(1, 100, res)
    d.createDataset("1D_ArbType2_DampedOscillations",
                    [("time", [len(timeAxis)], "float64", "s")],
                    [("Oscillation", [len(timeAxis)], "float64", "V")]
                    )
    d.addParameter("X Label", "Time")
    d.addParameter("Y Label", "Voltage")
    d.addParameter("Plot Title", "Damped Oscillations")
    d.addData([ [timeAxis, np.sin(2 * np.pi * timeAxis)/timeAxis] ])

# 1D: Scan
if True:
    length = int(1e2)
    mu, sigma = 1., 0.1
    gaussianNoise = mu + sigma*np.random.randn(length)
    t0 = 0.0
    tf = 100.0
    d.createDataset("1D_Scan_LinearWaveform",
                    [("indepName1", [2], "float64", "s")],
                    [("depName1", [int(length)], "float64", "V"), ("depName2", [int(length)], "float64", "V")])
    shorthandTime = [t0, tf]
    d.addParameter("Scan Type", "Linear")
    d.addData([[shorthandTime,gaussianNoise,gaussianNoise]])

# 2D: Arbitrary Type 1
if True:
    d.createDataset("2D_ArbType1_QubitFluxSweep1",
                    [("Flux Bias", [1], "float64", "V"), ("Frequency", [1], "float64", "GHz")],
                    [("S21", [1], "float64", "dB")]
                    )
    d.addParameter("X Label", "Flux Bias")
    d.addParameter("Y Label", "Frequency")
    d.addParameter("Plot Title", "Qubit Flux Sweep")
    net = []
    for i in np.arange(5, 6, .01):
        for j in np.arange(-0.5, 0.5, .05):
            net.append([float(j),float(i),gaussian(i, 5.5+0.2*np.sin(10*j), .05)])
    d.addData(net) #add 100 rows of data at once d.getData() #single row

# 2D: Arbitrary Type 2
if False:
    net = []
    for i in np.arange(5, 6, .01):
        for j in np.arange(-0.5, 0.5, .05):
            net.append([float(j),float(i),gaussian(i, 5.5+0.2*np.sin(10*j), .05)])
    d.createDataset("2D_ArbType2_QubitFluxSweep2",
                    [("Flux Bias", [len(net)], "float64", "V"), ("Frequency", [len(net)], "float64", "GHz")],
                    [("S21", [1], "float64", "dB")]
                    )
    d.addParameter("X Label", "Flux Bias")
    d.addParameter("Y Label", "Frequency")
    d.addParameter("Plot Title", "Qubit Flux Sweep")
    d.addData(np.array(net).T) #add 100 rows of data at once d.getData() #single row

# 2D Scan
if True:
    freqList = np.arange(5, 6, .01)
    d.createDataset("2D_Scan_QubitFluxSweepScan",
                    [("Flux Bias", [1], "float64", "V"), ("Frequency", [2], "float64", "GHz")],
                    [("S21", [len(freqList)], "float64", "dB")]
                    )
    d.addParameter("X Label", "Flux Bias")
    d.addParameter("Y Label", "Frequency")
    d.addParameter("Plot Title", "Qubit Flux Sweep")
    d.addParameter("Scan Type", "Linear")
    net = []
    for j in np.arange(-0.5, 0.5, .05):
        net.append([float(j), [freqList[0],freqList[1]], gaussian(freqList, 5.5+0.2*np.sin(10*j), .05)])
    d.addData(net) #add 100 rows of data at once d.getData() #single row
