from dataChest import *
import numpy as np
import time
d = dataChest()

#1D Arbitrary Data (Option 1 Style)
#Random Number Generator
print "1D Arbitrary Data (Option 1 Style):" #Most inneficient style by far
numPoints = 4e4
print "\tNumber of Points =", numPoints
mu, sigma = 1, 0.1
#gaussian = mu + sigma*np.random.randn(histLen)
d.createDataset("Histogram1by1", [("indepName1", [1], "float64", "Seconds")], [("depName1", [1], "float64", "Volts")])
d.addParameter("X Label", "Time")
d.addParameter("Y Label", "Digitizer Noise")
d.addParameter("Plot Title", "Random Number Generator")
net = []
for ii in range(0, int(numPoints)):
    net.append([float(ii)*1e-4,np.random.rand()*0.5])
t0 = time.time()
d.addData(net) #single row
tf = time.time()
print "\tTotal Write Time =", tf-t0
t0 = time.time()
d.addData(net) #single row
tf = time.time()
print "\tTotal Read Time =", tf-t0

#1D Arbitrary Data (Option 2 Style)
#Sinusoid
print "1D Arbitrary Data (Option 2 Style):"
res = 1e-7
timeAxis = np.arange(0.0, 1.0, res)
print "\tNumber of Points =", 1.0/res
d.createDataset("DampedOscillations", [("time", [len(timeAxis)], "float64", "Seconds")],
                [("Oscillatory", [len(timeAxis)], "float64", "Volts"),
                 #("Underdamped", [len(t1)], "float64", "Volts"),
                 #("Envelope", [len(t1)], "float64", "Volts")
                 ])
d.addParameter("X Label", "Time")
d.addParameter("Y Label", "Voltage")
d.addParameter("Plot Title", "Damped Oscillations")
t0 = time.time()
d.addData([ [timeAxis, np.sin(2 * np.pi * timeAxis)] ])
tf = time.time()
print "\tTotal Write Time =", tf-t0
t0 = time.time()
d.getData()
tf = time.time()
print "\tTotal Read Time =", tf-t0

#1D Linear Scan (Log Scan is same exact thing, just interpretted differently by grapher)
print "1D Linear Scan Data (Log Scan Redundant):"
length =1e5
print "\tNumber of Points =", length
mu, sigma = 1, 0.1
gaussian = mu + sigma*np.random.randn(length)
t0 = 0.0
tf = 100.0
d.createDataset("LinearWaveform", [("indepName1", [2], "float64", "Seconds")], [("depName1", [int(length)], "float64", "Volts")])
data = [t0, tf]

d.addParameter("X Label", "Time")
d.addParameter("Y Label", "Digitizer Noise")
d.addParameter("Plot Title", "Linear Waveform Data")
d.addParameter("X Scan Type", "Lin")
t0 = time.time()
d.addData([[data,gaussian]])
tf = time.time()
print "\tTotal Write Time =", tf-t0
t0 = time.time()
d.getData()
tf = time.time()
print "\tTotal Read Time =", tf-t0

#2D Arbitrary Data (Option 1)
print "2D Arbitrary Data (Option 1):"
xyGridRes = 5e-3
print "\tNumber of Points =", 1/xyGridRes
t1 = np.arange(-0.5, 0.5, step=xyGridRes)
t2 = np.arange(-0.5, 0.5, step=xyGridRes)
ImageData = []
for ii in range(0, len(t1)):
    for jj in range(0, len(t2)):
        #if jj<len(t2)-1:
        ImageData.append([t1[ii], t2[jj], np.sin(t1[ii]**2+t2[jj]**2)])

d.createDataset("2DArbitraryOpt1", [("indepName1", [1], "float64", "Volts"),
                                        ("indepName2", [1], "float64", "Power")],
                                       [("depName1", [1], "float64", "Current")])

d.addParameter("X Label", "Bias1")
d.addParameter("Y Label", "Bias2")
d.addParameter("Plot Title", "Q(Bias1,Bias2)")
d.addParameter("Image Type", "Pixel")
d.addParameter("X Resolution", len(t1))
d.addParameter("Y Resolution", len(t1))
d.addParameter("X Increment", xyGridRes)
d.addParameter("Y Increment", xyGridRes)
t0 = time.time()
d.addData(ImageData)
tf = time.time()
print "\tTotal Write Time =", tf-t0
t0 = time.time()
d.getData()
tf = time.time()
print "\tTotal Read Time =", tf-t0

##Arbitrary 2D datasets 
print "2D Arbitrary Data (Option 2):"
length = 1e4
x = np.random.rand(length)
y = np.random.rand(length)
z = np.sin(x)+np.cos(y)

d.createDataset("2DArbitraryOpt2", [("indepName1", [len(x)], "float64", "Volts"),
                                        ("indepName2", [len(x)], "float64", "Power")],
                                       [("depName1", [len(x)], "float64", "Current")])

d.addParameter("X Label", "Voltage")
d.addParameter("Y Label", "Power")
d.addParameter("Plot Title", "Q(Voltage,Power)")
t0 = time.time()
d.addData([[x,y,z]])
tf = time.time()
print "\tTotal Write Time =", tf-t0
t0 = time.time()
d.getData()
tf = time.time()
print "\tTotal Read Time =", tf-t0

###2D Scan Data
##print "2D Scan Data (Option 1):"
##xyGridRes = 1e-5
##print "\tNumber of Points =", 1/xyGridRes
##t1 = np.arange(-0.5, 0.5, step=xyGridRes)
###t2 = np.arange(-0.5, 0.5, step=xyGridRes)
##
##d.createDataset("2DScan", [("indepName1", [1], "float64", "Volts"),
##                                        ("indepName2", [2], "float64", "Power")],
##                                       [("depName1", [len(t1)], "float64", "Current")])
##
##d.addParameter("X Label", "Bias1")
##d.addParameter("Y Label", "Bias2")
##d.addParameter("Plot Title", "Q(Bias1,Bias2)")
##d.addParameter("Scan Type", "Lin-Lin")
##t0 = time.time()
##d.addData([[t1[0], [-0.5, 0.5], t1]]) # *&^%&*%$#@%&%^$* no useful feedback when data is data = [t1[0], [-0.5, 0.5], t1]
##tf = time.time()
##print "\tTotal Write Time =", tf-t0
##t0 = time.time()
##d.getData()
##tf = time.time()
##print "\tTotal Read Time =", tf-t0


