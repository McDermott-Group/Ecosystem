import sys
sys.dont_write_bytecode = True
import MGui             # Handles all gui operations. Independent of labrad.

#from PyQt4 import QtCore, QtGui
from PyQt4 import QtCore, QtGui
from MDevices.Device import Device
from MDevices.MVirtualDevice import MVirtualDevice
from MDevices.Mhdf5Device import Mhdf5Device

import labrad
import grapher as alexGrapher
from MNodeEditor.MNodes import runningAverage
from MNodeEditor import MNodeTree

from MNodeEditor.MNodes import MDeviceNode

class nViewer:
    gui = None
    devices =[]
    
    def __init__(self, parent = None):
        # Establish a connection to labrad
        try:
            cxn = labrad.connect()
        except:
            print("Please start the labrad manager")
            sys.exit(0)
        try:
            tele = cxn.telecomm_server
        except:
            print("Please start the telecomm server")
            sys.exit(1)
        self.gui = MGui.MGui()
        Random = Device("Random")
        Random.connection(cxn)

        Random.setServerName("my_server")
        Random.addParameter("Random Pressure","pressure", None, log = False)
        Random.addParameter("Random Temperature", "temperature", None)
        #LeidenDRTemperature.selectDeviceCommand("select_device", 0)
        Random.addPlot()
        Random.setPlotRefreshRate(0.5)
        Random.setRefreshRate(0.5)
        Random.setYLabel("Hi", "Custom Units")
        Random.begin()
       # self.devices.append(Random)
        self.gui.addDevice(Random)
        
        localTemp = Device("Local Temperatures", lock_log_settings = True)
        localTemp.connection(cxn)
        localTemp.setServerName("my_server2")
        localTemp.addParameter("Outside Temperature", "temperature", None)
        localTemp.addParameter("Outside pressure", "pressure", None)
        localTemp.addParameter("Humidity", "moisture", None)
        
        localTemp.addButton("Madison Weather",  None, "changeLocation", 5)
        localTemp.addButton("St. Paul Weather", None,  "changeLocation", 2)

        localTemp.addPlot()
        localTemp.setPlotRefreshRate(2)
        localTemp.setRefreshRate(2)
        localTemp.setYLabel("Temperature")
        localTemp.begin()
        #self.devices.append(localTemp)
        self.gui.addDevice(localTemp)

        grapher = Mhdf5Device("Grapher")
        grapher.begin()
        
        self.gui.addDevice(grapher)
       # Start the datalogger. This line can be commented
        #out if no datalogging is required.
       # print self.devices

        self.nodeTree = MNodeTree.NodeTree()
#        
        temp = MDeviceNode.MDeviceNode(localTemp)
        self.nodeTree.addNode(temp)
        directInput = temp.addAnchor(name = "avg", type = "input", terminate = True, precision = 2)
        
        
        virtdev = MVirtualDevice("Test Node", yLabel = "Test Node Y Label",  units = "Test Units")
        virtDevNode = MDeviceNode.MDeviceNode(virtdev)
        self.gui.addDevice(virtdev)
        self.nodeTree.addNode(virtDevNode)
        anchor2 = virtDevNode.addAnchor(name = "test input", type = "input")
        anchor3 = virtDevNode.addAnchor(name = "raw input", type = "input")
        
        avg = runningAverage.runningAverage()
        avg.setWindowWidth(20)
        dataInput = avg.getAnchorByName("data")
        output = avg.getAnchorByName("running avg")
#        
        anchor1 = temp.getAnchorByName("Outside Temperature")
        # print "Trying to connect two anchors"
        self.nodeTree.connect(anchor1,dataInput)
        self.nodeTree.connect(anchor2,output)
        self.nodeTree.connect(anchor1,anchor3)
        self.nodeTree.connect(directInput,output)
       # print randomNode.getAnchors()
        # Create the gui
       # a = alexGrapher.Main()
        
        #self.gui.addWidget(alexGrapher.Main())
        self.gui.addWidget(QtGui.QLabel("HI"))
        self.gui.setRefreshRate(0.5)
        self.gui.startGui( 'Leiden Gui',tele)
        

        
# In phython, the main class's __init__() IS NOT automatically called

viewer = nViewer()  
viewer.__init__()