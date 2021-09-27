#The purpose of this file is to create data using the dataChest.py library for testing purposes of upgrading the
#dataChest.py from python 2 to python 3

from dataChest import *
d = dataChest(['DataChestTutorial','python2to3','Test Data for Testing'])
import numpy as np
d.createDataset('TestV2.7',[('indepName1',[1],'float64','s')],[('depName1', [1], 'float64', 'V')])
d.addParameter('X Label', 'Time')
d.addParameter('Y Label', 'Digitizer Noise')
d.addParameter('Plot Title', 'Random Number Generator')
net=[]
for ii in range (0,100):
    net.append([float(ii), np.random.rand()])
d.addData(net)
d.getData()