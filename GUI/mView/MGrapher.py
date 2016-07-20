import sys
from PyQt4 import QtGui, QtCore
from functools import partial
from dateStamp import *
from dataChest import *
import datetime
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt
import random
class mGraph(QtGui.QWidget):
	def __init__(self, device, parent=None):
		QtGui.QWidget.__init__( self,parent)

		self.figure = plt.figure()
		self.canvas = FigureCanvas(self.figure)
		self.canvas.setSizePolicy(QtGui.QSizePolicy.Expanding, 
            QtGui.QSizePolicy.Expanding)
		self.device = device
		
		self.home = NavigationToolbar.home
		NavigationToolbar.home = self.go_home
		self.toolbar = NavigationToolbar(self.canvas, self)
		self.canvas.mpl_connect('button_press_event', self.disableAutoUpdate)
		self.setStyleSheet("""QPushButton{
					color:rgb(189,195, 199); 
					background:rgb(70, 80, 88)}""")
		self.toolbar.setStyleSheet("""background:rgb(189, 195, 199);""")
        
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
		self.ax = self.figure.add_subplot(111)
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
		if dataSet is not None:
			data = dataSet.getData()
			self.ax.hold(False)
			for i in range(1, len(data[-1])):
				column = [row[i] for row in data]
				times = [row[0] for row in data]
				if self.currTimeRange is None:
					self.ax.plot(times,column,label =
                        self.device.getFrame().getNicknames()[i-1])
				else:
					dstamp = dateStamp()
					startTime = dstamp.utcNowFloat()-self.currTimeRange
					if timeRange is not None and startTime<float(data[0][0]):
						self.currTimeRange = None
					for y in range(len(data)):
						if data[len(data)-y-1][0] < startTime:
							index = y
							times = [row[0] for row in data[-index:]]
							column = [row[i] for row in data[-index:]]
							break
					self.ax.plot(times,column,label = 
                        self.device.getFrame().getNicknames()[i-1])
				
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
							
				self.ax.set_xlabel("UTC Time in Seconds")
			
				self.ax.hold(True)
			

			self.canvas.draw()
