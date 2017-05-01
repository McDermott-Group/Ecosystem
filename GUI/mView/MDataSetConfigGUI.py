from PyQt4 import QtGui
import os
from MWeb import web
from functools import partial
from dataChestWrapper import dataChestWrapper
import traceback
from MPopUp import PopUp
import atexit
import time
import re


class DataSetConfigGUI(QtGui.QDialog):
    """Allows user to create custom data logs."""

    def __init__(self, parent=None):
        super(DataSetConfigGUI, self).__init__(parent)
        atexit.register(self.saveState)

        # Save initial state just in case changes are canceled
        self.initialStates = []
        for device in web.devices:
            self.initialStates.append(
                device.getFrame().DataLoggingInfo().copy())
       # print self.initialStates
        # Create a tab for new dataset settings
        mainTabWidget = QtGui.QTabWidget()
        self.advancedSettingsWidget = DataSetSettings(self, advanced=True)
        self.simpleSettingsWidget = DataSetSettings(self, advanced=False)

        mainTabWidget.addTab(self.simpleSettingsWidget, "Basic")
        mainTabWidget.addTab(self.advancedSettingsWidget, "Advanced")

        # Create the main layout for the GUI.
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

    def saveState(self):
        pass

    def okClicked(self):
        # Take a look at what changed
        root = os.environ['DATA_CHEST_ROOT']
        root = root.replace("/","\\")
        for i, device in enumerate(web.devices):
            # print "Data logging info:",device.getFrame().DataLoggingInfo()
            # If any changes were made, reinitialize the datalogger.
            # print "initial: ",self.initialStates[i]
            # print "final: ",device.getFrame().DataLoggingInfo()
            dir = device.getFrame().DataLoggingInfo()['location']

            if self.initialStates[i] != device.getFrame().DataLoggingInfo():
               # print "some info was changed"
                chest = device.getFrame().DataLoggingInfo()['chest']
                try:
                    if chest != None:
                        chest.configureDataSets()
                except Exception as e:
                    traceback.print_exc()
                    self.cancel()
            for y, device in enumerate(web.devices):
                for i, checkbox in enumerate(self.advancedSettingsWidget.checkboxes[y]):
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
        for i, device in enumerate(web.devices):
            for key in device.getFrame().DataLoggingInfo().keys():
                device.getFrame().DataLoggingInfo()[
                    key] = self.initialStates[i][key]

        self.close()


