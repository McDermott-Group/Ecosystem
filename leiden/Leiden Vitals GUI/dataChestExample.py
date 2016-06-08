from dataChest import *
from dateStamp import *
import numpy as np
import time
# Root Directory for this instance
d= dataChest("DataChestTutorial")
# Create a directory
#d.mkdir("MyDir")
# List the contents of the folder
print "Contents:", d.ls()
print "Working Directory: ", d.pwd()
numpoints = 100
# Create a dataset
d.createDataset("sin "+str(numpoints),
				[("time", [1], "int32", "")],
				[("sin" ,[1], "float64", "V")]
				)
			
# d1.createDataset("newDataShape",
				# [("GateBias", [1], "float64", "V"),
				# ("Frequency", [1000], "float64", "Hz")], 
				# [("Transmission", [1000], "complex128", "dB")] )
# # Datestamp is useful for time
dStamp = dateStamp()
utcFloat = dStamp.utcNowFloat()
# print "utcFloat:", utcFloat

# # Let's get the name of the dataset
# datasetName = d.getDatasetName()
# print "Data set Name:", datasetName

# # Lets get the list of variables
# varsList = d1.getVariables()
# indepVarsList = varsList[0]
# depVarsList = varsList[1]
# print indepVarsList
# print depVarsList

# # Lets practice adding data
# d2.createDataset("TestDataSet", 
					# [("ind1", [1], "float64", "s")],
					# [("dep1", [1], "complex128", "V")]
					# )
# # Add a row of data
#d2.addData([[1.0, 2.0+1j*2.0]])
# Add two rows of data		
	
for i in range(0, numpoints):
	#time.sleep(1)
	d.addData([[i, float(i)]]) 
	if(i == 7):
		d.addData([[i, np.nan]])
#Let's open a dataset
# currentDataset = d1.getDatasetName()
# print currentDataset
