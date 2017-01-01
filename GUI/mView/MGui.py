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
import MGrapher
import MAlert
from MWeb import web


class MGui(QtGui.QMainWindow):
    """Handles construction of GUI using mView framework."""
    print("##########################################")
    print("## Starting mView (C) Noah Meltzer 2016 ##")
    print("##########################################")
    # Holds the Qlabels that label the parameters.
    parameters = [[]]
    # Each tile on the GUI is called a frame, this is the list of them.
    tiles = []
    # All layouts for each device.
    grids = []
    # All devices connected and not connected to the GUI.
    devices = None
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
    # This is the main font used for text in the GUI.
    font = QtGui.QFont()
    font.setBold(False)
    font.setWeight(50)
    font.setKerning(True)
    # The staring column to put tiles in.
    VBoxColumn = 0
    # Used to allow query to keep calling itself.
    keepGoing = True

    def initGui(self, devices, parent=None):
        """Configure all GUI elements."""
        QtGui.QWidget.__init__(self, parent)
        app.setActiveWindow(self)
        QtGui.QApplication.setStyle(QtGui.QStyleFactory.create('plastique'))
        # On GUI exit, run stop function.
        atexit.register(self.stop)
        
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
        
        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(exitAction)
        
        NotifierMenu = menubar.addMenu('&Notifier')
        NotifierMenu.addAction(NotifierSettingsAction)
        
        DeviceMenu = menubar.addMenu('&Devices')
        DeviceMenu.addAction(deviceSettingsAction)
        # Keeps track of the number of widgets, used for placing tiles
        # into the correct column.
        numWidgets = 0
        # Configure the size policy of all tiles.
        frameSizePolicy = QtGui.QSizePolicy()
        frameSizePolicy.setVerticalPolicy(4)
        frameSizePolicy.setHorizontalPolicy(QtGui.QSizePolicy.Preferred)
        # Configure the layouts.
        self.mainVBox.append(QtGui.QVBoxLayout())
        self.mainVBox.append(QtGui.QVBoxLayout())
        self.mainHBox.addLayout(self.mainVBox[0])
        self.mainHBox.addLayout(self.mainVBox[1])
        # Which column are we adding a tile to next.
        self.VBoxColumn = 0
        
        devices = web.devices
        buttons = self.buttons
        titles = self.titles
        grids = self.grids
        tiles = self.tiles
        lcds = self.lcds
        params = self.parameters
        # Do for each device.
        for i in range(len(devices)):
            # Add a QFrame, this is the border, and the parent of all
            # GUI elements that go inside.
            tiles.append(QtGui.QFrame(self))
            # Switch off adding tiles to columns.
            if self.VBoxColumn == 0:
                self.VBoxColumn = 1
            else:
                self.VBoxColumn = 0
            self.mainVBox[self.VBoxColumn].addWidget(tiles[i])
            # Add new titles, grids, parameters, 
            # and lcds for the new parameter.
            titles.append(QtGui.QLabel(tiles[i]))
            grids.append(QtGui.QGridLayout())
            params.append([])
            lcds.append([])
            self.units.append([])
            self.buttons.append([])
            # Configure grid layout.
            grids[i].setSpacing(10)
            grids[i].addWidget(titles[i], 1, 0)
            grids[i].setColumnStretch(0, 1)
            # Configure the tile (the box surrounding 
            # information for each device).
            tiles[i].setSizePolicy(frameSizePolicy)
            tiles[i].setStyleSheet("background: rgb(52, 73, 94)")
            tiles[i].setFrameShape(QtGui.QFrame.Panel)
            tiles[i].setFrameShadow(QtGui.QFrame.Plain)
            tiles[i].setSizePolicy(QtGui.QSizePolicy.Preferred,
                    QtGui.QSizePolicy.Preferred)
            # Used for dpi scaling (works pretty well but not amazing).
            if self.scrnWidth > self.scrnHeight:
                web.ratio = float(self.scrnWidth) / 1800 + 1
            else:
                web.ratio = float(self.scrnHeight) / 1800 + 1
            tiles[i].setLineWidth(web.ratio)
            tiles[i].setLayout(grids[i])
            # Configure the layout of the buttons within the grid.
            buttonLayout = QtGui.QHBoxLayout()
            grids[i].addLayout(buttonLayout, 1, 1)
            # Create all buttons.
            deviceFrameButtons = devices[i].getFrame().getButtons()
            if deviceFrameButtons[0]:
                for b in range(len(deviceFrameButtons)):
                    # Append a new button to the array of buttons and
                    # set the parent as the current frame.
                    buttons[i].append(QtGui.QPushButton(tiles[i]))
                    # Set the text of the button to the name specified 
                    # when the device was initialized.
                    buttons[i][b].setText(deviceFrameButtons[b][0])
                    # Add the button to the screen.
                    buttonLayout.addWidget(buttons[i][b])
                    # Connect the button to function, 
                    # passing the number of the button that was clicked.
                    buttons[i][b].clicked.connect(
                            partial(devices[i].prompt, b))
                    # Make the button pretty.
                    buttons[i][b].setStyleSheet("color:rgb(189, 195, 199); "
                            "background:rgb(70, 80, 88)")
                    buttons[i][b].setFont(self.font)   
            # Make the titles look nice.
            titles[i].setStyleSheet("color:rgb(189, 195, 199);")
            self.font.setPointSize(18)
            titles[i].setFont(self.font)
            self.font.setPointSize(12)
            # Get the title of the device.
            titles[i].setText(devices[i].getFrame().getTitle())
            titles[i].setGeometry(QtCore.QRect(10, 10,
                    titles[i].fontMetrics().boundingRect(
                    titles[i].text()).width(), 40))
            nicknames = devices[i].getFrame().getNicknames()
            for y in range(len(nicknames)):
                # Add a new parameter to the current device.
                params[i].append(QtGui.QLabel(tiles[i]))
                self.units[i].append(QtGui.QLabel(tiles[i]))
                # Get the width of the text.
                params[i][y].setFont(self.font)
                params[i][y].setAlignment(QtCore.Qt.AlignLeft)
                self.units[i][y].setFont(self.font)
                self.units[i][y].setAlignment(QtCore.Qt.AlignRight)
                # Configure the QLCDnumber widgets that display
                # information.
                lcds[i].append(QtGui.QLCDNumber())
                lcds[i][y].setNumDigits(11)
                lcds[i][y].setSegmentStyle(QtGui.QLCDNumber.Outline)
                lcds[i][y].display("-")
                lcds[i][y].setFrameShape(QtGui.QFrame.Panel)
                lcds[i][y].setFrameShadow(QtGui.QFrame.Plain)
                lcds[i][y].setLineWidth(web.ratio)
                lcds[i][y].setMidLineWidth(100)
                lcds[i][y].setStyleSheet("color:rgb(189, 195, 199);\n")
                lcds[i][y].setFixedHeight(self.scrnHeight / 30)
                lcds[i][y].setMinimumWidth(self.scrnWidth / 7)
                # Make the parameters pretty.
                params[i][y].setWordWrap(True)
                params[i][y].setStyleSheet("color:rgb(189, 195, 199);")    
                # Hide everything until we know that it should be
                # displayed. This is essential to be able to handle
                # arrays.
                params[i][y].hide()
                lcds[i][y].hide()
                self.units[i][y].hide()
                # If a nickname for the setting has been defined, 
                # go ahead and display whatever is necessary.
                if nicknames[y] is not None:
                    params[i][y].show()
                    lcds[i][y].show()
                    self.units[i][y].show()
                    params[i][y].setText(nicknames[y])
                    grids[i].addWidget(params[i][y], y + 2, 0)
                    lcdHBoxLayout = QtGui.QHBoxLayout()
                    lcdHBoxLayout.addStretch(1)
                    lcdHBoxLayout.addWidget(lcds[i][y])
                    
                    grids[i].addLayout(lcdHBoxLayout, y + 2, 1)
                    grids[i].addWidget(self.units[i][y], y + 2, 2)
            # Configure the plots.
            if devices[i].getFrame().isPlot():
                dc = MGrapher.mGraph(devices[i])
                yPos = len(nicknames) + 3
                devices[i].getFrame().setPlot(dc)
                grids[i].addWidget(dc, yPos, 0, yPos, 3)
                
        self.mainVBox[0].addStretch(0)
        self.mainVBox[1].addStretch(0)
        print("GUI initialized.")

    def mousePressEvent(self, event):
        focused_widget = QtGui.QApplication.focusWidget()
        if isinstance(focused_widget, QtGui.QScrollArea):
            focused_widget.clearFocus()
        QtGui.QMainWindow.mousePressEvent(self, event)

    def stop(self):
        """Stop and close mView cleanly."""
        print("Closing mView...")
        self.keepGoing = False
        exit()
        
    def openNotifierSettings(self):
        """Open the notifier settings GUI."""
        # NOTE, this is run on the main thread, so while it is open
        # the main GUI will not be running.
        self.NotifierGUI = NotifierGUI()
        self.NotifierGUI.exec_()

    def setRefreshRate(self, period):
        web.guiRefreshRate = period

    def openConfig(self):
        self.Config = ConfigGui(self)
        self.Config.exec_()

    def startGui(self, devices, title, dataTitle, tele):
        """Start the GUI."""
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
        # Call the class's initialization function.
        self.initGui(devices)
        self.setWindowTitle(title)
        # Show the GUI.
        self.show()
        self.timer = QtCore.QTimer(self)
        # Update the GUI every so often. This CAN ONLY be done 
        # in the main thread.
        self.timer.singleShot(web.guiRefreshRate * 1000, self.update)
        try:
            QtGui.QApplication.focusWidget().clearFocus()
        except:
            pass
        sys.exit(app.exec_())

    def update(self):
        """Update the GUI."""
        error = False
        # Loop through all devices.
        for i in range(len(web.devices)):
            # If there is no error with the device.
            frame = web.devices[i].getFrame()
            if not frame.isError():
                # Get the readings from the frame.
                readings = frame.getReadings()
                precisions = frame.getPrecisions()
                if readings is not None:
                    # Check if the reading is out of range.
                    outOfRange = frame.getOutOfRangeStatus()
                    nicknames = frame.getNicknames()
                    # Update all QLcds with the reading.
                    for y in range(len(outOfRange)):
                        # The key for a reading is "device:param".
                        key = frame.getTitle() + ":" + nicknames[y] 
                        # Check if the specific reading is out of range.
                        if outOfRange[key]:
                            # If the reading is out of range, make
                            # everything orange.
                            orange = "color:rgb(200, 100, 50);\n"
                            self.lcds[i][y].setStyleSheet(orange)
                            self.units[i][y].setStyleSheet(orange)
                            self.parameters[i][y].setStyleSheet(orange)
                        else:
                            # Otherwise, things should be white.
                            white = "color:rgb(189, 195, 199);\n"
                            self.lcds[i][y].setStyleSheet(white) 
                            self.units[i][y].setStyleSheet(white) 
                            self.parameters[i][y].setStyleSheet(white) 
                    for y in range(len(nicknames)):
                        # Segments should be flat
                        self.lcds[i][y].setSegmentStyle(QtGui.QLCDNumber.Flat)
                        try:
                            # If the readings are not NaN, then display
                            # a reading.
                            format = "%." + str(int(precisions[y])) + "f"
                            if not math.isnan(readings[y]):
                                self.lcds[i][y].display(format %readings[y])
                            # If the reading is nan, or there is none,
                            # it is denoted by "---".
                            else:
                                self.lcds[i][y].display("---")
                        except TypeError:
                            traceback.print_exc()
                        # If there are units, put them next to
                        # the number.
                        if frame.getUnits():
                            self.units[i][y].setText(frame.getUnits()[y])
                            self.font.setPointSize(18)
                            self.units[i][y].setFont(self.font)
                            self.font.setPointSize(12)
            else:
                # Otherwise if there is an error, show that on 
                # the gui through outlined lcd numbers.
                for y in range(len(self.lcds[i])):
                    self.lcds[i][y].setSegmentStyle(QtGui
                        .QLCDNumber.Outline)
                    self.lcds[i][y].display("-")
                    
        if self.keepGoing:
            self.timer.singleShot(web.guiRefreshRate * 1000, self.update)
        return


app = QtGui.QApplication(sys.argv)