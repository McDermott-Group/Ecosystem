from dataChest import *
import numpy as np
import time
d1 = dataChest(["dataCorruption2"])


#1D Arbitrary Data (Option 1 Style)
#Random Number Generator
print "1D Arbitrary Data (Option 1 Style):" #Most inneficient style by far
numPoints = 1e6
print "\tNumber of Points =", numPoints
d1.createDataset("Histogram1by1", [("indepName1", [1], "float64", "Seconds")], [("depName1", [1], "float64", "Volts")])
d1.addParameter("X Label", "Time")
d1.addParameter("Y Label", "Digitizer Noise")
d1.addParameter("Plot Title", "Random Number Generator")

for ii in range(0, int(numPoints)):
    d1.addData([[float(ii),1.0]])
    time.sleep(1.0)
