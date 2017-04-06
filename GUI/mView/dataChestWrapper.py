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
__version__ = "1.0.0"
__maintainer__ = "Noah Meltzer"
__status__ = "Beta"

import re


import datetime as dt
import time
#from PyQt4 import QtCore, QtGui
from MWeb import web
import time
from dateStamp import *
from dataChest import *
import os
import traceback
from sys import getsizeof
class dataChestWrapper:
    """
    The dataChestWrapper class handles all datalogging. An instance 
    of dataChestWrapper should be created in the main class in order to
    begin datalogging.
    """
    def __init__(self, device):
        """Initiallize the dataChest."""
        # Define the current time.
       
        now = dt.datetime.now()
        # Create a devices reference that can be accessed 
        # outside of this scope.
        self.device = device
        self.device.getFrame().setDataChestWrapper(self)
        # These arrays will hold all dataChest data sets.
        self.dataSet = None
        
        # The done function must be called when the GUI exits.
        
        self.dataSet = None
        self.hasData = False
        self.keepLoggingNan = True
        self.dStamp = dateStamp()
        self.restoreState()
        
    def restoreState(self):
        dataname = web.persistentData.persistentDataAccess(None, 'DataLoggingInfo', str(self.device), 'name')
        channels = web.persistentData.persistentDataAccess(None, 'DataLoggingInfo', str(self.device), 'channels')
        location = web.persistentData.persistentDataAccess(None, 'DataLoggingInfo', str(self.device),  'location')
        #Do a sanity check
        #print "device:", self.device
        for nickname in self.device.getFrame().getNicknames():
            if channels == None or nickname not in channels.keys():
                channels = self.device.getFrame().DataLoggingInfo()['channels']
                print "Error when retreiving logged channels in config file, restoring to", channels
        if dataname is None:
            dataname = self.device.getFrame().getTitle()

        self.device.getFrame().DataLoggingInfo()['name'] = dataname
        if channels != None:
            self.device.getFrame().DataLoggingInfo()['channels'] = channels
        self.device.getFrame().DataLoggingInfo()['location'] = location
    def saveState(self):
        #print "saving"
        
        
            #web.persistentData.persistentDataAccess(device.getFrame().DataLoggingInfo(),"DataLoggingInfo", str(device))
        #print "saving datachest state to persistent data..."
        dataname = self.device.getFrame().DataLoggingInfo()['name']
        channels = self.device.getFrame().DataLoggingInfo()['channels']
        location = self.device.getFrame().DataLoggingInfo()['location']
        web.persistentData.persistentDataAccess(dataname, 'DataLoggingInfo', str(self.device), 'name')
        web.persistentData.persistentDataAccess(channels, 'DataLoggingInfo', str(self.device), 'channels')
        web.persistentData.persistentDataAccess(location, 'DataLoggingInfo', str(self.device), 'location')
        #print "datachest persistent data saved."
    def configureDataSets(self):
        """
        Initialize the datalogger, if datasets already exist, use them.
        Otherwise create new ones.
        """
        
        now = dt.datetime.now()
        self.hasData = True
        # Generate a title for the dataset. NOTE: if 
        # the title of the device is changed in the device's constructor
        # in the main class, then a different data set will be created. 
        # This is because datasets are stored using the name of
        # the device, which is what the program looks for when checking
        # if there are data files that already exist.
        title = str(self.device.getFrame().DataLoggingInfo()['name']).replace(" ", "_")
        # Datasets are stored in the folder 'DATA_CHEST_ROOT\year\month\'
        # Try to access the current month's folder, if it does not
        # exist, make it.
        location = self.device.getFrame().DataLoggingInfo()['location']
        # root = os.environ['DATA_CHEST_ROOT']
        # relativePath =  os.path.relpath(root, dir)
        # print "Configuring datalogging for", str(self.device)+" located at", location
        if location != None:
                root = os.environ['DATA_CHEST_ROOT']
                relativePath =  os.path.relpath(location, root)
                if relativePath == '.':
                    raise IOError("Cannot create dataset directly under DATA_CHEST_ROOT.")
                path = relativePath.split("\\")
                #print "path:", str(path[0])
                self.dataSet = dataChest(str(path[0]))
                self.dataSet.cd('')
                relativepath = os.path.relpath(location, self.dataSet.pwd().replace("/","\\"))
                path = relativePath.split("\\")
                
                for folder in path[1::]:
                    self.dataSet.cd(folder)
                #print "Configuring datalogging for", str(self.device)+" located at", location
                
        if location == None:
           
           folderName = time.strftime('%x').replace(' ', '_')
           folderName = folderName.replace('/','_')
           self.dataSet = dataChest(folderName)
           
           # try:
                # self.dataSet.cd(folderName)
           # except:
                # self.dataSet.mkdir(folderName)
                # self.dataSet.cd(folderName)
           try:
                self.device.getFrame().DataLoggingInfo()['location'] = os.path.abspath(
                     self.dataSet.pwd())
           except:
                 traceback.print_exc()
                
        # Look at the names of all existing datasets and check
        # if the name contains the title of the current device. 
        existingFiles = self.dataSet.ls()
        # foundit becomes true if a dataset file already exists.
        foundit = False
        # Go through all existing dataset files.
        for y in range(len(existingFiles[0])):
            # If the name of the file contains the (persistant) title 
            # generated by the code, open that dataset and use it.
            if title in existingFiles[0][y]:
                self.dataSet.openDataset(existingFiles[0][y], 
                    modify=True)
             
                foundit = True
                # If the number of variables in the data set has changed since last time,
                # Then we do not want to use the old dataset.
                
                if len(self.dataSet.getVariables()[1]) != len(self.device.getFrame().getNicknames()):
                    
                    foundit = False
                else:
                    #print("Existing data set found for %s: %s."
                         #   %(title, existingFiles[0][y]))
                     pass
        # If the dataset does not already exist, we must create it.
        if not foundit:
            # print("Creating dataset for %s." %title)
            # Name of the parameter. This is the name of the parameter
            # displayed on the gui except without spaces or 
            # non-alphanumerical characters.
            paramName = None
            # Arrays to hold any variables.
            depvars = []
            indepvars = []
            # For each device, assume it is not connected and we should
            # not log data until the GUI actually gets readings.
            # Loop through all parameters in the device.
            # print "Setting up datalogging for device", self.device.getFrame().getTitle()
            nicknames = self.device.getFrame().getNicknames()
           # print "Nicknames:", self.device.getFrame().getNicknames()
            for y, name in enumerate(nicknames):
                # If the name of the parameter has not been defined as
                # None in the constructor, then we want to log it.
                if name is not None:
                    # The name of the parameter in the dataset is
                    # the same name displayed on the GUI except without 
                    # non-alphanumerical characters. Use regular
                    # expressions to do this.
                    paramName = str(name).replace(" ","_")
                    paramName = re.sub(r'\W+', '', paramName)
                    # Create the tuple that defines the parameter.
                    #print self.device, "device units: ", self.device.getFrame().getUnits()
                    #print "nicknames:", nicknames
                    tup = (paramName, [1], "float64",
                            str(self.device.getUnit(name)))
                    # Add it to the array of dependent variables.
                    depvars.append(tup)
            # Get the datestamp from the datachest helper class.
            dStamp = dateStamp()
            # Time is the only independent variable.
            indepvars.append(("time", [1], "utc_datetime", "s"))
            # The vars variable holds ALL variables.
            vars = []
            vars.extend(indepvars)
            vars.extend(depvars)
            # Construct the data set
            self.dataSet.createDataset(title, indepvars, depvars)
            # The DataWidth parameter says how many variables 
            # (independent and dependent) make up the dataset.
            # DataWidth is used internally only.
            self.dataSet.addParameter("DataWidth", len(vars))
            
            #if self.device.getFrame().getYLabel() is not None:
                # Configure the label of the y axis given in the
                # device's constructor.
            
        self.device.getFrame().setDataSet(self.dataSet)

    def done(self):
        """
        Run when GUI is exited. Cleanly terminates the dataset 
        with NaN values.
        """
        
        dStamp = dateStamp()
        # If the dataset was being logged.
        if self.hasData:
            vars = []
            vars.append(dStamp.utcNowFloat())
            # Append NaN.
            try:
                for y in range(1, self.dataSet.getParameter("DataWidth")):
                    vars.append(np.nan)
                self.dataSet.addData([vars])
            except:
                traceback.print_exc()
                
    def save(self):
        '''Stores the data'''
        # For all datasets, check if there are readings
        #for i in range(0, len(self.devices)):
       # dStamp = dateStamp()
        #dStamp.utcNowFloat()
        
        t1 = time.time()
        if not self.hasData:
            
            self.configureDataSets()
        if self.hasData:
            #print "HERE E"
            
            depvars = []
            indepvars = []
            vars = []
            readings = []

            currentlyLogging = False
            #devReadings = self.device.getFrame().getReadings()
           # print "DevReadings:", devReadings
            enabled = self.device.getFrame().DataLoggingInfo()['channels']
            #print "enabled:", enabled
            
            custUnits = self.device.getFrame().getCustomUnits()
            if custUnits is '':
                nickname = self.device.getFrame().getNicknames()[0]
                custUnits = self.device.getUnit(nickname)
            if custUnits is None:
                custUnits = ''
            self.dataSet.addParameter("y_label", self.device.getFrame().getYLabel())
            #print "setting units:", custUnits
            self.dataSet.addParameter("custom_units", custUnits)
            for y,param in enumerate(self.device.getParameters()):
                # Channels that should be logged
                
                
                nickname = param
                # This checks if the reading is displayed on the GUI
                # if it is not, then it does not include it in
                # the dataset.
                #print self.device, "enabled: ",enabled
                try:
                    if nickname is not None and enabled[nickname]:
                        self.keepLoggingNan= True
                        currentlyLogging = True
                except:
                    traceback.print_exc()
                    
                    #print "readings:", devReadings
                    # If the device has readings.
                reading = self.device.getReading(param)
                if reading is not None and enabled[param]:
                    readings.append(float(reading))
                else:
                    readings.append(np.nan)

            # If the device has readings, add data to dataset.
            if(readings is not None and currentlyLogging):
                #print self.device, "is logging"
                indepvars.append(self.dStamp.utcNowFloat())
                depvars.extend(readings)
                vars.extend(indepvars)
                vars.extend(depvars)
                varslist = self.dataSet.getVariables()
                #print vars
                try:
                      self.dataSet.addData([vars])        
                except:
                    traceback.print_exc()
                    print("%s: Problem storing data. Will try to reconfigure data sets."
                          %self.device.getFrame().getTitle())
                    self.configureDataSets()
                
            if self.keepLoggingNan and not currentlyLogging:
                print self.device, "not logging"
                self.done()

                self.keepLoggingNan = False
                currentlyLogging = False
            t2 = time.time()
            #print "Time to save data for", self.device, ":", t2-t1