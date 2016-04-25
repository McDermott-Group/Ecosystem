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
name = Leiden Vitals Gui
version = 1.0.8
description = Monitors Leiden Devices

### END NODE INFO
"""
# Libraries necessary for basic operation
import sys
import time
# Libraries needed to run GUI.
from LeidenGuiConfig import *
from PyQt4 import QtCore, QtGui
# Libraries needed to use labRad.
import labrad
import labrad.units as units
from labrad.units import WithUnit
# Libraries needed to use multithreading.
from multiprocessing.pool import ThreadPool
from Queue import Queue
import threading
# Import UTF8 encoding
try:
	    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
	   return s

# The below command is for reference only, please do not remove it. It is run to convert QT designer files to .pyc files.
# pyuic4 C:\Users\Noah\Documents\College\GuiProjects\Compressor_1\compressorGui.ui -o C:\Users\Noah\Documents\College\GuiProjects\Compressor_1\compressorGui.py

# The class for the main GUI page
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
	# The following variables represent the threads used to communicate serially
	# with the devices.
	pressureThread = None
	flowMeterThread = None
	extTemperatureThread = None
	# cxn holds the labRad connection.
	cxn = None
	# Holds the compressor state
	compressorIsRunning = False
   
	def __init__(self, parent = None):
		'''Initialize all necessary variables and components.'''
		# Initialize GUI
		QtGui.QWidget.__init__(self, parent)
		self.ui = Ui_Dialog()
		self.ui.setupUi(self)
		# Configure the periodic call to the update() function every second
		timer = QtCore.QTimer(self)
		timer.timeout.connect(self.update)
		timer.start(1000)
		# Configure the pushbutton event handler.
		self.compButton = self.ui.inputCompOnOff
		self.compButton.clicked.connect(self.compButtonClicked)
		# Attempt to connect to all devices.
		if(self.attemptConnection()):
			self.ui.dataStatus.setText("All servers connected")
		else:
			self.ui.dataStatus.setText("Error: One or more servers is not connected.")
		# Check to see which servers are currently connected and create threads
		# that will run in the backround and communicate with the devices.
		# Threading is necessary because serial communication is slow and if
		# we synchronously execute all steps needed to communicate, the GUI becomes very slow.
		# A queue ADT is used as a via between the background processes and the forground
		# (GUI).
		if(self.isVacuumMonitor):
			self.vacq = Queue()
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
				try:
					# And if its background task is finished communicating with the device.
					if(not self.flowMeterThread.isAlive()):
						# Get the reading out of the Queue
						flowRate = self.flowq.get()
						# Recreate the thread. Threads cannot be 'restarted,' they must be created again.
						self.flowMeterThread = threading.Thread(target = self.getFlowRate, args=[self.flowq])
						# Run the thread.
						self.flowMeterThread.start()
						# Display the reading in the GUI.
						self.ui.dataCompFlowRate.display(flowRate._value)
						# Update the GUI's units with the ones supplied with the reading.
						self.ui.labelCompUnitFlowRate_1.setText(flowRate.units)
						# A flat setment style denotes the correct operation of the device and a correct reading.
						self.ui.dataCompFlowRate.setSegmentStyle(Qt.QLCDNumber.Flat)
				except:
					# If there were any problems, handle them.
					print("Problem with Omega Flow Monitor server. Will try to reconnect.")
					# Set the GUI status. 
					self.ui.dataStatus.setText("Problem with Temperature Monitor")
					# The flow meter has an issue, setting isFlowMeter to false will tell the program to try to reconnect.
					self.isFlowMeter = False
					# A segment style of Outline denotes a malfunctioning server and a reading that may not be accurate.
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
						# A flat setment style denotes the correct operation of the device and a correct reading.
						self.ui.dataCompExtTemp.setSegmentStyle(QtGui.QLCDNumber.Flat)
				except:
					# If there were any problems, handle them.
					print("Problem with Omega Temperature server. Will try to reconnect.")
					# Set the GUI status. 
					self.ui.dataStatus.setText("Problem with Temperature Monitor")
					# The flow meter has an issue, setting isFlowMeter to false will tell the program to try to reconnect.
					self.isTemperatureMeter = False
					# A segment style of Outline denotes a malfunctioning server and a reading that may not be accurate.
					self.ui.dataCompExtTemp.setSegmentStyle(QtGui.QLCDNumber.Outline)
			else:
				self.ui.dataCompExtTemp.setSegmentStyle(QtGui.QLCDNumber.Outline)

			# If the Pfeiffer Vacuum Monitor is connected.
			if(self.isVacuumMonitor):
				# A try-catch clause because there are many potential things that could fail
				# when communicating.
				try:
					# If the background task that communicates with the device is finished
					if(not self.pressureThread.isAlive()):
						# Retreive the list of pressures from the top of the list.
						pressures = self.vacq.get()
						# Create a new thread.
						self.pressureThread = threading.Thread(target = self.getPressures, args=[self.vacq])
						# Start the new thread.
						self.pressureThread.start()
						# The pressures come in an array. The first element is the OVC, the second is the IVC, the third is the Still pressure.
						self.ui.dataPresPresOVC.display(pressures[3]._value)
						self.ui.labelPresUnits_1.setText(pressures.units)
						self.ui.dataPresPresIVC.display(pressures[4]._value)
						self.ui.labelPresUnits_2.setText(pressures.units)
						self.ui.dataPresStillPress.display(pressures[5]._value)
						self.ui.labelPresUnits_3.setText(pressures.units)
						# Set the segment styles to flat, denoting that readings are accurate.
						self.ui.dataPresPresOVC.setSegmentStyle(QtGui.QLCDNumber.Flat)
						self.ui.dataPresPresIVC.setSegmentStyle(QtGui.QLCDNumber.Flat)
						self.ui.dataPresStillPress.setSegmentStyle(QtGui.QLCDNumber.Flat)
				except:
					# If there was a problem executing any of the above commands, handle them.
					# Print an error message.
					print("Problem with Pfeiffer MaxiGauge Server. Will try to reconnect.")
					# Show an error message in the status section of the GUI
					self.ui.dataStatus.setText("Problem with Pfeiffer MaxiGauge")
					# Tell the program that there is no vacuum monitor connected.
					self.isVacuumMonitor = False
					# Set the segment styles to outline.
					self.ui.dataPresPresOVC.setSegmentStyle(QtGui.QLCDNumber.Outline)
					self.ui.dataPresPresIVC.setSegmentStyle(QtGui.QLCDNumber.Outline)
					self.ui.dataPresStillPress.setSegmentStyle(QtGui.QLCDNumber.Outline)
			else:
				# If the vacuum monitor is not connected, set all segment styles to outline.
				self.ui.dataPresPresOVC.setSegmentStyle(QtGui.QLCDNumber.Outline)
				self.ui.dataPresPresIVC.setSegmentStyle(QtGui.QLCDNumber.Outline)
				self.ui.dataPresStillPress.setSegmentStyle(QtGui.QLCDNumber.Outline)
			
	def attemptConnection(self):
		'''Attempt to connect to all servers.'''
		# If there is no connection to labrad, try to reconnect.
		if(not self.isLabRad):
			# Try to connect.
			self.connectToLabrad()
			# If it's connected
			if(self.isLabRad):
				print("Found Labrad, connected.")
			#Otherwise, the newLabradConnection will not be equal to the current connection status.
			# This check is to ensure that the message only prints once, not everytime attemptConnection() is called.
			elif(not self.newLabRadConnection is self.isLabRad):
				print("Could not connect to Labrad, "
				"Labrad may not be running.")
				self.newLabRadConnection = self.isLabRad
		# If there is no connection to the flow meter, try to reconnect.
		if(not self.isFlowMeter):
			# Try to connect.
			self.connectToOmegaFlowMeter()
			# if there is now a flowmeter connected.
			if(self.isFlowMeter):
				# Start the thread. (Same way as explained earlier.)
				self.flowq = Queue()
				self.flowMeterThread = threading.Thread(target = self.getFlowRate, args=[self.flowq])
				self.flowMeterThread.start()
				print("Found Omega Flow Monitor, connected.")
			# If the flow meter has been disconnected for a while, do not re-print the error message.
			elif(not self.newFlowConnection is self.isFlowMeter):
				print("Cound not connect to Omega Flow Meter, "
				"server might not be running.")
				self.newFlowConnection = self.isFlowMeter
		# Exact same idea as above if clause.
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
		# Exact same idea as above if clause.
		if(not self.isVacuumMonitor):
			self.connectToPressureMonitor()
			if(self.isVacuumMonitor):
				self.vacq = Queue()
				self.pressureThread = threading.Thread(target = self.getPressures, args=[self.vacq])
				self.pressureThread.start()
				print("Found Pfeiffer MaxiGauge, connected.")
			elif (not self.newVacuumConnection is self.isVacuumMonitor):
				print("Could not connect to Pfeiffer MaxiGauge, "
				"server might not be running.")
				self.newVacuumConnection = self.isVacuumMonitor
		# If they are all connected.
		if(self.isVacuumMonitor and self.isTemperatureMeter and self.isFlowMeter and self.isLabRad):
			self.isAllConnected = True
		else:
			self.isAllConnected = False
		return self.isAllConnected
		
	def connectToLabrad(self):
		'''Connect to labrad.'''
		try:
			# Try to establis a connection with labrad.
			self.cxn = labrad.connect()
			# There is labrad, so isLabRad should be true.
			self.isLabRad = True
			self.ui.dataStatus.setText("Found LabRad")

		except:
			# If the connection fails, catch the error and handle it.
			self.ui.dataStatus.setText("Could not connect to LabRad, please run LabRad.")
			self.isLabRad = False
			
	def connectToOmegaFlowMeter(self):
		'''Connect to the Omega Flow Meter'''
		try:
			# The flowMeter variable should hold a reference to the flow meter.
			self.flowMeter = self.cxn.omega_ratemeter_server
			# Select the 0th device (as we always do)
			self.flowMeter.select_device(0)
			# There is a flow meter connected
			self.isFlowMeter = True
			# Let the user know that we found a flow meter.
			self.ui.dataStatus.setText("Found Omega Flow Monitor")
		except:
			# If anything above failed, we will try to reconnect later.
			self.isFlowMeter = False
			
	def getFlowRate(self, queue):
		'''Get the flow rate from the Omega Flow Meter.'''
		try:
			# Make a call the flow meter's setting that gets the flow rate.
			flowRate = self.flowMeter.get_rate()
			# Push the reading to the queue, it will be read later.
			queue.put(flowRate)
			# Return the flow rate. The return value is not used, but it is  there if we want it.
			return(flowRate)
		except:
			self.isFlowMeter = False
			return
		
	def connectToOmegaTemperatureMonitor(self):
		'''Connect to the Temperature monitor.'''
		# Same Idea a the connectToOmegaFlowMeter() method.
		try:
			self.temperatureMonitor = self.cxn.omega_temp_monitor_server
			self.temperatureMonitor.select_device(0)
			self.isTemperatureMeter = True
			self.ui.dataStatus.setText("Found Omega Temperature Monitor")
		except:
			self.isTemperatureMeter = False
			return
			
	def getExtWaterTemperature(self, queue):
		'''Get the external water temperature from the Omega Temperature Monitor'''
		# Exact same functionality as the getFlowRate() function.
		try:
			temperature = self.temperatureMonitor.get_temperature()
			queue.put(temperature)
			return(temperature)
		except:
			self.isTemperatureMeter = False
			return
			
	def connectToPressureMonitor(self):
		'''Connect to the Pfeiffer MaxiGauge server'''
		# Same idea as the connectToOmegaFlowMeter() method.
		try:
			self.pressureMonitor = self.cxn.pfeiffer_vacuum_maxigauge
			self.pressureMonitor.select_device(0)
			self.isVacuumMonitor = True
			self.ui.dataStatus.setText("Found Pfeiffer MaxiGauge")
		except:
			self.isVacuumMonitor = False
			return
			
	def getPressures(self, queue):
		'''Get the readings from the Pfeiffer MaxiGauge server'''
		# Same operation as the getFlowRate() method.
		try:
			pressures = self.pressureMonitor.get_pressures()
			queue.put(pressures)
			return(pressures)
		except:
			self.isVacuumMonitor=False
			return
		
	def compButtonClicked(self):
		'''Handle the button click event for the turn compressor on/off button'''
		# If the compressor is currently running, we want to turn it off.
		if(self.compressorIsRunning):
			# Create a popUp to warn the user that they are about to turn the compressor off.
			self.dialog = PopUp("Warning: you are about to turn off the compressor.")
			# The dialog.exec_() function runs the popup and does not let the user interact with the main window unil the popup is closed.
			self.dialog.exec_()
			# The popup's consent feild will be true iff the user clicks the 'OK' button. False otherwise.
			if(self.dialog.consent is True):
				print("Compressor Shutting Down")
				self.compressorIsRunning = False;
				# The button should now read "turn on"
				self.compButton.setText("Turn On")
				# Update the on-screen compressor status.
				self.ui.dataCompState.setText("Off")
				# The red background color of the button shows that the compressor is running.
				self.compButton.setStyleSheet("background-color: maroon")
			else:
				# Otherwise, if the user pressed the cancel button, do not do anything.
				print("canceled.")
		else:
			# Otherwise, if the compressor is currently off, warn the user that they are about to turn the compressor on.
			self.dialog = PopUp("Warning: you are about to turn on the compressor.")
			self.dialog.exec_()
			# if the user gives consent, turn it on.
			if(self.dialog.consent is True):
				print("Starting Compressor")
				self.compressorIsRunning = True;
				self.compButton.setText("Turn Off")
				# Update the on-screen compressor status.
				self.ui.dataCompState.setText("Running")
				# a background color of green denotes that the compressor is currently on.
				self.compButton.setStyleSheet("background-color: green")
			else:
				print("canceled.")	

class PopUp(QtGui.QDialog):
	'''Small class for a popup window'''
	consent = None
	def __init__(self, message, parent=None):
		'''Initialize the pop-up'''
		# The user gives a message to display.
		self.msg = message
		# Initialize the rest of the widget.
		QtGui.QWidget.__init__(self, parent)
		self.ui = Ui_Dialog()
		self.setupUi(self)
		
	def setupUi(self, Dialog):
		'''Configure the look and function of the pop up'''
		Dialog.setObjectName("Warning")
		Dialog.resize(500,400)
		Dialog.setStyleSheet(_fromUtf8("background: rgb(52, 73, 94)"))
		# Create a new label that will display the message.
		self.warning = QtGui.QLabel(Dialog)
		self.warning.setText(self.msg)
		# Configure a font to use.
		font = QtGui.QFont()
		font.setPointSize(12)
		font.setBold(False)
		font.setWeight(50)
		font.setKerning(True)
		# Apply the formatting to the message.
		self.warning.setWordWrap(True)
		self.warning.setAlignment(QtCore.Qt.AlignCenter)
		self.warning.setStyleSheet(_fromUtf8("color:rgb(189, 195, 199);"))
		self.warning.setFont(font)
		# Create an 'Ok' button at the bottom of the screen.
		self.okButton = QtGui.QPushButton(Dialog)
		self.okButton.setStyleSheet(_fromUtf8("color:rgb(189, 195, 199); background: rgb(52, 73, 94)\n"))
		self.okButton.setGeometry(QtCore.QRect(20, 330, 191, 61))
		self.okButton.setText("Ok")
		self.okButton.setStyleSheet("background-color: green")
		self.okButton.setFont(font)
		self.okButton.clicked.connect(self.okClicked)
		# Create a 'Cancel button' at the bottom of the screen.
		self.cancelButton = QtGui.QPushButton(Dialog)
		self.cancelButton.setStyleSheet(_fromUtf8("color:rgb(189, 195, 199); background: rgb(52, 73, 94)\n"))
		self.cancelButton.setGeometry(QtCore.QRect(290, 330, 191, 61))
		self.cancelButton.setText("Cancel")
		self.cancelButton.setStyleSheet("background-color: maroon")
		self.cancelButton.setFont(font)
		self.cancelButton.clicked.connect(self.cancelClicked)
		
	def okClicked(self):
		'''Called when the ok button is clicked'''
		# Clicking the ok button gives consent for whatever you are doing.
		self.consent = True
		# Close the popup
		self.close()
	def cancelClicked(self):
		'''Called when the cancel button is clicked.'''
		# The user has not given consent.
		self.consent = False
		# Close the popup.
		self.close()

if __name__ == "__main__":
	app=QtGui.QApplication(sys.argv)
	myapp = MyForm()
	myapp.show()
	sys.exit(app.exec_())