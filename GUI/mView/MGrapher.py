import sys
from PyQt4 import QtGui, QtCore
from functools import partial
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
		self.plot()
		
		self.timer = QtCore.QTimer(self)
		self.timer.timeout.connect(self.plot)
		self.timer.start(1000)
	 
		self.hideButton = QtGui.QPushButton("Show Plot")
		self.hideButton.clicked.connect(self.togglePlot)
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
		buttonLayout.addWidget(self.hideButton);
		layout = QtGui.QVBoxLayout()
		layout.addLayout(buttonLayout)
		layout.addWidget(self.canvas)
		layout.addWidget(self.toolbar)
		

		self.setLayout(layout)
	def go_home(self, *args, **kwargs):
		#print 'new home'
		self.timer.start(1000)
		#self.canv.axes.autoscale_view(True,True,True)
		self.plot()
	def disableAutoUpdate(self, event):
		self.timer.stop()
	def togglePlot(self):
	
		if not self.hidden:
			print "hiding"
			self.canvas.hide()
			self.toolbar.hide()
			self.timer.stop()
			self.hideButton.setText("Show Plot")
			self.hidden = True
			#self.hideButton.clicked.connect(partial(self.hidePlot, False))
		elif  self.hidden:
			print "showing"
			self.canvas.show()
			self.toolbar.show()
			self.plot()
			#self.canvas.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
			self.timer.start(1000)
			self.hideButton.setText("Hide Plot")
			self.hidden = False
			#self.hideButton.clicked.connect(partial(self.hidePlot, True))
	def plot(self):
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
				column = [row[i] for row in data]
				times = [row[0] for row in data]
				#print column
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
