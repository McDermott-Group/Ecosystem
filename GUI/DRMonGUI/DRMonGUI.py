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
version = 1.1.0
description = Monitors Leiden Devices
"""
import sys
sys.dont_write_bytecode = True
import MGui             # Handles all gui operations. Independent of labrad.

#from PyQt4 import QtCore, QtGui
import time
from Device import Device
from multiprocessing.pool import ThreadPool
import threading
import labrad
import labrad.units as units
from dataChestWrapper import *

class nViewer:
    gui = None
    devices =[]
    
    def __init__(self, parent = None):
        # Establish a connection to labrad
        try:
            cxn = labrad.connect()
        except:
            print("Please start the labrad manager")
            time.sleep(2)

            sys.exit(0)
        try:
            tele = cxn.telecomm_server
        except:
            print("Please start the telecomm server")
            time.sleep(2)
            sys.exit(1)


        mks_pdr2000 = Device("Keg")
        mks_pdr2000.setServerName("mks_pdr2000_server")
        mks_pdr2000.addParameter("Pressure 1", "get_pressure", None, 0)
        mks_pdr2000.addParameter("Pressure 2", "get_pressure", None, 1)
       # time.sleep(2)
        mks_pdr2000.setYLabel("Pressure")
        mks_pdr2000.selectDeviceCommand("select_device", 0)
        mks_pdr2000.addPlot()
        mks_pdr2000.connection( cxn)
        mks_pdr2000.begin()
        self.devices.append(mks_pdr2000)

        lake370 = Device("Lakeshore 370")
        lake370.setServerName("lakeshore_ruox")
        lake370.setPlotRefreshRate(8)
        lake370.setRefreshRate(8)
        for i in range(0,5):
            lake370.addParameter("Temperature "+str(i+1), "temperatures", None,i)
        lake370.setYLabel("Temperature")
        lake370.selectDeviceCommand("select_device", 0)
        lake370.addPlot()
        lake370.connection(cxn)
        lake370.begin()
        self.devices.append(lake370)
        
        mks_pdr2000v2 = Device("Return")
        mks_pdr2000v2.setServerName("mks_pdr2000_server")
        mks_pdr2000v2.addParameter("Pressure 1", "get_pressure", None, 0)
        mks_pdr2000v2.addParameter("Pressure 2", "get_pressure", None, 1)
        mks_pdr2000v2.addPlot()
        mks_pdr2000v2.setYLabel("Pressure")
        mks_pdr2000v2.selectDeviceCommand("select_device", 1)
        mks_pdr2000v2.connection(cxn)
        mks_pdr2000v2.begin()
        self.devices.append(mks_pdr2000v2)

        lake218 = Device("Lakeshore 218")
        lake218.setServerName("lakeshore_218")
        lake218.addParameter("Sensor 1", "get_temperature", None)
        lake218.addParameter("Sensor 2", "get_temperature", None)
        lake218.addParameter("Sensor 3", "get_temperature", None)
        lake218.addParameter("Sensor 4", "get_temperature", None)
        lake218.addParameter("Sensor 5", "get_temperature", None)
        lake218.addParameter("Sensor 6", "get_temperature", None)
        lake218.addParameter("Sensor 7", "get_temperature", None)
        lake218.addParameter("Sensor 8", "get_temperature", None)
        lake218.addPlot()
        lake218.setYLabel("Temperature")
        lake218.selectDeviceCommand("select_device", 0)
        lake218.connection(cxn)
        lake218.begin()
        self.devices.append(lake218)
        
        mks_pdr2000v3 = Device("Still")
        mks_pdr2000v3.setServerName("mks_pdr2000_server")
        mks_pdr2000v3.addParameter("Pressure 1", "get_pressure", None, 0)
        mks_pdr2000v3.addParameter("Pressure 2", "get_pressure", None, 1)
        mks_pdr2000v3.addPlot()
        mks_pdr2000v3.setYLabel("Pressure")
        mks_pdr2000v3.selectDeviceCommand("select_device", 2)
        mks_pdr2000v3.connection( cxn)
        mks_pdr2000v3.begin()
        self.devices.append(mks_pdr2000v3)
        
      
        # # # # #Compressor.addButton("Turn Off", "You are about to turn the compressor off." , "status", None)
        # # # # #Compressor.addButton("Turn On", "You are about to turn the compressor on." , "status", None)
     
        
        # Start the datalogger. This line can be commented
        # out if no datalogging is required.
        self.chest = dataChestWrapper(self.devices)
        
        # Create the gui
        self.gui = MGui.MGui()
        self.gui.startGui(self.devices, 'Leiden Gui', 'Leiden Data', tele)
        
        
# In phython, the main class's __init__() IS NOT automatically called
viewer = nViewer()  
viewer.__init__()
