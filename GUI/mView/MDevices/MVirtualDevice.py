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


import MDevice
from MWeb import web


class MVirtualDevice(MDevice.MDevice):
    def __init__(self, *args, **kwargs):
        super(MVirtualDevice, self).__init__(*args)
        yLabel = kwargs.get("yLabel", "")
        custUnits = kwargs.get("units", "")
        # print "SETTING Y LABEL", yLabel, kwargs
        self.frame.setYLabel(yLabel, custUnits)

        # print "args:", args

        # web.virtualDevices.append(self)
        self.begin(auto_refresh_node=False)

    def onBegin(self):
        # print "--------beginning virt device---------"
        self.log(True)

    # def addParameter(self, *args, **kwargs):
    # name = args[0]
    # units = kwargs.get("units", None)
    # precision = kwargs.get("precision", 2)
    # self.frame.nicknames.append(name)
    # self.frame.units.append(units)
    # self.frame.precisions.append(precision)
    def addButton(self, *args, **kwargs):
        pass

    def onLoad(self):
        self.log(True)
        self.plot(True)
        self.configureDataLogging()

    def setYLabel(self, yLbl, **kwargs):
        units = kwargs.get(units, "")
        self.frame.setYLabel(yLbl, units)

    def query(self, *args):
        pass

    def setRefreshRate(self, *args):
        self.frame.setRefreshRate(period)

    def setPlotRefreshRate(self, period):
        self.frame.setPlotRefreshRate(period)

    def addPlot(self, length=None):
        # self.frame.addPlot(length)
        # Datalogging must be enabled if we want to plot data.
        self.frame.enableDataLogging(False)
        return self.frame.getPlot()
