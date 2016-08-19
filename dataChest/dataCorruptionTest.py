from dataChest import *
import numpy as np
import time

#create array of dataChest objects for data corruption tests
dataChestObjArray = []
for objIndex in range(0,100):
    dataChestObjArray.append(dataChest(["dataCorruptionTest"]))
    d = dataChestObjArray[objIndex]
    d.createDataset("AllOnes", [("indepName1", [1], "float64", "s")], [("depName1", [1], "float64", "V")])
    d.addParameter("X Label", "Time")
    d.addParameter("Y Label", "All Ones")
    d.addParameter("Plot Title", "Is Dataset Corrupted")


for ii in range(0, 12*60*60): #will take about ~13 hours since it takes finite time to write to all 100 files
    for objIndex in range(0,100):
        d = dataChestObjArray[objIndex]
        d.addData([[float(ii),1.0]])
    time.sleep(1.0)

