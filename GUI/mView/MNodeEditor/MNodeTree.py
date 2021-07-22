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


from MPipe import MPipe
import os
import sys
import inspect
from glob import glob
from MWeb import web


class NodeTree:
    scene = None
    pipes = []
    # def __init__(self):
    nodes = []
    # print os.getcwd()
    path = os.path.dirname(os.path.abspath(
        inspect.getfile(inspect.currentframe())))

    os.chdir(path + "\MNodes")
    # print os.getcwd()
    for file in glob("*.py"):
        web.nodeFilenames.append(file)
        # print file

    def getPipes(self):
        '''Returns all pipes in the tree.'''
        return self.pipes

    def addPipe(self, pipe):
        '''Add a pipe to the tree.'''
        self.pipes.append(pipe)
        return self.pipes[-1]

    def deletePipe(self, pipeToDel):
        '''Delete pipe from tree'''

        pipeToDel.setLabel(None)
        start = pipeToDel.getStartAnchor()
        end = pipeToDel.getEndAnchor()
        start.connect(None)
        if end != None:
            end.connect(None)

        for i, pipe in enumerate(self.pipes):
            if pipe is pipeToDel:
                self.pipes[i] = None
                del self.pipes[i]
        start.parentNode().pipeDisconnected()
        if end != None:
            end.parentNode().pipeDisconnected()

    def connect(self, anchor, endAnchor=None):
        '''Connect anchors with a pipe.'''
        try:
            # print "endAnchor:", endAnchor
            # print "anchor:", anchor
            if endAnchor != None:
                pipe = MPipe(anchor, self.scene)
                self.pipes.append(pipe)
                self.pipes[-1].connect(endAnchor)
                endAnchor.connect(self.pipes[-1])
                endAnchor.parentNode().pipeConnected(endAnchor, self.pipes[-1])
                endAnchor.pipeConnected(self.pipes[-1])
            else:
                if len(self.getPipes()) == 0:
                    # print "adding pipe"
                    pipe = self.addPipe(MPipe(anchor, self.scene))
                else:
                    # print "A pipe exists"
                    if self.getPipes()[-1].isUnconnected():
                        self.getPipes()[-1].connect(anchor)
                        pipe = self.getPipes()[-1]
                    else:
                       # print "Creating pipe"
                        pipe = self.addPipe(MPipe(anchor, self.scene))

                anchor.pipeConnected(pipe)
                anchor.parentNode().pipeConnected(anchor, pipe)

            anchor.connect(pipe)
        except ValueError as e:
            # print "ERROR:",e
            self.deletePipe(self.pipes[-1])

    def addNode(self, node):
        # node.setScene(self.scene)
        node.setTree(self)
        node.begin()
        self.nodes.append(node)
        return node

    def getNodes(self):
        return self.nodes

    def getGuiNodes(self):
        return [node for node in self.getNodes() if node.getType() == 'output']
