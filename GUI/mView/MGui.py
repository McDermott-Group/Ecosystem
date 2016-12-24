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
__version__ = "2.0.0"
__maintainer__ = "Noah Meltzer"
__status__ = "Beta"

"""
description = Handles construction of GUI using mView framework.
"""
import sys
sys.dont_write_bytecode = True

from PyQt4 import QtCore, QtGui

import threading

from functools import partial

from NotifierGUI import NotifierGUI
from MConfigGui import ConfigGui
import MGrapher
import MAlert
from MWeb import web

import math

import numpy as np

import atexit
import traceback

class MGui(QtGui.QMainWindow):
    print "##########################################"
    print "## Starting mView (C) Noah Meltzer 2016 ##"
    print "##########################################"
    # Holds the Qlabels that label the parameters
    parameters = [[]]
    # Each tile on the gui is called a frame, this is the list of them
    tiles = []
    # All layouts for each device
    grids = []
    # All devices connected and not connected to gui
    devices = None
    # The main vertical box layout for the gui.
    mainVBox = [QtGui.QVBoxLayout()]
    # The main horizontal box layout for the gui
    mainHBox = QtGui.QHBoxLayout()
    # The titles of all devices
    titles = []
    # The dataset for each device
    dataSets = []
    # Holds all lcds for all devices
    lcds = [[]]
    # Holds all units for all devices
    units = [[]]
    # Holds all buttons for all devices
    buttons = [[]]
    # This is the main font used for text in the GUI
    font = QtGui.QFont()
    font.setBold(False)
    font.setWeight(50)
    font.setKerning(True)
    # This is the default refresh rate
    #refreshRateSec = 1
    # The staring column to put tiles in
    VBoxColumn = 0
    # Used to allow Query to keep calling itself.
    keepGoing = True
    
    def initGui(self, devices, parent = None):
        '''Configure all gui elements.'''
        QtGui.QWidget.__init__(self, parent)
        app.setActiveWindow(self)
        QtGui.QApplication.setStyle(QtGui.QStyleFactory.create('plastique'))
        # On GUI exit, run stop function
        atexit.register(self.stop)
        web.devices = devices
        # Make gui area scrollable
        self.main_widget = QtGui.QWidget()
        self.main_widget.setLayout(self.mainHBox)
        self.scrollArea = QtGui.QScrollArea()
        self.scrollArea.setWidget(self.main_widget)
        self.scrollArea.setWidgetResizable(True)
        self.setCentralWidget(self.scrollArea)
        # Setup stylesheet
        self.scrollArea.setStyleSheet("background:rgb(70, 80, 88)")
        # Configure the menu bar
        menubar = self.menuBar()
        menubar.setStyleSheet("QMenuBar {background-color: rgb(189, 195, 199)}"
                "QMenuBar::item {background: transparent} QMenu{background-color:rgb(189, 195, 199)}")
        # Menu bar menus
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
        # Keeps track of the number of widgets, used for placing tiles into the correct column
        numWidgets = 0
        # Configure the size policy of all tiles
        frameSizePolicy = QtGui.QSizePolicy()
        frameSizePolicy.setVerticalPolicy(4)
        frameSizePolicy.setHorizontalPolicy(QtGui.QSizePolicy.Preferred)
        # Configure the layouts
        self.mainVBox.append(QtGui.QVBoxLayout())
        self.mainVBox.append(QtGui.QVBoxLayout())
        self.mainHBox.addLayout(self.mainVBox[0])
        self.mainHBox.addLayout(self.mainVBox[1])
        # Which column are we adding a tile to next
        self.VBoxColumn = 0
        # For each device
        for i in range(len(web.devices)):
            # Add a QFrame, this is the border, and the parent of all gui elements that go inside.
            self.tiles.append(QtGui.QFrame(self))
            # Switch off adding tiles to columns
            if self.VBoxColumn == 0:
                self.VBoxColumn = 1
            else:
                self.VBoxColumn = 0
            self.mainVBox[self.VBoxColumn].addWidget(self.tiles[i])
            # Add new titles, grids, parameters, 
            # and lcds for the new parameter
            self.titles.append(QtGui.QLabel(self.tiles[i]))
            self.grids.append(QtGui.QGridLayout())
            self.parameters.append([])
            self.lcds.append([])
            self.units.append([])
            self.buttons.append([])
            # Configure grid layout
            self.grids[i].setSpacing(10)
            self.grids[i].addWidget(self.titles[i], 1, 0)
            self.grids[i].setColumnStretch(0,1)
            # Configure the tile (the box surrounding 
            # information for each device)
            self.tiles[i].setSizePolicy(frameSizePolicy)
            self.tiles[i].setStyleSheet("background: rgb(52, 73, 94)")
            self.tiles[i].setFrameShape(QtGui.QFrame.Panel)
            self.tiles[i].setFrameShadow(QtGui.QFrame.Plain)
            self.tiles[i].setSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
            # Used for dpi scaling (works pretty well but not amazing)
            if self.scrnWidth>self.scrnHeight:
                web.ratio =float(self.scrnWidth)/1800+1
            else:
                web.ratio =float(self.scrnHeight)/1800+1
            self.tiles[i].setLineWidth(web.ratio)
            self.tiles[i].setLayout(self.grids[i])
            # Configure the layout of the buttons within the grid
            buttonLayout = QtGui.QHBoxLayout()
            self.grids[i].addLayout(buttonLayout, 1, 1)
            # Create all buttons.
            if(len(web.devices[i].getFrame().getButtons()[0])>0):
                for b in range(0, len(web.devices[i]
                    .getFrame().getButtons())):
                    # Append a new button to the array of buttons and 
                    # set the parent as the current frame
                    self.buttons[i].append(QtGui
                        .QPushButton(self.tiles[i]))
                    # Set the text of the button to the name specified 
                    # when the device was initialized                   
                    self.buttons[i][b].setText(web.devices[i]
                        .getFrame().getButtons()[b][0])
                    # Add the button to the screen.
                    buttonLayout.addWidget(self.buttons[i][b])
                    # Connect the button to function, 
                    # passing the number of the button that was clicked
                    self.buttons[i][b].clicked.connect(partial(web
                        .devices[i].prompt, b))
                    # Make the button pretty
                    self.buttons[i][b].setStyleSheet("color:rgb(189," 
                        "195, 199); background:rgb(70, 80, 88)")
                    self.buttons[i][b].setFont(self.font)   
            # Make the titles look nice
            self.titles[i].setStyleSheet("color:rgb(189, 195, 199);")
            self.font.setPointSize(18)
            self.titles[i].setFont(self.font)
            self.font.setPointSize(12)
            # Get the title of the device
            self.titles[i].setText(web.devices[i].getFrame().getTitle())
            self.titles[i].setGeometry(QtCore.QRect(10,10,self.titles[i]
                .fontMetrics().boundingRect(self.titles[i]
                    .text()).width(),40))
            for y in range(0, len(web.devices[i].getFrame().getNicknames())):
                # Add a new parameter to the current device
                self.parameters[i].append(QtGui.QLabel(self.tiles[i]))
                self.units[i].append(QtGui.QLabel(self.tiles[i]))
                #Get the width of the text
                self.parameters[i][y].setFont(self.font)
                self.parameters[i][y].setAlignment(QtCore.Qt.AlignLeft)
                self.units[i][y].setFont(self.font)
                self.units[i][y].setAlignment(QtCore.Qt.AlignRight)
                # Configure the QLCDnumber widgets that display information
                self.lcds[i].append(QtGui.QLCDNumber())
                self.lcds[i][y].setNumDigits(11)
                self.lcds[i][y].setSegmentStyle(QtGui.QLCDNumber.Outline)
                self.lcds[i][y].display("-")
                self.lcds[i][y].setFrameShape(QtGui.QFrame.Panel)
                self.lcds[i][y].setFrameShadow(QtGui.QFrame.Plain)
                self.lcds[i][y].setLineWidth(web.ratio)
                self.lcds[i][y].setMidLineWidth(100)
                self.lcds[i][y].setStyleSheet("color:rgb(189, 195, 199);\n")
                self.lcds[i][y].setFixedHeight(self.scrnHeight/30)
                self.lcds[i][y].setMinimumWidth(self.scrnWidth/7)
                # Make the parameters pretty
                self.parameters[i][y].setWordWrap(True)
                self.parameters[i][y].setStyleSheet("color:rgb(189, 195, 199);")    
                # Hide everything until we know that it should be displayed.
                # This is essential to be able to handle arrays
                self.parameters[i][y].hide()
                self.lcds[i][y].hide()
                self.units[i][y].hide()
                # If a nickname for the setting has been defined, 
                # go ahead and display whatever is necessary
                if(web.devices[i].getFrame().getNicknames()[y] is not None):
                    self.parameters[i][y].show()
                    self.lcds[i][y].show()
                    self.units[i][y].show()
                    self.parameters[i][y].setText(devices[i].getFrame()
                        .getNicknames()[y])
                    self.grids[i].addWidget(self.parameters[i][y], y+2, 0)
                    lcdHBoxLayout = QtGui.QHBoxLayout()
                    lcdHBoxLayout.addStretch(1)
                    lcdHBoxLayout.addWidget(self.lcds[i][y])
                    
                    self.grids[i].addLayout(lcdHBoxLayout, y+2, 1)
                    self.grids[i].addWidget(self.units[i][y], y+2, 2)
            # Configure the plots
            if (web.devices[i].getFrame().isPlot()):
                dc = MGrapher.mGraph(web.devices[i])
                yPos = len(web.devices[i].getFrame().getNicknames())+3
                web.devices[i].getFrame().setPlot(dc)
                self.grids[i].addWidget(dc, yPos, 0,yPos,3 )
                
        self.mainVBox[0].addStretch(0)
        self.mainVBox[1].addStretch(0)
        print("Gui initialized")

    def mousePressEvent(self, event):
        focused_widget = QtGui.QApplication.focusWidget()
        if isinstance(focused_widget, QtGui.QScrollArea):
            focused_widget.clearFocus()
        QtGui.QMainWindow.mousePressEvent(self, event)

    def stop(self):
        '''Stop and close mView cleanly'''
        print "Closing mView"
        self.keepGoing = False
        exit()
        
    def openNotifierSettings(self):
        '''Open the notifier settings gui'''
        # NOTE, this is run on the main thread, so while it is open the main
        # GUI will not be running.
        self.NotifierGUI = NotifierGUI()
        self.NotifierGUI.exec_()

    def setRefreshRate(self, period):
        web.guiRefreshRate = period

    def openConfig(self):
        self.Config = ConfigGui(self)
        self.Config.exec_()

    def startGui(self, devices, title, dataTitle, tele):
        '''Start the GUI'''
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
        # Call the class's init function
        self.initGui(devices)
        self.setWindowTitle(title)
        # Show the gui
        self.show()
        self.timer = QtCore.QTimer(self)
        # Update the gui every so often. This CAN ONLY be done 
        # in the main thread.
        self.timer.singleShot(web.guiRefreshRate*1000, self.update)
        #self.MAlert.begin()
        QtGui.QApplication.focusWidget().clearFocus()
        sys.exit(app.exec_())

    def update(self):
        '''Update the GUI.'''
        error = False
        # Loop through all devices.
        for i in range(len(web.devices)):
            # If there is no error with the device.
            if not web.devices[i].getFrame().isError():
                # Get the readings from the frame.
                readings = web.devices[i].getFrame().getReadings()
                precisions = web.devices[i].getFrame().getPrecisions()
                if readings is not None:
                    # Update all QLcds with the reading.
                    for y in range(len(web.devices[i].getFrame().getOutOfRangeStatus())):
                        # Check if the reading is out of range.
                        outOfRange = web.devices[i].getFrame().getOutOfRangeStatus()
                        # The key for a reading is "device:param".
                        key = web.devices[i].getFrame().getTitle()+":"+web.devices[i].getFrame().getNicknames()[y] 
                        # Check if the specific reading is out of range.
                        if outOfRange[key]:
                            # If the reading is out of range, make everything orange
                            self.lcds[i][y].setStyleSheet("color:rgb(200, 100, 50);\n")
                            self.units[i][y].setStyleSheet("color:rgb(200, 100, 50);\n")
                            self.parameters[i][y].setStyleSheet("color:rgb(200, 100, 50);\n")
                        else:
                            pass
                            # Otherwise, things should be white.
                            self.lcds[i][y].setStyleSheet("color:rgb(189, 195, 199);\n") 
                            self.units[i][y].setStyleSheet("color:rgb(189, 195, 199);\n") 
                            self.parameters[i][y].setStyleSheet("color:rgb(189, 195, 199);\n") 
                    for y in range(len(web.devices[i].getFrame().getNicknames())):
                        # Segments should be flat
                        self.lcds[i][y].setSegmentStyle(QtGui.QLCDNumber.Flat)
                        try:
                            # If the readings are not nan, then display
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
                            pass
                        # If there are units, put them next to the number.
                        if web.devices[i].getFrame().getUnits():
                            self.units[i][y].setText(web.devices[i]
                                .getFrame().getUnits()[y])
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
            self.timer.singleShot(web.guiRefreshRate*1000, self.update)
        return
            
app=QtGui.QApplication(sys.argv)



