import sys
import time
from tendo import singleton

import labrad
from dataChestWrapper import *
import MGui
from MDevices.Device import Device
from MDevices.Mhdf5Device import Mhdf5Device
from MNodeEditor import MNodeTree
from MNodeEditor.MNodes import MDeviceNode
import runningAverage


class LakeShore211Viewer:
    """LK211Gui. Viewer"""

    gui = None
    devices = []

    def __init__(self, parent=None):
        try:
            cxn = labrad.connect()
        except:
            print("Please Start the LabRad manager")
            time.sleep(2)
            sys.exit(1)
        try:
            tele = cxn.telecomm_server
        except:
            print("Please start the telecomm server")
            time.sleep(2)
            sys.exit(1)

        self.gui = MGui.MGui()
        Thermometer = Device("LakeShore")
        Thermometer.connection(cxn)
        Thermometer.setServerName("lakeshore_211")
        Thermometer.addParameter("Temperature", "get_temperature", None, index=0)
        Thermometer.selectDeviceCommand("select_device", 0)
        Thermometer.setYLabel("Temperature")
        Thermometer.addPlot()
        Thermometer.begin()
        self.gui.addDevice(Thermometer)

        " Smooth the noise in the data"
        self.nodeTree = MNodeTree.NodeTree()
        thermometerNode = MDeviceNode.MDeviceNode(Thermometer)
        self.nodeTree.addNode(thermometerNode)
        rawTempOutput = thermometerNode.getAnchorByName("Temperature")
        avgTemp = thermometerNode.addAnchor(
            name="Average Temperature ", type="input", terminate=True
        )

        avg = runningAverage.runningAverage()
        avg.setWindowWidth(100)
        avgInput = avg.getAnchorByName("data")
        avgOutput = avg.getAnchorByName("running avg")
        self.nodeTree.connect(rawTempOutput, avgInput)
        self.nodeTree.connect(avgOutput, avgTemp)

        self.gui.startGui("Lakeshore 211 GUI", tele)


viewer = LakeShore211Viewer()
viewer.__init__()
