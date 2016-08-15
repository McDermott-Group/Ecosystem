import sys
from PyQt4 import QtGui, QtCore
from functools import partial
from dateStamp import *
from dataChest import *
import datetime
import matplotlib
from matplotlib.dates import DateFormatter, AutoDateFormatter, AutoDateLocator
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt
matplotlib.use('TkAgg')
import logging as l
LOG_FILENAME = 'mGrapherLog.log'
import random
import threading
import traceback
import time
import numpy as np
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
        #self.figure.tight_layout()
        self.line = []
        self.line.append(self.ax.plot(1,1, label = "Getting Data...")[0])
        self.canvas.draw()
        #plt.style.use('dark_background')
        self.home = NavigationToolbar.home
        #self.zoom = NavigationToolbar.Zoom-to-rectangle
        NavigationToolbar.home = self.enableAutoScaling
        #NavigationToolbar.Zoom-to-rectangle = self.disableAutoScaling
        self.toolbar = NavigationToolbar(self.canvas, self)
        #self.toolbar.set_message("HELLO")
        #self.cidp = self.canvas.mpl_connect('pick_event', self.onPick)
        self.cid = self.canvas.mpl_connect('button_press_event', self.disableAutoScaling)
       
        #self.cid = plt.get_current_fig_manager().toolbar.events()[3].triggered.connect(self.disableAutoScaling)
        self.setStyleSheet("""QPushButton{
                    color:rgb(189,195, 199); 
                    background:rgb(70, 80, 88)}""")
        self.toolbar.setStyleSheet("""
                    color:rgb(0,0,0); 
                    background:rgb(200, 200, 200);""")
        #self.ax.xaxis.label.set_color('rgb(189,195, 199)')
        self.matPlotInfo = QtGui.QLabel()
        self.alertFont = QtGui.QFont()
        self.alertFont.setPointSize(12)
        self.matPlotInfo.setStyleSheet(
                                "color:rgb(200, 69, 50);")
        self.matPlotInfo.setText("Auto refresh disabled, click HOME button to enable.")
        self.matPlotInfo.setFont(self.alertFont)
        
        self.hidden = True
        self.home = True
        self.currTimeRange = 120
        self.plot(self.currTimeRange)
        
        self.refreshRateSec = device.getFrame().getPlotRefreshRate()
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(partial(self.plot, self.currTimeRange))
        self.timer.start(self.refreshRateSec*1000)
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
        
        self.matPlotInfo.hide()
        
        layout = QtGui.QVBoxLayout()
        layout.addLayout(buttonLayout)
        layout.addLayout(buttonLayout2)
        layout.addLayout(buttonLayout3)
        layout.addWidget(self.matPlotInfo)
        layout.addWidget(self.canvas)
        layout.addWidget(self.toolbar)
        

        self.setLayout(layout)

#self.canvas.show()
        # keepTrying = True
        # dataSet =  self.device.getFrame().getDataSet()
        # while dataSet != None:
            # try:
                # dataSet =  self.device.getFrame().getDataSet()
                # data = dataSet.getData()
                # for i in range(1, len(data[-1])):
                    
                    # times = [datetime.datetime.fromtimestamp(row[0]) for row in data]
                    # column = [row[i] for row in data]

                # #print "Drew Graphs"
            # except:
                # traceback.print_exc()
                # time.sleep(0.1)

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
            self.timer.stop()
            self.hideButton.setText("Show Plot")
            self.disableAutoScaling()
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
            self.timer.start(self.refreshRateSec*1000)
            self.hideButton.setText("Hide Plot")
            self.enableAutoScaling()
            self.hidden = False
            
    def plot(self, timeRange):
        if not self.hidden:
            if timeRange != self.currTimeRange:
                self.timer.stop()
                self.timer.timeout.disconnect()
                self.currTimeRange = timeRange
                self.timer.timeout.connect(partial(self.plot, self.currTimeRange))
                self.timer.start(self.refreshRateSec*1000)

            dataSet =  self.device.getFrame().getDataSet()
            # If the dataset exists
            if dataSet is not None:
                # Get all data from the dataset
                data = dataSet.getData()
                self.ax.hold(False)
                try:
                    # for each entry in the dataset [[time], [[data], [data], [data...]]]
                    #print data
                    # Get the corresponding times that the values were recorded
                    times = [datetime.datetime.fromtimestamp(row[0]) for row in data]
             
                    for i in range(1, len(data[-1])):
                        # Get colum. aka all values from parameter i over time
                        column = [row[i] for row in data]
                       
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
                                    #print times[0]
                                    column = [row[i] for row in data[-index:]]
                                    # Exit the loop
                                    break
                           
                        l.debug("")
                        l.debug("Device: "+self.device.getFrame().getTitle())
                        l.debug("i: "+ str(i))
                            #print dataSet.getVariables()
                        l.debug( "data[-1]: " + str(data[-1]))
                        l.debug( "len(data[-1]): "+ str( len(data[-1])))
                        l.debug("num rows: "+ str(dataSet.getNumRows()))
                        l.debug( "len(data): "+ str(len(data)))
                        l.debug(str(times[-1]))
                        
                        try:
                            while(len(self.line)<=i):
                                self.line.append(self.ax.plot(1,1, label =dataSet.getVariables()[1][i-1][0])[0])
                                
                            self.line[i].set_data(times,column)
                            self.ax.legend(loc='upper left', shadow=True, fancybox=True)
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
                        legend = self.ax.legend(loc='upper left')
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
                        self.ax.grid(True)
                       
                except Exception as e :
                   print "Error"
                  # traceback.print_exc()
                   l.debug("DEVICE: "+self.device.getFrame().getTitle())
                   l.debug("ERROR")
                   l.debug( (type(e)))
                   l.debug(traceback.print_exc())
                   l.debug( (e))
                   l.debug( "i: " + str(i))
                   l.debug( "len(data[-1]): " + str( len(data[-1])))
                   l.debug( "num rows: " + str(dataSet.getNumRows()))
                   l.debug( "len(data): " + str(len(data)))
                   l.debug( "data[-1]: " + str(data[-1]))
                   l.debug( "[row[1] for row in data] " + str([row[1] for row in data]))
                try:
              
                    
                    #self.line.set_data(range(20),np.random.rand(20))
                    self.ax.grid(True)
                    #self.ax.clear(self.ax.yaxis)
                    #self.ax.cla()
             

                        
                    if self.home:
                        self.ax.set_xlim(times[0], times[-1])
                        self.ax.relim()
                        self.ax.autoscale()
                    
                
    
                    #print self.ax.get_data_interval()
                    self.ax.draw_artist(self.figure)
                    self.ax.draw_artist(self.ax.patch)
                    
                    locator = AutoDateLocator()
                    
                    self.ax.xaxis.set_major_locator(locator)
                    self.ax.xaxis.set_major_formatter(DateFormatter('%m/%d %H:%M:%S'))
                    self.figure.autofmt_xdate()
                    #print [time.toordinal() for time in times]
                    self.ax.draw_artist(self.ax.yaxis)
                    self.ax.draw_artist(self.ax.xaxis)
                    
                    
                    for line in self.line:
                        self.ax.draw_artist(line)
                   
                    
                    #self.ax.axis('off')
                    
                    
                    
                    self.ax.draw_artist(legend)
                   
                    self.canvas.update()
                    
                    self.canvas.flush_events()
                
                except:
                    
                    traceback.print_exc()
                    self.ax.set_xlim(times[0], times[-1])
                    self.ax.relim()
                    self.ax.autoscale()
                    #print self.ax.get_data_interval()
                    pass
            
    