class DataSetSettings(QtGui.QWidget):
    def __init__(self, configGui, parent=None,  **kwargs):
        super(DataSetSettings, self).__init__(parent)
        isAdvanced = kwargs.get('advanced', False)
        self.configGui = configGui
        font = QtGui.QFont()
        font.setPointSize(14)
        self.locationLabels = []
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
        hbox.addWidget(QtGui.QLabel("\t" + str(os.environ['DATA_CHEST_ROOT']).replace("/","\\")))
        # self.checkboxes.append([])
        # grid.addWidget(QtGui.QLabel("Data Log Locations: "),1,0,1,2)

        if not isAdvanced:
            grid = QtGui.QGridLayout()
            mainLayout.addLayout(grid)
            title = QtGui.QLabel(str("Log Folder: "))
            title.setFont(font)
            grid.addWidget(title, 0, 0)
            location = QtGui.QLabel(
                web.devices[0].getFrame().DataLoggingInfo()['location'])
            grid.addWidget(location, 0, 1)
            button = QtGui.QPushButton("Browse...", self)
            button.clicked.connect(partial(self.openFileDialog, None, grid, 0))
            buttonHbox = QtGui.QHBoxLayout()
            grid.addLayout(buttonHbox, 0, 3)
            buttonHbox.addStretch(0)
            buttonHbox.addWidget(button)

            defaultButton = QtGui.QPushButton(
                "Automatically Configure Data Sets", self)
            defaultButton.clicked.connect(partial(self.resetToDefault, grid))
            mainLayout.addWidget(defaultButton)
            mainLayout.addStretch(0)
        else:
            row = 2

            for y, device in enumerate(web.devices):
                # print " device:", device
                row += 1
                lock = device.getFrame().DataLoggingInfo()[
                    'lock_logging_settings']
                title = QtGui.QLabel(str(device) + ": ")
                title.setFont(font)
                grid.addWidget(title, row, 0)
                location = QtGui.QLabel(str(device.getFrame()
                                            .DataLoggingInfo()['location']))
                self.locationLabels.append(location)
                grid.addWidget(location, row, 1)
                button = QtGui.QPushButton("Browse...", self)
                button.setEnabled(not lock)
                button.clicked.connect(
                    partial(self.openFileDialog, device, grid, row))
                buttonHbox = QtGui.QHBoxLayout()
                grid.addLayout(buttonHbox, row, 3)
                buttonHbox.addStretch(0)
                buttonHbox.addWidget(button)
                self.checkboxes.append([])
                for nickname in device.getFrame().getNicknames():
                    row += 1
                    #hBox = QtGui.QHBoxLayout()
                    checkbox = QtGui.QCheckBox(self)
                    checkbox.setEnabled(not lock)
                    self.checkboxes[y].append(checkbox)
                    # print device, "Data logging info: ",
                    # device.getFrame().DataLoggingInfo()
                    checkbox.setChecked(device.getFrame().DataLoggingInfo()[
                                        'channels'][nickname])
                    #grid.addLayout(hBox, row, 0)
                    grid.addWidget(QtGui.QLabel(nickname), row, 0)
                    grid.addWidget(checkbox, row, 1)
                    # hBox.addWidget(checkbox)
                    # hBox.addWidget(QtGui.QLabel(nickname))
                    # hBox.addStretch(0)

    def resetToDefault(self, grid):

        for i, device in enumerate(web.devices):
            device.getFrame().DataLoggingInfo()[
                'name'] = device.getFrame().getTitle()
            lock = device.getFrame().DataLoggingInfo()['lock_logging_settings']
            if lock:
                newFolder = time.strftime('%x').replace(' ', '_')
                newFolder = newFolder.replace('/', '_')
                currentLoc = device.getFrame().DataLoggingInfo()['location']
                print "currentLoc:", currentLoc
                newLoc = currentLoc.split('\\')
                print "newLocation3:", newLoc
                # If the folder we are in is in the format 'MM_DD_YY', then
                # Assume MView created it and we should back out and create a
                # new folder.
                r = re.compile('.{2}_.{2}_.{2}')
                if r.match(newLoc[-1]):
                    newLoc = newLoc[:-1:]
                print "newLocation2:", newLoc
                newLoc.append(newFolder)
                print "newLocation:", newLoc
                newLoc = "\\".join([str(dir) for dir in newLoc])
                device.getFrame().DataLoggingInfo()['location'] = newLoc

            try:
                chest = device.getFrame().DataLoggingInfo()['chest']
                if chest != None:
                    chest.configureDataSets()
                    location = str(
                        device.getFrame().DataLoggingInfo()['location'])
                    self.configGui.advancedSettingsWidget.locationLabels[i].setText(
                        location)
            except:
                print "ERROR:", device
                traceback.print_exc()

        grid.itemAtPosition(0, 1).widget().setText(location)

    def openFileDialog(self, device, grid,  row):
        root = os.environ['DATA_CHEST_ROOT']
        root = root.replace("/","\\")
        if device != None:
            name = device.getFrame().DataLoggingInfo()['name']
            dir = QtGui.QFileDialog.getSaveFileName(self, "Save New Data Set...",
                                                    web.devices[0].getFrame().DataLoggingInfo()['location'], "")
            dir = os.path.abspath(dir).rsplit('\\', 1)
            location = dir[0]
            name = dir[1]
        else:
            dir = QtGui.QFileDialog.getExistingDirectory(self, "Save Data In...",
                                                         web.devices[0].getFrame().DataLoggingInfo()['location'])
            location = os.path.abspath(str(dir))
        # print dir

        # print "root:", root
        # print "location:",location
        if not root in location:
                # print "ERROR"
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
            relativePath = os.path.relpath(location, root)
            if device != None:

                # print "New path for", str(device)+":", location
                device.getFrame().DataLoggingInfo()['name'] = name
                device.getFrame().DataLoggingInfo()['location'] = location
            else:
                # print "location labels size : ",len(self.configGui.advancedSettingsWidget.locationLabels)
                # print "location labels:
                # ",self.configGui.advancedSettingsWidget.locationLabels
                for i, device in enumerate(web.devices):

                    lock = device.getFrame().DataLoggingInfo()[
                        'lock_logging_settings']
                    if not lock:
                        device.getFrame().DataLoggingInfo()[
                            'name'] = device.getFrame().getTitle()
                        device.getFrame().DataLoggingInfo()[
                            'location'] = location
                        self.configGui.advancedSettingsWidget.locationLabels[i].setText(
                            location)
            grid.itemAtPosition(row, 1).widget().setText(location)
        # else:
            # print "DATA_CHEST_ROOT Directory must be a parent directory of datalogging location."
        #grid.itemAtPosition(row, 2).widget().setText(dir.replace(root, ''))
        return dir
