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
description = Handles easy construction of GUI

### END NODE INFO
"""
from PyQt4 import QtCore, QtGui
from multiprocessing.pool import ThreadPool
import threading
import sys
import ctypes
from functools import partial
import os
import dataChest
from dataChestWrapper import *
from dateStamp import *
from datetime import *


class NGui(QtGui.QDialog):


	
	dialog = None
	parameters = [[]]
	frames = []
	grids = []
	devices = None
	mainVBox = QtGui.QVBoxLayout()
	mainHBox = QtGui.QHBoxLayout()
	titles = []
	dataSets = []
	lcds = [[]]
	units = [[]]
	buttons = [[]]
	
	font = QtGui.QFont()
	font.setPointSize(12)
	font.setBold(False)
	font.setWeight(50)
	font.setKerning(True)
	def initGui(self, devices, parent = None):
		'''Create a base gui to start from'''
		QtGui.QWidget.__init__(self, parent)
		# Make pretty
		self.setStyleSheet("background:rgb(70, 80, 88)")
		# Get list of devices
		self.devices = devices
		# Stack the device frames
		self.setLayout(self.mainHBox)
		self.mainHBox.addLayout(self.mainVBox)
		# For each device, add a GUI frame for it.
		
		
		now = datetime.now()
		
		
		#self.chest = dataChest.dataChest(str(now.year))
		self.chest = dataChestWrapper(devices)
		# try:
			# self.chest.mkdir(str(now.month))
			# self.chest.cd(str(now.month))
			
		# except:
			# self.chest.cd(str(now.month))
			
			
		for i in range(0,len(self.devices)):
			#Append a new gui frame
			self.frames.append(QtGui.QFrame(self))
			self.mainVBox.addWidget(self.frames[i])
			# Add new titles, grids, parameters, and lcds for the new parameter
			self.titles.append(QtGui.QLabel(self.frames[i]))
			self.grids.append(QtGui.QGridLayout())
			self.parameters.append([])
			self.lcds.append([])
			self.units.append([])
			self.buttons.append([])
			#self.dataSets.append()
			#print(i)
			
			# Configure grid layout
			self.grids[i].setSpacing(10)
			self.grids[i].addWidget(self.titles[i], 1, 0)
			self.grids[i].setColumnStretch(0,1)
			# Configure the frame (the box surrounding information for each device)
			self.frames[i].setStyleSheet("background: rgb(52, 73, 94)")
			self.frames[i].setFrameShape(QtGui.QFrame.WinPanel)
			self.frames[i].setFrameShadow(QtGui.QFrame.Plain)
			self.frames[i].setLineWidth(2)
			self.frames[i].setLayout(self.grids[i])
			# Configure the layout of the buttons within the grid
			buttonLayout = QtGui.QHBoxLayout()
			self.grids[i].addLayout(buttonLayout, 1, 1)
			# Create all buttons.
			if(len(self.devices[i].getFrame().getButtons()[0])>0):
				for b in range(0, len(self.devices[i].getFrame().getButtons())):
					# Append a new button to the array of buttons and set the parent as the current frame
					self.buttons[i].append(QtGui.QPushButton(self.frames[i]))
					# Set the text of the button to the name specified when the device was initialized
					self.buttons[i][b].setText(self.devices[i].getFrame().getButtons()[b][0])
					# Add the button to the screen.
					buttonLayout.addWidget(self.buttons[i][b])
					# Connect the button to function, passing the number of the button that was clicked
					self.buttons[i][b].clicked.connect(partial(self.devices[i].prompt, b))
					# Make the button pretty
					self.buttons[i][b].setStyleSheet("color:rgb(189, 195, 199); background:rgb(70, 80, 88)")
					self.buttons[i][b].setFont(self.font)
					
			# Make the titles look nice
			self.titles[i].setStyleSheet("color:rgb(189, 195, 199);")
			self.font.setPointSize(18)
			self.titles[i].setFont(self.font)
			self.font.setPointSize(12)
			# Get the title of the device
			self.titles[i].setText(self.devices[i].getFrame().getTitle())
			self.titles[i].setGeometry(QtCore.QRect(10,10,self.titles[i].fontMetrics().boundingRect(self.titles[i].text()).width(),40))
			
			
			# try:
			# #The name of the dataset should be the name of the device
				# self.chest.openDataset(self.devices[i].getFrame().getTitle())
			# except:
				# print self.devices[i].getFrame().getTitle()
				# title = str(self.devices[i].getFrame().getTitle()).replace(" ", "")
				# depvars = []

				# for y in range (0, len(self.devices[i].getFrame().getNicknames())):
					# paramName = str(self.devices[i].getFrame().getNicknames()[y] if  \
								# self.devices[i].getFrame().getNicknames()[y] is not None \
								# else str(y)).replace(" ", "")
					# tup = (paramName, [1], "float64", str(self.devices[i].getFrame().getUnits()))
					# depvars.append(tup)
					# print depvars
				# self.chest.createDataset(title,
										# [("time", [1], "utc_datetime","")],
										# depvars)
				# self.dataSets.append(self.chest)

			for y in range(0, len(self.devices[i].getFrame().getNicknames())):
				# Add a new parameter to the current device
				self.parameters[i].append(QtGui.QLabel(self.frames[i]))
				self.units[i].append(QtGui.QLabel(self.frames[i]))
				
				#print(set)
				#Get the width of the text
				self.parameters[i][y].setFont(self.font)
				self.parameters[i][y].setAlignment(QtCore.Qt.AlignLeft)
				self.units[i][y].setFont(self.font)
				self.units[i][y].setAlignment(QtCore.Qt.AlignRight)
				# Configure the QLCDnumber widgets that display information
				self.lcds[i].append(QtGui.QLCDNumber())
				self.lcds[i][y].setNumDigits(11)
				self.lcds[i][y].setSegmentStyle(QtGui.QLCDNumber.Flat)
				self.lcds[i][y].setFrameShape(QtGui.QFrame.WinPanel)
				self.lcds[i][y].setFrameShadow(QtGui.QFrame.Plain)
				self.lcds[i][y].setLineWidth(100)
				self.lcds[i][y].setMidLineWidth(100)
				self.lcds[i][y].setStyleSheet("color:rgb(189, 195, 199);\n")
				self.lcds[i][y].setFixedSize(350,60)
				# Make the parameters pretty
				self.parameters[i][y].setWordWrap(True)
				self.parameters[i][y].setStyleSheet("color:rgb(189, 195, 199);")	
				# Hide everything until we know that it should be displayed. This is essential to be able to handle arrays
				self.parameters[i][y].hide()
				self.lcds[i][y].hide()
				self.units[i][y].hide()
				# If a nickname for the setting has been defined, go ahead and display whatever is necessary
				if(self.devices[i].getFrame().getNicknames()[y] is not None):
					self.parameters[i][y].show()
					self.lcds[i][y].show()
					self.units[i][y].show()
					self.parameters[i][y].setText(devices[i].getFrame().getNicknames()[y])
					self.grids[i].addWidget(self.parameters[i][y], y+2, 0)
					self.grids[i].addWidget(self.lcds[i][y], y+2, 1)
					self.grids[i].addWidget(self.units[i][y], y+2, 2)
					
		# dataChestFrame = QtGui.QFrame(self)
		# dataChestFrame.setStyleSheet("background: rgb(52, 73, 94)")
		# dataChestFrame.setFrameShape(QtGui.QFrame.WinPanel)
		# dataChestFrame.setFrameShadow(QtGui.QFrame.Plain)
		# dataChestFrame.setLineWidth(2)
		
		# dataChestGrid = QtGui.QGridLayout()
		# dataChestGrid.setSpacing(10)
		# dataChestLabel = QtGui.QLabel(dataChestFrame)
		# dataChestLabel.setText("Data Chest Root")
		# self.font.setPointSize(18)
		# dataChestLabel.setFont(self.font)
		# self.font.setPointSize(12)
		# dataChestLabel.setStyleSheet("color:rgb(189, 195, 199);")	

		# pathLabel = QtGui.QLabel(dataChestFrame)
		# pathLabel.setFont(self.font)
		# pathLabel.setStyleSheet("color:rgb(189, 195, 199);")
		# envPath = os.environ.get('DATA_CHEST_ROOT')
		# print os.environ['DATA_CHEST_ROOT']
		# pathLabel.setText(envPath if envPath is not None else "Please Configure DATA_CHEST_ROOT")
		# #pathLabel.setText(envPath)
		# browseButton = QtGui.QPushButton(dataChestFrame)
		# browseButton.setText("Browse")
		# browseButton.setFont(self.font)
		# browseButton.setStyleSheet("color:rgb(189, 195, 199); background:rgb(70, 80, 88)")
		# dataChestFrame.setLayout(dataChestGrid)
		
		# dataChestGrid.addWidget(dataChestLabel, 1, 0)
		# dataChestGrid.addWidget(browseButton,2,1)
		# dataChestGrid.addWidget(pathLabel,2,0)
		# dataChestGrid.setColumnStretch(0,1)
		# self.mainVBox.addWidget(dataChestFrame)
		# browseButton.clicked.connect(partial(self.selectFolder, pathLabel))
		
		print("Gui initialized")
		return
	def startGui(self, devices, title, dataTitle):
		# Used as the name of the dataChest data title
		self.dataTitle = dataTitle
		# Call the class's init function
		self.initGui(devices)
		self.setWindowTitle(title)
		#self.chest = dataChestWrapper.dataChestWrapper(dataTitle)
		# Show the gui
		self.show()
		timer = QtCore.QTimer(self)
		# Update the gui every so often. This CAN ONLY be done in the main thread.
		timer.timeout.connect(self.update)
		timer.start(1000)
		
		sys.exit(app.exec_())
		
	def selectFolder(self, pathLabel):
		# dir_ = QtGui.QFileDialog.getExistingDirectory(None, 'Select a folder:', 'C:\\', QtGui.QFileDialog.ShowDirsOnly)
		# pathLabel.setText(dir_)
		# os.environ['DATA_CHEST_ROOT'] = str(dir_)
		# print(os.environ['DATA_CHEST_ROOT'])
		# Reconfigure datachest
		# now = datetime.datetime.now()
		# self.dataName = dataSetName
		# #This is not the right way to do it
		# self.chest = dataChest(str(now.year))
		# try:
			# self.chest.mkdir(str(now.month))
			# self.chest.cd(str(now.month))
		# except:
			# self.chest.cd(str(now.month))
			
		return dir_
	
	def update(self):
		readings = [];
		error = False;
	
		# loop through all devices
		for i in range(0, len(self.devices)):
			# If there is no error with the device
			if(not self.devices[i].getFrame().isError()):
				# Save Data to DataChest
				now = datetime.now()
			
				# Get the readings from the frame
				readings = self.devices[i].getFrame().getReadings();
				#dStamp = dateStamp()
				#print(self.dataSets[i])
				
				if(readings is not None):
					# Holds an array containing the new data for use when adding data to the current dataset
					newData = []

					# Update all QLcds with the reading
					for y in range(0, len(readings)):
						self.lcds[i][y].setSegmentStyle(QtGui.QLCDNumber.Flat)
						self.lcds[i][y].display(readings[y])
						# Add the independent variables to the new dataset
						# #newData.append(dStamp.utcNowFloat())
						# If there are units, put them next to the number
						if(len(self.devices[i].getFrame().getUnits())>0):
							self.units[i][y].setText(self.devices[i].getFrame().getUnits()[y])
							self.font.setPointSize(18)
							self.units[i][y].setFont(self.font)
							self.font.setPointSize(12)
							self.units[i][y].setStyleSheet("color:rgb(189, 195, 199);")
				# Store all data sets
				# Add the dependent variables to the new dataset
					#print(readings)
					#newData.extend(readings)
					#print([newData])
					#self.dataSets[i].addData([newData])
			else:
				# Otherwise if there is an error, show that on the gui through outlined lcd numbers
				for y in range(0, len(self.lcds[i])):
					self.lcds[i][y].setSegmentStyle(QtGui.QLCDNumber.Outline)
					self.lcds[i][y].display("-")
		return
			

app=QtGui.QApplication(sys.argv)

