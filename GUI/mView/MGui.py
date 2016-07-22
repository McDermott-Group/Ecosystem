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
version = 1.0.1
description = Handles easy construction of GUI
"""
import sys
sys.dont_write_bytecode = True
from PyQt4 import QtCore, QtGui
from multiprocessing.pool import ThreadPool
import threading
import ctypes
from functools import partial
import os
from NotifierGUI import NotifierGUI
import math
import MAlert
import numpy as np
import MGrapher


class MGui(QtGui.QMainWindow):
	
	dialog = None
	parameters = [[]]
	frames = []
	grids = []
	devices = None
	mainVBox = [QtGui.QVBoxLayout()]
	mainHBox = QtGui.QHBoxLayout()
	titles = []
	dataSets = []
	lcds = [[]]
	units = [[]]
	buttons = [[]]
	plots = [[]]
	font = QtGui.QFont()
	#font.setPointSize(12)
	font.setBold(False)
	font.setWeight(50)
	font.setKerning(True)
	VBoxColumn = 0
	def initGui(self, devices, parent = None):
		'''Create a base gui to start from'''
		QtGui.QWidget.__init__(self, parent)
		# Make pretty
		self.central_widget = QtGui.QWidget()
		self.setCentralWidget(self.central_widget)
		self.central_widget.setLayout(self.mainHBox)
		self.setStyleSheet("background:rgb(70, 80, 88)")
		# # Get list of devices
		# self.devices = devices
		# Stack the device frames
		# #self.setLayout(self.mainHBox)
		
		#self.mainHBox.addLayout(self.mainVBox[self.VBoxColumn])
		
		menubar = self.menuBar()
		menubar.setStyleSheet("QMenuBar {background-color: rgb(189, 195, 199)}"
				"QMenuBar::item {background: transparent} QMenu{background-color:rgb(189, 195, 199)}")
		#self.statusBar()
		#self.statusBar().setStyleSheet("background-color: rgb(189, 195, 199)")

		exitAction = QtGui.QAction('&Exit', self)        
		exitAction.setShortcut('Ctrl+Q')
		exitAction.setStatusTip('Exit application')
		exitAction.triggered.connect(QtGui.qApp.quit)
				
		NotifierSettingsAction = QtGui.QAction('&Settings...', self)
		NotifierSettingsAction.triggered.connect(self.openNotifierSettings)
		
		fileMenu = menubar.addMenu('&File')
		fileMenu.addAction(exitAction)
		
		NotifierMenu = menubar.addMenu('&Notifier')
		NotifierMenu.addAction(NotifierSettingsAction)
		# For each device, add a GUI frame for it.
		numWidgets = 0
		
		self.scrollArea = QtGui.QScrollArea()
		
		
		self.scrollArea.setWidget(self.central_widget)
		self.scrollArea.setWidgetResizable(True)

		self.setCentralWidget(self.scrollArea)
		frameSizePolicy = QtGui.QSizePolicy()
		frameSizePolicy.setVerticalPolicy(4)
		frameSizePolicy.setHorizontalPolicy(QtGui.QSizePolicy.Preferred)
		
		self.mainVBox.append(QtGui.QVBoxLayout())
		self.mainVBox.append(QtGui.QVBoxLayout())
		self.mainHBox.addLayout(self.mainVBox[0])
		self.mainHBox.addLayout(self.mainVBox[1])
		self.VBoxColumn = 0
		for i in range(0,len(self.devices)):
			# numWidgets = numWidgets+1
			# #Append a new gui frame
			self.frames.append(QtGui.QFrame(self))

			if self.VBoxColumn == 0:
				self.VBoxColumn = 1
			else:
				self.VBoxColumn = 0
			self.mainVBox[self.VBoxColumn].addWidget(self.frames[i])
			# Add new titles, grids, parameters, 
			# and lcds for the new parameter
			self.titles.append(QtGui.QLabel(self.frames[i]))
			self.grids.append(QtGui.QGridLayout())
			self.parameters.append([])
			self.lcds.append([])
			self.units.append([])
			self.buttons.append([])
			self.plots.append([])
			# Configure grid layout
			self.grids[i].setSpacing(10)
			self.grids[i].addWidget(self.titles[i], 1, 0)
			self.grids[i].setColumnStretch(0,1)
			# Configure the frame (the box surrounding 
			# information for each device)
			self.frames[i].setSizePolicy(frameSizePolicy)
			
			self.frames[i].setStyleSheet("background: rgb(52, 73, 94)")
			self.frames[i].setFrameShape(QtGui.QFrame.Panel)
			self.frames[i].setFrameShadow(QtGui.QFrame.Plain)
			self.frames[i].setSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
			self.ratio =float(self.scrnWidth)/1800+1
			#print(self.ratio)
			self.frames[i].setLineWidth(self.ratio)
			self.frames[i].setLayout(self.grids[i])
			# Configure the layout of the buttons within the grid
			buttonLayout = QtGui.QHBoxLayout()
			self.grids[i].addLayout(buttonLayout, 1, 1)
			# Create all buttons.
			if(len(self.devices[i].getFrame().getButtons()[0])>0):
				for b in range(0, len(self.devices[i]
					.getFrame().getButtons())):
					# Append a new button to the array of buttons and 
					# set the parent as the current frame
					self.buttons[i].append(QtGui
						.QPushButton(self.frames[i]))
					# Set the text of the button to the name specified 
					# when the device was initialized					
					self.buttons[i][b].setText(self.devices[i]
						.getFrame().getButtons()[b][0])
					# Add the button to the screen.
					buttonLayout.addWidget(self.buttons[i][b])
					# Connect the button to function, 
					# passing the number of the button that was clicked
					self.buttons[i][b].clicked.connect(partial(self
						.devices[i].prompt, b))
					# Make the button pretty
					self.buttons[i][b].setStyleSheet("color:rgb(189," 
						"195, 199); background:rgb(70, 80, 88)")
					self.buttons[i][b].setFont(self.font)	
			# Make the titles look nice
			self.titles[i].setStyleSheet("color:rgb(189, 195, 199);")
			self.font.setPointSize(18)
			self.titles[i].setFont(self.font)
			self.font.setPointSize(12)
			# Get the title of the device
			self.titles[i].setText(self.devices[i].getFrame().getTitle())
			self.titles[i].setGeometry(QtCore.QRect(10,10,self.titles[i]
				.fontMetrics().boundingRect(self.titles[i]
					.text()).width(),40))
			for y in range(0, len(self.devices[i].getFrame().getNicknames())):
				# Add a new parameter to the current device
				self.parameters[i].append(QtGui.QLabel(self.frames[i]))
				self.units[i].append(QtGui.QLabel(self.frames[i]))
				#Get the width of the text
				self.parameters[i][y].setFont(self.font)
				self.parameters[i][y].setAlignment(QtCore.Qt.AlignLeft)
				self.units[i][y].setFont(self.font)
				self.units[i][y].setAlignment(QtCore.Qt.AlignRight)
				# Configure the QLCDnumber widgets that display information
				self.lcds[i].append(QtGui.QLCDNumber())
				self.lcds[i][y].setNumDigits(11)
				self.lcds[i][y].setSegmentStyle(QtGui.QLCDNumber.Outline)
				self.lcds[i][y].display("-")
				self.lcds[i][y].setFrameShape(QtGui.QFrame.Panel)
				self.lcds[i][y].setFrameShadow(QtGui.QFrame.Plain)
				self.lcds[i][y].setLineWidth(self.ratio)
				self.lcds[i][y].setMidLineWidth(100)
				self.lcds[i][y].setStyleSheet("color:rgb(189, 195, 199);\n")
				self.lcds[i][y].setFixedHeight(self.scrnHeight/30)
				self.lcds[i][y].setMinimumWidth(self.scrnWidth/7)

				# Make the parameters pretty
				self.parameters[i][y].setWordWrap(True)
				self.parameters[i][y].setStyleSheet(
					"color:rgb(189, 195, 199);")	
				# Hide everything until we know that it should be displayed.
				# This is essential to be able to handle arrays
				self.parameters[i][y].hide()
				self.lcds[i][y].hide()
				self.units[i][y].hide()
				# If a nickname for the setting has been defined, 
				# go ahead and display whatever is necessary
				if(self.devices[i].getFrame().getNicknames()[y] is not None):
					self.parameters[i][y].show()
					self.lcds[i][y].show()
					self.units[i][y].show()
					self.parameters[i][y].setText(devices[i].getFrame()
						.getNicknames()[y])
					self.grids[i].addWidget(self.parameters[i][y], y+2, 0)
					lcdHBoxLayout = QtGui.QHBoxLayout()
					lcdHBoxLayout.addStretch(1)
					lcdHBoxLayout.addWidget(self.lcds[i][y])
					
					self.grids[i].addLayout(lcdHBoxLayout, y+2, 1)
					self.grids[i].addWidget(self.units[i][y], y+2, 2)
			# Configure the plots
			if (self.devices[i].getFrame().getPlot()):
				self.main_widget = self.frames[i]
				dc = MGrapher.mGraph(self.devices[i])
				yPos = len(self.devices[i].getFrame().getNicknames())+3
				self.grids[i].addWidget(dc, yPos, 0,yPos,3 )
				
		self.mainVBox[0].addStretch(0)
		self.mainVBox[1].addStretch(0)
		print("Gui initialized")
		return
	def openNotifierSettings(self):
		# Start the notifier gui
		# NOTE, this is run on the main thread, so while it is open the main
		# GUI will not be running.
		self.NotifierGUI = NotifierGUI(self.devices)
		self.NotifierGUI.exec_()
		#print "The mins received were", (self.NotifierGUI.getMins())
		# Start the messenger service
		try:
			self.MAlert.stop()
		except:
			print("Starting MAlert for first time")
		self.MAlert = MAlert.MAlert(self.NotifierGUI.getCheckboxes(),
											self.NotifierGUI.getMins(),
											self.NotifierGUI.getMaxs(),
											self.NotifierGUI.getContacts(),
											self.devices,
											self.tele)
	def startGui(self, devices, title, dataTitle, tele):
		'''Start the GUI'''
		# Used as the name of the dataChest data title
		self.dataTitle = dataTitle
		# Start the notifier
		self.tele = tele
		self.devices = devices
		self.NotifierGUI = NotifierGUI(self.devices)
		self.MAlert = MAlert.MAlert(self.NotifierGUI.getCheckboxes(),
											self.NotifierGUI.getMins(),
											self.NotifierGUI.getMaxs(),
											self.NotifierGUI.getContacts(),
											self.devices,
											self.tele)
		screen_resolution = QtGui.QDesktopWidget().screenGeometry()
		self.scrnWidth = screen_resolution.width()
		self.scrnHeight = screen_resolution.height()
		# Call the class's init function
		self.initGui(devices)
		self.setWindowTitle(title)
		# Show the gui
		self.show()
		timer = QtCore.QTimer(self)
		# Update the gui every so often. This CAN ONLY be done 
		# in the main thread.
		timer.timeout.connect(self.update)
		timer.start(100)
		self.MAlert.begin()
		sys.exit(app.exec_())

	def update(self):
		'''Update the GUI'''
		readings = []
		error = False
		# loop through all devices
		for i in range(0, len(self.devices)):
			# If there is no error with the device
			if(not self.devices[i].getFrame().isError()):
				# Get the readings from the frame
				readings = self.devices[i].getFrame().getReadings();
				if(readings is not None):
					# Holds an array containing the new data for use 
					# when adding data to the current dataset
					newData = []
					# Update all QLcds with the reading
					for y in range(0, len(self.devices[i].getFrame().getNicknames())):
						self.lcds[i][y].setSegmentStyle(
							QtGui.QLCDNumber.Flat)
						z = self.devices[i].getFrame().getReadingIndices()
						try:
							if(not math.isnan(readings[z[y]])):
								self.lcds[i][y].display(readings[z[y]])
							else:
								self.lcds[i][y].display("-")
						except TypeError:
							pass
						# If there are units, put them next to the number
						if(len(self.devices[i].getFrame().getUnits())>0):
							self.units[i][y].setText(self.devices[i]
								.getFrame().getUnits()[y])
							self.font.setPointSize(18)
							self.units[i][y].setFont(self.font)
							self.font.setPointSize(12)
							self.units[i][y].setStyleSheet(
								"color:rgb(189, 195, 199);")
			else:
				# Otherwise if there is an error, show that on 
				# the gui through outlined lcd numbers
				for y in range(0, len(self.lcds[i])):
					self.lcds[i][y].setSegmentStyle(QtGui
						.QLCDNumber.Outline)
					self.lcds[i][y].display("-")
		return
			


app=QtGui.QApplication(sys.argv)


