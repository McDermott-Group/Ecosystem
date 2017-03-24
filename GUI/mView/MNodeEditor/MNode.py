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



from MAnchor import MAnchor
import traceback
from MWeb import web
class MNode(object):
    # Attribute that lets MView find this MNode
    
    def __init__(self, *args, **kwargs):
        
        web.nodes.append(self)
        

        self.tree = None
        #self.begin()
        self.anchors = []
        self.callAnchorAdded  = False
        
    def begin(self,  *args,  **kwargs):
        ''' Create a new node'''
        #print "wrong begin called"
        self.onBegin()
        pass
    def onBegin(self):
        pass
    def setTree(self, tree):
        self.tree = tree
        
    def setTitle(self, title): 
        self.title = title
    def propogateData(self, pd):
        self.propogateData = pd
        
    def isPropogateData(self):
        return self.propogateData
        
    def getTitle(self):
        return self.title
        
    def refreshData(self):
        #print "node:", str(self), "refresh data called"
        try:
           self.onRefreshData()
        except:
            traceback.print_exc()
            pass
    def onRefreshData(self):
        pass
    def getAnchors(self):
        return self.anchors
        
    def addAnchor(self, anchor=None, **kwargs):
        propagate = not kwargs.get('terminate', False)
        if anchor == None:
            name = kwargs.get('name', None)
            type = kwargs.get('type', None)
            suggestedData = kwargs.get('data', None)
            
            if name == None or type == None:
                raise RuntimeError("If no anchor is passed to MNode.addAnchor(), then \'name\', \'type\' keyword arguments must be given.")

            anchor = MAnchor(name, self, len(self.anchors), type = type, data = suggestedData) # adds itself
        anchor.propagateData(propagate)
        self.anchors.append(anchor)
        self.anchorAdded(anchor, **kwargs)
        
        return anchor

    def removeAnchor(self, anchor = None, **kwargs):
        #print "specified anchor:", anchor
        if anchor == None:
            #print "deleting last anchor"
            self.anchors[-1].delete()
            del self.anchors[-1]
        else:
            anchor.delete()
            for i, anc in enumerate(self.anchors):
                if anc is anchor:
                    del anchor[i]
    
    def getAnchorByName(self, name):
        #print "self.anchors:", [str(anchor) for anchor in self.anchors]
        for anchor in self.anchors:
            if str(anchor) == name:
                #print "Found anchor: ", anchor
                return anchor
        raise LookupError(str(name)+" is not a anchor in "+str(self)+".")
    def onLoad(self):
        self.callAnchorAdded = True
        pass
    def pipeDisconnected(self):
        pass
        
    def pipeConnected(self, anchor, pipe):
       pass
       
    def anchorAdded(self, anchor, **kwargs):
        pass
        
        
    def __str__(self):
        return self.title
    def setColor(self, r, g, b):
        pass

        
