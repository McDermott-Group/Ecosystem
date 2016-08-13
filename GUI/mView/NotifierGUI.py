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
import sys
sys.dont_write_bytecode = True
from PyQt4 import QtCore, QtGui
import inspect
import cPickle as pickle
import os
import inspect
import traceback 

class NotifierGUI(QtGui.QDialog):
    
    def __init__(self,devices, parent = None):
        '''Initialize the Notifier Gui'''
        super(NotifierGUI, self).__init__(parent)
        # Create a new tab
        tabWidget = QtGui.QTabWidget()
        # Get stack trace
        stack = inspect.stack()
        # The location to store config data
        #self.location = os.path.abspath(os.curdir)
        self.location = os.path.dirname(traceback.extract_stack()[0][0])
        
        print "Looking for config file in: ", self.location
        # New SMS widget
        self.alert = AlertConfig(devices, self.location)
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
        self.setWindowTitle("Notifier Settings")
        self.devices = devices
        # Get the location of the main class, and store the info there
        # print("  I was called by {}".format(str(location)))
    def saveData(self):
        '''Save the data upon exit'''
        # Arrays used to assist in storing data
        self.allDataDict = {}
        try:
            for device in self.devices:
                title = device.getFrame().getTitle()
                for nickname in device.getFrame().getNicknames():
                    if(nickname is not None):
                        key = title+":"+nickname
                        deviceDataArray = []
                        deviceDataArray.append(self.alert
                            .allWidgetDict[key][0].isChecked())
                        if len(self.alert.allWidgetDict[key][1].text()) is not 0:
                            deviceDataArray.append(float(self.alert
                                .allWidgetDict[key][1].text()))
                        else:
                            deviceDataArray.append('')
                        if len(self.alert.allWidgetDict[key][2].text()) is not 0:
                            deviceDataArray.append(float(self.alert
                                .allWidgetDict[key][2].text()))
                        else:
                            deviceDataArray.append('')
                        deviceDataArray.append(self.alert
                            .allWidgetDict[key][3].text())
                        if(deviceDataArray[1]>deviceDataArray[2]
                            and deviceDataArray[1] is not None
                            and deviceDataArray[2] is not None):
                            #print(deviceDataArray[1])
                            raise
                        self.allDataDict[title+":"+nickname] = deviceDataArray
                # Pickle the arrays and store them
                pickle.dump(self.allDataDict, open(
                    os.path.join(self.location, 'NotifierConfig.mview')
                    , 'wb'))
                #print("Data Saved")
        except ValueError:
            
            print("Enter only numbers into 'Minimum' and 'Maximum' fields.")
            print("Data Not Saved")
            
        except:
            #traceback.print_exc()
            print("Minimum values cannot be greater than maximum values.")
            print("Data Not Saved")
        # Close the window
        self.close()
        
    def getDict(self):
        return self.allDataDict
        
class AlertConfig(QtGui.QWidget):
    def __init__(self,devices, location, parent = None):
        super(AlertConfig, self).__init__(parent)
        self.devices = devices
        # Configure the layout
        layout = QtGui.QGridLayout()
        # where to find the notifier data
        self.location = location
        # Set the layout
        self.setLayout(layout)
        self.mins = {}
        self.maxs = {}
        self.contacts = {}
        self.checkBoxes = {}
        self.allWidgetDict = {}
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
        cnctlbl.setText("Contact (NAME1,NAME2,etc...)")
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
                u = y-1
                if(paramName is not None):
                    title = self.devices[j].getFrame().getTitle()
                    nickname = self.devices[j].getFrame().getNicknames()[u]
                    key = (title+":"+nickname)
                    if(key in self.allDataDict):
                        for data in self.allDataDict[key]:
                            # All widget dict holds the Qt objects
                            self.allWidgetDict[key] = [QtGui.QCheckBox(),
                                                    QtGui.QLineEdit(),
                                                    QtGui.QLineEdit(),
                                                    QtGui.QLineEdit()]  
                            self.allWidgetDict[key][0].setChecked(
                                self.allDataDict[key][0])
                            self.allWidgetDict[key][1].setText(
                                str(self.allDataDict[key][1]))
                            self.allWidgetDict[key][2].setText(
                                str(self.allDataDict[key][2]))
                            self.allWidgetDict[key][3].setText(
                                str(self.allDataDict[key][3]))
                    else:
                        self.allWidgetDict[key] = [QtGui.QCheckBox(),
                                                    QtGui.QLineEdit(),
                                                    QtGui.QLineEdit(),
                                                    QtGui.QLineEdit()]  
                    label = QtGui.QLabel()
                    # Add the new widgets
                    label.setText(paramName)
                    layout.addWidget(label, z, 1)
                    layout.addWidget(self.allWidgetDict[key][1], z, 3)                  
                    layout.addWidget(self.allWidgetDict[key][2],z, 5)
                    layout.addWidget(self.allWidgetDict[key][3],z, 7)
                    layout.addWidget(self.allWidgetDict[key][0],z, 2)
                    
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
        try:
            self.allDataDict = pickle.load(open(os.path.join(
                self.location, 'NotifierConfig.mview'), 'rb'))
            NotifierGUI.allDataDict = self.allDataDict
            print "Config Data Opened"

        except:
            #traceback.print_exc()
            self.allDataDict = {}
            print("No config file found")
        return self.allDataDict
