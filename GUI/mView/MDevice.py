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
from MWeb import web
import traceback
import time


class MDevice(QThread):
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
    updateSignal = pyqtSignal()
    lock = threading.Lock()

    def __init__(self, name, *args, **kwargs):
        '''Initializes the device:

    1. Sets the frame title. 1.
    2. Sets the refresh rate. 2.

    Function arguments:

    :param name: The name of the device

   '''
        super(MDevice, self).__init__()
        self.lockLoggingSettings = kwargs.get("lock_logging_settings", False)
        self.defaultLogLocation = kwargs.get("default_log_location", None)
        self.dataType = kwargs.get("data_type", "float32")
        # Create a new MFrame
        web.devices.append(self)
        self.frame = MFrame()
        # print "Setting title to:", name, args
        self.frame.setTitle(name)
        self.name = name
        self.refreshRate = 1
        self.container = None
        self.datachest = None
        self.keepGoing = True
        self.settingResultIndices = []

        self.doneLoading = False

        #self.memory_tracker = tracker.SummaryTracker()
    def log(self, log):
        """ Tell the device whether to log data or not

        :param log: Boolean

    """
        self.frame.enableDataLogging(log)
        if not log:
            self.plot(False)

    def isLogging(self):
        '''Getter for whether or not datalogging is enabled for this device.

      :rtype: boolean

   '''
        return self.frame.isDataLogging()

    def setContainer(self, container):
        # traceback.print_stack()
        self.container = container
        self.frame.setContainer(container)

    def getContainer(self):
        return self.container

    def updateContainer(self):
        '''Refresh the devices container (Tile) on the GUI
      by emitting an update signal
   '''
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

    def addPlot(self, length=None, *args):

        self.frame.addPlot(length)
        # Datalogging must be enabled if we want to plot data.
        self.log(True)
        return self.frame.getPlot()

    def getFrame(self):
        """Return the device's frame."""
        return self.frame

    def stop(self):
        # print "stopping device thread..."
        self.keepGoing = False
        # print "device thread stopped."

        self.close()

    def plot(self, plot):
        self.frame.setHasPlot(plot)

    def begin(self, **kwargs):
        '''Start the device. 
   '''
        # Automatically refresh node data in callQuery
        self.refreshNodeDataInCallQuery = kwargs.get('auto_refresh_node', True)
        # if not self.refreshNodeDataInCallQuery:
        # print self, "will not automatically refresh node data"
        # traceback.print_stack()
        self.onBegin()
        # self.frame.setReadingIndex(self.settingResultIndices)
        self.configureDataLogging()
        # Each device NEEDS to run on a different thread
        # than the main thread (which ALWAYS runs the GUI).
        # This thread is responsible for querying the devices.
