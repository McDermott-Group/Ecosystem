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

class MPipeGraphicsItem(QtGui.QGraphicsPathItem):
    def __init__(self, startAnchor, scene, parent = None):
        QtGui.QGraphicsPathItem.__init__(self, parent = None)
        self.scene = scene
        self.path = QtGui.QPainterPath(startAnchor.getGlobalLocation())
        self.pen = QtGui.QPen()
        self.pen.setStyle(2);
        self.pen.setWidth(3)
        self.pen.setColor(QtGui.QColor(189, 195, 199))
        # Add itself to the scene
        self.scene.addItem(self)
        # Set up bounding rectangle
        self.bound = QtCore.QRectF(0,0,1,1)
        self.mousePos = QtCore.QPoint(0,0)
    def paint(self, painter, option, widget):
        self.prepareGeometryChange()
        if not self.isUnconnected():
            self.setBrush( QtGui.QColor(255, 0, 0) )
            self.setPath(self.path)
            path2 = QtGui.QPainterPath()
            path2.moveTo(self.startAnchor.getGlobalLocation())
            path2.lineTo(self.endAnchor.getGlobalLocation())
            painter.setPen(self.pen)
            painter.drawPath(path2)
    def sceneMouseMove(self, event):
        #print "Scene mouse move"
        self.origMouseMoveEvent(event)
        self.update()
        self.prepareGeometryChange()
        
    def mouseMoveEvent(self, event):
        self.update()
        self.prepareGeometryChange()
        QtGui.QGraphicsPathItem.mouseMoveEvent(self, event)
   
    def boundingRect(self):
      
        if not self.isUnconnected():
            #self.prepareGeometryChange()
            width = self.endAnchor.getGlobalLocation().x()- self.startAnchor.getGlobalLocation().x()
            height = self.endAnchor.getGlobalLocation().y()- self.startAnchor.getGlobalLocation().y()
            # Must do each rectange differently depending on the quadrant the line is in.
            if(width<0 and height<0):
                self.bound = QtCore.QRectF(self.startAnchor.getGlobalLocation().x()+width,self.startAnchor.getGlobalLocation().y()+height, width*-1, height*-1 )
            elif(width<0):
                self.bound = QtCore.QRectF(self.startAnchor.getGlobalLocation().x()+width,self.startAnchor.getGlobalLocation().y(), width*-1, height)
            elif(height<0):
                self.bound = QtCore.QRectF(self.startAnchor.getGlobalLocation().x(),self.startAnchor.getGlobalLocation().y()+height, width, height*-1 )
            else:
                self.bound = QtCore.QRectF(self.startAnchor.getGlobalLocation().x(),self.startAnchor.getGlobalLocation().y(), width,height)
            return self.bound
        else:
            return self.bound
   def destruct(self):
        '''This is where the pipe destroys itself :(. '''
        pass