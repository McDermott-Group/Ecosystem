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
__version__ = "1.0.1"
__maintainer__ = "Noah Meltzer"
__status__ = "Beta"

import traceback
import inspect
import MPersistentData
class web:
    """
    Organizes global variables. Allows all other classes to easily
    access important parameters central to mView. Stores and opens all
    data.
    """
    # Store minimum and maximum values for all readings. MAlert uses
    # this to check if readings are still in bounds.
    
    
    limitDict = {}
    # All devices.
    devices = []
    # The default refresh GUI rate.
    guiRefreshRate = 1
    # Holds reference to the telecomm server.
    telecomm = None
    # DPI scaling ratio.
    ratio = 1
    scrnHeight = None
    scrnWidth = None
    # List of virtual devices
    virtualDevices = []
    gui = None
    title = None
    nodeFilenames = []

    persistentData = None
    
   
    