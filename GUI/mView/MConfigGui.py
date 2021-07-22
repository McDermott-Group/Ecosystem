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

__author__ = "Noah Meltzer"
__copyright__ = "Copyright 2016, Noah Meltzer, McDermott Group"
__license__ = "GPL"
__version__ = "1.0.2"
__maintainer__ = "Noah Meltzer"
__status__ = "Beta"

import traceback
from PyQt4 import QtGui

from MWeb import web


class ConfigGui(QtGui.QDialog):
    """
    Allows the user to configure the refresh rates for plots, devices
    and LCD numbers.
    """

    def __init__(self, parent=None):
        super(ConfigGui, self).__init__(parent)
        # Create a tab for update speed settings.
        mainTabWidget = QtGui.QTabWidget()
        mainTabWidget.addTab(refreshRateContents(), "Refresh Rates")
        # Create the main layout for the GUI.
        mainLayout = QtGui.QVBoxLayout()
        # Add the tab widget to the main layout.
        mainLayout.addWidget(mainTabWidget)
        # The button layout will hold the OK button.
        buttonLayout = QtGui.QHBoxLayout()
        okButton = QtGui.QPushButton(self)
        okButton.setText("OK")
        # Give the button some cusion so that it will not be streched
        # out.
        buttonLayout.addStretch(0)
        buttonLayout.addWidget(okButton)
        # Add the button.
        mainLayout.addLayout(buttonLayout)
        self.setLayout(mainLayout)
        self.setWindowTitle("Device Config")
        # Close the window when the ok button is clicked.
        okButton.clicked.connect(self.close)


class refreshRateContents(QtGui.QWidget):
    def __init__(self, parent=None):
        super(refreshRateContents, self).__init__(parent)

        mainLayout = QtGui.QVBoxLayout()

        self.setLayout(mainLayout)
        self.refreshTabWidget = QtGui.QTabWidget()

        mainLayout.addWidget(self.refreshTabWidget)
        self.refreshTabWidget.addTab(self.guiRefreshConfig(), "GUI")

        for device in web.devices:
            self.refreshTabWidget.addTab(devRefRateConfig(device),
                                         device.getFrame().getTitle())

    def guiRefreshConfig(self):
        guiRefConfig = QtGui.QWidget()
        guiRefLayout = QtGui.QVBoxLayout()
        guiRefLayoutH = QtGui.QHBoxLayout()
        guiRefLayoutH.addWidget(QtGui.QLabel("GUI Refresh period:"))
        guiRefLayoutH.addStretch(0)
        self.refRateEdit = QtGui.QLineEdit()
        # print "Gui ref rate:", web.persistentData(None, 'guiRefreshRate')
        self.refRateEdit.setText(
            str(web.persistentData.persistentDataAccess(None, 'guiRefreshRate')))
        guiRefLayoutH.addWidget(self.refRateEdit)
        guiRefLayoutH.addWidget(QtGui.QLabel('s'))
        self.refRateEdit.editingFinished.connect(self.updateMainGuiRefRate)

        guiRefLayout.addLayout(guiRefLayoutH)
        guiRefConfig.setLayout(guiRefLayout)
        return guiRefConfig

    def updateMainGuiRefRate(self):
        try:
            web.persistentData.persistentDataAccess(
                float(self.refRateEdit.text()), 'guiRefreshRate')

        except:
            traceback.print_exc()


class devRefRateConfig(QtGui.QWidget):
    def __init__(self, device, parent=None):
        super(devRefRateConfig, self).__init__(parent)

        self.device = device

        devRefConfig = QtGui.QWidget()
        devRefLayout = QtGui.QVBoxLayout()
        devRefLayoutH = QtGui.QHBoxLayout()
        title = device.getFrame().getTitle()
        devRefLayoutH.addWidget(QtGui.QLabel("%s update period:"
                                             % title))
        devRefLayoutH.addStretch(0)

        devRefConfig.setLayout(devRefLayout)
        self.devRefRateEdit = QtGui.QLineEdit()
        self.devRefRateEdit.editingFinished.connect(self.updateDevRefRate)

        self.devRefRateEdit.setText(str(device.getFrame().getRefreshRate()))
        devRefLayoutH.addWidget(self.devRefRateEdit)
        devRefLayoutH.addWidget(QtGui.QLabel('s'))

        devRefLayout.addLayout(devRefLayoutH)

        if device.getFrame().isPlot():
            plotRefLayoutH = QtGui.QHBoxLayout()
            title = device.getFrame().getTitle()
            plotRefLayoutH.addWidget(QtGui.QLabel("%s plot refresh rate:"
                                                  % title))
            plotRefLayoutH.addStretch(0)
            self.plotRefRateEdit = QtGui.QLineEdit()
            self.plotRefRateEdit.setText(
                str(device.getFrame().getPlotRefreshRate()))
            self.plotRefRateEdit.editingFinished.connect(
                self.updateDevPlotRate)
            plotRefLayoutH.addWidget(self.plotRefRateEdit)
            plotRefLayoutH.addWidget(QtGui.QLabel('s'))
            devRefLayout.addLayout(plotRefLayoutH)
        self.setLayout(devRefLayout)

    def updateDevPlotRate(self):
        refreshRate = self.plotRefRateEdit.text()
        try:
            self.device.getFrame().setPlotRefreshRate(float(refreshRate))
        except:
            traceback.print_exc()
            print(("[%s]: %s is not a number."
                  % (self.device.getFrame().getTitle(), refreshRate)))

    def updateDevRefRate(self):
        refreshRate = self.devRefRateEdit.text()
        try:
            self.device.getFrame().setRefreshRate(float(refreshRate))
        except:
            traceback.print_exc()
            print(("[%s]: %s is not a number."
                  % (self.device.getFrame().getTitle(), refreshRate)))
