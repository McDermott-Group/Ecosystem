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

"""
description = Creates the plots seen on GUI.
"""

import sys
sys.dont_write_bytecode = True

from PyQt4 import QtGui, QtCore

from functools import partial

from dateStamp import *
from dataChest import *

import datetime
import time
import matplotlib

from matplotlib.dates import DateFormatter, AutoDateFormatter, AutoDateLocator
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt
matplotlib.use('TkAgg')

import threading
import traceback

import numpy as np

from MWeb import web
from MCheckableComboBoxes import  MCheckableComboBox

class mGraph(QtGui.QWidget):
    def __init__(self, device, parent=None):
        QtGui.QWidget.__init__( self,parent)
        # Create a matplotlib figure
        self.figure = plt.figure()
        self.figure.set_facecolor('r')
        # Create a QFrame to house the plot. This is not necessary, just makes it look nice
        self.matframe = QtGui.QFrame()
        self.matLayout = QtGui.QVBoxLayout()
        self.matLayout.setSpacing(0)
        self.matframe.setLayout(self.matLayout)
        self.matframe.setFrameShape(QtGui.QFrame.Panel)
        self.matframe.setFrameShadow(QtGui.QFrame.Plain)
        self.matframe.setStyleSheet("background-color: rgb(70,80,88); margin:0px; border:2px solid rgb(0, 0, 0); ")
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(QtGui.QSizePolicy.Preferred, 
            QtGui.QSizePolicy.Preferred)
        # This is the device we want to use
        self.device = device
        # This sets up axis on which to plot
        self.ax = self.figure.add_subplot(111, axisbg = (189.0/255, 195.0/255, 199.0/255))
        # Add the matplotlib canvas to the QFrame
        self.matLayout.addWidget(self.canvas)
        # The following lines set up all the colors, makes it look nice. The code to do it is
        # far from pretty and I am planning on cleaning this up a bit.
        self.figure.patch.set_color((70.0/255, 80.0/255, 88.0/255))
        self.figure.patch.set_edgecolor((70.0/255, 80.0/255, 88.0/255))
        self.ax.spines['bottom'].set_color((189.0/255, 195.0/255, 199.0/255))
        self.ax.spines['top'].set_color((189.0/255, 195.0/255, 199.0/255)) 
        self.ax.spines['right'].set_color((189.0/255, 195.0/255, 199.0/255))
        self.ax.spines['left'].set_color((189.0/255, 195.0/255, 199.0/255))
        self.ax.tick_params(axis='x', colors=(189.0/255, 195.0/255, 199.0/255))
        self.ax.tick_params(axis='y', colors=(189.0/255, 195.0/255, 199.0/255))
        self.ax.title.set_color((189.0/255, 195.0/255, 199.0/255))
        self.ax.yaxis.label.set_color((189.0/255, 195.0/255, 199.0/255))
        self.ax.xaxis.label.set_color((189.0/255, 195.0/255, 199.0/255))
        self.ax.xaxis.get_offset_text().set_color((189.0/255, 195.0/255, 199.0/255))
        self.ax.yaxis.get_offset_text().set_color((189.0/255, 195.0/255, 199.0/255))
        # This is an array of all the lines on the plot. A line for every parameter
        self.line = []
        #self.legend = self.ax.legend(loc='upper left')
        self.mins = 0
        self.maxes = 1
        # Each element of line holds a plot, to be combined onto the same graph
        self.line.append(self.ax.plot(1,1, label = "Getting Data...")[0])

        # In order to handle interactivity, I had to do some odd stuff with the
        # toolbar buttons. Self.home holds the original function called when the home button on the toolbar
        # is clicked.
        self.home = NavigationToolbar.home
        # We now change the function that is called when the toolbar is clicked.
        NavigationToolbar.home = self.enableAutoScaling
        self.toolbar = NavigationToolbar(self.canvas, self)
        #print [item for item in dir(self.toolbar) if type(item) == QtGui.QDialog]
        self.cid = self.canvas.mpl_connect('button_press_event', self.disableAutoScaling)
        self.setStyleSheet("QPushButton{\
                    color:rgb(189,195, 199); \
                    background:rgb(70, 80, 88)};\
                    ")
        self.toolbarFrame = QtGui.QFrame()
        toolbarFrameLayout = QtGui.QVBoxLayout()
        toolbarFrameLayout.addWidget(self.toolbar)
        self.toolbar.setParent(None)
        self.toolbarFrame.setLayout(toolbarFrameLayout)
        self.toolbarFrame.setStyleSheet("\
                    border:2px solid rgb(0,0,0);\
                    color:rgb(189,195,199); \
                    background:rgb(70, 80, 88);\
                    ")
        self.toolbar.setStyleSheet("\
                    border:0px solid rgb(0,0,0);\
                    QDialog{background:rgb(250, 80, 88)}\
                    ")
        #print dir(self.toolbar)
        #print self.toolbar.children()
       # print self.toolbar.setPalette
        self.matPlotInfo = QtGui.QLabel()
        self.alertFont = QtGui.QFont()
        self.alertFont.setPointSize(12)
        self.matPlotInfo.setStyleSheet(
                                "color:rgb(200, 69, 50);")
        self.matPlotInfo.setText("Auto refresh disabled, click HOME button to enable.")
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
        self.timer.start(self.refreshRateSec*1000)
        #print "initializing lineselect"
       
        #did it store data?
        self.dataOk = True
        self.hideButton = QtGui.QPushButton("Show Plot")
        self.hideButton.clicked.connect(self.togglePlot)
        self.thrtysecButton = QtGui.QPushButton("30 Sec")
        self.thrtysecButton.clicked.connect(partial(self.plot, 30))
        self.twoMinButton = QtGui.QPushButton("2 Min")
        self.twoMinButton.clicked.connect(partial(self.plot, 120))
        self.fiveMinButton = QtGui.QPushButton("5 Min")
        self.fiveMinButton.clicked.connect(partial(self.plot, 300))
        self.thrtyMinButton = QtGui.QPushButton("30 Min")
        self.thrtyMinButton.clicked.connect(partial(self.plot, 1800))
        self.twoHrButton = QtGui.QPushButton("2 Hr")
        self.twoHrButton.clicked.connect(partial(self.plot, 7200))
        self.tenHrButton = QtGui.QPushButton("10 Hr")
        self.tenHrButton.clicked.connect(partial(self.plot, 36000))
        self.oneDayButton = QtGui.QPushButton("24 Hr")
        self.oneDayButton.clicked.connect(partial(self.plot, 86400))
        self.oneWkButton = QtGui.QPushButton("1 Wk")
        self.oneWkButton.clicked.connect(partial(self.plot, 604800))
        self.twoWkButton = QtGui.QPushButton("2 Wk")
        self.twoWkButton.clicked.connect(partial(self.plot, 1209600))
        self.allButton = QtGui.QPushButton("All Time")
        self.allButton.clicked.connect(partial(self.plot, None))
        
        
        self.canvas.hide()
        self.toolbar.hide()

        # set the layout
        
        buttonLayout = QtGui.QHBoxLayout()
        buttonLayout.addWidget(self.hideButton)
        buttonLayout.addStretch(0)
        buttonLayout2 = QtGui.QHBoxLayout()
        settingsbuttons1 = QtGui.QHBoxLayout()
        
        buttonLayout3 = QtGui.QHBoxLayout()

        buttonLayout2.addWidget(self.thrtysecButton)
        buttonLayout2.addWidget(self.twoMinButton)
        buttonLayout2.addWidget(self.fiveMinButton)
        buttonLayout2.addWidget(self.thrtyMinButton)
        buttonLayout2.addWidget(self.twoHrButton)
        buttonLayout2.addStretch(0)
        buttonLayout3.addWidget(self.tenHrButton)
        buttonLayout3.addWidget(self.oneDayButton)
        buttonLayout3.addWidget(self.oneWkButton)
        buttonLayout3.addWidget(self.twoWkButton)
        buttonLayout3.addWidget(self.allButton)
        buttonLayout3.addStretch(0)
        self.thrtysecButton.hide()
        self.twoMinButton.hide()
        self.fiveMinButton.hide()
        self.thrtyMinButton.hide()
        self.twoHrButton.hide()
        self.tenHrButton.hide()
        self.oneDayButton.hide()
        self.oneWkButton.hide()
        self.twoWkButton.hide()
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
        timeButtonsLayout.addLayout(buttonLayout)
        timeButtonsLayout.addLayout(buttonLayout2)
        timeButtonsLayout.addLayout(buttonLayout3)
        timeButtonsLayout.addWidget(self.matPlotInfo)
        layout.addWidget(self.matframe)
        layout.addWidget(self.toolbarFrame)
        

        self.setLayout(layout)
        
     
    def enableAutoScaling(self):
        self.timer.start(self.refreshRateSec*1000)
        #self.canvas.mpl_disconnect(self.cid)
        #self.cid = self.canvas.mpl_connect('button_press_event', self.disableAutoScaling)
        self.home = True
        self.matPlotInfo.hide()
        # self.deviceThread = threading.Thread(target = 
            # self.plot, args=[self.currTimeRange])
        # If the main thread stops, stop the child thread
        # self.deviceThread.daemon = True
        # Start the thread
        # self.deviceThread.start()
        
        self.plot(self.currTimeRange)
    def disableAutoScaling(self, event):
        self.home = False
        self.matPlotInfo.show()
        self.canvas.update()
        #plt.show()
        #print event.name
        #self.canvas.mpl_disconnect(self.cid)
        #self.cid = self.canvas.mpl_connect('button_press_event', self.enableAutoScaling)
        self.timer.stop()
        #self.zoom(self.toolbar)
    def togglePlot(self):
    
        if not self.hidden:
            self.canvas.hide()
            self.toolbar.hide()
            self.thrtysecButton.hide()
            self.twoMinButton.hide()
            self.fiveMinButton.hide()
            self.thrtyMinButton.hide()
            self.twoHrButton.hide()
            self.tenHrButton.hide()
            self.oneDayButton.hide()
            self.oneWkButton.hide()
            self.twoWkButton.hide()
            self.allButton.hide()
            self.matPlotInfo.hide()
            self.matframe.hide()
            self.lineSelect.hide()
            self.toolbarFrame.hide()
            self.timer.stop()
            self.hideButton.setText("Show Plot")
            self.hidden = True
            
        elif  self.hidden:
            self.canvas.show()
            self.toolbar.show()
            self.thrtysecButton.show()
            self.twoMinButton.show()
            self.fiveMinButton.show()
            self.thrtyMinButton.show()
            self.twoHrButton.show()
            self.tenHrButton.show()
            self.oneDayButton.show()
            self.oneWkButton.show()
            self.twoWkButton.show()
            self.allButton.show()
            self.plot(self.currTimeRange)
            self.matframe.show()
            self.lineSelect.show()
            self.toolbarFrame.show()
            self.timer.start(self.refreshRateSec*1000)
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
             #data = dataSet.getData()
             self.line[0].remove()
             self.line = []
             for i in  range(len(varNames)):
                #print varNames
                self.line.append(self.ax.plot(1,1, label = varNames[i])[0])
                text = QtCore.QString(varNames[i])
                #print "using Lineselect"
                self.lineSelect.addItem(text)
                self.lineSelect.setFont(self.dropdownFont)
                self.lineSelect.setChecked(i, True)

    def changeIndependenVarRange(self, timeRange):
        if not self.hidden:
            if timeRange != self.currTimeRange:
                self.timer.stop()
                self.timer.timeout.disconnect()
                self.currTimeRange = timeRange
                self.timer.timeout.connect(lambda: self.plot( self.currTimeRange))
                self.timer.start(self.refreshRateSec*1000)
            if self.refreshRateSec != self.device.getFrame().getPlotRefreshRate():
                #print "New plot refresh rate: ", self.device.getFrame().getPlotRefreshRate()
                self.refreshRateSec = self.device.getFrame().getPlotRefreshRate()
                self.timer.stop()
                self.timer.timeout.disconnect()
                self.currTimeRange = timeRange
                self.timer.timeout.connect(lambda: self.plot( self.currTimeRange))
                self.timer.start(self.refreshRateSec*1000)
    #def getData(self, dataSet):
    def getDataRangeFromDataSet(self, dataSet, time):
        if dataSet:
            data = dataSet.getData()
            i = len(data)-1;
            while data[i][0]>(data[-1][0]-time):
                
                i-=1
            data = data[i:-1]
            #print data
            dataT = np.transpose(data)
          
          
            return  data
            #colums = [data[i][:] for i in range]
           # print "times: ",dataTup = 
        else:
            return None
    def plot(self, time):
            times = None
            self.changeIndependenVarRange(time)
            dataSet =  self.device.getFrame().getDataSet()
            
            if not self.initialized:
                self.initializePlot(dataSet)
                self.legend = self.ax.legend(loc='upper left')
                # This is the ONLY time canvas.draw is called. It should NOT be called anywhere else if
                # the graphing speed is to be fast.
                self.canvas.draw()
            else:
                
                data = self.getDataRangeFromDataSet(dataSet, time)
                #data = 
                #data = dataSet.getData()
                for i in range(len(data[0])-1):
                    #print dataT
                    #print "len(dataT):", len(dataT)
                   # print "len(dataT["+str(i+1)+"]:", len(dataT[i+1])
                  
                    #print "i", i
                    #print len(self.line)
                    if self.lineSelect.isChecked(i):
                        
                        #print self.line[i]
                        #datetime.datetime.fromtimestamp(dataT[0])
                        #self.line[i](self.ax.plot(1,1, label = dataSet.getVariables()[1][i-1][0])[0])
                        times = [datetime.datetime.fromtimestamp(row[0]) for row in data]
                        column = [row[i+1] for row in data]
                        #print "times: ", len(times)
                        #print "dataT: ", len(dataT[i+1])
                        if not self.line[i].get_visible():
                            self.line[i].set_visible(True)
                        self.line[i].set_data(times,column)
                        self.legend = self.ax.legend(loc='upper left')
                        self.ax.grid(True)
                        self.ax.hold(True)
                        #self.ax.plot_date(times, \
                         #   column, \
                           # label = dataSet.getVariables()[1][i-1][0])
                    else:
                        self.line[i].set_visible(False);
                    pass
                self.ax.set_title(self.device.getFrame().getTitle(), color = (189.0/255, 195.0/255, 199.0/255))
                if self.home and times:
                    #print times[0]
                    #print times[-1]
                    self.ax.set_xlim(times[0], times[-1])
                    #self.ax.set_ylim(self.mins, self.maxes)
                    self.ax.relim(visible_only=True)
                    self.ax.autoscale(axis = 'y')
                
                if(self.device.getFrame().getYLabel() is not None 
                    and len(self.device.getFrame().getCustomUnits()) is not 0):
                    self.ax.set_ylabel(self.device.getFrame().getYLabel()+" ("+
                            self.device.getFrame().getCustomUnits()+")")
                elif (self.device.getFrame().getYLabel() is not None 
                    and len(self.device.getFrame().getUnits()[i-1]) is not 0):
                    
                    self.ax.set_ylabel(self.device.getFrame().getYLabel()+" ("+
                            self.device.getFrame().getUnits()[i-1]+")")
                                    
                locator = AutoDateLocator()
                    
                self.ax.xaxis.set_major_locator(locator)
                self.ax.xaxis.set_major_formatter(DateFormatter('%m/%d %H:%M:%S'))
                self.figure.autofmt_xdate()
                #print [time.toordinal() for time in times]
                self.ax.draw_artist(self.figure)
                self.ax.draw_artist(self.ax.patch)
                self.ax.draw_artist(self.ax.yaxis)
                self.ax.draw_artist(self.ax.xaxis)
                
                #print self.line
                
                #self.ax.autoscale()
                

                
                for i,line in enumerate(self.line):
                        self.ax.draw_artist(line)   
                            
                

                self.ax.set_xlabel("Time")
                self.ax.draw_artist(self.legend)
                    
                self.canvas.update()
                
                self.canvas.flush_events()
    
