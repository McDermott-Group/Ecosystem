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
__version__ = "1.0.2"
__maintainer__ = "Noah Meltzer"
__status__ = "Beta"

from MFrame import MFrame
from PyQt4.QtCore import QObject, pyqtSignal, pyqtSlot, QThread
class MDevice(QThread):
    updateSignal = pyqtSignal()
    def __init__(self, name):
        super(MDevice, self).__init__()

        self.frame = MFrame()
        self.frame.setTitle(name)
        # Datachest wrapper.
       # Dictionary holding datalogging settings
         # Datalogging disabled by default


       # Refresh rate of plot.
        self.plotRefreshRate = 1
        # RefreshRate for the device.
        self.refreshRate = 1
        self.container = None
       
        
    def setContainer(self, container):
        self.container = container
        self.frame.setContainer(container)
    def getContainer(self):
        return self.container
    def updateContainer(self):
        if self.container != None:
           self.updateSignal.emit()
            
    def addParameter(self, *args):
        print ("ERROR: Child of MDevice must "
            "implement MDevice.addParameter().")
        exit(1)
        
    def addButton(self, *args):
        print("ERROR: Child of MDevice must "
            "implement MDevice.addButton().")
        exit(1)
    def query(self, *args):
        print("ERROR: Child of MDevice must "
            "implement MDevice.query().")
        exit(1)
    def setYLabel(self, *args):
        print("ERROR: Child of MDevice must "
            "implement MDevice.setYLabel().")
        exit(1)
    def setRefreshRate(self, *args):
        print("ERROR: Child of MDevice must "
            "implement MDevice.setRefreshRate().")
        exit(1)
    def setPlotRefreshRate(self, *args):
         print("ERROR: Child of MDevice must "
            "implement MDevice.setPlotRefreshRate().")
         exit(1)
    def addPlot(self, *args):
        print("ERROR: Child of MDevice must "
            "implement MDevice.addplot().")
        exit(1)
    def getFrame(self):
        """Return the device's frame."""
        return self.frame
    def stop(self):
        print "stopping device thread..."
        self.keepGoing = False
        print "device thread stopped."
    def begin(self):
      
        self.frame.setNicknames(self.nicknames)
        self.frame.setReadingIndices(self.settingResultIndices)
        self.frame.DataLoggingInfo()['name'] = self.frame.getTitle()
        self.frame.DataLoggingInfo()['chest'] = dataChestWrapper(self)
        self.datachest = self.frame.DataLoggingInfo()['chest']
        
    def logData(self, b, channels = None):
        self.frame.DataLoggingInfo['channels'] = channels
        self.frame.enableDataLogging(b)
        
    def __str__(self):
        if self.frame.getTitle() is None:
            return "Unnamed Device"
        return self.frame.getTitle()

   
