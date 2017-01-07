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
        self.advancedSettingsWidget = DataSetSettings(advanced = True)
        self.simpleSettingsWidget = DataSetSettings(advanced = False)
        
        mainTabWidget.addTab(self.simpleSettingsWidget, "Basic")
        mainTabWidget.addTab(self.advancedSettingsWidget, "Advanced")
        
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
                    traceback.print_exc()
                    self.cancel()
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
            for key in device.getFrame().DataLoggingInfo().keys():
                device.getFrame().DataLoggingInfo()[key] = self.initialStates[i][key]

         self.close()
class DataSetSettings(QtGui.QWidget):
    def __init__(self, parent = None, **kwargs):
        super(DataSetSettings, self).__init__(parent)
        isAdvanced = kwargs.get('advanced', False)
        font = QtGui.QFont()
        font.setPointSize(14)
        
        hbox = QtGui.QHBoxLayout()
        mainLayout = QtGui.QVBoxLayout()
        self.checkboxes = []
        grid = QtGui.QGridLayout()
        self.setLayout(mainLayout)
        mainLayout.addLayout(hbox)
        mainLayout.addLayout(grid)
        rootlbl = QtGui.QLabel("DATA_CHEST_ROOT:")
        rootlbl.setFont(font)
        hbox.addWidget(rootlbl)
        hbox.addWidget(QtGui.QLabel("\t"+str(os.environ['DATA_CHEST_ROOT'])))
        
       # grid.addWidget(QtGui.QLabel("Data Log Locations: "),1,0,1,2)
        
        if not isAdvanced:
            grid = QtGui.QGridLayout()
            mainLayout.addLayout(grid)
            title = QtGui.QLabel(str("Log Folder: "))
            title.setFont(font)
            grid.addWidget(title,0,0)
            location =  QtGui.QLabel(web.devices[0].getFrame().DataLoggingInfo()['location'])
            grid.addWidget(location, 0, 1)
            button = QtGui.QPushButton("Browse...",self)
            button.clicked.connect(partial(self.openFileDialog, None, grid, 0))
            buttonHbox = QtGui.QHBoxLayout()
            grid.addLayout(buttonHbox, 0, 3)
            buttonHbox.addStretch(0)
            buttonHbox.addWidget(button)
        else:
            row = 2
            for device in web.devices:
                row += 1
                title = QtGui.QLabel(str(device)+": ")
                title.setFont(font)
                grid.addWidget(title,row,0)
                grid.addWidget(QtGui.QLabel(str(device.getFrame()
                    .DataLoggingInfo()['location'])),row,1)
                button = QtGui.QPushButton("Browse...",self)
                button.clicked.connect(partial(self.openFileDialog, device, grid, row))
                buttonHbox = QtGui.QHBoxLayout()
                grid.addLayout(buttonHbox, row, 3)
                buttonHbox.addStretch(0)
                buttonHbox.addWidget(button)

                for nickname in device.getFrame().getNicknames():
                    row += 1
                    #hBox = QtGui.QHBoxLayout()
                    checkbox = QtGui.QCheckBox(self)
                    self.checkboxes.append(checkbox)
                    checkbox.setChecked(device.getFrame().DataLoggingInfo()['channels'][nickname])
                    #grid.addLayout(hBox, row, 0)
                    grid.addWidget(QtGui.QLabel(nickname), row, 0)
                    grid.addWidget(checkbox, row, 1)
                    #hBox.addWidget(checkbox)
                    #hBox.addWidget(QtGui.QLabel(nickname))
                    #hBox.addStretch(0)
    def openFileDialog(self, device, grid,  row):
        root = os.environ['DATA_CHEST_ROOT']
        if device!=None:
            name =   device.getFrame().DataLoggingInfo()['name']
        dir = QtGui.QFileDialog.getSaveFileName(self, "Save New Data Set...", 
            web.devices[0].getFrame().DataLoggingInfo()['location']+"\\"+name , "")
             
        #print dir
        
        dir = os.path.abspath(dir).rsplit('\\',1)
        location = dir[0]
        name = dir[1]
        
        if not root in location:
                print "ERROR"
                errorMsg = PopUp(str(
                    "ERROR: Directory must be inside of directory in DATA_CHEST_ROOT."
                    ))
                errorMsg.exec_()
        elif root == location:
          print "ERROR"
          errorMsg = PopUp(str(
              "ERROR: Data must be stored inside of a "
              "DIRECTORY which is itself under DATA_CHEST_ROOT."
              ))
          errorMsg.exec_()
        else:
            relativePath =  os.path.relpath(location, root)
            if device != None:
            
                print "New path for", str(device)+":", location
                device.getFrame().DataLoggingInfo()['name'] = name
                device.getFrame().DataLoggingInfo()['location'] = location
            else:
                for device in web.devices:
                    device.getFrame().DataLoggingInfo()['name'] = device.getFrame().getTitle()
                    device.  device.getFrame().DataLoggingInfo()['location'] = location
            grid.itemAtPosition(row, 1).widget().setText(location)
        # else:
            # print "DATA_CHEST_ROOT Directory must be a parent directory of datalogging location."
        #grid.itemAtPosition(row, 2).widget().setText(dir.replace(root, ''))
        return dir
        