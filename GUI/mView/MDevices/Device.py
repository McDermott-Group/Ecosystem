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
__version__ = "2.0.2"
__maintainer__ = "Noah Meltzer"
__status__ = "Beta"




import labrad
from labrad.units import Value, ValueArray
from dataChestWrapper import dataChestWrapper
# from dataChestWrapper import dataChestWrapper
# from MFrame import MFrame
import MPopUp
from MDevice import MDevice
import threading

from MWeb import web
import traceback
from sys import getsizeof
from PyQt4 import QtGui, QtCore
class Device(MDevice):
    """The device class handles a LabRAD device."""
    def __init__(self, *args):

        super(Device, self).__init__(*args)

        # Get all the stuff from the constructor.
        # Has a the device made an appearance, this is so we dont alert
        # the user more than once if a device dissapears.
        self.foundDevice = False
        self.name = args[0]
        # Nicknames of settings (the ones that show up on the GUI).
        #self.nicknames = []
        #Units for the settings to be used with the values on the GUI.
        #self.settingUnits = []
        # List of the precisions for the values on the GUI.
        #self.precisions = []
        # List of settings that the user wants run on their device.
        settings = []
        # The actual names of the settings.
        #self.settingNames = []
        # Stores the actual reference to the labrad server.
        deviceServer = None
        # True if device is functioning correctly.
        self.isDevice = False
        # Used for device.select_device(selectedDevice) setting.
        self.selectedDevice = 0
        # Store the setting to select device (almost always
        # 'select_device').
        self.setDeviceCmd = None    
        # Store the buttons along with their parameters.
        buttons = [[]]
        # Arguments that should be passed to settings if necessary.
        #self.settingArgs =[]    
        #self.settingResultIndices = []
        self.frame.setYLabel(None)
        
        # Determine which buttons get messages.
        self.buttonMessages = []
        # Setup all buttons.
        self.buttonNames = []
        self.buttonSettings = []
        self.buttons = []
    
        # Tells thread to keep going.
        self.keepGoing = True
        
        self.frame.setTitle(self.name)
        

    def setServerName(self, name):
        self.serverName = name
        
    def onAddParameter(self, parameter, setting = None, arg=None, **kwargs):
        precision = kwargs.get('precision', 2)
        units = kwargs.get('units', None)
        index = kwargs.get('index', None)
        self.frame.DataLoggingInfo()['channels'][parameter] = kwargs.get('log', True)
        
        self.setCommand(parameter, [setting, arg])
        self.setReadingIndex(parameter, index)
        self.setPrecision(parameter, precision)
        #self.nicknames.append(parameter)
        #self.settingArgs.append(arg)
        #self.settingUnits.append(units)
        #self.precisions.append(precision)
        self.setParamVisibility(parameter, True)
        
        return (parameter, units, precision)
    def connection(self, cxn):
        self.cxn = cxn
        self.ctx = cxn.context()

    def addButton(self, name, msg, action, arg=None):

        button = []
        button.append(name)
        button.append(action)
        button.append(msg)
        button.append(arg)
        self.addButtonToGui(button)
        
    def setYLabel(self, yLbl, units=''):
        self.frame.setYLabel(yLbl, units)

    def selectDeviceCommand(self, cmd=None, arg=0):  
        self.setDeviceCmd = cmd
        self.selectedDevice = arg
    
    def onBegin(self):
        #print "onbegin here"
        #self.frame.setNicknames(self.nicknames)
        
        self.frame.DataLoggingInfo()['name'] = self.name
        self.frame.DataLoggingInfo()['chest'] = dataChestWrapper(self)
        self.datachest = self.frame.DataLoggingInfo()['chest']
        # # Each device NEEDS to run on a different thread 
        # # than the main thread (which ALWAYS runs the GUI).
        # # This thread is responsible for querying the devices.
        # self.deviceThread = threading.Thread(target=self.query, args=[])
        # # If the main thread stops, stop the child thread.
        # self.deviceThread.daemon = True
        # # Start the thread.
        # self.deviceThread.start()

    def setRefreshRate(self, period):
      
        if  self.frame.getTitle()is None:
            raise IOError("Refresh Rates cannot be set until name is given to device.")
       
        if self.frame.getRefreshRate() == None:
             self.frame.setRefreshRate(period)
    def setPlotRefreshRate(self, period):

        if  self.frame.getTitle()is None:
            raise IOError("Refresh Rates cannot be set until name is given to device.")
        if self.frame.getPlotRefreshRate() == None:
            self.frame.setPlotRefreshRate(period)

    def addPlot(self, length=None):
        self.frame.addPlot(length)
        # Datalogging must be enabled if we want to plot data.
        self.frame.enableDataLogging(True)
        return self.frame.getPlot()

    def connect(self):  
        """Connect to the device."""
        try:
            # Attempt to connect to the server given the connection 
            # and the server name.
            self.deviceServer = getattr(self.cxn, self.serverName)()
            # If the select device command is not None, run it.
            if self.setDeviceCmd is not None:
                getattr(self.deviceServer,
                        self.setDeviceCmd)(self.selectedDevice,
                                           context=self.ctx)
            #print("Found device: %s." %self.serverName)
            return True
        except:
            # The nFrame class can pass an error along with a message.
            traceback.print_exc()
            self.frame.raiseError("LabRAD issue.")
            return False
        
    # def getFrame(self):
        # """Return the device's frame."""
        # return self.frame

    # def logData(self, b):
        # self.frame.enableDataLogging(b)
    
    def prompt(self, button):
        """If a button is clicked, handle it."""#name action msg arg
        #print "button clicked:", button
        # button.append(name)
        # button.append(action)
        # button.append(msg)
        # button.append(arg)
        # [name, action, msg, arg]
        #    0     1      2    3
        resp = None
        try:
            actual_button = button
            # If the button has a warning message attatched.
            if actual_button[2] is not None:
                # Create a new popup.
                self.warning = MPopUp.PopUp(actual_button[2])
                # Stop the main GUI thread and run the popup.
                self.warning.exec_()
                # If and only if the 'ok' button is pressed.
                if self.warning.consent:
                    # If the setting associated with the button also 
                    # has an argument for the setting.
                    
                    if actual_button[3] is not None:
                        resp = getattr(self.deviceServer,
                                actual_button[1])(actual_button[3], context=self.ctx)
                    # If just the setting needs to be run.
                    else:
                        print "actual button:", actual_button
                        resp = getattr(self.deviceServer, actual_button[1])(context=self.ctx)
            # Otherwise if there is no warning message, do not make
            # a popup.
            else:
                # If there is an argument that must be passed to
                # the setting.
                if actual_button[3] is not None:
                    resp = getattr(self.deviceServer,
                            actual_button[1])(actual_button[3], context=self.ctx)
                else:
                    resp = getattr(self.deviceServer, actual_button[1])(context=self.ctx)
            print "Response:", resp
            
            if resp != None:
                p = QtGui.QMessageBox()
                p.setText(str("Response: "+str(resp)))
                p.setWindowTitle("Query Response")
                p.exec_()
        except:
            traceback.print_exc()
            return

    def query(self):
        """Query the device for readings."""
        #print "size of", self, ":", getsizeof(self)
        # If the device is attached.
        #print "querying device"
        if not self.isDevice:
            # Try to connect again, if the value changes, then we know 
            # that the device has connected.
            if self.connect() is not self.isDevice:
                self.isDevice = True
        # Otherwise, if the device is already connected.
        
        else:
            try:
                #readings = []   # Stores the readings.
                #units = []      # Stores the units.
                #precisions = []
                for i, name in enumerate(self.getParameters()):
                    command = self.getCommand(name)
                   # print "command:", command
                    if command[0] is None:
                        #print "found none setting for", name
                        #units.append(None)
                        #readings.append(None)
                        #precisions.append(None)
                        continue
                    # If the setting needs to be passed arguments
              
                    #print "Name of setting", self.settingNames[i]
                    if command[1] is not None:
                        reading = getattr(self.deviceServer,
                                command[0])(command[1],
                                context=self.ctx)
                    else:
                        reading = getattr(self.deviceServer,
                                command[0])(context=self.ctx)

                    # If the reading is an array of values and units.
                    if isinstance(reading, ValueArray):
                        index = self.getReadingIndex(name)
                        units = reading.units
                        if index != None and \
                                isinstance(reading[index], Value):
                            reading = reading[index]
                        elif len(reading) == 1:
                            reading = reading[0]
                        else:
                            reading = reading[i]
                        self.setReading(name, reading)
                        self.setUnit(name, units)
                    if isinstance(reading, Value):
                        #print "Received labrad Value type"
                        
                        preferredUnits = self.getUnit(name)
                        if preferredUnits is not None and \
                                reading.isCompatible(preferredUnits):
                            reading = reading.inUnitsOf(preferredUnits)
                        u = reading.units
