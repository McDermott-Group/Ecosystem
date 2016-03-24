from dataChest import *
import numpy as np
histLen = 100000
d = dataChest()

#create histogram data 1 point at a time
#mu, sigma = 1, 0.1
#gaussian = mu + sigma*np.random.randn(histLen)
d.createDataset("Histogram1by1", [("indepName1", [1], "float64", "Seconds")], [("depName1", [1], "float64", "Volts")])
net = []
for ii in range(0, 10000):
    net.append([float(ii)*1e-4,np.random.rand()*0.5])
d.addData(net) #single row

d.addParameter("X Label", "Time")
d.addParameter("Y Label", "Digitizer Noise")
d.addParameter("Plot Title", "Gaussian Noise Generator")

###create damped sinusoid
##t1 = np.arange(0.0, 2.0, 0.00001)
##d.createDataset("DampedOscillations", [("time", [len(t1)], "float64", "Seconds")],
##                [("Oscillatory", [len(t1)], "float64", "Volts"),
##                 ("Underdamped", [len(t1)], "float64", "Volts"),
##                 ("Envelope", [len(t1)], "float64", "Volts")])
##d.addParameter("X Label", "Time")
##d.addParameter("Y Label", "Voltage")
##d.addParameter("Plot Title", "Damped Oscillations")
##d.addData([[t1, np.sin(2 * np.pi * t1),
##            np.exp(-t1) * np.sin(2 * np.pi * t1),
##            np.exp(-t1)]])

###Arbitrary 2D datasets DO THIS TONIGHT
##x = np.random.rand(100)
##y = np.random.rand(100)
##z = np.sin(x)+np.cos(y)
##
##d.createDataset("LogarithmicWaveform", [("indepName1", [len(x)], "float64", "Volts"),
##                                        ("indepName2", [len(x)], "float64", "Power")],
##                                       [("depName1", [len(x)], "float64", "Current")])
##
##d.addParameter("X Label", "Voltage")
##d.addParameter("Y Label", "Power")
##d.addParameter("Plot Title", "Q(Voltage,Power)")
##d.addData([[x,y,z]])

#2D Pixel Sweeps (include log possibilities at some point)
##t1 = np.arange(-5.0, 5.0, step=0.05)
##t2 = np.arange(-5.0, 5.0, step=0.05)
##ImageData = []
##for jj in range(0, len(t2)):
##    for ii in range(0, len(t1)):
##        #if jj<len(t2)-1:
##        ImageData.append([t1[ii], t2[jj], np.sin(t1[ii]**2+t2[jj]**2)])
##
##d.createDataset("PixelPlot", [("indepName1", [1], "float64", "Volts"),
##                                        ("indepName2", [1], "float64", "Power")],
##                                       [("depName1", [1], "float64", "Current")])
##
##d.addParameter("X Label", "Bias1")
##d.addParameter("Y Label", "Bias2")
##d.addParameter("Plot Title", "Q(Bias1,Bias2)")
##d.addParameter("Image Type", "Pixel")
##d.addParameter("X Resolution", len(t1))
##d.addParameter("Y Resolution", len(t1))
##d.addParameter("X Increment", 0.05)
##d.addParameter("Y Increment", 0.05)
##d.addData(ImageData)


#OLDDDDD
#create histogram data
mu, sigma = 1, 0.1
gaussian = mu + sigma*np.random.randn(histLen)
d.createDataset("Histogram", [("indepName1", [histLen], "float64", "Seconds")], [("depName1", [histLen], "float64", "Volts")])
data = []
#print "gaussian=", gaussian
for ii in range(0, histLen):
    data.append(float(ii))
d.addData([[data,gaussian]]) #single row
d.addParameter("X Label", "Time")
d.addParameter("Y Label", "Digitizer Noise")
d.addParameter("Plot Title", "Gaussian Noise Generator")
#print d.getData()
##
###create damped sinusoid
##t1 = np.arange(0.0, 2.0, 0.00001)
##d.createDataset("DampedOscillations", [("time", [len(t1)], "float64", "Seconds")],
##                [("Oscillatory", [len(t1)], "float64", "Volts"),
##                 ("Underdamped", [len(t1)], "float64", "Volts"),
##                 ("Envelope", [len(t1)], "float64", "Volts")])
##d.addParameter("X Label", "Time")
##d.addParameter("Y Label", "Voltage")
##d.addParameter("Plot Title", "Damped Oscillations")
##d.addData([[t1, np.sin(2 * np.pi * t1),
##            np.exp(-t1) * np.sin(2 * np.pi * t1),
##            np.exp(-t1)]])
##
##
###Linear Waveform
###single
##mu, sigma = 1, 0.1
##gaussian = mu + sigma*np.random.randn(histLen)
##t0 = 0.0
##tf = 69.0
##d.createDataset("LinearWaveform", [("indepName1", [2], "float64", "Seconds")], [("depName1", [histLen], "float64", "Volts")])
##data = [t0, tf]
##
##d.addParameter("X Label", "Time")
##d.addParameter("Y Label", "Digitizer Noise")
##d.addParameter("Plot Title", "Linear Waveform Data")
##d.addParameter("X Scan Type", "Lin")
##d.addData([[data,gaussian]])
##
###multiple
##t1 = np.arange(0.0, 2.0, 0.00001)
##t0 = 0.0
##tf = 69.0
##d.createDataset("MultipleLinearWaveforms", [("indepName1", [2], "float64", "Seconds")],
##                [("Oscillatory", [len(t1)], "float64", "Volts"),
##                 ("Underdamped", [len(t1)], "float64", "Volts"),
##                 ("Envelope", [len(t1)], "float64", "Volts")])
##data = [t0, tf]
##
##d.addParameter("X Label", "Time")
##d.addParameter("Y Label", "Voltage")
##d.addParameter("Plot Title", "Damped Oscillations Lin Style")
##d.addParameter("X Scan Type", "Lin")
##d.addData([[data, np.sin(2 * np.pi * t1),
##            np.exp(-t1) * np.sin(2 * np.pi * t1),
##            np.exp(-t1)]])
##
###Logarithmic Waveform
##mu, sigma = 1, 0.1
##gaussian = mu + sigma*np.random.randn(histLen)
##f0 = 10**-1
##ff = 10**9
##d.createDataset("LogarithmicWaveform", [("indepName1", [2], "float64", "Hz")], [("depName1", [histLen], "float64", "dBm")])
##data = [f0, ff]
##
##d.addParameter("X Label", "Frequency")
##d.addParameter("Y Label", "Power")
##d.addParameter("Plot Title", "Logarithmic Waveform Data")
##d.addParameter("X Scan Type", "Log")
##d.addData([[data,gaussian]])
##
###Arbitrary 2D datasets
##x = np.random.rand(100)
##y = np.random.rand(100)
##z = np.sin(x)+np.cos(y)
##
##d.createDataset("LogarithmicWaveform", [("indepName1", [len(x)], "float64", "Volts"),
##                                        ("indepName2", [len(x)], "float64", "Power")],
##                                       [("depName1", [len(x)], "float64", "Current")])
##
##d.addParameter("X Label", "Voltage")
##d.addParameter("Y Label", "Power")
##d.addParameter("Plot Title", "Q(Voltage,Power)")
##d.addData([[x,y,z]])

