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
### BEGIN NODE INFO
[info]
name = Leiden Vitals Gui
version = 1.1.0
description = Monitors Leiden Devices

### END NODE INFO
"""
import NGui				# Handles all gui operations. Independent of labrad.
from PyQt4 import QtCore, QtGui
from NFrame import NFrame		# Handles the information passibg between 
from Device import Device
from multiprocessing.pool import ThreadPool
import threading
import labrad
import labrad.units as units
class nViewer:
	gui = None
	devices =[]
	def __init__(self, parent = None):
	
		cxn = labrad.connect();
		
		
		testDevice = Device("my_server", "Random Number Generator", ["Random Pressure", "Random Temperature"], ["pressure", "temperature"], cxn, ["Pressure","Temperature"], ["pressure", "temperature"], ["You are about to get a random pressure", None])
		self.devices.append(testDevice)
		
		# testDevice = Device("Compressor", ["Water Temperature In", "Water Temperature Out"])
		# self.devices.append(testDevice)
		
		# testDevice = Device("External Water Temperature", ["Ext. Temperature"])
		# self.devices.append(testDevice)
		
		Flow = Device("omega_ratemeter_server","External Water Flow Rate", ["Flow Rate"], ["get_rate"], cxn, None, None, None, "select_device", 0)
		self.devices.append(Flow)
		
		testDevice = Device("pfeiffer_vacuum_maxigauge", "Pressure Monitor", [None, None, None, "Pressure OVC","Pressure IVC", "Still Pressure"], ["get_pressures"], cxn, None, None, None,"select_device", 0)
		self.devices.append(testDevice)
		
		# testDevice = Device("Fridge Temperature", ["Still", "Exchange", "Mix (TT)", "Mix (PT-1000)", "50K", "3K"])
		# self.devices.append(testDevice)
	
		self.gui = NGui.NGui()
		self.gui.startGui(self.devices)

		
viewer = nViewer()	
viewer.__init__()
