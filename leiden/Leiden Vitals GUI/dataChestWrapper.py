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

# Utilities libraries.


"""
### BEGIN NODE INFO
[info]
name = NGui class
version = 1.0.1
description = Handles datalogging using DataChest

### END NODE INFO
"""

from PyQt4 import QtCore, QtGui
import os
from dataChest import *
import sys
from dateStamp import *
import datetime
import threading
import numpy

class dataChestWrapper:

	def __init__(self, devices):
		now = datetime.datetime.now()
		self.devices = devices
		self.dataSets = []
		#This is not the right way to do it
		self.chest = dataChest(str(now.year))
		
		for i in range(0, len(self.devices)):
			title = str(self.devices[i].getFrame().getTitle()).replace(" ", "")
			self.dataSets.append(dataChest(str(now.year)))
				
			try:
				self.dataSets[i].cd(str(now.month))
			except:
				self.dataSets[i].mkdir(str(now.month))
				self.dataSets[i].cd(str(now.month))
		
			# The name of the dataset should be the name of the device
			
			existingFiles = self.dataSets[i].ls()
			#print(len(existingFiles[0]))
			paramName = None
			
			#print existingFiles
			#print(title)
			foundit = False
			#print("HERE")
			for y in range(0, len(existingFiles[0])):
				#print("HEREB")
				#print "checking file: ",existingFiles[0][y]
				#print "Against: ", title, "\n"
				if(title in existingFiles[0][y]):
					self.dataSets[i].openDataset(existingFiles[0][y], modify = True)
					foundit = True
				
			if(foundit):
				print("Previously existing data found for "+title)
			else:
				#print self.devices[i].getFrame().getTitle()
				#title = str(self.devices[i].getFrame().getTitle()).replace(" ", "")
				depvars = []
				indepvars = []
				#print(len(self.devices[i].getFrame().getNicknames()))
				for y in range (0, len(self.devices[i].getFrame().getNicknames())):
					if(self.devices[i].getFrame().getNicknames()[y] is not None):
						paramName = str(self.devices[i].getFrame().getNicknames()[y] if  \
									self.devices[i].getFrame().getNicknames()[y] is not None \
									else str(y)).replace(" ", "")
						#print(str(self.devices[i].getFrame().getUnits()))
						tup = (paramName, [1], "float64", str(self.devices[i].getFrame().getUnits()))
						depvars.append(tup)
				dStamp = dateStamp()
				indepvars.append(("time", [1], "utc_datetime", "s"))
				vars = []
				vars.extend(indepvars)
				vars.extend(depvars)
				#print "vars:", vars
				#self.chest.createDataset(title,
				#						indepvars,
				#						depvars)
				#self.chest.addParameter("DataWidth", len(vars))
				#print(len(vars))
				
			
					
				self.dataSets[i].createDataset(title,
										indepvars,
										depvars)
				self.dataSets[i].addParameter("DataWidth", len(vars))

				
				#print self.dataSets[i].getParameter("DataWidth")
				#print self.dataSets[i].getDatasetName()
				#print self.dataSets[i].ls()
		#self.chest.cd(str(now.year))
		#print os.environ['DATA_CHEST_ROOT']
		#print now.year
		self.deviceThread = threading.Thread(target = self.save, args=[])
		# If the main thread stops, stop the child thread
		self.deviceThread.daemon = True
		# Start the thread
		self.deviceThread.start()
		
	def save(self):
		#print("HEREA")
		#print self.chest.pwd()
		for i in range(0, len(self.dataSets)):
			depvars = []
			indepvars = []
			vars = []
			readings = []
			for y in range(0, len(self.devices[i].getFrame().getNicknames())):
				if(self.devices[i].getFrame().getNicknames()[y] is not None):
					if(self.devices[i].getFrame().getReadings() is not None):
						readings.append(self.devices[i].getFrame().getReadings()[y])
					else:
						readings.append(np.nan)
			#readings = self.devices[i].getFrame().getReadings()
			dStamp = dateStamp()
			#print(self.devices[i].getFrame().getTitle())
			#print "readings", readings
			if(readings is not None):
				#for y in range(0, len(readings)):
				#print("Readings NOT NONE")
				#print(self.devices[i].getFrame().getTitle())
				indepvars.append(dStamp.utcNowFloat())
				depvars.extend(readings)
				#print([indepvars.extend(depvars)])
				
				#print vars
				vars.extend(indepvars)
				vars.extend(depvars)
				#print "vars:", vars
				#print len(self.dataSets[i].getData())
				self.dataSets[i].addData([vars])
				#print vars
			else:
				#print self.dataSets[i].getParameter("DataWidth")
				vars.append(dStamp.utcNowFloat())
				for y in range(1, self.dataSets[i].getParameter("DataWidth")):
					vars.append(np.nan)
				#print("READINGS NONE")
				#print(self.devices[i].getFrame().getTitle())
				#print vars
				self.dataSets[i].addData([vars])
				#print "Nan"
			
		threading.Timer(1, self.save).start()

		#self.chest.createDataset(self.dataName)