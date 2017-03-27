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

class MNodeGraphicsItem(QtGui.QGraphicsItem):
    def __init__(self, parent = None, **args, **kwargs)
        QtGui.QGraphicsItem.__init__(self,parent)
         #default color'
        self.color = (50,50,50)
        self.nodeFrame = QtGui.QFrame()
    def begin(self,   **kwargs):
        self.scene.addItem(self)
        self.nodeLayout = QtGui.QGridLayout()
        self.font = QtGui.QFont()
        self.font.setPointSize(15)
        self.label = QtGui.QLabel(self.title,self.nodeFrame)
        self.label.setFont(self.font)
        self.label.setStyleSheet("color:rgb(189,195,199)")
        self.nodeLayout.addWidget(self.label, 0, 0)
        self.nodeFrame.setLayout(self.nodeLayout)
        pProxy = QtGui.QGraphicsProxyWidget(self)
        pProxy.setWidget(self.nodeFrame)
        # Tell the gui that the item is moveable, slectable, and focusable and that 
        # it accepts hover events.
        self.setFlag(QtGui.QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QtGui.QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QtGui.QGraphicsItem.ItemIsFocusable, True)
        self.setAcceptsHoverEvents(True)
        # Bounding rectangles
        self.rect = QtCore.QRectF(0, 0, self.nodeFrame.width(),self.nodeFrame.height())
        self.rect2 = QtCore.QRectF(-20, -20, 220,220)
        # Tell the gui that the item is moveable, slectable, and focusable and that 
        # it accepts hover events.
        self.textPen = QtGui.QPen()
        self.textPen.setWidth(2)
        self.textPen.setColor(QtGui.QColor(189, 195, 199))
        self.nodeBrush = QtGui.QBrush(QtGui.QColor(*self.color))
    def getNodeWidget(self):
        return self.nodeFrame
        
    def getNodeLayout(self):
        return self.nodeLayout
    def addAnchor(self, anchor=None, **kwargs):
        self.rect = QtCore.QRectF(0, 0, self.nodeFrame.width(),self.nodeFrame.height())
        self.rect2 = QtCore.QRectF(0, 0,self.nodeFrame.width(),self.nodeFrame.height())
        
    def setColor(self,r, g, b):
            self.color = (r, g, b)
            self.nodeFrame.setStyleSheet(".QFrame{background:rgba("+str(r)+','+str(g)+','+str(b)+', 20)}')
    def getColor(self):
        return self.color
        
    def setScene(self, scene):
        self.scene = scene
        
    def setTitle(self, title): 
        self.label.setText(title)
            
    def hoverEnterEvent(self, event):
        self.prepareGeometryChange()
        self.textPen.setStyle(QtCore.Qt.DotLine)
        QtGui.QGraphicsItem.hoverEnterEvent(self, event)
        
    def hoverLeaveEvent(self, event):
        self.prepareGeometryChange()
        self.textPen.setStyle(QtCore.Qt.SolidLine)
        QtGui.QGraphicsItem.hoverLeaveEvent(self, event)
        
    def mouseMoveEvent(self, event):
        self.prepareGeometryChange()
        QtGui.QGraphicsItem.mouseMoveEvent(self, event)
        
    def mousePressEvent(self, event):
        self.prepareGeometryChange()
        QtGui.QGraphicsItem.mousePressEvent(self, event)
        
    def boundingRect(self):
        return self.rect2
        
    def paint(self, painter, option, widget):
        self.rect2.setHeight(self.nodeFrame.height())
        self.rect2.setWidth(self.nodeFrame.width())

        painter.setBrush(self.nodeBrush)
        painter.setPen(self.textPen)
        painter.setFont(self.font)
        painter.drawRect(self.rect2)
