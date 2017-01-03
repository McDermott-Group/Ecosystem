from PyQt4 import QtGui
import os
from MWeb import web
from functools import partial

class DataSetConfigGUI(QtGui.QDialog):
    """Allows user to create custom data logs."""
    def __init__(self, parent = None):
        super(DataSetConfigGUI, self).__init__(parent)
        #Create a tab for new dataset settings
        mainTabWidget = QtGui.QTabWidget()
        mainTabWidget.addTab(NewDataSetSettings(), "Create New Dataset")
        #Create the main layout for the GUI.
        mainLayout = QtGui.QVBoxLayout()
        # Add teh tab widget to the main layout.
        mainLayout.addWidget(mainTabWidget)
        # The button layout that will hold the OK button.
        buttonLayout = QtGui.QHBoxLayout()
        okButton = QtGui.QPushButton(self)
        okButton.setText("OK")
        cancelButton = QtGui.QPushButton(self)
        cancelButton.setText("Cancel")
        # Give the button some cusion so that it will not be streched
        # out.
        buttonLayout.addStretch(0)
        buttonLayout.addWidget(okButton)
        buttonLayout.addWidget(cancelButton)
        # Add the button.
        mainLayout.addLayout(buttonLayout)
        self.setLayout(mainLayout)
        self.setWindowTitle("DataChest Config")

class NewDataSetSettings(QtGui.QWidget):
    def __init__(self, parent = None):
        super(NewDataSetSettings, self).__init__(parent)
        
        mainLayout = QtGui.QVBoxLayout()

        grid = QtGui.QGridLayout()
        self.setLayout(mainLayout)
        mainLayout.addLayout(grid)
        grid.addWidget(QtGui.QLabel("DATA_CHEST_ROOT Environment Variable:"),0,0)
        grid.addWidget(QtGui.QLabel("\t"+str(os.environ['DATA_CHEST_ROOT'])), 0, 2)

        grid.addWidget(QtGui.QLabel("Data Log Locations: "),1,0,1,2)

        row = 2
        for device in web.devices:
            row += 1
            grid.addWidget(QtGui.QLabel(str(device)),row,0)
            grid.addWidget(QtGui.QLabel(str(device.getFrame().DataLoggingInfo()['location'])),row,2)
            button = QtGui.QPushButton("Browse...",self)
            button.clicked.connect(partial(self.openFileDialog, device, grid, row))
            grid.addWidget(button,row, 3)
            for nickname in device.getFrame().getNicknames():
                row += 1
                hBox = QtGui.QHBoxLayout()
                checkbox = QtGui.QCheckBox(self)
                checkbox.setChecked(device.getFrame().DataLoggingInfo()['channels'][nickname])
                grid.addLayout(hBox, row, 0)
                hBox.addWidget(checkbox)
                hBox.addWidget(QtGui.QLabel(nickname))
                hBox.addStretch(0)
    def openFileDialog(self, device, grid,  row):
        dir = os.path.abspath(QtGui.QFileDialog.getExistingDirectory(self, "Open Folder", 
            device.getFrame().DataLoggingInfo()['location']))
        device.getFrame().DataLoggingInfo()['location'] = dir
        grid.itemAtPosition(row, 2).widget().setText(dir)
        return dir
        