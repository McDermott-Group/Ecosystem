from dataChest import *
import numpy as np
import time

#create array of dataChest objects for data corruption tests
dataChestObjArray = []
numObjs = 100
for objIndex in range(0,numObjs):
    dataChestObjArray.append(dataChest(["dataCorruptionTest"]))
    d = dataChestObjArray[objIndex]
    d.createDataset("AllOnes", [("indepName1", [1], "float64", "s")], [("depName1", [1], "float64", "V")])
    d.addParameter("X Label", "Time")
    d.addParameter("Y Label", "All Ones")
    d.addParameter("Plot Title", "Is Dataset Corrupted")

numWrites = 12*60*60 # vary if you like
for ii in range(0, numWrites): #will take about ~13 hours since it takes finite time to write to all 100 files
    for objIndex in range(0,numObjs):
        d = dataChestObjArray[objIndex]
        d.addData([[float(ii),1.0]])
    time.sleep(1.0)
    print ii
#Check for corrupted files

for objIndex in range(0,numObjs):
    d = dataChestObjArray[objIndex]
    name = d.getDatasetName()
    data = d.getData()
    if len(data) != numWrites:
        print "Invalid length for dataset with name=", name
    else:
        for ii in range(0, numWrites):
            if list(data[ii]) != [float(ii), 1.0]:
                print "Corrupted dataset with name =", name
                print "row number ", ii, " has an incorrect value."
                break #this way the number of prints = number of files with at least one corrupted row
    
    
    

