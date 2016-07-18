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
		self.canvas.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
		#self.canvas.updateGeometry()
		self.device = device
		
		self.home = NavigationToolbar.home
		NavigationToolbar.home = self.go_home
		self.toolbar = NavigationToolbar(self.canvas, self)
		self.canvas.mpl_connect('button_press_event', self.disableAutoUpdate)
		self.setStyleSheet("""QPushButton{
					color:rgb(189,195, 199); 
					background:rgb(70, 80, 88)}""")
		self.toolbar.setStyleSheet("background:rgb(189, 195, 199);")
		#self.toolbar.hide()
		self.currTimeRange = 120
		self.plot(self.currTimeRange)
		
		self.timer = QtCore.QTimer(self)
		self.timer.timeout.connect(partial(self.plot, self.currTimeRange))
		self.timer.start(1000)
	 
		self.hideButton = QtGui.QPushButton("Show Plot")
		self.hideButton.clicked.connect(self.togglePlot)
		self.thrtysecButton = QtGui.QPushButton("30 Sec")
		self.thrtysecButton.clicked.connect(partial(self.plot, 30))
		self.twoMinButton = QtGui.QPushButton("1 Min")
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
		# self.button1 = QtGui.QPushButton('Zoom')
		# self.button1.clicked.connect(self.zoom)
		 
		# self.button2 = QtGui.QPushButton('Pan')
		# self.button2.clicked.connect(self.pan)
		 
		# self.button3 = QtGui.QPushButton('Home')
		# self.button3.clicked.connect(self.home)


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
		#print 'new home'
		self.timer.start(1000)
		#self.canv.axes.autoscale_view(True,True,True)
		self.plot(self.currTimeRange)
	def disableAutoUpdate(self, event):
		self.timer.stop()
	def togglePlot(self):
	
		if not self.hidden:
			print "hiding"
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
			#self.hideButton.clicked.connect(partial(self.hidePlot, False))
		elif  self.hidden:
			print "showing"
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
			#self.canvas.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
			self.timer.start(1000)
			self.hideButton.setText("Hide Plot")
			self.hidden = False
			#self.hideButton.clicked.connect(partial(self.hidePlot, True))
	def plot(self, timeRange):
			
		if timeRange != self.currTimeRange:
			self.timer.stop()
			self.timer.timeout.disconnect()
			self.currTimeRange = timeRange
			#print self.currTimeRange
			self.timer.timeout.connect(partial(self.plot, self.currTimeRange))
			self.timer.start(1000)
		''' plot some random stuff '''
		#data = [random.random() for i in range(25)]
		dataSet =  self.device.getFrame().getDataSet()
		#print data
		if dataSet is not None:
			#print self.device.getFrame().getDataSet().getData()[-1]
			data = dataSet.getData()
			
				
			#print data
			self.ax.hold(False)
			for i in range(1, len(data[-1])):
				#print len(data[-1])
				column = [row[i] for row in data]
				
				times = [row[0] for row in data]
				if self.currTimeRange is None:
					
					self.ax.plot(times,column,label = self.device.getFrame().getNicknames()[i-1])
				else:
					dstamp = dateStamp()
					startTime = dstamp.utcNowFloat()-self.currTimeRange
					if timeRange is not None and startTime<float(data[0][0]):
						#print "Not enough data, showing all time instead."
						self.currTimeRange = None
					for y in range(len(data)):
						#print data[len(data)-y-1][0]
						if data[len(data)-y-1][0] < startTime:
							#print round(data[len(data)-y-1][0])
							#print startTime
							index = y
							times = [row[0] for row in data[-index:]]
							column = [row[i] for row in data[-index:]]
							break
					# print "col", len(column)
					# print "time", len(times)
					#print self.device.getFrame().getNicknames()
					#print len( data)
					self.ax.plot(times,column,label = self.device.getFrame().getNicknames()[i-1])
				
				self.ax.legend(loc='upper left')
				self.ax.set_title(self.device.getFrame().getTitle())
				if(self.device.getFrame().getYLabel() is not None and len(self.device.getFrame().getCustomUnits()) is not 0):
					#print "using cust units"
					self.ax.set_ylabel(self.device.getFrame().getYLabel()+" ("+
							self.device.getFrame().getCustomUnits()+")")
				elif (self.device.getFrame().getYLabel() is not None and len(self.device.getFrame().getUnits()[i-1]) is not 0):
					#print "using units"
					self.ax.set_ylabel(self.device.getFrame().getYLabel()+" ("+
							self.device.getFrame().getUnits()[i-1]+")")
				
			
				self.ax.hold(True)
			

			self.canvas.draw()
