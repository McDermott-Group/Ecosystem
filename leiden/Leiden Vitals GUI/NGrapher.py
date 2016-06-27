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
#from matplotlib.figure import Figure
from matplotlib import rc
import matplotlib.pyplot as plt
progname = os.path.basename(sys.argv[0])
progversion = "0.1"
from datetime import datetime as t
import time
class MyMplCanvas(FigureCanvas):
	"""Ultimately, this is a QWidget (as well as a FigureCanvasAgg, etc.)."""

	def __init__(self, parent=None, width=5, height=4, dpi=100):
		#self.fig = Figure(figsize=(5, 4), dpi=100)
		self.fig = plt.figure()
		self.axes = self.fig.add_subplot(1,1,1)
		# We want the axes cleared every time plot() is called
		#self.axes.hold(False)

		#self.compute_initial_figure()

		#
		FigureCanvas.__init__(self, self.fig)
		self.setParent(parent)

		FigureCanvas.setSizePolicy(self,
								   QtGui.QSizePolicy.Expanding,
								   QtGui.QSizePolicy.Expanding)
		FigureCanvas.updateGeometry(self)
		font = {'size'   : 10}

		rc('font', **font)


class DynamicMplCanvas(MyMplCanvas):
	"""A canvas that updates itself every second with a new plot."""

	def __init__(self, device, *args, **kwargs):
		self.device = device
		MyMplCanvas.__init__(self, *args, **kwargs)
		timer = QtCore.QTimer(self)
		timer.timeout.connect(self.update_figure)
		timer.start(1000)
		self.data = []
		self.times = []
		self.startTime = time.time()
		self.endTime = time.time()
	def compute_initial_figure(self):
		self.axes.plot(range(len(self.device.getFrame().getReadings()))
				, self.device.getFrame().getReadings(), 'r')

	def update_figure(self):
		if(self.device.getFrame().getReadings() is not None):
			self.data.append((self.device.getFrame().getReadings()))
			self.times.append(time.time()-self.startTime)
			#thisData = []
			#print(self.data)
			
			# only plot data shown on GUI
			#print

			self.axes.clear()
			if self.device.getFrame().getPlotLength() is not None:
				while len(self.data) > self.device.getFrame().getPlotLength():
					self.data.pop(0)
					self.endTime = self.times.pop(0)+self.startTime
				print(self.endTime-self.startTime)
				self.axes.set_xlim(self.endTime-self.startTime, time.time()-self.startTime)
			datalen = len(self.data)-1

			if (type(self.data[datalen]) is list):
				for i in range(len(self.device.getFrame().getReadingIndices())):
					#print(self.device.getFrame().getReadingIndices())

					index = self.device.getFrame().getReadingIndices()[i]
				
		
					column = [row[index] for row in self.data]
					#print column
					#time = [row[index] for row[1] in self.data]
					self.axes.plot(self.times, column, label = self.device.getFrame().getNicknames()[i])
					#b,self.axes = self.fig.subplots()
					#self.axes.plot(column, label = "Test")

			#else:
				#print "printing 1d array: ", self.device.getFrame().getTitle()
				#self.axes.plot(self.data, label = self.device.getFrame().getNicknames()[0])
				
			
			self.axes.set_xlabel("Time Since "+time.ctime(self.startTime)+" (s)", fontsize = 10)
			self.axes.legend(loc='upper left')
			if(self.device.getFrame().getYLabel() is not None and
						len(self.device.getFrame().getUnits()) is not 0):
				
				self.axes.set_ylabel(self.device.getFrame().getYLabel()+" ("+
							self.device.getFrame().getUnits()[0]+")", fontsize = 10)
			
			elif(self.device.getFrame().getYLabel() is not None and
						len(self.device.getFrame().getCustomUnits()) is not 0):
				self.axes.set_ylabel(self.device.getFrame().getYLabel()+" ("+
							self.device.getFrame().getCustomUnits()+")", fontsize = 10)
			

			self.draw()

# qApp = QtGui.QApplication(sys.argv)

# aw = ApplicationWindow()
# aw.setWindowTitle("%s" % progname)
#aw.show()
#sys.exit(qApp.exec_())
#qApp.exec_()