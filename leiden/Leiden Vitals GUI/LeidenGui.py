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

#from PyQt4 import QtCore, QtGui

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
			cxn = labrad.connect();
		except:
			print("Please start the labrad manager")
		##################################################################
		# How to Use nViewer:	 
		################################################################
		#	nViewer can be used with any labrad server, and given a new device class (it must have a "prompt" function), anything else.
		#	It is meant to be a tool which allows much, much easier creation of straightforward gui's.
		#	To create you own, make a new class in which you establish a connection to labrad, create new
		#	device instances, and start the gui.
		#
		#
		# Here are the steps to create your own gui.
		# 1. Establish LabRad connection
		#		cxn = labrad.connect()
		#
		# 2. Create Device
		#		 ex = Device("NAME OF LABRAD SERVER", 
		#						 "TITLE TO BE SHOWN ON GUI", 
		#						 [LIST OF FIELDS TO BE DISPLAYED ON GUI],
		#						 [LIST OF THOSE FIELDS' CORRESPONDING SERVER SETTINGS], 
		#						 [ARGUMENTS TO BE PASSED TO THOSE SETTINGS]
		#						 CONNECTION REFERENCE,
		#						 ["LIST","OF","BUTTONS"], 
		#						 ["SETTINGS", "ACTIVATED", "BY BUTTONS"], 
		#						 ["ALERT TO BE DISPLAYED WITH EACH BUTTON PRESS", "NONE IF NO MESSAGE"]
		#						 ["ARGUMENTS PASSED TO THE SETTINGS TRIGGERED BY THE BUTTONS"]
		#						"yAxis Label"(OPTIONAL),
		#						"SELECT DEVICE COMMAND (OPTIONAL FOR SERVERS THAT DO NOT REQUIRE DEVICE SELECTION)", 
		#						 "DEVICE NUMBER",)
		# 3. Start the dataChest datalogger, this line can be commented out
		#	if no datalogging is required.
		#			self.chest = dataChestWrapper(self.devices)
		#	
		# 4. Start nGui and name the window
		# 		self.gui = NGui.NGui()
		#		self.gui.startGui(self.devices, Window title)
		#
		# 5. Initialize nViewer OUTSIDE OF THE CLASS
		#		viewer = nViewer()	
		#		viewer.__init__()
		###################################################################
		
		# This is my test server
		testDevice = Device("my_server", "Random Number Generator", ["Random Pressure", "Random Temperature"], ["pressure", "temperature"], [None, None], cxn, ["Pressure","Temperature"], ["pressure", "temperature"], ["You are about to get a random pressure", None],[None,None])
		self.devices.append(testDevice)
		# Leiden DR monitor
		LeidenDRTemperature = Device("leiden_dr_temperature", 
						"Leiden DR", 
						["Mix (PT-1000)",
						"Mix (TT)", 
						"Still",
						"Exchange"], 
						["mix_temperature_pt1000",
						"mix_temperature",
						"still_temperature", 
						"exchange_temperature"],
						[None], cxn, None,None, None,[None])
		self.devices.append(LeidenDRTemperature)
		# Compressor Monitor
		Compressor = Device("cp2800_compressor",
						"Compressor",
						["Input Water Temperature", 
						"Output Water Temperature", 
						"Helium Temperature",
						"Oil Temperature"],
						["temperaturesforgui"], 
						[None], cxn, 
						["Turn On", "Turn Off"], 
						["status", "status"], 
						["You are about to turn the compressor on",
						"You are about to turn the compressor off"], 
						[None, None], "Temperature", "select_device", 0)
		self.devices.append(Compressor)
		# Omega Temperature Monitor server
		Temperature = Device("omega_temp_monitor_server",
						"External Water Temperature",
						["Temperature"],
						["get_temperature"],
						[None], cxn, None, None, None, [None],None,
						"select_device", 0)
		self.devices.append(Temperature)
		# Omega Flow Meter
		Flow = Device("omega_ratemeter_server","External Water Flow Rate", 
						["Flow Rate"], 
						["get_rate"],
						[None], cxn, None, None, None, None,None,
						"select_device", 0)
		self.devices.append(Flow)
		# Pfeiffer Vacuum Monitor
		vacuum = Device("pfeiffer_vacuum_maxigauge", "Pressure Monitor", 
						[None, None, None, 
						"OVC Pressure",
						"IVC Pressure", 
						"Still Pressure"], 
						["get_pressures"], 
						[None], cxn, None, None, None,[None],None,
						"select_device", 0)
		self.devices.append(vacuum)
		
		# Start the datalogger. This line can be commented
		# out if no datalogging is required.
		#self.chest = dataChestWrapper(self.devices)
		
		# Create the gui
		self.gui = NGui.NGui()
		self.gui.startGui(self.devices, 'Leiden Gui', 'Leiden Data')
		
		
# In phython, the main class's __init__() IS NOT automatically called
viewer = nViewer()	
viewer.__init__()
