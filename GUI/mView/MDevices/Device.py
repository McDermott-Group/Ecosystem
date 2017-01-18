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

import atexit


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
        self.nicknames = []
        #Units for the settings to be used with the values on the GUI.
        self.settingUnits = []
        # List of the precisions for the values on the GUI.
        self.precisions = []
        # List of settings that the user wants run on their device.
        settings = []
        # The actual names of the settings.
        self.settingNames = []
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
        self.settingArgs =[]    
        self.settingResultIndices = []
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
        
    def addParameter(self, parameter, setting, arg=None, index=None,
            units=None, precision=2, **kwargs):
        
        self.frame.DataLoggingInfo()['channels'][parameter] = kwargs.get('log', True)
        self.settingNames.append(setting)
        self.settingResultIndices.append(index)
        self.nicknames.append(parameter)
        self.settingArgs.append(arg)
        self.settingUnits.append(units)
        self.precisions.append(precision)
        
    def connection(self, cxn):
        self.cxn = cxn
        self.ctx = cxn.context()

    def addButton(self, name, msg, action, arg=None):
        self.buttons.append([])
        #i = len(self.buttons) - 1
        button = self.buttons[-1]
        button.append(name)
        button.append(action)
        button.append(msg)
        button.append(arg)
        self.frame.setButtons(self.buttons)
        
    def setYLabel(self, yLbl, units=''):
        self.frame.setYLabel(yLbl, units)

    def selectDeviceCommand(self, cmd=None, arg=0):  
        self.setDeviceCmd = cmd
        self.selectedDevice = arg
    
    def begin(self):
      
        self.frame.setNicknames(self.nicknames)
        self.frame.setReadingIndices(self.settingResultIndices)
        self.frame.DataLoggingInfo()['name'] = self.name
        self.frame.DataLoggingInfo()['chest'] = dataChestWrapper(self)
        self.datachest = self.frame.DataLoggingInfo()['chest']
        # Each device NEEDS to run on a different thread 
        # than the main thread (which ALWAYS runs the GUI).
        # This thread is responsible for querying the devices.
        self.deviceThread = threading.Thread(target=self.query, args=[])
        # If the main thread stops, stop the child thread.
        self.deviceThread.daemon = True
        # Start the thread.
        self.deviceThread.start()

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
            print("Found device: %s." %self.serverName)
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
        try:
            print button
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
                        getattr(self.deviceServer,
                                actual_button[1])(actual_button[3])
                    # If just the setting needs to be run.
                    else:
                        getattr(self.deviceServer, actual_button[1])
            # Otherwise if there is no warning message, do not make
            # a popup.
            else:
                # If there is an argument that must be passed to
                # the setting.
                if actual_button[3] is not None:
                    getattr(self.deviceServer,
                            actual_button[1])(actual_button[3])
                else:
                    getattr(self.deviceServer, actual_button[1])
        except:
            traceback.print_exc()
            return

    def query(self):
        """Query the device for readings."""
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
                readings = []   # Stores the readings.
                units = []      # Stores the units.
                precisions = []
                for i in range(len(self.settingNames)):
                    # If the setting needs to be passed arguments
                    if self.settingArgs[i] is not None:
                        reading = getattr(self.deviceServer,
                                self.settingNames[i])(self.settingArgs[i],
                                context=self.ctx)
                    else:
                        reading = getattr(self.deviceServer,
                                self.settingNames[i])(context=self.ctx)
                    # If the reading has a value and units.
                    if isinstance(reading, Value):
                        pass
                    # If the reading is an array of values and units.
                    if isinstance(reading, ValueArray):
                        indices = self.settingResultIndices
                        if indices != None and \
                                isinstance(reading[indices[i]], Value):
                            reading = reading[indices[i]]
                        elif len(reading) == 1:
                            reading = reading[0]
                        else:
                            reading = reading[i]
                            
                    if isinstance(reading, Value):
                        #print "Received labrad Value type"
                        preferredUnits = self.settingUnits[i]
                        if preferredUnits is not None and \
                                reading.isCompatible(preferredUnits):
                            reading = reading.inUnitsOf(preferredUnits)
                        u = reading.units
                        #print "units:", u
                        readings.append(reading[u])
                        units.append(u)
                        precisions.append(self.precisions[i])
                    elif type(reading) is list:
                        for j in range(len(reading)):
                            rd = reading[j]
                            if isinstance(rd, Value):
                                preferredUnits = self.settingUnits[i]
                                if preferredUnits is not None and \
                                        rd.isCompatible(preferredUnits):
                                    rd = rd.inUnitsOf(preferredUnits)
                                u = rd.units
                                readings.append(rd[u])
                                units.append(u)
                                precisions.append(self.precisions[i])
                            else:
                                readings.append(reading[i])
                                units.append("")
                                precisions.append(self.settingPrecisions[i])
                    else:
                        try:
                            readings.append(reading)
                            units.append("")
                            precisions.append(self.precisions[i])
                        except:
                            print("Problem with readings, type '%s' "
                                  "cannot be displayed."
                                  %str(type(reading)))
                # Pass the readings and units to the frame.
                self.frame.setReadings(readings)
                #print "setting units"
                self.frame.setUnits(units)
                self.frame.setPrecisions(precisions)
                # Save the data.
                self.datachest.save()
                # If there was an error, retract it.
                self.frame.retractError()
            except IndexError as e:
                traceback.print_exc()
                print("[%s] Something appears to be wrong with what "
                      "the labrad server is returning."
                      %str(self.frame.getTitle()))
                print("\tReading: %s" %str(readings))
                print("\tUnits: %s" %units)
                print("\t%s" %str(e))
            except:
                traceback.print_exc()
                self.frame.raiseError("Problem communicating with %s."
                        %self.name)
                self.frame.setReadings(None)
                self.isDevice = False
        # Query calls itself again, this keeps the thread alive.
        if self.keepGoing:
            
            self.updateContainer()
            threading.Timer(self.frame.getRefreshRate(),
                    self.query).start()
        return