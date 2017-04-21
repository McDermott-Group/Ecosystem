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


from MNodeEditor.MNode import MNode
from MNodeEditor.MAnchor import MAnchor
import traceback
from PyQt4 import QtCore, QtGui
from functools import partial
import numpy as np
import time
class MDeviceNode(MNode):
    def __init__(self, device, *args, **kwargs):
        super(MDeviceNode, self).__init__(None,*args, **kwargs)

        self.device = device
        self.title = str(device)
        #print "Adding Node for device:", device
        self.dontAddanotherparam = False
        
    def onBegin(self):
        self.device.getFrame().setNode(self)
        # If the node represents a labrad device, then the title displayed on the node
        # should be the same as the title of the device
        self.setTitle(self.device.getFrame().getTitle())
        # Without this next line, adding an anchor adds a parameter
        # and adding a parameter adds an anchor which causes an infinite
        # loop.
        nicknames = self.device.getFrame().getNicknames()
        self.dontAddanotherparam = True

        for i,param in enumerate(nicknames):
            self.addAnchor(MAnchor(param,self,  i+1, type = 'output'))
        devAnchor = self.addAnchor(name = 'Self', type = 'output')
        devAnchor.setData(self.getDevice())
        
        self.dontAddanotherparam = False
            #print "Adding anchor", self.getAnchors()[-1]
    def isPropogateData(self):
        return self.propogateData
        
    def getDevice(self):
        return self.device

    def anchorAdded(self, anchor, **kwargs):
        if not self.dontAddanotherparam:
            self.device.addParameter(str(anchor), None, None, **kwargs)
            pass
    def onRefreshData(self):
        try:
            for i, anchor in enumerate(self.getAnchors()):
               
                if str(anchor)=='Self':   
                    continue
                reading = self.device.getReading(str(anchor))
               
                if anchor.getType() == 'output' and anchor.param != 'Self' and reading != None:
                    try:
                        
                        data = self.device.getReading(str(anchor))
                        metadata = (str(anchor), self.device.getUnit(str(anchor)), None)
                        if data != None:
                            anchor.setMetaData(metadata)
                            anchor.setData(data)
                    except:
                        traceback.print_exc()
                elif anchor.getType() == 'input':
                    data = anchor.getData()
                    metadata = anchor.getMetaData()
                    if data != None:      
                        reading = data
                        self.device.setReading(str(anchor), reading)
                    if metadata != None:
                        self.device.setUnit(str(anchor), metadata[1])
        except:
            traceback.print_exc()
      