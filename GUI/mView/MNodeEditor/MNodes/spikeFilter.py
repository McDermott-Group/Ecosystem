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
__version__ = "0.0.1"
__maintainer__ = "Noah Meltzer"
__status__ = "Beta"

# Import MNodeEditor libraries
from MNodeEditor.MNode import MNode
from MNodeEditor.MAnchor import MAnchor
# Numpy to help with numbers
import numpy as np

class spikeFilter(MNode):
    def __init__(self, *args, **kwargs):
        '''Initialize parent, and begin the parent.'''
        # Initialize parent.
        super(spikeFilter, self).__init__(*args, **kwargs)
        # Begin parent.
        self.begin()
        # Set up variables to hold current and previous
        # reading
        self.prev = np.nan
        self.curr = np.nan
        
    def onBegin(self, *args, **kwargs):
        '''Called when parent finished beginning.'''
        # Anchor for the raw data input
        self.dataAnchor = self.addAnchor(name = 'raw_data', type = 'input')
        # Anchor for the threshold (we dont necessarily need 
        # to create an anchor for this, but we will anyway.)
        self.thresholdAnchor = self.addAnchor(name = 'threshold', type = 'input')
        # An anchor for the data output. 
        # Note that this anchor has an 'ouput' type.
        self.output = self.addAnchor(name = 'filtered_data', type = 'output')
        # Set the title of our node.
        self.setTitle("Spike Filter")
        
    def onRefreshData(self):
        '''Refresh anchor data.'''
        # Get the current reading from the data anchor.
        self.curr = self.dataAnchor.getData()
        # Get the threshold value from the threshold anchor.
        threshold = self.thresholdAnchor.getData()
        # If the previous reading is a valid number (not 
        # necessarily the case on startup) then continue.
        if self.prev != np.nan or self.prev != None:
                # If the absolute value of the difference is less than
                # the threshold...
               if abs(self.prev-self.curr) < threshold:
                    # Then set the data on the output anchor to the current reading.
                    self.output.setData(self.curr)
               else:
                    # Otherwise, the data should be nan.
                    self.output.setData(np.nan)
        # Update the previous value
        self.prev = self.curr
          