#        self.deviceThread = threading.Thread(target=self.callQuery, args=[])
#        # If the main thread stops, stop the child thread.
#        self.deviceThread.daemon = True
#        # Start the thread.
#        self.deviceThread.start()
        self.callQuery()

    def configureDataLogging(self):
        if self.isLogging():
            # print self, "is datalogging"
            self.frame.DataLoggingInfo()['name'] = self.name
            self.frame.DataLoggingInfo()['chest'] = dataChestWrapper(
                self, data_type=self.dataType)
            self.frame.DataLoggingInfo()[
                'lock_logging_settings'] = self.lockLoggingSettings
            if self.defaultLogLocation != None:
                # If the current directory is a subdirectory of the default,
                # then that is ok and the current directory should not be
                # changed.
                print "current location:", self.frame.DataLoggingInfo()['location']
                print "default:", self.defaultLogLocation
                if not(self.defaultLogLocation in self.frame.DataLoggingInfo()['location']):
                    print "Paths not ok"

                    self.frame.DataLoggingInfo()[
                        'location'] = self.defaultLogLocation
            self.datachest = self.frame.DataLoggingInfo()['chest']

    def onBegin(self):
        '''Called at the end of MDevice.begin(). This is called before 
        MView starts. This allows us to configure settings that 
        MView might use while starting. This might include datalog 
        locations or device-specific information.'''
        pass

    def loaded(self):

        print self, "loaded."
        self.onLoad()
        self.doneLoading = True

    def isLoaded(self):
        return self.doneLoading

    def onLoad(self):
        '''Called at the end of MGui.startGui(), when the main 
        MView GUI has finished loading. This allows the 
        MDevice to configure pieces of MView only available
        once the program has fully loaded.'''
        pass

    def onAddParameter(self, *args, **kwargs):
        '''Called when when a new parameter is added. 
    It is passed whatever MDevice.addParameter() is passed. 
    (Note: MDevice.onAddParameter() and MDevice.addParameter() 
    are different). This function must return a tuple in 
    the form ((str) Parameter Name, (int)Precision, (str) units)
   '''
        return (args[0], args[1], args[2])

    def setPrecisions(self, precisions):
        self.frame.setPrecisions(precisions)

    def setSigFigs(self, parameter, sigfigs):
        self.frame.setSigFigs(parameter, sigfigs)

    def _setReadings(self, readings, update=True):
        '''Tell the frame what the readings are so that they can be logged.

        :param readings: Type: list

   '''

        # readings = self.frame.getReadings()
        # print "set readings called"
        # traceback.print_stack()
        # if readings != None:
        # node = self.frame.getNode()
        # anchorData = []
        # # # print "HERE A"
        # if node is not None:

        # for input in node.getAnchors():
        # if input.getType() == 'input':
        # print "INPUT ANCHOR", input
        # data = input.getData()
        # if data != None and type(data) is list:
        # anchorData.append(data[-1])
        # elif data != None:
        # anchorData.append(None)
        # print "readigns:", readings
        # print "anchordata:", anchorData
        # readings.extend(anchorData)
        # print "comb readigns:", readings

        # else:
    def isOutOfRange(self, key):
        return self.frame.getOutOfRangeStatus(key)

    def setOutOfRange(self, key):
        # print self, key, "is out of range"
        self.frame.setOutOfRange(key)

    def setInRange(self, key):
        self.frame.setInRange(key)

    def disableRange(self):
        self.frame.disableRange()

    def setReading(self, parameter, reading):
        self.frame.setReading(parameter, reading)

    def getUnit(self, parameter):
        return self.frame.getUnit(parameter)

    def setUnit(self, parameter, unit):
        self.frame.setUnit(parameter, unit)

    def setPrecision(self, parameter, precision):
        self.frame.setPrecision(parameter, precision)

    def getPrecision(self, parameter):
        return self.frame.getPrecision(parameter)

    def getSigFigs(self, parameter):
        return self.frame.getSigFigs(parameter)

    def getReading(self, parameter):
        return self.frame.getReading(parameter)

    def setReadingIndex(self, parameter, index):
        self.frame.setReadingIndex(parameter, index)

    def getReadingIndex(self, parameter):
        return self.frame.getReadingIndex(parameter)

    def setCommand(self, parameter, command):
        # print "Setting command for", parameter, "is", command
        self.frame.setCommand(parameter, command)

    def getCommand(self, parameter):
        # print "Getting Parameter:",self.frame.getCommand(parameter)
        return self.frame.getCommand(parameter)

    def getParameters(self):
        return self.frame.getParameters()

    def getNicknames(self):
        return self.frame.getNicknames()

    def setParamVisibility(self, parameter, visible):
        self.frame.setParamVisibility(parameter, True)

    def getParamVisibility(self, paramteter):
        return self.frame.getParamVisibility(parameter)

    def getReadingIndex(self, parameter):
        return self.frame.getReadingIndex(parameter)
#    def addReading(self, reading, units=None, precision=None):
#        currReadings = self.frame.getReadings()
#        currReadings.extend(reading)
#        self.frame.setReadings(currReadings)
#
#        if precision == None:
#            currPrecisions = self.frame.getPrecisions()
#            currPrecisions.append(precisions)
#            self.frame.setPrecisions(precisions)
#        if units == None:
#            currUnits = self.frame.getUnits()
#            currUnits.append(units)
#            self.frame.setUnits(units)
#
#        self.updateContainer()

    def callQuery(self):
        '''Automatically called periodically, 
        determined by MDevice.Mframe.getRefreshRate(). 
        There is also a MDevice.Mframe.setRefreshRate()
        function with which the refresh rate can be configured.
        '''
        # print "-----------------------------------"
        if not self.keepGoing:
            return

        # self.lock.acquire()
        self.query()
        # self.lock.release()
        node = self.frame.getNode()
        if node is not None and self.refreshNodeDataInCallQuery:
            self.frame.getNode().refreshData()
        if self.datachest is not None and self.doneLoading:
            try:
                t1 = time.time()
                self.datachest.save()
                t2 = time.time()
            except:
                traceback.print_exc()

        if web.gui != None and web.gui.MAlert != None:
            web.gui.MAlert.monitorReadings(self)

        self.updateContainer()

        if self.keepGoing:
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
        """Adds a parameter to the GUI. The first argument is the name,
        the other arguments are specific to the device driver.
        """
        try:
            name = args[0]
        except:
            raise AttributError(
                "The first argument of addParameter() must be a name")

        show = kwargs.get("show", True)
        units = kwargs.get('units', None)
        sigfigs = kwargs.get('significant_figures', None)
        precision = kwargs.get('precision', None)
        if sigfigs is None and precision is None:
            precision = 2
        index = kwargs.get('index', None)
        log = kwargs.get("log", self.isLogging())
        self.frame.addParameter((name, units, precision))
        self.setReadingIndex(name, index)
        self.setPrecision(name, precision)
        self.setSigFigs(name, sigfigs)
        self.setUnit(name, units)
        self.onAddParameter(*args, **kwargs)
        self.frame.setParamVisibility(name, show)
        self.frame.DataLoggingInfo()['channels'][name] = log

    def logData(self, b):
        """Enable or disable datalogging for the device."""
        # if channels!= None:
        #    self.frame.DataLoggingInfo['channels'] = channels
        self.frame.enableDataLogging(b)

    def __str__(self):
        if self.frame.getTitle() is None:
            return "Unnamed Device"
        return self.frame.getTitle()
