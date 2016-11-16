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
        PT1000s.addPlot()
        PT1000s.begin()
        self.devices.append(PT1000s)
        
        
        LeidenDRTemperature = Device("Leiden DR")
        LeidenDRTemperature.connection(cxn)

        LeidenDRTemperature.setServerName("leiden_dr_temperature")
        LeidenDRTemperature.addParameter("Mix (PT-1000)",
                "mix_temperature_pt1000", None)
        LeidenDRTemperature.addParameter("Mix (TT)",
                "mix_temperature", None)
        LeidenDRTemperature.addParameter("Still",
                "still_temperature", None)
        LeidenDRTemperature.addParameter("Exchange",
                "exchange_temperature", None)
        LeidenDRTemperature.selectDeviceCommand("select_device", 0)
        LeidenDRTemperature.addPlot()
        LeidenDRTemperature.begin()
        LeidenDRTemperature.setYLabel("Temperature")
        self.devices.append(LeidenDRTemperature)

        Compressor = Device("Compressor")
        Compressor.setServerName("cp2800_compressor")
        Compressor.addButton("Turn Off",
                "You are about to turn the compressor off.",
                "status", None)
        Compressor.addButton("Turn On",
                "You are about to turn the compressor on.",
                "status", None)
        Compressor.addParameter("Input Water Temperature",
                "temperaturesforgui", None, 0)
        Compressor.addParameter("Output Water Temperature",
                "temperaturesforgui", None, 1)
        Compressor.addParameter("Helium Temperature",
                "temperaturesforgui", None, 2)
        Compressor.addParameter("Oil Temperature",
                "temperaturesforgui", None, 3)
        Compressor.addPlot()
        Compressor.setYLabel("Temperature")
        Compressor.selectDeviceCommand("select_device", 0)
        Compressor.connection(cxn)
        Compressor.begin()
        self.devices.append(Compressor)
        
        Vacuum = Device("Vacuum")
        Vacuum.setServerName("pfeiffer_vacuum_maxigauge")
        Vacuum.connection(cxn)
        Vacuum.addPlot()
        # Vacuum.addParameter("Sensor 1", "get_pressures", None, 0)
        # Vacuum.addParameter("Sensor 2", "get_pressures", None, 1)
        # Vacuum.addParameter("Sensor 3", "get_pressures", None, 2)
        Vacuum.addParameter("OVC Pressure", "get_pressures", None, 3)
        Vacuum.addParameter("IVC Pressure", "get_pressures", None, 4)
        Vacuum.addParameter("Still Pressure", "get_pressures", None, 5)
        Vacuum.setYLabel("Pressure")
        Vacuum.selectDeviceCommand("select_device", 0)
        Vacuum.begin()
        self.devices.append(Vacuum)
        
        Temperature = Device("Temperature")
        Temperature.connection(cxn)
        Temperature.setServerName("omega_temperature_monitor")
        Temperature.addParameter("Exteranal Water Temperature",
                "get_temperature")
        Temperature.selectDeviceCommand("select_device", 0)
        Temperature.addPlot()
        Temperature.setYLabel("Temperature")
        Temperature.begin()
        self.devices.append(Temperature)

        Flow = Device("Flow Meter")
        Flow.connection(cxn)
        Flow.setServerName("omega_ratemeter")
        Flow.addParameter("External Water Flow Rate", "get_rate")
        Flow.selectDeviceCommand("select_device", 0)
        Flow.setYLabel("Flow Rate")
        Flow.addPlot()
        Flow.begin()
        self.devices.append(Flow)

        # Start the datalogger. This line can be commented
        # out if no datalogging is required.
        self.chest = dataChestWrapper(self.devices)
        
        # Create the gui.
        self.gui = MGui.MGui()
        self.gui.startGui(self.devices, 'Leiden DR GUI', 'Leiden Data', tele)
        
        
# In Python, the main class's __init__() IS NOT automatically called.
viewer = nViewer()    
viewer.__init__()