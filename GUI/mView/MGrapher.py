import sys
from PyQt4 import QtGui, QtCore
from functools import partial
from dateStamp import *
from dataChest import *
import datetime
from matplotlib.dates import DateFormatter, AutoDateFormatter, AutoDateLocator
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt
import logging as l
LOG_FILENAME = 'mGrapherLog.log'
import random
import threading
class mGraph(QtGui.QWidget):
    def __init__(self, device, parent=None):
        QtGui.QWidget.__init__( self,parent)
        
        l.basicConfig(filename=LOG_FILENAME,level=l.DEBUG)
        l.debug('mGrapher.py Log file')
        self.figure = plt.figure()
        
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(QtGui.QSizePolicy.Preferred, 
            QtGui.QSizePolicy.Preferred)
        self.device = device
        self.ax = self.figure.add_subplot(111)
        self.figure.patch.set_alpha(1.0)
        #plt.style.use('dark_background')
        self.home = NavigationToolbar.home
        NavigationToolbar.home = self.go_home
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.canvas.mpl_connect('button_press_event', self.disableAutoUpdate)
        self.setStyleSheet("""QPushButton{
                    color:rgb(189,195, 199); 
                    background:rgb(70, 80, 88)}""")
        self.toolbar.setStyleSheet("""
                    color:rgb(0,0,0); 
                    background:rgb(200, 200, 200);""")
        #self.ax.xaxis.label.set_color('rgb(189,195, 199)')

        self.currTimeRange = 120
        self.plot(self.currTimeRange)
        
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(partial(self.plot, self.currTimeRange))
        self.timer.start(1000)
        
     
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
        self.hidden = True
        # set the layout
        
        buttonLayout = QtGui.QHBoxLayout()
        buttonLayout.addWidget(self.hideButton)
        buttonLayout.addStretch(0)
        buttonLayout2 = QtGui.QHBoxLayout()
        
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
            
        layout = QtGui.QVBoxLayout()
        layout.addLayout(buttonLayout)
        layout.addLayout(buttonLayout2)
        layout.addLayout(buttonLayout3)

        layout.addWidget(self.canvas)
        layout.addWidget(self.toolbar)
        

        self.setLayout(layout)
    def go_home(self, *args, **kwargs):
        self.timer.start(1000)
        
        # self.deviceThread = threading.Thread(target = 
            # self.plot, args=[self.currTimeRange])
        # If the main thread stops, stop the child thread
        # self.deviceThread.daemon = True
        # Start the thread
        # self.deviceThread.start()
        
        self.plot(self.currTimeRange)
    def disableAutoUpdate(self, event):
        self.timer.stop()
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
            self.timer.start(1000)
            self.hideButton.setText("Hide Plot")
            self.hidden = False
            
    def plot(self, timeRange):
        if timeRange != self.currTimeRange:
            self.timer.stop()
            self.timer.timeout.disconnect()
            self.currTimeRange = timeRange
            self.timer.timeout.connect(partial(self.plot, self.currTimeRange))
            self.timer.start(1000)

        dataSet =  self.device.getFrame().getDataSet()
        # If the dataset exists
        if dataSet is not None:
            # Get all data from the dataset
            data = dataSet.getData()
            self.ax.hold(False)
            try:
                # for each entry in the dataset [[time], [[data], [data], [data...]]]
                #print data
                for i in range(1, len(data[-1])):
                    # Get colum. aka all values from parameter i over time
                    column = [row[i] for row in data]
                    # Get the corresponding times that the values were recorded
                    times = [datetime.datetime.fromtimestamp(row[0]) for row in data]
                    #print times
                    # If the there is  no defined a time range
                    if self.currTimeRange is None:
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
                                column = [row[i] for row in data[-index:]]
                                # Exit the loop
                                break
                        # Plot yo stuff
                    l.debug("")
                    l.debug("Device: "+self.device.getFrame().getTitle())
                    l.debug("i: "+ str(i))
                        #print dataSet.getVariables()
                    l.debug( "len(data[-1]): "+ str( len(data[-1])))
                    l.debug("num rows: "+ str(dataSet.getNumRows()))
                    l.debug( "len(data): "+ str(len(data)))
                    self.ax.plot_date(times,column,'-',label = 
                        dataSet.getVariables()[1][i-1][0])
                    # Add a legend
                    self.ax.legend(loc='upper left')
                    self.ax.set_title(self.device.getFrame().getTitle())
                    if(self.device.getFrame().getYLabel() is not None 
                        and len(self.device.getFrame().getCustomUnits()) is not 0):
                        self.ax.set_ylabel(self.device.getFrame().getYLabel()+" ("+
                                self.device.getFrame().getCustomUnits()+")")
                    elif (self.device.getFrame().getYLabel() is not None 
                        and len(self.device.getFrame().getUnits()[i-1]) is not 0):
                        
                        self.ax.set_ylabel(self.device.getFrame().getYLabel()+" ("+
                                self.device.getFrame().getUnits()[i-1]+")")
                                
                    self.ax.set_xlabel("Time")
                
                    self.ax.hold(True)
                    locator = AutoDateLocator()
                    #self.ax.fmt_xdata = AutoDateFormatter()
                    #self.ax.xaxis.set_major_locator(locator)
                    self.ax.xaxis.set_major_locator(locator)
                    #self.ax.xaxis.set_major_formatter(DateFormatter('%m/%d'))
                    self.ax.xaxis.set_major_formatter(DateFormatter('%m/%d %H:%M:%S'))
                    self.figure.autofmt_xdate()
                    #self.figure.tight_layout()
                    self.ax.grid(True)
            except Exception as e :
               print "Error"
               l.debus("DEVICE: "+self.device.getFrame().getTitle())
               l.debug("ERROR")
               l.debug( (type(e)))
               l.debug( (e))
               l.debug( "i: " + str(i))
               l.debug( "len(data[-1]): " + str( len(data[-1])))
               l.debug( "num rows: " + str(dataSet.getNumRows()))
               l.debug( "len(data): " + str(len(data)))
               l.debug( "data[-1]: " + str(data))
               l.debug( "[row[1] for row in data] " + str([row[1] for row in data]))
            

            self.canvas.draw()
    