#                        print "---------------------"
#                        print "name:", name                        
#                        print "units:", u
#                        print "value:", reading._value
                        self.setReading(name, reading._value)
                        self.setUnit(name, u)
                        
                    elif type(reading) is list:
                        for j in range(len(reading)):
                            rd = reading[j]
                            if isinstance(rd, Value):
                                preferredUnits = self.getUnit(name)
                                if preferredUnits is not None and \
                                        rd.isCompatible(preferredUnits):
                                    rd = rd.inUnitsOf(preferredUnits)
                                u = rd.units
         
                                self.setReading(name, rd._value)
                                self.setUnit(name, u)
                                #precisions.append(self.precisions[i])
                            else:
                                self.setReading(name,reading[i])
                                self.setUnit(name, "")
                                #precisions.append(self.settingPrecisions[i])
                    else:
                        try:
                            self.setReading(name,reading)
                            self.setUnit(name, "")
                            #precisions.append(self.precisions[i])
                        except:
                            print("Problem with readings, type '%s' "
                                  "cannot be displayed."
                                  %str(type(reading)))

                # Pass the readings and units to the frame.
                #self.setReadings(readings, False)
                #print "setting units"
                #self.frame.setUnits(units)
                #self.frame.setPrecisions(precisions)

                # If there was an error, retract it.
                self.frame.retractError()
            except IndexError as e:
                traceback.print_exc()
                print e
                print("[%s] Something appears to be wrong with what "
                      "the labrad server is returning."
                      %str(self.frame.getTitle()))

            except:
                traceback.print_exc()
                self.frame.raiseError("Problem communicating with %s."
                        %self.name)
               # self.frame.setReading(str(self),None)
                self.isDevice = False
        # Query calls itself again, this keeps the thread alive.
        #if self.keepGoing:
     
        
        return