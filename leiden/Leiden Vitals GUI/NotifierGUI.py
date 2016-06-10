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
name = NotifierGUI
version = 1.0.1
description = Allows user to enter data about when to notify

### END NODE INFO
"""
from PyQt4 import QtCore, QtGui
import sys
import pickle

class NotifierGUI(QtGui.QDialog):
	def __init__(self,devices, parent = None):
		super(NotifierGUI, self).__init__(parent)
		tabWidget = QtGui.QTabWidget()
		self.smsTab = SMSTab(devices)
		tabWidget.addTab(self.smsTab, "SMS Alerts")
		mainLayout = QtGui.QVBoxLayout()
		mainLayout.addWidget(tabWidget)
		self.setLayout(mainLayout)
		buttonLayout = QtGui.QHBoxLayout()
		mainLayout.addLayout(buttonLayout)
		okButton = QtGui.QPushButton(self)
		okButton.setText("Ok")
		cancelButton = QtGui.QPushButton(self)
		cancelButton.setText("Cancel")
		buttonLayout.addWidget(okButton)
		buttonLayout.addWidget(cancelButton)
		
		okButton.clicked.connect(self.saveData)
		cancelButton.clicked.connect(self.close)
	def saveData(self):
		print("Saving Data")
		allData = []
		txtmins = []
		txtmaxs = []
		txtcontacts = []
		for i in range(0, len(self.smsTab.mins)):
			txtmins.append(str(self.smsTab.mins[i].text()))
			#allData = [self.smsTab.mins,self.smsTab. maxs,self.smsTab.contacts]
			txtmaxs.append(str(self.smsTab.maxs[i].text()))
			txtcontacts.append(str(self.smsTab.contacts[i].text()))

		allData.append(txtmins)
		allData.append(txtmaxs)
		allData.append(txtcontacts)
		print(txtmins)

		pickle.dump(allData, open("NotifierConfig.p", "wb"))
		self.close()

class SMSTab(QtGui.QWidget):
	def __init__(self,devices, parent = None):
		super(SMSTab, self).__init__(parent)
		self.devices = devices
		layout = QtGui.QGridLayout()

		self.setLayout(layout)
		self.mins = []
		self.maxs = []
		self.contacts = []
		
		self.openData()
		
		font = QtGui.QFont()
		font.setPointSize(14)
		
		minlbl = QtGui.QLabel()
		minlbl.setText("Minimum")
		layout.addWidget(minlbl, 1,1)
		
		maxlbl = QtGui.QLabel()
		maxlbl.setText("Maximum")
		layout.addWidget(maxlbl, 1,2)
		
		cnctlbl = QtGui.QLabel()
		cnctlbl.setText("Contact")
		layout.addWidget(cnctlbl, 1,3)
		z = 1
		x = 0
		for i in range(1, len(devices)+1):
			j = i-1
			label = QtGui.QLabel()
			label.setText(self.devices[j].getFrame().getTitle())
			label.setFont(font)
			layout.addWidget(label, z, 0)
			z=z+1
			
			for y in range(1, len(self.devices[j].getFrame().getNicknames())+1):
				paramName = self.devices[j].getFrame().getNicknames()[y-1]
				if(paramName is not None):
					if(len(self.allDatatxt[0])>x):
						self.mins.append(QtGui.QLineEdit())
						self.mins[x].setText(self.allDatatxt[0][x])
					else:
						self.maxs.append(QtGui.QLineEdit())
					if(len(self.allDatatxt[1])>x):
						self.maxs.append(QtGui.QLineEdit())
						self.maxs[x].setText(self.allDatatxt[1][x])
					else:
						self.contacts .append(QtGui.QLineEdit())
					if(len(self.allDatatxt[2])>x):
						self.contacts .append(QtGui.QLineEdit())
						self.contacts [x].setText(self.allDatatxt[2][x])
					else:
						self.mins.append(QtGui.QLineEdit())
					self.maxs.append(QtGui.QLineEdit())
					self.contacts.append(QtGui.QLineEdit())
					label = QtGui.QLabel()
					
					label.setText(paramName)
					layout.addWidget(label, z, 0)
					layout.addWidget(self.mins[x], z, 1)
					layout.addWidget(self.maxs[x],z, 2)
					layout.addWidget(self.contacts[x],z, 3)
					z = z+1
					x = x+1
	
	def openData(self):
		try:
			self.allDatatxt = pickle.load(open('NotifierConfig.p', 'rb'))
			#print "mins: ", self.allDatatxt
		except:
			self.allDatatxt = [[],[],[]]
			print("No config file found")
# if __name__ == '__main__':
	# app = QtGui.QApplication(sys.argv)
	# # dialog = NotifierGUI()
	
	# sys.exit(dialog.exec_())