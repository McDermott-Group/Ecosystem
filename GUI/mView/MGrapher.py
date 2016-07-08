# Copyright (C) 2016 Noah Meltzer and the internet
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


"""
version = 1.1.0
description = Adds graphing functionality
"""

from __future__ import unicode_literals
import sys
sys.dont_write_bytecode = True
import os
import random

from matplotlib.backends import qt_compat
use_pyside = qt_compat.QT_API == qt_compat.QT_API_PYSIDE
if use_pyside:
	from PySide import QtGui, QtCore
else:
	from PyQt4 import QtGui, QtCore

#from numpy import arange, sin, pi
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4 import NavigationToolbar2QT as NavigationToolbar

#from matplotlib.figure import Figure
from matplotlib import rc

import matplotlib.pyplot as plt
progname = os.path.basename(sys.argv[0])
progversion = "0.1"
from datetime import datetime as t
import time
from matplotlib.figure import Figure
class MplCanvas(FigureCanvas):
	"""Ultimately, this is a QWidget (as well as a FigureCanvasAgg, etc.)."""

	def __init__(self):
		
		self.fig = Figure()
		self.axes = self.fig.add_subplot(1,1,1)
		FigureCanvas.__init__(self, self.fig)
		FigureCanvas.setSizePolicy(self, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
		FigureCanvas.updateGeometry(self)
		


class DynamicMplCanvas(QtGui.QWidget):
	"""A canvas that updates itself every second with a new plot."""

	def __init__(self, device, parent = None):
		#super(DynamicMplCanvas, self).__init__()
		QtGui.QWidget.__init__( self,parent)
		self.device = device
		font = {'size'   : 10}
		rc('font', **font)
		# Weird stuff to detect home button press
		self.home = NavigationToolbar.home
		NavigationToolbar.home = self.go_home
		
		
		self.canv = MplCanvas()
		self.navi = NavigationToolbar(self.canv, self)
		print self.navi.home
		self.canv.mpl_connect('button_press_event', self.disableAutoUpdate)
		
		self.vbl = QtGui.QVBoxLayout()
		self.vbl.addWidget(self.canv)
		self.vbl.addWidget(self.navi)
		self.setLayout( self.vbl )
		
		self.timer = QtCore.QTimer(self)
		self.timer.timeout.connect(self.update_figure)
		self.timer.start(1000)
		
		self.data = []
		self.times = []
		self.startTime = time.time()
		self.endTime = time.time()
		
	def compute_initial_figure(self):
		self.axes.plot(range(len(self.device.getFrame().getReadings()))
				, self.device.getFrame().getReadings(), 'r')
	def go_home(self, *args, **kwargs):
		#print 'new home'
		self.timer.start(1000)
		self.canv.axes.autoscale_view(True,True,True)
		#NavigationToolbar.home(self, *args, **kwargs)
	def disableAutoUpdate(self, event):
		self.timer.stop()
		#print('button=%d, x=%d, y=%d, xdata=%f, ydata=%f' % (event.button, event.x, event.y, event.xdata, event.ydata))
	def update_figure(self):
		if(self.device.getFrame().getReadings() is not None):
			self.data.append((self.device.getFrame().getReadings()))
			self.times.append(time.time()-self.startTime)
			#thisData = []
			#print(self.data)
			
			# only plot data shown on GUI
			#print
		

			self.canv.axes.clear()
			if self.device.getFrame().getPlotLength() is not None:
				while len(self.data) > self.device.getFrame().getPlotLength():
					self.data.pop(0)
					self.endTime = self.times.pop(0)+self.startTime
				print(self.endTime-self.startTime)
				self.canv.axes.set_xlim(self.endTime-self.startTime, time.time()-self.startTime)
			datalen = len(self.data)-1

			if (type(self.data[datalen]) is list):
				for i in range(len(self.device.getFrame().getReadingIndices())):
					#print(self.device.getFrame().getReadingIndices())

					index = self.device.getFrame().getReadingIndices()[i]
				
		
					column = [row[index] for row in self.data]
					#print column
					#time = [row[index] for row[1] in self.data]
					self.canv.axes.plot(self.times, column, label = self.device.getFrame().getNicknames()[i])
					#b,self.axes = self.fig.subplots()
					#self.axes.plot(column, label = "Test")

			#else:
				#print "printing 1d array: ", self.device.getFrame().getTitle()
				#self.axes.plot(self.data, label = self.device.getFrame().getNicknames()[0])
				
			
			self.canv.axes.set_xlabel("Time Since "+time.ctime(self.startTime)+" (s)", fontsize = 10)
			self.canv.axes.legend(loc='upper left')
			if(self.device.getFrame().getYLabel() is not None and
						len(self.device.getFrame().getUnits()) is not 0):
				
				self.canv.axes.set_ylabel(self.device.getFrame().getYLabel()+" ("+
							self.device.getFrame().getUnits()[0]+")", fontsize = 10)
			
			elif(self.device.getFrame().getYLabel() is not None and
						len(self.device.getFrame().getCustomUnits()) is not 0):
				self.canv.axes.set_ylabel(self.device.getFrame().getYLabel()+" ("+
							self.device.getFrame().getCustomUnits()+")", fontsize = 10)
			

			self.canv.draw()

# qApp = QtGui.QApplication(sys.argv)

# aw = ApplicationWindow()
# aw.setWindowTitle("%s" % progname)
#aw.show()
#sys.exit(qApp.exec_())
#qApp.exec_()