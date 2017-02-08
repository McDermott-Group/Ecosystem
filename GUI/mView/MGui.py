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
__copyright__ = "Copyright 2016, McDermott Group"
__license__ = "GPL"
__version__ = "2.0.1"
__maintainer__ = "Noah Meltzer"
__status__ = "Beta"

import sys
import math
import atexit
import traceback
from functools import partial
from PyQt4 import QtCore, QtGui

from NotifierGUI import NotifierGUI
from MConfigGui import ConfigGui
from MDataSetConfigGUI import DataSetConfigGUI
from MPersistentData import MPersistentData
from MWeb import web
import MGrapher
import MAlert
from MWeb import web
from MNodeEditor.MNodeEditorHandler import MNodeEditorHandler
from MDeviceContainerWidget import MDeviceContainerWidget

class MGui(QtGui.QMainWindow):
    """Handles construction of GUI using mView framework."""
    print("##########################################")
    print("## Starting mView (C) Noah Meltzer 2016 ##")
    print("##########################################")
    web.persistentData = MPersistentData()
    # Holds the Qlabels that label the parameters.
    parameters = [[]]
    # Each tile on the GUI is called a frame, this is the list of them.
    tiles = []
    # All layouts for each device.
    grids = []
    # The main vertical box layout for the GUI.
    mainVBox = [QtGui.QVBoxLayout()]
    # The main horizontal box layout for the GUI.
    mainHBox = QtGui.QHBoxLayout()
    # The titles of all devices.
    titles = []
    # The dataset for each device.
    dataSets = []
    # Holds all lcds for all devices.
    lcds = [[]]
    # Holds all units for all devices.
    units = [[]]
    # Holds all buttons for all devices.
    buttons = [[]]
    deviceWidgets = []
    # This is the main font used for text in the GUI.
    font = QtGui.QFont()
    font.setBold(False)
    font.setWeight(50)
    font.setKerning(True)
    # The staring column to put tiles in.
    VBoxColumn = 0
    # Used to allow query to keep calling itself.
    keepGoing = True
    
    # splash_pix = QtGui.QPixmap('logo.png')
    # splash = QtGui.QSplashScreen(splash_pix, QtCore.Qt.WindowStaysOnTopHint)
    # splash.show()
    def __init__(self):
        atexit.register(self.stop)
    def initGui(self, devices, parent=None):
        """Configure all GUI elements."""
        QtGui.QWidget.__init__(self, parent)
        app.setActiveWindow(self)
        QtGui.QApplication.setStyle(QtGui.QStyleFactory.create('plastique'))
        
        web.gui = self
        # Make the GUI fullscreen.
        self.showMaximized()
       
        web.devices = devices
        # Make GUI area scrollable.
        self.main_widget = QtGui.QWidget()
        self.main_widget.setLayout(self.mainHBox)
        self.scrollArea = QtGui.QScrollArea()
        self.scrollArea.setWidget(self.main_widget)
        self.scrollArea.setWidgetResizable(True)
        self.setCentralWidget(self.scrollArea)

        # Setup stylesheet.
        self.scrollArea.setStyleSheet("background:rgb(70, 80, 88)")
        # Configure the menu bar.
        menubar = self.menuBar()
        menubar.setStyleSheet("QMenuBar {background-color: "
                "rgb(189, 195, 199)}"
                "QMenuBar::item {background: transparent} "
                "QMenu{background-color:rgb(189, 195, 199)}")
        # Menu bar menus.
        exitAction = QtGui.QAction('&Exit', self)        
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(QtGui.qApp.quit)
                
        NotifierSettingsAction = QtGui.QAction('&Settings...', self)
        NotifierSettingsAction.triggered.connect(self.openNotifierSettings)
        
        deviceSettingsAction = QtGui.QAction('&Configure...', self)
        deviceSettingsAction.triggered.connect(self.openConfig)
        
        newDataSetAction = QtGui.QAction('&Data Logging Configuration...', self)
        newDataSetAction.triggered.connect(self.openNewDataSetConfig)
        
        virtualDevicesConfigAction = QtGui.QAction('&Virtual devices editor...',self)
        virtualDevicesConfigAction.triggered.connect(self.openVirtualDevicesConfig)
        
        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(exitAction)
        
        NotifierMenu = menubar.addMenu('&Notifier')
        NotifierMenu.addAction(NotifierSettingsAction)
        
        DeviceMenu = menubar.addMenu('&Devices')
        DeviceMenu.addAction(deviceSettingsAction)
        
        DataChestMenu = menubar.addMenu('&DataChest')
        DataChestMenu.addAction(newDataSetAction)
        
        VirtualDevicesMenu = menubar.addMenu('&Virtual Devices')
        VirtualDevicesMenu.addAction(virtualDevicesConfigAction)
        # Keeps track of the number of widgets, used for placing tiles
        # into the correct column.
        self.neh = MNodeEditorHandler()
        numWidgets = 0
        # Configure the size policy of all tiles.
        self.frameSizePolicy = QtGui.QSizePolicy()
        self.frameSizePolicy.setVerticalPolicy(4)
        self.frameSizePolicy.setHorizontalPolicy(QtGui.QSizePolicy.Preferred)
       
        # Configure the layouts.
        self.mainVBox.append(QtGui.QVBoxLayout())
        self.mainVBox.append(QtGui.QVBoxLayout())
        self.mainHBox.addLayout(self.mainVBox[0])
        self.mainHBox.addLayout(self.mainVBox[1])
        self.mainVBox[0].setAlignment(QtCore.Qt.AlignTop)
        self.mainVBox[1].setAlignment(QtCore.Qt.AlignTop)

        # Which column are we adding a tile to next.
        devices = web.devices
        self.index = 0
        for i,device in enumerate(devices):
            self.addDevice(device)
        #self.mainVBox[0].addStretch(0)
        #self.mainVBox[1].addStretch(0)
        print("GUI initialized.")
    def stop(self):
        '''Stop MView.'''
        print "Shutting down MView."
        print "all devices:", web.devices
        for device in web.devices:
            print "stopping", str(device)
            device.stop()
            device.getFrame().getDataChestWrapper().done()
            device.getFrame().getDataChestWrapper().saveState()
        web.persistentData.saveState()
        self.neh.stop()
        
    def addDevice(self, device):
        if self.VBoxColumn == 0:
            self.VBoxColumn = 1
        else:
            self.VBoxColumn = 0
       
        container = MDeviceContainerWidget(device, self)
        self.deviceWidgets.append(container)
        self.mainVBox[self.VBoxColumn].addWidget(container)
    def addWidget(self, widget):
        if self.VBoxColumn == 0:
            self.VBoxColumn = 1
        else:
            self.VBoxColumn = 0
        self.mainVBox[self.VBoxColumn].addWidget(widget)
    def mousePressEvent(self, event):
        
        focused_widget = QtGui.QApplication.focusWidget()
        if isinstance(focused_widget, QtGui.QScrollArea):
            focused_widget.clearFocus()
        QtGui.QMainWindow.mousePressEvent(self, event)

    def closeEvent(self, event):
        print("Closing mView...")
        self.stop()
        exit()
    def openNotifierSettings(self):
        
        """Open the notifier settings GUI."""
        # NOTE, this is run on the main thread, so while it is open
        # the main GUI will not be running.
        self.NotifierGUI = NotifierGUI()
        self.NotifierGUI.exec_()
        
    def openNewDataSetConfig(self):
        """Open the new data set configuration GUI."""
        # NOTE, this is run on the main thread, so while it is open
        # the main GUI will not be running.
        self.DataSetConfigGUI = DataSetConfigGUI()
        self.DataSetConfigGUI.exec_()
        
    def setRefreshRate(self, period):
        web.persistentData.persistentDataAccess(period,'guiRefreshRate')
        
    def openVirtualDevicesConfig(self):
        self.neh.showEditor()

    def openConfig(self):
        self.Config = ConfigGui(self)
        self.Config.exec_()

    def startGui(self, devices, title, dataTitle, tele, autostart = True):
        """Start the GUI."""
        print "Starting GUI."
        # Used as the name of the dataChest data title.
        self.dataTitle = dataTitle
        web.devices = devices
        # Start the notifier.
        web.telecomm = tele
        self.NotifierGUI = NotifierGUI()
        self.MAlert = MAlert.MAlert()
        self.MAlert.begin()
        
        screen_resolution = QtGui.QDesktopWidget().screenGeometry()
        self.scrnWidth = screen_resolution.width()
        self.scrnHeight = screen_resolution.height()
        web.scrnWidth = self.scrnWidth
        web.scrnHeight = self.scrnHeight
        if self.scrnWidth > self.scrnHeight:
            web.ratio = float(self.scrnWidth) / 1800 + 1
        else:
            web.ratio = float(self.scrnHeight) / 1800 + 1
        # Call the class's initialization function.
        self.initGui(devices)
        self.setWindowTitle(title)
        web.title = title
        # Show the GUI.
        self.show()
        self.timer = QtCore.QTimer(self)
        self.neh.begin()
        # Update the GUI every so often. This CAN ONLY be done 
        # in the main thread.
        if self.keepGoing:
            self.timer.singleShot(web.persistentData.persistentDataAccess(None, 'guiRefreshRate', default = web.guiRefreshRate) * 1000, self.update)
        # try:
            # QtGui.QApplication.focusWidget().clearFocus()
        # except:
            # pass
        if autostart:
            self.showGui()
    def showGui(self):
        sys.exit(app.exec_())

    def update(self):
        """Update the GUI."""
        pass
       


app = QtGui.QApplication(sys.argv)