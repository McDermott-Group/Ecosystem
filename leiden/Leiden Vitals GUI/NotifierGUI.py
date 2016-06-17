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
# version = 1.0.5
# description = Allows user to configure notifications
"""

from PyQt4 import QtCore, QtGui
import sys
import pickle

class NotifierGUI(QtGui.QDialog):
	def __init__(self,devices, parent = None):
		'''Initialize the Notifier Gui'''
		super(NotifierGUI, self).__init__(parent)
		# Create a new tab
		tabWidget = QtGui.QTabWidget()
		# New SMS widget
		self.alert = AlertConfig(devices)
		# AlDatatxt holds the text contents of all data entered in table
		self.allDatatxt = [[],[],[],[]]
		# The settings window has a tab
		tabWidget.addTab(self.alert, "Alert Configuration")
		# Configure layouts
		mainLayout = QtGui.QVBoxLayout()
		mainLayout.addWidget(tabWidget)
		self.setLayout(mainLayout)
		buttonLayout = QtGui.QHBoxLayout()
		mainLayout.addLayout(buttonLayout)
		# Configure buttons
		okButton = QtGui.QPushButton(self)
		okButton.setText("Ok")
		cancelButton = QtGui.QPushButton(self)
		cancelButton.setText("Cancel")
		# Add buttons
		buttonLayout.addStretch(1)
		buttonLayout.addWidget(okButton)
		buttonLayout.addWidget(cancelButton)
		# Configure buttons
		okButton.clicked.connect(self.saveData)
		cancelButton.clicked.connect(self.close)
	def saveData(self):
		'''Save the data upon exit'''
		#print("Saving Data")
		# Arrays used to assist in storing data
		self.allDatatxt = []
		txtmins = []
		txtmaxs = []
		txtcontacts = []
		boolChecked = []
		# For all of the rows
		
		try:
			for i in range(0, len(self.alert.mins)):
				# Put the text in the textboxes in the arrays
				if(len(self.alert.mins[i].text()) is not 0):
					#print(i)
					#print()
					txtmins.append(str(float(self.alert.mins[i].text())))
				else:
					txtmins.append(self.alert.mins[i].text())
					
				if(len(self.alert.maxs[i].text()) is not 0):
					txtmaxs.append(str(float(self.alert.maxs[i].text())))
				else:
					txtmaxs.append(self.alert.maxs[i].text())
					
				if(len(txtmaxs[i]) is not 0 and len(txtmins[i]) is not 0):
				
					if(float(txtmaxs[i])<float(txtmins[i])):
						print("Error: min cannot be greater than max")
						raise
				txtcontacts.append(str(self.alert.contacts[i].text()))
				boolChecked.append(self.alert.checkBoxes[i].isChecked())
			print("Saving all data")
		
	
			# Combine all arrays
			self.allDatatxt.append(txtmins)
			self.allDatatxt.append(txtmaxs)
			self.allDatatxt.append(txtcontacts)
			self.allDatatxt.append(boolChecked)
			
			#print "just stored" ,(self.allDatatxt)
			# Pickle the arrays and store them
			pickle.dump(self.allDatatxt, open("NotifierConfig.nview", "wb"))
		except:
			print("Data not saved, make sure you enter numbers. ")
			# "Exponents can be written '4e5'.")
		# Close the window
		self.close()
	def getMins(self):
		return self.alert.openData()[0]
	def getMaxs(self):
		return self.alert.openData()[1]
	def getContacts(self):
		return self.alert.openData()[2]
	def getCheckboxes(self):
		return self.alert.openData()[3]
		
class AlertConfig(QtGui.QWidget):
	def __init__(self,devices, parent = None):
		super(AlertConfig, self).__init__(parent)
		self.devices = devices
		# Configure the layout
		layout = QtGui.QGridLayout()
		# Set the layout
		self.setLayout(layout)
		self.mins = []
		self.maxs = []
		self.contacts = []
		self.checkBoxes = []
		# Retreive the previous settings
		self.openData()
		# Set up font
		font = QtGui.QFont()
		font.setPointSize(14)
		# Labels for the columns
		enablelbl = QtGui.QLabel()
		enablelbl.setText("Enable")
		layout.addWidget(enablelbl, 1,2)

		minlbl = QtGui.QLabel()
		minlbl.setText("Minimum")
		layout.addWidget(minlbl, 1,3)
		
		maxlbl = QtGui.QLabel()
		maxlbl.setText("Maximum")
		layout.addWidget(maxlbl, 1,5)
		
		cnctlbl = QtGui.QLabel()
		cnctlbl.setText("Contact (Separate with comma, no space)")
		layout.addWidget(cnctlbl, 1,7)
		# These are indexing variables
		z = 1
		x = 0
		# Go through and add all of the devices and their parameters to the gui.
		for i in range(1, len(devices)+1):
			# j is also used for indexing
			j = i-1
			# Create the labels for all parameters
			label = QtGui.QLabel()
			label.setText(self.devices[j].getFrame().getTitle())
			label.setFont(font)
			layout.addWidget(label, z, 1)
			z=z+1
			# Create all of the information fields and put the saved data in
			# them.
			for y in range(1, len(self.devices[j].getFrame().getNicknames())+1):
				paramName = self.devices[j].getFrame().getNicknames()[y-1]
				if(paramName is not None):
					if(len(self.allDatatxt[3])>x):
						self.checkBoxes.append(QtGui.QCheckBox())
						self.checkBoxes[x].setChecked(self.allDatatxt[3][x])
					else:
						self.checkBoxes.append(QtGui.QCheckBox())
					if(len(self.allDatatxt[0])>x):
						self.mins.append(QtGui.QLineEdit())
						self.mins[x].setText(str(self.allDatatxt[0][x]))
					else:
						self.maxs.append(QtGui.QLineEdit())
					if(len(self.allDatatxt[1])>x):
						self.maxs.append(QtGui.QLineEdit())
						self.maxs[x].setText(str(self.allDatatxt[1][x]))
					else:
						self.contacts .append(QtGui.QLineEdit())
					if(len(self.allDatatxt[2])>x):
						self.contacts .append(QtGui.QLineEdit())
						self.contacts [x].setText(str(self.allDatatxt[2][x]))
					else:
						self.mins.append(QtGui.QLineEdit())
					self.maxs.append(QtGui.QLineEdit())
					self.contacts.append(QtGui.QLineEdit())
					label = QtGui.QLabel()
					# Add the new widgets
					label.setText(paramName)
					layout.addWidget(label, z, 1)
					layout.addWidget(self.mins[x], z, 3)					
					layout.addWidget(self.maxs[x],z, 5)
					layout.addWidget(self.contacts[x],z, 7)
					layout.addWidget(self.checkBoxes[x],z, 2)
					
					if(len(self.devices[j].getFrame().getUnits())>(y-1)):
						unitLabel = QtGui.QLabel()
						unitLabel.setText(self.devices[j].getFrame()
							.getUnits()[y-1])
						layout.addWidget(unitLabel,z,4)
						unitLabel = QtGui.QLabel()
						unitLabel.setText(self.devices[j].getFrame()
							.getUnits()[y-1])
						layout.addWidget(unitLabel,z,6)
					# These are used for indexing
					z = z+1
					x = x+1
	
	def openData(self):
		'''Retreive a user's previous settings.'''
		#print("opening data")
		self.allDatatxt = pickle.load(open('NotifierConfig.nview', 'rb'))

		try:
			self.allDatatxt = pickle.load(open('NotifierConfig.nview', 'rb'))
			NotifierGUI.allDatatxt = self.allDatatxt
			#print "mins: ", self.allDatatxt
		except:
			self.allDatatxt = [[],[],[],[]]
			print("No config file found")
		return self.allDatatxt
	
# if __name__ == '__main__':
	# app = QtGui.QApplication(sys.argv)
	# # dialog = NotifierGUI()
	
	# sys.exit(dialog.exec_())
