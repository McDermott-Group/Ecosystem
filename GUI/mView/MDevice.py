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
from dataChestWrapper import dataChestWrapper
from MFrame import MFrame
class MDevice(object):
    def __init__(self, name):
        self.frame = MFrame()
        # Datachest wrapper.
        self.datachest = dataChestWrapper(self)
        atexit.register(self.stop)
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
    def logData(self, b):
        self.frame.enableDataLogging(b)

    
