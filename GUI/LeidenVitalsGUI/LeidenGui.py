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

import sys
import time
from tendo import singleton

import labrad

from dataChestWrapper import *
import MGui # Handles all GUI operations. Independent of LabRAD.
from MDevices.Device import Device


class nViewer:
    gui = None
    devices =[]
    def __init__(self, parent = None):
        # Establish a connection to LabRAD.
        try:
            # Thiss will sys.exit(-1) if other instance is running.
            me = singleton.SingleInstance()
        except:
            print("Multiple instances cannot be running")
            time.sleep(2)
            sys.exit(1)
        try:
            cxn = labrad.connect() # Attempt to establish a labrad connection.
        except:
            # If no connection can be made, abort with an error message.
            print("Please start the LabRAD manager")
            time.sleep(2)
            sys.exit(0)
        try:
            # As of writing, there is one class in MView itself that is dependent
            # on LabRad, and it requires the telecomm server to be running. 
            # This is subject to change.
            tele = cxn.telecomm_server
        except:
            # If no connection can be made, abort with an error message.
            print("Please start the telecomm server")
            time.sleep(2)
            sys.exit(1)

        PT1000s = Device("50K and 3K Pt1000 Temperatures")
        PT1000s.connection(cxn)
        PT1000s.setServerName("goldstein_s_pt1000_temperature_monitor")
        PT1000s.addParameter("50K Stage Temperature",
                "get_temperatures", None, 0, precision=1)
        PT1000s.addParameter("3K Stage Temperature",
                "get_temperatures", None, 1, precision=1)
        # PT1000s.addParameter("50K Stage PT1000 Resistance",
                # "get_resistances", None, 0)
        # PT1000s.addParameter("3K Stage PT1000 Resistance",
                # "get_resistances", None, 1)
        PT1000s.selectDeviceCommand("select_device", 0)
        PT1000s.setYLabel("Temperature")
        PT1000s.addPlot()
        PT1000s.begin()
        self.devices.append(PT1000s)

        LeidenDRTemperature = Device("Dilution Unit Temperatures")
        LeidenDRTemperature.connection(cxn)
        LeidenDRTemperature.setServerName("leiden_dr_temperature")
        LeidenDRTemperature.addParameter("Still Temperature",
                "still_temperature", None)
        LeidenDRTemperature.addParameter("Exchange Temperature",
                "exchange_temperature", None)
        LeidenDRTemperature.addParameter("Mix Temperature",
                "mix_temperature", None)
        LeidenDRTemperature.addPlot()
        LeidenDRTemperature.begin()
        LeidenDRTemperature.setYLabel("Temperature")
        self.devices.append(LeidenDRTemperature)
        
        LeidenDRTemperature = Device("Mix Pt1000 Temperature")
        LeidenDRTemperature.connection(cxn)
        LeidenDRTemperature.setServerName("leiden_dr_temperature")
        LeidenDRTemperature.addParameter("Mix Temperature",
                "mix_temperature_pt1000", None)
        LeidenDRTemperature.addPlot()
        LeidenDRTemperature.begin()
        LeidenDRTemperature.setYLabel("Temperature")
        self.devices.append(LeidenDRTemperature)

        Vacuum = Device("Vacuum")
        Vacuum.connection(cxn)
        Vacuum.setServerName("pfeiffer_vacuum_maxigauge")
        Vacuum.addParameter("OVC Pressure", "get_pressures", None, 3,
                'mbar', 4)
        Vacuum.addParameter("IVC Pressure", "get_pressures", None, 4,
                'mbar', 4)
        Vacuum.addParameter("Still Pressure", "get_pressures", None, 5,
                'mbar', 4)
        Vacuum.setYLabel("Pressure")
        Vacuum.selectDeviceCommand("select_device", 0)
        Vacuum.addPlot()
        Vacuum.begin()
        self.devices.append(Vacuum)

        Temperature = Device("Water Temperature")
        Temperature.connection(cxn)
        Temperature.setServerName("omega_temperature_monitor")
        Temperature.addParameter("Exteranal Water Temperature",
                "get_temperature")
        Temperature.selectDeviceCommand("select_device", 0)
        Temperature.setYLabel("Temperature")
        Temperature.addPlot()
        Temperature.begin()
        self.devices.append(Temperature)

        Compressor = Device("Compressor")
        Compressor.connection(cxn)
        Compressor.setServerName("cp2800_compressor")
        Compressor.addButton("Turn Off",
                "You are about to turn the compressor off.",
                "stop", None)
        Compressor.addButton("Turn On",
                "You are about to turn the compressor on.",
                "start", None)
        Compressor.addParameter("Input Water Temperature",
                "current_temperatures_only", None, 0, 'degC', 1)
        Compressor.addParameter("Output Water Temperature",
                "current_temperatures_only", None, 1, 'degC', 1)
        Compressor.addParameter("Helium Temperature",
                "current_temperatures_only", None, 2, 'degC', 1)
        Compressor.addParameter("Oil Temperature",
                "current_temperatures_only", None, 3, 'degC', 1)
        Compressor.selectDeviceCommand("select_device", 0)
        Compressor.setYLabel("Temperature")
        Compressor.addPlot()
        Compressor.begin()
        self.devices.append(Compressor)

        Flow = Device("Water Flow")
        Flow.connection(cxn)
        Flow.setServerName("omega_ratemeter")
        Flow.addParameter("External Water Flow Rate", "get_rate")
        Flow.selectDeviceCommand("select_device", 0)
        Flow.setYLabel("Flow Rate")
        Flow.addPlot()
        Flow.begin()
        self.devices.append(Flow)

        # Create the gui.
        self.gui = MGui.MGui()
        self.gui.startGui(self.devices, 'Leiden DR GUI',
                tele)


# In Python, the main class's __init__() IS NOT automatically called.
viewer = nViewer()    
viewer.__init__()