'''          
            # If the dataset exists
            if dataSet is not None: 
               
                    
                # Get all data from the dataset
                data = dataSet.getData()
                self.ax.hold(False)
                try:
                    # for each entry in the dataset [[time], [[data], [data], [data...]]]
                    #print data
                    # Get the corresponding times that the values were recorded

                    #print data
                    for i in range(1, len(data[-1])):
                        
                        # Get colum. aka all values from parameter i over time
                        
                       
                        #print times
                        # If the there is  no defined a time range
                        if self.currTimeRange is None:
                            column = [row[i] for row in data]
                            times = [datetime.datetime.fromtimestamp(row[0]) for row in data]
                            # Plot all of the data (columns) vs time
                            # self.ax.plot_date(times, column, label =
                                # dataSet.getVariables()[1][i-1][0])
                            pass
                        else:
                            # Otherwise, if the user PREVIOUSLY defined a time range, 
                            # we need to look for the beginning of it.
                            # Start by getting the current time
                            dstamp = dateStamp()
                            # The dataset should be from now to -timerange
                            # time(now)-time(range)
                            startTime = dstamp.utcNowFloat()-self.currTimeRange
                            # If timeRange is not None, then we know we need
                            # to display only a certain range of values
                            # However, if the starttime defined is less than the lowest time, we
                            # do not have enough data to display the whole thing, so we must 
                            # display all that we have instead. We do this by setting
                            # currTimeRange = 0.
                            if timeRange is not None and startTime<float(data[0][0]):
                                self.currTimeRange = None
                            # For all entries in data
                            for y in range(len(data)):
                                # We are searching backwards through the dataset to find a time 
                                # just before the time range specified
                                if data[len(data)-y-1][0] < startTime:
                                    # once we find it, we know the beginning index of the data to be
                                    # displayed
                                    index = y
                                    # Get the times and datafrom the index and columns to the end of the dataset
                                    times = [datetime.datetime.fromtimestamp(row[0]) for row in data[-index:]]
                                    #print times[0]
                                    column = [row[i] for row in data[-index:]]
                                    # Exit the loop
                                    break

                        try:
                            # while(len(self.line)<=i):
                            #print i
                                # print "Appending"
                            
                            #if self.lineSelect.isChecked(i-1):
                                #self.maxes = max(self.maxes, max(data))
                                #self.mins = min(self.mins, min(data))
                            #self.line.append(self.ax.plot(1,1, label = dataSet.getVariables()[1][i-1][0])[0])
                           # self.line[-1].set_data(times,column)
                            
                                #pass
                            print "Line len: ",len(self.line)
                            print "Length times", len(times)
                            print "Length data", len(column)
                            print "time[0]", times[0]
                           
                            #legend = self.ax.legend(loc='upper left', shadow=True, fancybox=True)
                            # maxi = max(column)
                            # mini = min(column)
                            # newMax = max(column)
                            # newMini = min(column)
                            # if(newMax>maxi)
                                # maxi=newMax
                                # self.ax.set_ylim(mini-mini/2, maxi+maxi/2)
                            # if(newMini<mini)
                                # self.ax.set_ylim(mini-mini/2, maxi+maxi/2)
                            # maxi = max(column)
                            # mini = min(column)
                           
                            # self.ax.set_ylim(mini-mini/2, maxi+maxi/2)
                            # self.ax.set_xlim(min(times), max(times))
                            #self.ax.draw_artist(self.line[i])
                        except:

                            traceback.print_exc()                        

                            #print "Failed to log data"
                        # Add a legend
                        #legend = self.ax.legend(loc='upper left')
                        #self.ax.grid(True)
                       # self.ax.set_title(self.device.getFrame().getTitle(), color = (189.0/255, 195.0/255, 199.0/255))
                        #self.ax.hold(True)
                        
                        if(self.device.getFrame().getYLabel() is not None 
                            and len(self.device.getFrame().getCustomUnits()) is not 0):
                            self.ax.set_ylabel(self.device.getFrame().getYLabel()+" ("+
                                    self.device.getFrame().getCustomUnits()+")")
                        elif (self.device.getFrame().getYLabel() is not None 
                            and len(self.device.getFrame().getUnits()[i-1]) is not 0):
                            
                            self.ax.set_ylabel(self.device.getFrame().getYLabel()+" ("+
                                    self.device.getFrame().getUnits()[i-1]+")")
                                    
                        #self.ax.set_xlabel("Time")
                        #self.ax.hold(True)
                        
                        # locator = AutoDateLocator()
                        #self.ax.fmt_xdata = AutoDateFormatter()
                        #self.ax.xaxis.set_major_locator(locator)
                        #self.ax.xaxis.set_major_locator(locator)
                        #self.ax.xaxis.set_major_formatter(DateFormatter('%m/%d'))
                        
                        #self.ax.fmt_xdata = mdates.DateFormatter('%m/%d %H:%M:%S')
                        # print "type: ", type(times[-1])
                        # print "time[-1]: ",times[-1]
                        # self.ax.set_ylim(bottom = 733681, top = 733682)
                        
                        #self.figure.tight_layout()
                        #self.ax.grid(True)
               
                except Exception as e :
                   print "Error"
                try:
                    pass
                    
                   
                    
                    #self.ax.clear()
                    #self.ax.cla()
                    
                    # # if self.home:
                        # # self.ax.set_xlim(times[0], times[-1])
                        # # #self.ax.set_ylim(self.mins, self.maxes)
                        # # #self.ax.relim(visible_only = True)
                        # # self.ax.autoscale()
    
                    #print self.ax.get_data_interval()
                    
                    # # self.ax.draw_artist(self.figure)
                    # # self.ax.draw_artist(self.ax.patch)
                    
                    # # locator = AutoDateLocator()
                    
                    # # self.ax.xaxis.set_major_locator(locator)
                    # # self.ax.xaxis.set_major_formatter(DateFormatter('%m/%d %H:%M:%S'))
                    # # self.figure.autofmt_xdate()
                    # # #print [time.toordinal() for time in times]
                    # # self.ax.draw_artist(self.ax.yaxis)
                    # # self.ax.draw_artist(self.ax.xaxis)
                    
                    # # #print self.line
                    # # #self.ax.hold(False)
                    # # # # for i,line in enumerate(self.line):
                        # # # # if self.lineSelect.isChecked(i):
                            # # # # self.ax.draw_artist(line)
                    
                    
                    # # self.ax.autoscale()
                    # # self.ax.draw_artist(legend)
                    
                    # # self.canvas.update()
                    
                    # # self.canvas.flush_events()
                    
                except:
                    times = [datetime.datetime.fromtimestamp(row[0]) for row in data]
                    traceback.print_exc()
                    self.ax.set_xlim(times[0], times[-1])
                    self.ax.relim()
                    self.ax.autoscale()
                    #print self.ax.get_data_interval()
                    pass
            '''
        #self.timer.singleShot(self.device.getFrame().getPlotRefreshRate()*1000, partial(self.plot, timeRange))