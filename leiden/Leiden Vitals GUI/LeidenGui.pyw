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
import sys
import time
import traceback
# Libraries needed to run GUI.
from LeidenGuiConfig import *
from PyQt4 import QtCore, QtGui
# Libraries needed to use labRad.
import labrad
from labrad.units import WithUnit
import labrad.units as units
# Libraries needed to use multithreading.
from multiprocessing.pool import ThreadPool
import threading
from Queue import Queue

try:
	    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
	   return s

# The below command is for reference only. It is run to convert QT designer files to .pyc files.
#pyuic4 C:\Users\Noah\Documents\College\GuiProjects\Compressor_1\compressorGui.ui -o C:\Users\Noah\Documents\College\GuiProjects\Compressor_1\compressorGui.py
class MyForm(QtGui.QDialog):
	# The following boolean variables keep track of what is currently connected.
	isLabRad = False
	isFlowMeter = False 
	isTemperatureMeter = False
	isCompressor = False
	isVacuumMonitor = False
	isAllConnected = False
	#The following keep track of whether or not there is a new connection.
	newLabRadConnection = True
	newTemperatureConnection = True
	newFlowConnection = True
	newVacuumConnection = True
	# The following variables store references to their respective servers.
	temperatureMonitor = None
	compressor = None
	flowMeter = None
	pressureMonitor = None
	# The following variables represent the multiple threads used to communicate serially
	# with the devices/
	pressureThread = None
	flowMeterThread = None
	extTemperatureThread = None
	# cxn holds the labRad connection.
	cxn = None
	# Holds the compressor
	compressorIsRunning = False
	#timer = None
	t1 = 0;
   
	def __init__(self, parent = None):
		'''Initialize all necessary variables and components.'''
		# Configure GUI
		QtGui.QWidget.__init__(self, parent)
		self.ui = Ui_Dialog()
		self.ui.setupUi(self)
		# Configure the periodic call to the update function every second
		timer = QtCore.QTimer(self)
		timer.timeout.connect(self.update)
		timer.start(1000)
		# Configure the pushbutton event handler.
		self.compButton = self.ui.inputCompOnOff
		self.compButton.clicked.connect(self.compButtonClicked)
		
		# Attempt connection to all devices.
		if(self.attemptConnection()):
			self.ui.dataStatus.setText("All servers connected")
		else:
			self.ui.dataStatus.setText("Error: One or more servers is not connected.")
		# Check to see which servers are currently connected, and create threads
		# that will run in the backround and communicate with the devices.
		# Threading is necessary because serial communication is slow and if
		# we synchronously execute all steps needed to communicate, the GUI becomes very slow.
		# A queue ADT is used as a via between the background processes and the forground
		# (GUI).
		if(self.isVacuumMonitor):
			self.q = Queue()
			self.pressureThread = threading.Thread(target = self.getPressures, args=[self.q])
			self.pressureThread.start()
		if(self.isFlowMeter):
			self.flowq = Queue()
			self.flowMeterThread = threading.Thread(target = self.getFlowRate, args=[self.flowq])
			self.flowMeterThread.start()
		if(self.isTemperatureMeter):
			self.temperatureq = Queue()
			self.extTemperatureThread = threading.Thread(target = self.getExtWaterTemperature, args=[self.temperatureq])
			self.extTemperatureThread.start()
 
  
	def update(self):
			# Update the digital clock on the GUI with the correct time.
			self.ui.datatime.setText(time.ctime(time.time()))
			# Attempt to connect to any servers that are not connected.
			
			if(self.attemptConnection()):
				self.ui.dataStatus.setText("All servers connected")
			# If there is a flowMeter server connected
			if(self.isFlowMeter):
				# And if its background task is finished communicating with the device.
				try:
					if(not self.flowMeterThread.isAlive()):
						flowRate = self.flowq.get()
						self.flowMeterThread = threading.Thread(target = self.getFlowRate, args=[self.flowq])
						self.flowMeterThread.start()
						self.ui.dataCompFlowRate.display(flowRate._value)
						self.ui.labelCompUnitFlowRate_1.setText(flowRate.units)
						self.ui.dataCompFlowRate.setSegmentStyle(Qt.QLCDNumber.Flat)
				except:
					print("Problem with Omega Flow Monitor server. Will try to reconnect.")
					self.ui.dataStatus.setText("Problem with Temperature Monitor")
					self.isFlowMeter = False
					self.ui.dataCompFlowRate.setSegmentStyle(QTGui.QLCDNumber.Outline)
			else:
				self.ui.dataCompFlowRate.setSegmentStyle(QtGui.QLCDNumber.Outline)
			# If a temperature meter server is connected
			if(self.isTemperatureMeter):
				# A try-catch clause because there are many potential things that could fail
				# when communicating.
				try:
					# If the background task that communicates with the device is finished
					if(not self.extTemperatureThread.isAlive()):
						# Retrieve the temperature off the end of the Queue (put there by the 
						# getExtWaterTemperature()) function that was running in the background.
						temperature = self.temperatureq.get()
						# Threads cannot be restarted, we must create a brand new one.
						self.extTemperatureThread = threading.Thread(target = self.getExtWaterTemperature, args=[self.temperatureq])
						# Start the new thread
						self.extTemperatureThread.start()
						# Get the value of the returned temperature
						self.ui.dataCompExtTemp.display(temperature._value)
						# Get the units of the returned temperature
						self.ui.labelCompUnitExtTemp_1.setText(temperature.units)
						self.ui.dataCompExtTemp.setSegmentStyle(QtGui.QLCDNumber.Flat)
				except:
					print("Problem with Omega Temperature server. Will try to reconnect.")
					self.ui.dataStatus.setText("Problem with Temperature Monitor")
					self.isTemperatureMeter = False
					self.ui.dataCompExtTemp.setSegmentStyle(QtGui.QLCDNumber.Outline)
			else:
				self.ui.dataCompExtTemp.setSegmentStyle(QtGui.QLCDNumber.Outline)

			if(self.isVacuumMonitor):
				# A try-catch clause because there are many potential things that could fail
				# when communicating.
				try:
					# If the background task that communicates with the device is finished
					if(not self.pressureThread.isAlive()):
						pressures = self.q.get()
						self.pressureThread = threading.Thread(target = self.getPressures, args=[self.q])
						self.pressureThread.start()
						self.ui.dataPresPresOVC.display(pressures[3]._value)
						self.ui.labelPresUnits_1.setText(pressures.units)
						self.ui.dataPresPresIVC.display(pressures[4]._value)
						self.ui.labelPresUnits_2.setText(pressures.units)
						self.ui.dataPresStillPress.display(pressures[5]._value)
						self.ui.labelPresUnits_3.setText(pressures.units)
						self.ui.dataPresPresOVC.setSegmentStyle(QtGui.QLCDNumber.Flat)
						self.ui.dataPresPresIVC.setSegmentStyle(QtGui.QLCDNumber.Flat)
						self.ui.dataPresStillPress.setSegmentStyle(QtGui.QLCDNumber.Flat)
				except:
					print("Problem with Pfeiffer MaxiGauge Server. Will try to reconnect.")
					self.ui.dataStatus.setText("Problem with Pfeiffer MaxiGauge")
					self.isVacuumMonitor = False
					self.ui.dataPresPresOVC.setSegmentStyle(QtGui.QLCDNumber.Outline)
					self.ui.dataPresPresIVC.setSegmentStyle(QtGui.QLCDNumber.Outline)
					self.ui.dataPresStillPress.setSegmentStyle(QtGui.QLCDNumber.Outline)
			else:
				self.ui.dataPresPresOVC.setSegmentStyle(QtGui.QLCDNumber.Outline)
				self.ui.dataPresPresIVC.setSegmentStyle(QtGui.QLCDNumber.Outline)
				self.ui.dataPresStillPress.setSegmentStyle(QtGui.QLCDNumber.Outline)
			


	def attemptConnection(self):
		if(not self.isLabRad):
			self.connectToLabrad()
			if(self.isLabRad):
				print("Found Labrad, connected.")
			elif(not self.newLabRadConnection is self.isLabRad):
				print("Could not connect to Labrad, "
				"Labrad may not be running.")
				
		if(not self.isFlowMeter):
			self.connectToOmegaFlowMeter()
			if(self.isFlowMeter):
				self.flowq = Queue()
				self.flowMeterThread = threading.Thread(target = self.getFlowRate, args=[self.flowq])
				self.flowMeterThread.start()
				print("Found Omega Flow Monitor, connected.")
			elif(not self.newFlowConnection is self.isFlowMeter):
				print("Cound not connect to Omega Flow Meter, "
				"server might not be running.")
				self.newFlowConnection = self.isFlowMeter
				
		if(not self.isTemperatureMeter):
			self.connectToOmegaTemperatureMonitor()
			if(self.isTemperatureMeter):
				self.temperatureq = Queue()
				self.extTemperatureThread = threading.Thread(target = self.getExtWaterTemperature, args=[self.temperatureq])
				self.extTemperatureThread.start()
				print("Found Omega Temperature Monitor, connected.")
			elif (not self.newTemperatureConnection is self.isTemperatureMeter):
				print("Could not connect to Omega Temperature Meter, "
				"server might not be running.")
				self.newTemperatureConnection = self.isTemperatureMeter
			
		if(not self.isVacuumMonitor):
			self.connectToPressureMonitor()
			if(self.isVacuumMonitor):
				self.q = Queue()
				self.pressureThread = threading.Thread(target = self.getPressures, args=[self.q])
				self.pressureThread.start()
				print("Found Pfeiffer MaxiGauge, connected.")
			elif (not self.newVacuumConnection is self.isVacuumMonitor):
				print("Could not connect to Pfeiffer MaxiGauge, "
				"server might not be running.")
				self.newVacuumConnection = self.isVacuumMonitor
			
		if(self.isVacuumMonitor and self.isTemperatureMeter and self.isFlowMeter and self.isLabRad):
			self.isAllConnected = True
		else:
			self.isAllConnected = False
		return self.isAllConnected
		
	def connectToLabrad(self):
		try:
			self.cxn = labrad.connect()
			self.isLabRad = True
		except:
			self.ui.dataStatus.setText("Found LabRad")
			self.isLabRad = False
			
		
	def connectToOmegaFlowMeter(self):
		try:
			self.flowMeter = self.cxn.omega_ratemeter_server
			self.flowMeter.select_device(0)
			self.isFlowMeter = True
			self.ui.dataStatus.setText("Found Omega Flow Monitor")
		except:
			self.isFlowMeter = False
			
	def getFlowRate(self, queue):
		try:
			flowRate = self.flowMeter.get_rate()
			queue.put(flowRate)
			return(flowRate)
		except:
			self.isFlowMeter = False
			return
		
	def connectToOmegaTemperatureMonitor(self):
		try:
			self.temperatureMonitor = self.cxn.omega_temp_monitor_server
			self.temperatureMonitor.select_device(0)
			self.isTemperatureMeter = True
			self.ui.dataStatus.setText("Found Omega Temperature Monitor")
		except:
			self.isTemperatureMeter = False
			return
			
	def getExtWaterTemperature(self, queue):
		try:
			temperature = self.temperatureMonitor.get_temperature()
			queue.put(temperature)
			return(temperature)
		except:
			self.isTemperatureMeter = False
			return
			
	def connectToPressureMonitor(self):
		try:
			self.pressureMonitor = self.cxn.pfeiffer_vacuum_maxigauge
			self.pressureMonitor.select_device(0)
			self.isVacuumMonitor = True
			self.ui.dataStatus.setText("Found Pfeiffer MaxiGauge")
		except:
			self.isVacuumMonitor = False
			return
			
	def getPressures(self, queue):
		try:
			pressures = self.pressureMonitor.get_pressures()
			queue.put(pressures)
			return(pressures)
		except:
			self.isVacuumMonitor=False
			return
		
	def compButtonClicked(self):
		if(self.compressorIsRunning):
			self.dialog = PopUp("Warning: you are about to turn off the compressor.")
			self.dialog.exec_()
			if(self.dialog.consent is True):
				print("Compressor Shutting Down")
				self.compressorIsRunning = False;
				self.compButton.setText("Turn On")
				self.compButton.setStyleSheet("background-color: maroon")
			if(self.dialog.consent is False):
				print("canceled.")
		else:
			self.dialog = PopUp("Warning: you are about to turn on the compressor.")
			self.dialog.exec_()
			if(self.dialog.consent is True):
				print("Starting Compressor")
				self.compressorIsRunning = True;
				self.compButton.setText("Turn Off")
				self.compButton.setStyleSheet("background-color: green")
			if(self.dialog.consent is False):
				print("canceled.")	

