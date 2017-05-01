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


from PyQt4 import QtGui, QtCore
from MPipe import MPipe
from MWeb import web
import time
from functools import partial
import traceback
from MReadout import MReadout


class MAnchor(object):
    def __init__(self, name, node, index,  parent=None, **kwargs):
        # Get the keyword arguments
        self.type = kwargs.get('type', 'output')
        self.suggestedDataType = kwargs.get('data', None)
        self.node = node
        # get the tree.
        self.tree = node.tree
       # self.nodeLayout = node.getNodeLayout()
        #self.nodeFrame= node.getNodeWidget()
        # Initialize the base class.
        super(MAnchor, self).__init__()
        # No pipe connected on instatiation.
        self.pipes = []
        # The parent node.
        self.parent = node
        # The data on the anchor.
        self.data = None
        # Data on the direct input.
        self.directInputData = 0
        # Name displayed next to the anchor
        self.param = name
        # Holds metadata
        self.metadata = None
        # Propagate
        self.propagate = True

    def parentNode(self):
        '''Return the node that the anchor belongs to.'''
        return self.parent

    def setParentNode(self, node):
        '''Set the parent node.'''
        self.parent = node

    def getType(self):
        '''Get the anchor type'''
        return self.type

    def getPipes(self):
        '''Get the pipe connected to the anchor'''
        return self.pipes

    def setPipes(self, pipes):
        self.pipes = pipes

    def addPipe(self, pipe):
        self.pipes.append(pipe)

    def pipeConnected(self, pipe):
        # print "anchor->pipeConnected:", pipe
        # self.addPipe(pipe)
        if self.getType() == 'output':
            self.setData(self.data)
        else:
            self.data = pipe.getData()

    # def update(self):
        # if self.parentNode().isDevice:
            # self.parentNode().getDevice().updateContainer()
        # self.graphicsItem.refresh()

    def getData(self):

        if len(self.pipes) != 0:
            return self.getPipes()[0].getData()
        else:
            return self.data

    def propagateData(self, p):
        # traceback.print_stack()
        # print "-------propagate set", p
        self.propagate = p

    def setMetaData(self, metadata):
        for pipe in self.pipes:
            if pipe != None and self.type == 'output':
                pipe.setMetaData(metadata)

            self.metadata = metadata

    def getMetaData(self):
        return self.metadata

    def setData(self, data, **kwargs):
        # print "anchor", self, "set data called"
        holdRefresh = kwargs.get('hold_refresh', False)
        self.data = data
        if not holdRefresh:
            for pipe in self.pipes:
                if pipe != None and self.type == 'output':
                    # print "Anchor", self, "of", self.parent, "setting pipe
                    # data"
                    pipe.setData(data)
                if self.type == 'input':
                    # print "Input anchor", self.parentNode()
                    # print "propagateData:", self.propagate
                    if self.propagate:
                        # print "Pipes:", [str(pipe) for pipe in self.pipes]
                        # print "Calling refresh data from node:", self.parent,
                        # ", Anchor:", self
                        self.parentNode().refreshData()
                        if self.parentNode().getDevice() != None:
                            self.parentNode().getDevice().updateContainer()
                        pass

        # self.lcd.display(data)
    def propogateRefresh():
        self.setData(self.data)

    def disconnect(self):
        '''Disconnect and delete the pipe'''
        self.tree.deletePipe(self.pipe)

    def connect(self, pipe):
        # print "connect function called"
        self.addPipe(pipe)

    def isConnected(self):
        return not self.getPipes() == []

    def __str__(self):
        return str(self.param)
