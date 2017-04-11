# Copyright (C) 2016 Noah Meltzer
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.


"""
version = 1.1.1
description = Demonstration
"""

import sys
sys.dont_write_bytecode = True
import MGui     # Handles all GUI operations. Independent of  LabRAD.

from MDevices.RS232Device import RS232Device

from MNodeEditor import MNodeTree
from MNodeEditor.MNodes import MDeviceNode
from MNodeEditor.MNodes import runningAverage

import labrad
import time

from tendo import singleton

class mViewer:
    gui = None
    devices =[]
    
    def __init__(self, parent = None):
        # Establish a connection to LabRAD.
        try:
            me = singleton.SingleInstance() # will sys.exit(-1) if other instance is running
        except:
            print("Multiple instances cannot be running")
            time.sleep(2)
            sys.exit(1)
        try:
            cxn = labrad.connect()
        except:
            print("Please start the LabRAD manager")
            time.sleep(2)
            sys.exit(0)
        try:
            tele = cxn.telecomm_server
        except:
            print("Please start the telecomm server")
            time.sleep(2)
            sys.exit(1)
    
        self.gui = MGui.MGui()
        lm3000 = RS232Device("Light Meter 3000", "COM7", baud = 115200)
        lm3000.addButton("Off", 'b0', message = "You are about to turn off the LED.")
        lm3000.addButton("20%", 'b2')
        lm3000.addButton("50%", 'b5')
        lm3000.addButton("80%", 'b8')
        lm3000.addButton("100%", 'b9')
        lm3000.addParameter("Light Level", "s")
        lm3000.setYLabel("Light Level")
        lm3000.addPlot()
        lm3000.begin()
        self.gui.addDevice(lm3000)

        self.nodeTree = MNodeTree.NodeTree()
        
        lightMeterNode = MDeviceNode.MDeviceNode(lm3000)
        self.nodeTree.addNode(lightMeterNode)
        rawLightOutput = lightMeterNode.getAnchorByName("Light Level")
        avgLight = lightMeterNode.addAnchor(name = "Average Light Level", type = "input", terminate = True)

        avg = runningAverage.runningAverage()
        avg.setWindowWidth(100)
        avgInput = avg.getAnchorByName("data")
        avgOutput = avg.getAnchorByName("running avg")
        
        self.nodeTree.connect(rawLightOutput, avgInput)
        self.nodeTree.connect(avgOutput, avgLight)
        # self.nodeTree.connect(output, virtAvgInput)
         
        # Create the gui.
        
        self.gui.startGui('Leiden DR GUI', tele)
        
        
# In Python, the main class's __init__() IS NOT automatically called.
viewer = mViewer()    
viewer.__init__()