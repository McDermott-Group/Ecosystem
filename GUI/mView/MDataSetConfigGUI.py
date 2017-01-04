from PyQt4 import QtGui
import os
from MWeb import web
from functools import partial
from dataChestWrapper import dataChestWrapper
import traceback
from MPopUp import PopUp


class DataSetConfigGUI(QtGui.QDialog):
    """Allows user to create custom data logs."""
    def __init__(self, parent = None):
        super(DataSetConfigGUI, self).__init__(parent)
        #Save initial state just in case changes are canceled
        self.initialStates = []
        for device in web.devices:
            self.initialStates.append(device.getFrame().DataLoggingInfo().copy())
       # print self.initialStates
        #Create a tab for new dataset settings
        mainTabWidget = QtGui.QTabWidget()
        self.settingsWidget = NewDataSetSettings()
        mainTabWidget.addTab(self.settingsWidget, "Data Logging Config")
        #Create the main layout for the GUI.
        mainLayout = QtGui.QVBoxLayout()
        # Add teh tab widget to the main layout.
        mainLayout.addWidget(mainTabWidget)
        # The button layout that will hold the OK button.
        buttonLayout = QtGui.QHBoxLayout()
        okButton = QtGui.QPushButton(self)
        okButton.setText("OK")
        okButton.clicked.connect(self.okClicked)
        cancelButton = QtGui.QPushButton(self)
        cancelButton.setText("Cancel")
        cancelButton.clicked.connect(self.cancel)
        # Give the button some cusion so that it will not be streched
        # out.
        buttonLayout.addStretch(0)
        buttonLayout.addWidget(okButton)
        buttonLayout.addWidget(cancelButton)
        # Add the button.
        mainLayout.addLayout(buttonLayout)
        self.setLayout(mainLayout)
        self.setWindowTitle("DataChest Config")
    def okClicked(self):
        # Take a look at what changed
        root = os.environ['DATA_CHEST_ROOT']
        for i,device in enumerate(web.devices):
            # If any changes were made, reinitialize the datalogger.
            #print "initial: ",self.initialStates[i]
            #print "final: ",device.getFrame().DataLoggingInfo()
            dir = device.getFrame().DataLoggingInfo()['location']
            
        
            if self.initialStates[i] != device.getFrame().DataLoggingInfo():
                print "some info was changed"
                try:
                    device.getFrame().DataLoggingInfo()['chest'].configureDataSets()
                except Exception as e:
                    print(e)
            for device in web.devices:
                for i,checkbox in enumerate(self.settingsWidget.checkboxes):
                    device.getFrame().DataLoggingInfo()['channels'][device.getFrame()
                        .getNicknames()[i]] = (checkbox.checkState() != 0)
            self.close()
                   # traceback.print_exec()
                   
                    
                    
                # try:
                    # device.getFrame().DataLoggingInfo()['chest'] = dataChestWrapper(device)
                # except:
                    # traceback.print_exec()
       
    def cancel(self):
        # Revert all changes
         for i,device in enumerate(web.devices):
            info = device.getFrame().DataLoggingInfo() 
            info = self.initialStates[i]
         self.close()
class NewDataSetSettings(QtGui.QWidget):
    def __init__(self, parent = None):
        super(NewDataSetSettings, self).__init__(parent)
        
        mainLayout = QtGui.QVBoxLayout()
        self.checkboxes = []
        grid = QtGui.QGridLayout()
        self.setLayout(mainLayout)
        mainLayout.addLayout(grid)
        grid.addWidget(QtGui.QLabel("DATA_CHEST_ROOT Environment Variable:"),0,0)
        grid.addWidget(QtGui.QLabel("\t"+str(os.environ['DATA_CHEST_ROOT'])), 0, 1,1,2)

       # grid.addWidget(QtGui.QLabel("Data Log Locations: "),1,0,1,2)
        
        font = QtGui.QFont()
        font.setPointSize(14)
        
        row = 2
        for device in web.devices:
            row += 1
            title = QtGui.QLabel(str(device))
            title.setFont(font)
            grid.addWidget(title,row,0)
            grid.addWidget(QtGui.QLabel(str(device.getFrame()
                .DataLoggingInfo()['location'])),row,1)
            button = QtGui.QPushButton("Browse...",self)
            button.clicked.connect(partial(self.openFileDialog, device, grid, row))
            grid.addWidget(button,row, 3)
            for nickname in device.getFrame().getNicknames():
                row += 1
                hBox = QtGui.QHBoxLayout()
                checkbox = QtGui.QCheckBox(self)
                self.checkboxes.append(checkbox)
                checkbox.setChecked(device.getFrame().DataLoggingInfo()['channels'][nickname])
                grid.addLayout(hBox, row, 0)
                hBox.addWidget(checkbox)
                hBox.addWidget(QtGui.QLabel(nickname))
                hBox.addStretch(0)
    def openFileDialog(self, device, grid,  row):
        root = os.environ['DATA_CHEST_ROOT']
        name =   device.getFrame().DataLoggingInfo()['name']
        dir = QtGui.QFileDialog.getSaveFileName(self, "Save New Data Set...", 
            device.getFrame().DataLoggingInfo()['location']+"\\"+name , "")
         
        #print dir
        
        dir = os.path.abspath(dir).rsplit('\\',1)
        location = dir[0]
        name = dir[1]
        print "location:", location
        print "name:", name
        
        if not root in location:
                print "ERROR"
                errorMsg = PopUp(str("ERROR: Directory must be inside of DATA_CHEST_ROOT."))
                errorMsg.exec_()
        else:
            relativePath =  os.path.relpath(location, root)
            print "New path for", str(device)+":", location
            device.getFrame().DataLoggingInfo()['name'] = name
            device.getFrame().DataLoggingInfo()['location'] = location
            grid.itemAtPosition(row, 1).widget().setText(location)
        # else:
            # print "DATA_CHEST_ROOT Directory must be a parent directory of datalogging location."
        #grid.itemAtPosition(row, 2).widget().setText(dir.replace(root, ''))
        return dir
        