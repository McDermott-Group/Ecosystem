from PyQt4 import QtGui
import os
from MWeb import web
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
        
        self.setLayout(mainLayout)
        
        mainLayout.addWidget(QtGui.QLabel("DATA_CHEST_ROOT Environment Variable:"))
        mainLayout.addWidget(QtGui.QLabel("\t"+str(os.environ['DATA_CHEST_ROOT'])))
        mainLayout.addWidget(QtGui.QLabel("Current Log Locations: "))
        for device in web.devices:
            mainLayout.addWidget(QtGui.QLabel(str(device)))
            mainLayout.addWidget(QtGui.QLabel("\t"
                +str(device.getFrame().DataLoggingInfo()['location'])))
        