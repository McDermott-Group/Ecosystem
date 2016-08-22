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


        Return = Device("Return")
        Return.setServerName("mks_pdr2000_server")
        Return.addParameter("Pressure 1", "get_pressure", None, 0)
        Return.addParameter("Pressure 2", "get_pressure", None, 1)
        Return.addPlot()
        Return.setPlotRefreshRate(3)
        Return.setRefreshRate(3)
        Return.setYLabel("Pressure")
        Return.selectDeviceCommand("select_device", 0)
        Return.connection(cxn)
        Return.begin()
        self.devices.append(Return)
        
        Still = Device("Still")
        Still.setServerName("mks_pdr2000_server")
        Still.addParameter("Pressure 1", "get_pressure", None, 0)
        Still.addParameter("Pressure 2", "get_pressure", None, 1)
        Still.addPlot()
        Still.setPlotRefreshRate(3)
        Still.setRefreshRate(3)
        Still.setYLabel("Pressure")
        Still.selectDeviceCommand("select_device", 2)
        Still.connection(cxn)
        Still.begin()
        self.devices.append(Still)

        Keg = Device("Keg")
        Keg.setServerName("mks_pdr2000_server")
        Keg.addParameter("Pressure 1", "get_pressure", None, 0)
        Keg.addParameter("Pressure 2", "get_pressure", None, 1)
        Keg.addPlot()
        Keg.setPlotRefreshRate(3)
        Keg.setRefreshRate(3)
        Keg.setYLabel("Pressure")
        Keg.selectDeviceCommand("select_device", 1)
        Keg.connection(cxn)
        Keg.begin()
        self.devices.append(Keg)
        
        lake370 = Device("Lakeshore 370")
        lake370.setServerName("lakeshore_ruox")
        for i in range(0,5):
            lake370.addParameter("Temperature "+str(i+1), "temperatures", None,i)
        lake370.setYLabel("Temperature")
        lake370.selectDeviceCommand("select_device", 0)
        lake370.addPlot()
        lake370.setPlotRefreshRate(3)
        lake370.setRefreshRate(3)
        lake370.connection(cxn)
        lake370.begin()
        self.devices.append(lake370)

        lake218 = Device("Lakeshore 218")
        lake218.setServerName("lakeshore_218")
        lake218.addParameter("Sensor 1", "get_temperature", 1)
        lake218.addParameter("Sensor 2", "get_temperature", 2)
        lake218.addParameter("Sensor 3", "get_temperature", 3)
        lake218.addParameter("Sensor 4", "get_temperature", 4)
        lake218.addParameter("Sensor 5", "get_temperature", 5)
        lake218.addParameter("Sensor 6", "get_temperature", 6)
        lake218.addParameter("Sensor 7", "get_temperature", 7)
        lake218.addParameter("Sensor 8", "get_temperature", 8)
        lake218.addPlot()
        lake218.setPlotRefreshRate(3)
        lake218.setRefreshRate(3)
        lake218.setYLabel("Temperature")
        lake218.selectDeviceCommand("select_device", 0)
        lake218.connection(cxn)
        lake218.begin()
        self.devices.append(lake218)
        
        
        # Start the datalogger. This line can be commented
        # out if no datalogging is required.
        self.chest = dataChestWrapper(self.devices)
        
        # Create the gui
        self.gui = MGui.MGui()
        self.gui.startGui(self.devices, 'Leiden Gui', 'Leiden Data', tele)
        
        
# In phython, the main class's __init__() IS NOT automatically called
viewer = nViewer()  
viewer.__init__()
