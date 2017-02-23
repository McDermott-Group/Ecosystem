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
description = Monitors Leiden Devices
"""

import sys
sys.dont_write_bytecode = True
import MGui     # Handles all GUI operations. Independent of  LabRAD.

from Device import Device
from multiprocessing.pool import ThreadPool
import threading
import labrad
import labrad.units as units
import time
from dataChestWrapper import *
from tendo import singleton

class nViewer:
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
    
        
        PT1000s = Device("PT1000s")
        PT1000s.connection(cxn)
        PT1000s.setServerName("goldstein_s_pt1000_temperature_monitor")
        PT1000s.addParameter("3K", "get_temperatures", None, 0)
        PT1000s.addParameter("50K", "get_temperatures", None, 1)
        PT1000s.selectDeviceCommand("select_device", 0)
        PT1000s.setYLabel("Temperature")
        #PT1000s.addPlot()
        PT1000s.begin()
        self.devices.append(PT1000s)
        
        
   
        # Start the datalogger. This line can be commented
        # out if no datalogging is required.
        #self.chest = dataChestWrapper(self.devices)
        
        # Create the gui.
        self.gui = MGui.MGui()
        self.gui.startGui(self.devices, 'Leiden DR GUI', 'Leiden Data', tele)
        
        
# In Python, the main class's __init__() IS NOT automatically called.
viewer = nViewer()    
viewer.__init__()