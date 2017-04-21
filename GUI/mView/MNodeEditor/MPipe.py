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



class MPipe:
    def __init__(self, startAnchor, scene, parent = None):
       

        #startAnchor.parentNode().pipeConnected(startAnchor, self)
        # Create a new painter path starting at the location of the first anchor
        
        self.startAnchor = startAnchor
        self.endAnchor = None
        self.inputAnchor = None
        self.outputAnchor = None
        if startAnchor.getType()== 'output':
            self.label = str(startAnchor)
        self.data = None
        self.metadata = None
        
    def connect(self, endAnchor):
        '''Connect the other end of the pipe.'''
        if endAnchor.getType() == self.startAnchor.getType():
            print "Cannot connect two", endAnchor.getType(), "anchors together."
            raise ValueError("Invalid pipe connection.")
        self.inputAnchor = endAnchor
        self.outputAnchor = self.startAnchor
        if endAnchor.getType()== 'output':
            self.label = str(endAnchor)
            self.inputAnchor = self.startAnchor
            self.outputAnchor = self.endAnchor
        self.endAnchor = endAnchor
        
    def isUnconnected(self):
        return self.endAnchor == None

    def getStartAnchor(self):
        return self.startAnchor
        
    def getEndAnchor(self):
        return self.endAnchor
        
    def getData(self):
        return self.data
    
    def setData(self, data):
        
        self.data = data
        if self.inputAnchor != None:
            #print "pipe set data of ", self.inputAnchor
            self.inputAnchor.setData(data)
            self.inputAnchor.setMetaData(self.metadata)
    
    def getMetaData(self):
        return self.metadata
        
    def setMetaData(self, metadata):
        self.metadata = metadata
    def __str__(self):
        return str("Pipe: "+str(self.outputAnchor)+" -> "+str(self.inputAnchor))
    