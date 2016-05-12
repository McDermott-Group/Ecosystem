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
class NGui(QtGui.QDialog):

	dialog = None
	parameters = [[]]
	frames = []
	grids = []
	devices = None
	mainVBox = QtGui.QVBoxLayout()
	mainHBox = QtGui.QHBoxLayout()
	titles = []
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
		
		#self.resize(800,400)
		self.setStyleSheet("background:rgb(70, 80, 88)")
		
		
		self.devices = devices
		yPos = 5;
		
		self.setLayout(self.mainHBox)
		self.mainHBox.addLayout(self.mainVBox)
		#self.mainHBox.addStretch(1)
		# For each device, add a GUI frame for it.
		for i in range(0,len(self.devices)):
		
			#Append a new gui frame
			self.frames.append(QtGui.QFrame(self))
			#self.frames[i].setGeometry(QtCore.QRect(10, yPos, 300, 70+60*len(devices[i].getFrame().getNicknames())))
			self.mainVBox.addWidget(self.frames[i])
			# Add new titles, grids, parameters, and lcds for the new parameter
			self.titles.append(QtGui.QLabel(self.frames[i]))
			self.grids.append(QtGui.QGridLayout())
			self.parameters.append([])
			self.lcds.append([])
			self.units.append([])
			self.buttons.append([])
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
			
			buttonLayout = QtGui.QHBoxLayout()
			self.grids[i].addLayout(buttonLayout, 1, 1)
			print(self.devices[i].getFrame().getButtons())
			if(len(self.devices[i].getFrame().getButtons()[0])>0):
				for b in range(0, len(self.devices[i].getFrame().getButtons())):
					self.buttons[i].append(QtGui.QPushButton(self.frames[i]))
					self.buttons[i][b].setText(self.devices[i].getFrame().getButtons()[b][0])
					#ctypes.cast(ctypes.addressof(e), ctypes.POINTER(ctypes.c_int)).contents.value
					print()
					#self.buttons[i][b].setText(str(b))
					buttonLayout.addWidget(self.buttons[i][b])
					
					#self.buttons[i][b].clicked.connect(partial(self.buttonClicked, [b, i]))
					self.buttons[i][b].clicked.connect(partial(self.devices[i].prompt, b))
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
			
			for y in range(0, len(self.devices[i].getFrame().getNicknames())):
				# Add a new parameter to the current device
				self.parameters[i].append(QtGui.QLabel(self.frames[i]))
				self.units[i].append(QtGui.QLabel(self.frames[i]))
				self.parameters[i][y].setText(devices[i].getFrame().getNicknames()[y])
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
				self.parameters[i][y].setWordWrap(True)
				
				self.parameters[i][y].setStyleSheet("color:rgb(189, 195, 199);")
				#self.devices[i].getUnits[y]
				self.grids[i].addWidget(self.parameters[i][y], y+2, 0)
				self.grids[i].addWidget(self.lcds[i][y], y+2, 1)
				self.grids[i].addWidget(self.units[i][y], y+2, 2)
				
		print("Gui initialized")
		return
	def startGui(self, devices):
		self.initGui(devices)
		self.show()
		timer = QtCore.QTimer(self)
		timer.timeout.connect(self.update)
		timer.start(1000)
		sys.exit(app.exec_())
	def buttonClicked(self, buttonNum, i):
		self.devices[i].getFrame().buttonPressed(i)
		print("button "+str(index)+" was clicked")
		
	def update(self):
		readings = [];
		error = False;
		for i in range(0, len(self.devices)):

			if(not self.devices[i].getFrame().isError()):
				readings = self.devices[i].getFrame().getReadings();
				for y in range(0, len(readings)):
					self.lcds[i][y].setSegmentStyle(QtGui.QLCDNumber.Flat)
					self.lcds[i][y].display(readings[y])
					#print(len(self.devices[i].getFrame().getUnits()))
					if(len(self.devices[i].getFrame().getUnits())>0):
						#print(y)
						self.units[i][y].setText(self.devices[i].getFrame().getUnits()[y])
						self.font.setPointSize(18)
						self.units[i][y].setFont(self.font)
						self.font.setPointSize(12)
						self.units[i][y].setStyleSheet("color:rgb(189, 195, 199);")
				#print(self.devices[i].getFrame().errorMsg())
			else:
				for y in range(0, len(self.lcds[i])):
					self.lcds[i][y].setSegmentStyle(QtGui.QLCDNumber.Outline)
				
		return
			

app=QtGui.QApplication(sys.argv)

