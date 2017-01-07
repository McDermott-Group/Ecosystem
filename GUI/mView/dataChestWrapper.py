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
import atexit

import threading
import datetime as dt
from PyQt4 import QtCore, QtGui


from dateStamp import *
from dataChest import *
import os
import traceback
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
        # These arrays will hold all dataChest data sets.
        self.dataSet = None
        self.hasData = None
        # The done function must be called when the GUI exits.
        atexit.register(self.done)
        self.dataSet = None
        self.hasData = False
        self.keepLoggingNan = True
        self.dStamp = dateStamp()
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
               
               # self.dataSet = dataChest()
                
                #self.dataSet.cd("")
                #root =   os.path.abspath(self.dataSet.pwd())
                root = os.environ['DATA_CHEST_ROOT']
                relativePath =  os.path.relpath(location, root)
                if relativePath == '.':
                    raise IOError("Cannot create dataset directly under DATA_CHEST_ROOT.")
                    
                print "Root Location:", root
                print "relativePath:", relativePath
                path = relativePath.split("\\")
                print "path:",path
                #self.dataSet.cd('')
                self.dataSet = dataChest(path[0])
                self.dataSet.cd('')
                print "self.dataSet.pwd():", self.dataSet.pwd().replace("/","\\")
                print "location:",location
                relativepath = os.path.relpath(location, self.dataSet.pwd().replace("/","\\"))
                print "second relative path:", relativePath
               
                path = relativePath.split("\\")
                
                for folder in path[1::]:
                    self.dataSet.cd(folder)
               

                #self.dataSet = dataChest(path[0])
                #self.dataSet.cd(relativePath)
                
                print "Configuring datalogging for", str(self.device)+" located at", location
                
        if location == None:
           self.dataSet = dataChest(str(now.year))
           try:
                self.dataSet.cd(str(now.month))
           except:
                self.dataSet.mkdir(str(now.month))
                self.dataSet.cd(str(now.month))

           try:
                self.dataSet.cd(str(int(now.day / 7)))
           except:
                self.dataSet.mkdir(str(int(now.day / 7)))
                self.dataSet.cd(str(int(now.day / 7)))
                
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
                print("Existing data set found for %s: %s."
                        %(title, existingFiles[0][y]))
        # If the dataset does not already exist, we must create it.
        if not foundit:
            print("Creating dataset for %s." %title)
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
            nicknames = self.device.getFrame().getNicknames()
            for y in range(len(nicknames)):
                # If the name of the parameter has not been defined as
                # None in the constructor, then we want to log it.
                if nicknames[y] is not None:
                    # The name of the parameter in the dataset is
                    # the same name displayed on the GUI except without 
                    # non-alphanumerical characters. Use regular
                    # expressions to do this.
                    paramName = str(nicknames[y]).replace(" ","")
                    paramName = re.sub(r'\W+', '', paramName)
                    # Create the tuple that defines the parameter.
                    tup = (paramName, [1], "float64",
                            str(self.device.getFrame().getUnits()[y]))
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
            if self.device.getFrame().getYLabel() is not None:
                # Configure the label of the y axis given in the
                # device's constructor.
                self.dataSet.addParameter("Y Label",
                        self.device.getFrame().getYLabel())
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
        
        if self.device.getFrame().getReadings() is not None:
            # If the device did not have any readings and now it does
            # then we want to create a dataset.
            if not self.hasData:
                self.configureDataSets()
        if self.hasData:
            depvars = []
            indepvars = []
            vars = []
            readings = []

            currentlyLogging = False
            for y in range(len(self.device.getFrame().getNicknames())):
                # Channels that should be logged
                enabled = self.device.getFrame().DataLoggingInfo()['channels']
                nickname = self.device.getFrame().getNicknames()[y] 
                # This checks if the reading is displayed on the GUI
                # if it is not, then it does not include it in
                # the dataset.
                if nickname is not None and enabled[nickname]:
                    self.keepLoggingNan= True
                    currentlyLogging = True
                    devReadings = self.device.getFrame().getReadings()
                    # If the device has readings.
                    if devReadings is not None:
                        if devReadings[y] is not None:
                            readings.append(float(devReadings[y]))
                        else:
                            readings.append(np.nan)
                    else:
                        readings.append(np.nan)
                else:
                    readings.append(np.nan)

            # If the device has readings, add data to dataset.
            if(readings is not None and currentlyLogging):
              
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
                    print("%s: could not store data, this might be due"
                          " to a change made to the parameters of the "
                          "device, if this is the case then either "
                          "delete the data set from the current storage"
                          " directory or move it somewhere else."
                          %self.device.getFrame().getTitle())
          
                
            if self.keepLoggingNan and not currentlyLogging:
                self.done()

                self.keepLoggingNan = False
                currentlyLogging = False