class PopUp(QtGui.QDialog):
	consent = None
	def __init__(self, message, parent=None):
		self.msg = message
		QtGui.QWidget.__init__(self, parent)
		self.ui = Ui_Dialog()
		self.setupUi(self)
		
	def setupUi(self, Dialog):
		Dialog.setObjectName("Warning")
		Dialog.resize(500,400)
		Dialog.setStyleSheet(_fromUtf8("background: rgb(52, 73, 94)"))
		
		self.warning = QtGui.QLabel(Dialog)
		self.warning.setText(self.msg)
		
		font = QtGui.QFont()
		font.setPointSize(12)
		font.setBold(False)
		font.setWeight(50)
		font.setKerning(True)
		
		self.warning.setWordWrap(True)
		self.warning.setAlignment(QtCore.Qt.AlignCenter)
		self.warning.setStyleSheet(_fromUtf8("color:rgb(189, 195, 199);"))
		self.warning.setFont(font)
		
		self.okButton = QtGui.QPushButton(Dialog)
		self.okButton.setStyleSheet(_fromUtf8("color:rgb(189, 195, 199); background: rgb(52, 73, 94)\n"))
		self.okButton.setGeometry(QtCore.QRect(20, 330, 191, 61))
		self.okButton.setText("Ok")
		self.okButton.setStyleSheet("background-color: green")
		self.okButton.setFont(font)
		self.okButton.clicked.connect(self.okClicked)

		self.cancelButton = QtGui.QPushButton(Dialog)
		self.cancelButton.setStyleSheet(_fromUtf8("color:rgb(189, 195, 199); background: rgb(52, 73, 94)\n"))
		self.cancelButton.setGeometry(QtCore.QRect(290, 330, 191, 61))
		self.cancelButton.setText("Cancel")
		self.cancelButton.setStyleSheet("background-color: maroon")
		self.cancelButton.setFont(font)
		self.cancelButton.clicked.connect(self.cancelClicked)
		
	def okClicked(self):
		self.consent = True
		self.close()
	def cancelClicked(self):
		self.consent = False
		self.close()

		
if __name__ == "__main__":
	app=QtGui.QApplication(sys.argv)
	myapp = MyForm()
	myapp.show()
	sys.exit(app.exec_())