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
     def __init__(self, *args):
         super(Device, self).__init__(*args)
         self.frame.setTitle = args[0]
         web.virtualDevices.append(self)
     def addParameter(self, *args, **kwargs)
        name = args[0]
        units = kwargs.get("units", None)
        precision = kwargs.get("precision", 2)
        
        self.nicknames.append(name)
        elf.settingUnits.append(units)
        self.precisions.append(precision)
    def addButton(self, *args, **kwargs):
        pass
    def setYLabel(self, yLbl, **kwargs):
        units = kwargs.get(units, '')
        self.frame.setYLabel(yLbl, units)
    def query(self, *args):
        pass
    def setRefreshRate(self, *args):
        self.frame.setRefreshRate(period)
    def setPlotRefreshRate(self, period):
        self.frame.setPlotRefreshRate(period)
    def addPlot(self, length=None):
        self.frame.addPlot(length)
        # Datalogging must be enabled if we want to plot data.
        self.frame.enableDataLogging(True)
        return self.frame.getPlot()
    def query(self):
        pass