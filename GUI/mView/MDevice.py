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
import threading
from dataChestWrapper import dataChestWrapper
class MDevice(QThread):

    updateSignal = pyqtSignal()
    '''
  MView uses the MDevice class to give all sources of data a common 
  interface with which to interact in the context of MView. These 
  sources of data can be anything including but not limited to LabRad 
  servers, RS232 devices, GPIB Devices, they can even represent the 
  contents of .hdf5 files. Devices in MView are created by instantiating
  their device drivers. For example, if there are two RS232 devices, 
  we create two instances of the RS232 device driver. This means that 
  only one generic device driver needs to be created for one interface 
  (RS232, LabRad Servers, HDF5 files, etc.) and it can then be applied 
  to all devices that use the same interface.
  '''
    
    def __init__(self, name, *args):
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

        self.keepGoing = True
        self.settingResultIndices = []
        self.noLogging = False
    def log(self, log):
        self.noLogging = not log
    def setContainer(self, container):

        self.container = container
        self.frame.setContainer(container)
    def getContainer(self):
        return self.container
    def updateContainer(self):
        if self.container != None:
           self.updateSignal.emit()
    def addButton(self, *args):
        pass
    def setTitle(self, title):
        self.frame.setTitle(title)
    def query(self, *args):
        pass    
    def setYLabel(self, *args):
        pass
    def setRefreshRate(self, *args):
        pass
    def setPlotRefreshRate(self, *args):
        pass
    def addButtonToGui(self, button):
        self.frame.appendButton(button)
    def addReadout(self, name, units):
        self.nicknames.append(name)
        self.units.append(units)
    def addPlot(self, length = None, *args):

        self.frame.addPlot(length)
        # Datalogging must be enabled if we want to plot data.
        self.frame.enableDataLogging(True)
        return self.frame.getPlot()
    def getFrame(self):
        """Return the device's frame."""
        return self.frame
    def stop(self):
        print "stopping device thread..."
        self.keepGoing = False
        #print "device thread stopped."
        
        self.close()
    def begin(self):
      
        # self.frame.setNicknames(self.nicknames)
        # self.frame.setReadingIndices(self.settingResultIndices)
        # self.frame.DataLoggingInfo()['name'] = self.frame.getTitle()
        # self.frame.DataLoggingInfo()['chest'] = dataChestWrapper(self)
        # self.datachest = self.frame.DataLoggingInfo()['chest']
        
        #self.frame.setNicknames(self.nicknames)
    
        self.frame.setReadingIndices(self.settingResultIndices)
        if not self.noLogging:
            self.frame.DataLoggingInfo()['name'] = self.name
            self.frame.DataLoggingInfo()['chest'] = dataChestWrapper(self)
            self.datachest = self.frame.DataLoggingInfo()['chest']
        # Each device NEEDS to run on a different thread 
        # than the main thread (which ALWAYS runs the GUI).
        # This thread is responsible for querying the devices.
        self.deviceThread = threading.Thread(target=self.callQuery, args=[])
        # If the main thread stops, stop the child thread.
        self.deviceThread.daemon = True
        # Start the thread.
        self.deviceThread.start()
        self.onBegin()
    def onBegin(self):
        '''Called at the end of MDevice.begin(). This is called before 
        MView starts. This allows us to configure settings that 
        MView might use while starting. This might include datalog 
        locations or device-specific information.'''
        pass
    def onLoad(self):
       '''Called at the end of MGui.startGui(), when the main 
       MView GUI has finished loading. This allows the 
       MDevice to configure pieces of MView only available
       once the program has fully loaded.'''
       pass
    def onAddParameter(self):
        pass
    def setReadings(self, readings):
        self.frame.setReadings(readings)
    def callQuery(self):
        '''Automatically called periodically, 
        determined by MDevice.Mframe.getRefreshRate(). 
        There is also a MDevice.Mframe.setRefreshRate()
        function with which the refresh rate can be configured.
        '''
        if not self.keepGoing:
            return
        self.query()
        self.datachest.save()
        self.updateContainer()
        threading.Timer(self.frame.getRefreshRate(),
                    self.callQuery).start()
    def prompt(self, button):
        '''Called when 
    a device's button is pushed. Button is an array which 
    is associated with the button. The array is constructed 
    in the device driver code, and the PyQT button is then appended
    to the end by MView. The array associated with the button is passed 
    to prompt() in the device driver. The device driver then determines 
    what to do based on the button pushed. 
   '''
        pass
    def close(self):
        return
    def addParameter(self, *args, **kwargs):
        params = self.onAddParameter(*args)
        #print "params to be added:", params
        log = kwargs.get("log", True)
        self.frame.DataLoggingInfo()['channels'][args[0]] = log
        
        self.frame.addParameter(params)
    def logData(self, b, channels = None):
    
        self.frame.DataLoggingInfo['channels'] = channels
        self.frame.enableDataLogging(b)
        
    def __str__(self):
        if self.frame.getTitle() is None:
            return "Unnamed Device"
        return self.frame.getTitle()

   
