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
__version__ = "1.5.2"
__maintainer__ = "Noah Meltzer"
__status__ = "Beta"

from MWeb import web
import numpy as np
import traceback
import warnings
from pprint import pprint
import time


class MFrame:
    def __init__(self):
        """This class acts as the interface between the devices and all
        classes which use the device or any of its parameters."""
        # Name of device's server.
        self.serverTitle = None
        # Parameter names to be displayed on the GUI.
        # self.nicknames = []
        # Settings which are called by the GUI.
        # self.serverSettings = None
        # Device readings.
        # self.readings = []
        # Precisions.
        # self.precisions = []
        # Errors.
        self.error = False
        # Error messages.
        self.errmsg = None
        # Label on the y axis of the dataChest dataplot.
        self.yLabel = ""
        # Units used for each parameter.
        # self.units = []
        # Buttons on the GUI used to control the device.
        self.buttons = [[]]
        # Stores an index of a certain button.
        self.buttonInd = None
        # Is a specified button pushed?
        self.buttonPushed = False
        # Store the plots.
        self.isPlotBool = False
        # Just in case the user wants to label their NGui plot with
        # custom units (note these are only the units displayed onscreen,
        # not the units that the data is logged with).
        self.custUnits = ""
        # If the length of the graph should be plotted over a fixed interval.
        self.plotLength = None
        # Hold the datachest object.
        self.dataSet = None
        # Hold the plot.
        self.plot = None
        # # Datalogging disabled by default
        # self.logData = False
        # Datachest wrapper class
        self.dataChestWrapper = None
        # Dictionary holding datalogging settings
        self.datalogsettingsDict = {
            "logData": False,
            "location": None,
            "dataset": self.dataSet,
            "channels": {},
            "chest": None,
            "name": self.serverTitle,
            "lock_logging_settings": False,
        }

        restoredSettings = web.persistentData.persistentDataAccess(
            None, "DataLoggingInfo", self.serverTitle
        )
        # Is the parameter visible?
        self.paramVisibility = {}
        # name:[name, readings, units, precision]
        self.parameters = {}
        if restoredSettings != None:
            self.datalogsettingsDict = restoredSettings
        self.node = None
        self.container = None
        # Keeps track of order of parameters on GUI
        self.paramKeyOrder = []

    def setTitle(self, title):
        # print "Set title:", title
        self.serverTitle = title

    def getTitle(self):
        # print "Get Title:",self.serverTitle
        return self.serverTitle

    def getNicknames(self):
        # print "----------NICKNAMES WAS Got", self.nicknames
        names = self.getListOfParameterItems("name")
        # print "Getting nicknames:", names
        return self.getListOfParameterItems("name")

    def _setNicknames(self, nicknames):
        # print "Trying to set nicknames:", nicknames
        if len(nicknames) != len(list(self.parameters.keys())):
            raise ValueError(
                "The length of nicknames did not match the number of parameters."
                + "\nnames: "
                + str(nicknames)
                + "\n"
                + "Available Parameters: "
                + str(list(self.parameters.keys()))
            )

        for i, key in enumerate(self.parameters.keys()):
            self.setNickname(key, nicknames[i])

        # pprint(self.parameters)

        # print "---------- set nicknames NICKNAMES WAS SET", self.nicknames

    def setName(self, key, name):
        self.parameters[key]["name"] = name

    def _setReadings(self, readings):
        # print "-----Set Readings called:", readings
        # pprint(self.parameters)
        if len(readings) != len(list(self.parameters.keys())):
            raise ValueError(
                "The length of readings did not match the number of parameters."
                + "\nreadings: "
                + str(readings)
                + "\n"
                + "Available Parameters: "
                + str(list(self.parameters.keys()))
            )
        for i, key in enumerate(self.parameters.keys()):
            self.setReading(key, readings[i])

        # pprint(self.parameters)

    def setReading(self, name, reading):
        # traceback.print_stack()
        # print "name in MFrame:", name, reading
        try:
            self.parameters[name]["reading"] = reading
        except:
            warnings.warn(
                "Could not set reading of "
                + str(name)
                + ", it does not \
                        appear to be a parameter of "
                + str(self.getTitle())
            )

    def _getReadings(self):
        return self.getListOfParameterItems("reading")

    def getReading(self, parameter):
        try:
            return self.parameters[parameter]["reading"]
        except:
            warnings.warn("Could not get reading of " + str(parameter))

    def _setPrecisions(self, precisions):
        if len(precisions) != len(list(self.parameters.keys())):
            raise ValueError(
                "The length of precisions did not match the number of parameters."
                + "\nprecisions: "
                + str(precisions)
                + "\n"
                + "Available Parameters: "
                + str(list(self.parameters.keys()))
            )
        for i, key in enumerate(self.parameters.keys()):
            self.setPrecision(key, precisions[i])

    def setSigFigs(self, name, sigfigs):
        self.parameters[name]["sigfigs"] = sigfigs

    def getSigFigs(self, name):
        try:
            return self.parameters[name]["sigfigs"]
        except:
            warnings.warn("Could not get sigfigs of " + str(name))

    def setPrecision(self, name, precision):
        self.parameters[name]["precision"] = precision

    def getPrecision(self, name):
        try:
            return self.parameters[name]["precision"]
        except:
            warnings.warn("Could not get precision of " + str(name))

    def _getPrecisions(self):
        return self.getListOfParameterItems("precision")

    def setCommand(self, name, command):
        self.parameters[name]["command"] = command

    def getCommand(self, name):
        try:
            return self.parameters[name]["command"]
        except:
            warnings.warn("Could not get command of " + str(name))

    def setReadingIndex(self, name, index):
        # traceback.print_stack()
        try:
            self.parameters[name]["reading_index"] = index
        except:
            warnings.warn("Could not set reading index of " + str(name))

    def getReadingIndex(self, name):
        return self.parameters[name].get("reading_index", None)

    def raiseError(self, msg):
        self.error = True
        self.errmsg = msg

    def retractError(self):
        self.error = False
        self.errmsg = None

    def isError(self):
        return self.error

    def errorMsg(self):
        return self.errmsg

    def _setUnits(self, units):
        if len(units) != len(list(self.parameters.keys())):
            raise ValueError(
                "The length of units did not match the number of parameters."
                + "\nunits: "
                + str(units)
                + "\n"
                + "Available Parameters: "
                + str(list(self.parameters.keys()))
            )
        for i, key in enumerate(self.parameters.keys()):
            self.setUnit(key, units[i])

    def setUnit(self, name, unit):
        self.parameters[name]["units"] = unit

    def getUnit(self, parameter):
        try:
            return self.parameters[parameter]["units"]
        except:
            warnings.warn(
                "Could not get unit of "
                + str(parameter)
                + ", it does not \
                        appear to be a parameter of "
                + str(self.getTitle())
            )
            return None

    def getListOfParameterItems(self, itemkey):
        items = []
        for key in list(self.parameters.keys()):
            param = self.parameters[key]
            if param != None and itemkey in list(param.keys()):
                items.append(param[itemkey])
            else:
                items.append(None)
        return items

    def getParamKeyOrder(self):
        return self.paramKeyOrder

    def getCustomUnits(self):
        return self.custUnits

    def getButtons(self):
        return self.buttons

    def setButtons(self, buttons):
        self.buttons = buttons

    def appendButton(self, button):
        """Add another button to GUI."""
        self.buttons.append(button)

    def buttonPressed(self, buttonInd):
        self.buttonInd = buttonInd
        self.buttonPushed = True

    def getButtonPressed(self):
        self.buttonPushed = False
        return self.buttonInd

    def isButtonPressed(self):
        return self.buttonPushed

    def setYLabel(self, y, custUnits=""):
        self.custUnits = custUnits
        self.yLabel = y

    def getYLabel(self):
        return self.yLabel

    def addPlot(self, length=None):
        self.isPlotBool = True
        self.plotLength = length

    def setHasPlot(self, hasPlot):
        self.isPlotBool = hasPlot

    def isPlot(self):
        # print "is plot set to true"
        return self.isPlotBool

    def setPlot(self, p):
        self.plot = p

    def getPlot(self):
        return self.plot

    def setPlotRefreshRate(self, period):
        if self.getTitle() is None:
            raise IOError("Refresh Rates cannot be set until name is given to device.")
        web.persistentData.persistentDataAccess(
            period, "deviceRefreshRates", self.getTitle(), "plot"
        )

    def getPlotRefreshRate(self):
        # pprint.pprint(web.persistentDataDict)
        if self.getTitle() is None:
            raise IOError("Refresh Rates cannot be set until name is given to device.")
        return web.persistentData.persistentDataAccess(
            None, "deviceRefreshRates", self.getTitle(), "plot", default=1
        )

    def setRefreshRate(self, period):
        if self.getTitle() is None:
            raise IOError("Refresh Rates cannot be set until name is given to device.")

        web.persistentData.persistentDataAccess(
            period, "deviceRefreshRates", self.getTitle(), "readings"
        )

    def getRefreshRate(self):
        if self.getTitle() is None:
            raise IOError("Refresh Rates cannot be set until name is given to device.")
        return web.persistentData.persistentDataAccess(
            None, "deviceRefreshRates", self.getTitle(), "readings", default=1
        )

    def getPlotLength(self):
        return self.plotLength

    def setDataSet(self, dataSet):
        self.dataSet = dataSet

    def getDataSet(self):
        return self.dataSet

    def getDataChestWrapper(self):
        return self.dataChestWrapper

    def setDataChestWrapper(self, wrapper):
        self.dataChestWrapper = wrapper

    def enableDataLogging(self, b):
        self.datalogsettingsDict["logData"] = b

    def isDataLogging(self):
        return self.datalogsettingsDict["logData"]

    def DataLoggingInfo(self):
        # print "DATALOGGING INFO ACCESSED", self.datalogsettingsDict
        return self.datalogsettingsDict

    def getOutOfRangeStatus(self, key):
        return self.parameters[key]["out_of_range"]

    def setOutOfRange(self, key):
        self.parameters[key]["out_of_range"] = True

    def setInRange(self, key):
        self.parameters[key]["out_of_range"] = False

    def disableRange(self):
        for key in self.parameters:
            self.parameters[key]["out_of_range"] = False

    def setNode(self, node):
        self.node = node

    def getNode(self):
        return self.node

    def setContainer(self, container):
        self.container = container

    def getContainer(self):
        return self.container

    def setParameters(self, params):
        self.parameters = params

    def getParameter(self, name):
        try:
            return self.parameters[name]
        except:
            print(
                "Problem getting parameters for", name, ", could not find parameters."
            )

    def getParameters(self):
        return self.parameters

    def getParamAttr(self, *args, **kwargs):
        default = kwargs.get("default", None)
        curr = self.parameters[args[0]]
        for arg in args[1::]:
            if arg in list(curr.keys()):
                curr = curr[arg]
            else:
                curr[arg] = default

    def addParameter(self, params):
        """Adds to list of parameters displayed on the gui."""
        # print self.getTitle(), "----------add parameter called", params
        #        self.nicknames.append(params[0])
        #        self.precisions.append(params[1])
        #        self.units.append(params[2])
        #        self.readings.append(None)
        order = len(self.parameters)

        self.parameters[params[0]] = {
            "name": params[0],
            "reading": None,
            "units": params[1],
            "precision": params[2],
            "out_of_range": False,
        }
        self.paramKeyOrder.append(params[0])
        # print "---------- add parameter NICKNAMES WAS SET", self.parameters

    def setParamVisibility(self, param, visible):
        """Set whether or not a parameter shows up on the GUI."""
        if param in list(self.parameters.keys()):
            self.parameters[param]["visible"] = visible
        else:
            self.parameters[param] = {}
            self.parameters[param]["visible"] = visible

    def isParamVisible(self, param):
        """Get the visibility of a parameter."""
        return self.parameters[param]["visible"]

    def getRawDataSet(self, param):
        """Get a tuple structured as (name, units, [1-d data])."""

        origparam = param
        param = param.replace(" ", "_")
        # print "looking for", param
        # print "Variables: ", self.dataSet.getVariables()
        # print "data: ", np.transpose(self.dataSet.getData())
        loc = None
        # print "enumerate(self.dataSet.getVariables())",
        # enumerate(self.dataSet.getVariables())

        try:
            for i, var in enumerate(self.dataSet.getVariables()[1]):
                # print "var[0]:", var[0]
                if param == var[0]:
                    # print "Found it!"
                    loc = i
            if loc == None:
                return None
            t1 = time.time()
            data = list(np.transpose(self.dataSet.getData())[loc + 1])
            t2 = time.time()
            # Append the most recent reading as it is not yet in
            # the data set.

            # data.append(self.parameters[origparam]['reading'])
            # print "data retreived"
            variable = self.dataSet.getVariables()[1][loc][0]

            # print "------Time to get Raw data:", t2-t1
            return (variable, self.parameters[origparam]["units"], data)
        except:
            # traceback.print_exc ()
            return None

        # return self.dataSet.getVariables
