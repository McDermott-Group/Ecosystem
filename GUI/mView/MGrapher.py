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
__version__ = "2.0.2"
__maintainer__ = "Noah Meltzer"
__status__ = "Beta"

import numpy as np
import datetime as dt
import sys
from PyQt4 import QtGui, QtCore
from functools import partial
import matplotlib
from matplotlib.dates import DateFormatter, AutoDateLocator
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt
matplotlib.use('TkAgg')

from dateStamp import *
from dataChest import *
from MCheckableComboBoxes import MCheckableComboBox


class mGraph(QtGui.QWidget):
    def __init__(self, device, parent=None):
        QtGui.QWidget.__init__(self, parent)
        # Create a matplotlib figure.
        self.figure = plt.figure()
        self.figure.set_facecolor('r')
        # Create a QFrame to house the plot. This is not necessary,
        # just makes it look nice.
        self.matframe = QtGui.QFrame()
        self.matLayout = QtGui.QVBoxLayout()
        self.matLayout.setSpacing(0)
        self.matframe.setLayout(self.matLayout)
        self.matframe.setFrameShape(QtGui.QFrame.Panel)
        self.matframe.setFrameShadow(QtGui.QFrame.Plain)
        self.matframe.setStyleSheet("background-color: rgb(70,80,88); "
                "margin:0px; border:2px solid rgb(0, 0, 0); ")
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(QtGui.QSizePolicy.Preferred, 
            QtGui.QSizePolicy.Preferred)
        # This is the device we want to use.
        self.device = device
        # This sets up axis on which to plot.
        color = (189./255, 195./255, 199./255)
        self.ax = self.figure.add_subplot(111, axisbg=color)
        ax = self.ax
        # Add the matplotlib canvas to the QFrame.
        self.matLayout.addWidget(self.canvas)
        # The following lines set up all the colors, makes it look nice.
        # The code to do it is far from pretty and I am planning
        # on cleaning this up a bit.
        self.figure.patch.set_color((70./255, 80./255, 88./255))
        self.figure.patch.set_edgecolor((70./255, 80./255, 88./255))
        ax.spines['bottom'].set_color(color)
        ax.spines['top'].set_color(color) 
        ax.spines['right'].set_color(color)
        ax.spines['left'].set_color(color)
        ax.tick_params(axis='x', colors=color)
        ax.tick_params(axis='y', colors=color)
        ax.title.set_color(color)
        ax.yaxis.label.set_color(color)
        ax.xaxis.label.set_color(color)
        ax.xaxis.get_offset_text().set_color(color)
        ax.yaxis.get_offset_text().set_color(color)
        # This is an array of all the lines on the plot. A line for
        # every parameter.
        self.line = []
        self.mins = 0
        self.maxes = 1
        # Each element of line holds a plot, to be combined onto
        # the same graph.
        self.line.append(ax.plot(1, 1, label="Getting Data...")[0])

        # In order to handle interactivity, I had to do some odd stuff
        # with the toolbar buttons: self.home holds the original
        # function called when the home button on the toolbar
        # is clicked.
        self.home = NavigationToolbar.home
        # We now change the function that is called when the toolbar is
        # clicked.
        NavigationToolbar.home = self.enableAutoScaling
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.cid = self.canvas.mpl_connect('button_press_event',
                self.disableAutoScaling)
        self.setStyleSheet("QPushButton{\
                    color:rgb(189,195, 199); \
                    background:rgb(70, 80, 88)};")
        self.toolbarFrame = QtGui.QFrame()
        toolbarFrameLayout = QtGui.QVBoxLayout()
        toolbarFrameLayout.addWidget(self.toolbar)
        self.toolbar.setParent(None)
        self.toolbarFrame.setLayout(toolbarFrameLayout)
        self.toolbarFrame.setStyleSheet("\
                    border:2px solid rgb(0,0,0);\
                    color:rgb(189,195,199); \
                    background:rgb(70, 80, 88);")
        self.toolbar.setStyleSheet("\
                    border:0px solid rgb(0,0,0);\
                    QDialog{background:rgb(250, 80, 88)}")
        self.matPlotInfo = QtGui.QLabel()
        self.alertFont = QtGui.QFont()
        self.alertFont.setPointSize(12)
        self.matPlotInfo.setStyleSheet("color:rgb(200, 69, 50);")
        self.matPlotInfo.setText("Auto refresh disabled, "
                                 "click HOME button to enable.")
        self.matPlotInfo.setFont(self.alertFont)
        
        self.refreshRateSec = device.getFrame().getPlotRefreshRate()
        self.timer = QtCore.QTimer(self)
        
        self.hidden = True
        self.home = True
        self.initialized = False
        self.currTimeRange = 120
        self.lineSelect = MCheckableComboBox()
        self.lineSelect.setSizeAdjustPolicy(0)
        self.lineSelect.setStyleSheet("\
                    background-color:rgb(70, 80, 88);\
                    color:rgb(189,195, 199);")       
        self.plot(self.currTimeRange)

        self.timer.timeout.connect(partial(self.plot, self.currTimeRange))
        self.timer.start(self.refreshRateSec * 1000)

        # Did it store data?
        self.dataOk = True
        self.hideButton = QtGui.QPushButton("Show Plot")
        self.hideButton.clicked.connect(self.togglePlot)
        self.oneMinButton = QtGui.QPushButton("1 min")
        self.oneMinButton.clicked.connect(partial(self.plot, 60))
        self.tenMinButton = QtGui.QPushButton("10 min")
        self.tenMinButton.clicked.connect(partial(self.plot, 600))
        self.twoHrButton = QtGui.QPushButton("2 hr")
        self.twoHrButton.clicked.connect(partial(self.plot, 7200))
        self.twelveHrButton = QtGui.QPushButton("12 hr")
        self.twelveHrButton.clicked.connect(partial(self.plot, 43200))
        self.threeDayButton = QtGui.QPushButton("3 day")
        self.threeDayButton.clicked.connect(partial(self.plot, 259200))
        self.oneWkButton = QtGui.QPushButton("1 week")
        self.oneWkButton.clicked.connect(partial(self.plot, 604800))
        self.allButton = QtGui.QPushButton("All Time")
        self.allButton.clicked.connect(partial(self.plot, None))

        self.canvas.hide()
        self.toolbar.hide()

        # Set the layout.
        buttonLayout1 = QtGui.QHBoxLayout()
        buttonLayout1.addWidget(self.hideButton)
        buttonLayout1.addStretch(0)
        buttonLayout2 = QtGui.QHBoxLayout()
        settingsbuttons1 = QtGui.QHBoxLayout()

        buttonLayout2.addWidget(self.oneMinButton)
        buttonLayout2.addWidget(self.tenMinButton)
        buttonLayout2.addWidget(self.twoHrButton)
        buttonLayout2.addWidget(self.twelveHrButton)
        buttonLayout2.addWidget(self.threeDayButton)
        buttonLayout2.addWidget(self.oneWkButton)
        buttonLayout2.addWidget(self.allButton)
        buttonLayout2.addStretch(0)
        self.oneMinButton.hide()
        self.tenMinButton.hide()
        self.twoHrButton.hide()
        self.twelveHrButton.hide()
        self.threeDayButton.hide()
        self.oneWkButton.hide()
        self.allButton.hide()
        self.lineSelect.hide()
        self.matframe.hide()
        self.matPlotInfo.hide()
        self.toolbarFrame.hide()
        
        settingsbuttons1.addWidget(self.lineSelect)
        layout = QtGui.QVBoxLayout()
        allButtonsLayout = QtGui.QHBoxLayout()
        timeButtonsLayout = QtGui.QVBoxLayout()
        allButtonsLayout.addLayout(timeButtonsLayout)
        layout.addLayout(allButtonsLayout)
        allButtonsLayout.addLayout(settingsbuttons1)
        timeButtonsLayout.addLayout(buttonLayout1)
        timeButtonsLayout.addLayout(buttonLayout2)
        timeButtonsLayout.addWidget(self.matPlotInfo)
        layout.addWidget(self.matframe)
        layout.addWidget(self.toolbarFrame)

        self.setLayout(layout)

    def enableAutoScaling(self):
        self.timer.start(self.refreshRateSec * 1000)
        self.home = True
        self.matPlotInfo.hide()        
        self.plot(self.currTimeRange)

    def disableAutoScaling(self, event):
        self.home = False
        self.matPlotInfo.show()
        self.canvas.update()
        self.timer.stop()

    def togglePlot(self):    
        if not self.hidden:
            self.canvas.hide()
            self.toolbar.hide()
            self.oneMinButton.hide()
            self.tenMinButton.hide()
            self.twoHrButton.hide()
            self.twelveHrButton.hide()
            self.threeDayButton.hide()
            self.oneWkButton.hide()
            self.allButton.hide()
            self.matPlotInfo.hide()
            self.matframe.hide()
            self.lineSelect.hide()
            self.toolbarFrame.hide()
            self.timer.stop()
            self.hideButton.setText("Show Plot")
            self.hidden = True
        elif self.hidden:
            self.canvas.show()
            self.toolbar.show()
            self.oneMinButton.show()
            self.tenMinButton.show()
            self.twoHrButton.show()
            self.twelveHrButton.show()
            self.threeDayButton.show()
            self.oneWkButton.show()
            self.allButton.show()
            self.plot(self.currTimeRange)
            self.matframe.show()
            self.lineSelect.show()
            self.toolbarFrame.show()
            self.timer.start(self.refreshRateSec * 1000)
            self.hideButton.setText("Hide Plot")
            self.enableAutoScaling()
            self.hidden = False

    def initializePlot(self, dataSet):
        if dataSet:
            varNames = dataSet.getVariables()
            varNames = [varNames[1][i][0] for i in range(len(varNames[1]))]
            self.dropdownFont = QtGui.QFont()
            self.dropdownFont.setPointSize(12)
        if dataSet is not None:
            self.initialized = True
            self.line[0].remove()
            self.line = []

            for i in range(len(varNames)):
               self.line.append(self.ax.plot(1, 1, label=varNames[i])[0])
               text = QtCore.QString(varNames[i])
               self.lineSelect.addItem(text)
               self.lineSelect.setFont(self.dropdownFont)
               self.lineSelect.setChecked(i, True)

    def changeIndependenVarRange(self, timeRange):
        if not self.hidden:
            if timeRange != self.currTimeRange:
                self.timer.stop()
                self.timer.timeout.disconnect()
                self.currTimeRange = timeRange
                self.timer.timeout.connect(lambda:
                        self.plot(self.currTimeRange))
                self.timer.start(self.refreshRateSec * 1000)
            plotRefreshRate = self.device.getFrame().getPlotRefreshRate()
            if self.refreshRateSec != plotRefreshRate:
                self.refreshRateSec = plotRefreshRate
                self.timer.stop()
                self.timer.timeout.disconnect()
                self.currTimeRange = timeRange
                self.timer.timeout.connect(lambda:
                        self.plot(self.currTimeRange))
                self.timer.start(self.refreshRateSec * 1000)

    def getDataRangeFromDataSet(self, dataSet, time):
        if dataSet:
            data = dataSet.getData()
            i = len(data) - 1
            if time:
                while data[i][0] > (data[-1][0] - time):
                    i -= 1
                    if -1 * i > len(data):
                        return data
                data = data[i:-1]
                dataT = np.transpose(data)
            return data
        else:
            return None

    def plot(self, time):
            times = None
            self.changeIndependenVarRange(time)
            dataSet = self.device.getFrame().getDataSet()

            if not self.initialized:
                self.initializePlot(dataSet)
                self.legend = self.ax.legend(loc='upper left')
                # This is the ONLY time canvas.draw is called. It should
                # NOT be called anywhere else if the graphing speed is
                # to be fast.
                self.canvas.draw()
            else:
                data = self.getDataRangeFromDataSet(dataSet, time)
                #print data
                for i in range(len(data[0])-1):
                    if self.lineSelect.isChecked(i):
                        times = [dt.datetime.fromtimestamp(row[0])
                                 for row in data]
                        column = [row[i+1] for row in data]
                        if not self.line[i].get_visible():
                            self.line[i].set_visible(True)
                        self.line[i].set_data(times,column)
                        self.legend = self.ax.legend(loc='upper left')
                        self.ax.grid(True)
                        self.ax.hold(True)
                    else:
                        self.line[i].set_visible(False);
                    pass
                self.ax.set_title(self.device.getFrame().getTitle(),
                        color=(189./255, 195./255, 199./255))
                if self.home and times:
                    self.ax.set_xlim(times[0], times[-1])
                    self.ax.relim(visible_only=True)
                    self.ax.autoscale(axis='y')
                
                frame = self.device.getFrame()
                yLabel = frame.getYLabel()
                if yLabel is not None:
                    if frame.getCustomUnits():
                        self.ax.set_ylabel("%s (%s)" %(yLabel, 
                                frame.getCustomUnits()))
                    elif frame.getUnits()[i-1]:
                        self.ax.set_ylabel("%s (%s)" %(yLabel,
                                frame.getUnits()[i-1]))

                locator = AutoDateLocator()

                self.ax.xaxis.set_major_locator(locator)
                self.ax.xaxis.set_major_formatter(DateFormatter('%m/%d %H:%M:%S'))
                self.figure.autofmt_xdate()
                self.ax.draw_artist(self.figure)
                self.ax.draw_artist(self.ax.patch)
                self.ax.draw_artist(self.ax.yaxis)
                self.ax.draw_artist(self.ax.xaxis)

                for i, line in enumerate(self.line):
                        self.ax.draw_artist(line)   

                self.ax.set_xlabel("Time")
                self.ax.draw_artist(self.legend)
                    
                self.canvas.update()
                
                self.canvas.flush_events()