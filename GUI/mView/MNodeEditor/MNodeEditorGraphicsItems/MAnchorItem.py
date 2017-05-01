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


class MAnchorGraphicsItem(QtGui.QGraphicsItem):
    def __init__(self, parent=None, *args, **kwargs):
        QtGui.QGraphicsItem.__init__(self, parent)
        self.setFlag(QtGui.QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QtGui.QGraphicsItem.ItemIsFocusable, True)
        self.setAcceptsHoverEvents(True)
         # The QGraphics scene
        self.scene = node.scene
        # Add the anchor to the scene
        self.scene.addItem(self)
        # Configure the anchor based on its type
        self.setParentItem(node)
        # Configure the brush
        self.posY = 70 + 30 * self.index
        # Where is the anchor relative to the rest
        self.index = index
        self.directInput = None
        self.okDirectInput = None
        self.directInputLayout = None
        self.directInputData = 0
        self.nodeBrush = QtGui.QBrush(QtGui.QColor(*node.getColor()))

        self.anchorSize = int(8 * web.ratio)
        self.rect = QtCore.QRectF(
            self.posX,  self.posY, self.anchorSize,  self.anchorSize)

        # The QPen
        self.textPen = QtGui.QPen()
        self.textPen.setStyle(2);
        self.textPen.setWidth(2)
        self.textPen.setColor(QtGui.QColor(189, 195, 199))

        self.label = QtCore.QString(self.param)

    if self.type == 'output':
        # Bounding rectangle of the anchor
        self.posX = self.nodeFrame.width()

    elif self.type == 'input':
        self.posX = -20
    self.width = QtGui.QFontMetrics(self.font).boundingRect(label).width()
    # self.update(self.rect)
    self.labelWidget = QtGui.QLabel(self.label, self.nodeFrame)
    self.labelWidget.setStyleSheet("color:rgb(189, 195, 199)")
    self.nodeLayout.addWidget(self.labelWidget, self.index + 2, 0)
    self.lcd = MReadout(self.nodeFrame)

    self.lcd.setStyleSheet("color:rgb(189, 195, 199);\n")
    self.nodeLayout.addWidget(self.lcd, self.index + 2, 1)

    label = QtCore.QString(self.param)
    self.font = QtGui.QFont()
    self.font.setPointSize(10)

    if self.suggestedDataType == 'float':

        self.directInput = QtGui.QLineEdit(
            str(self.directInputData), self.nodeFrame)
        self.directInput.setValidator(QtGui.QDoubleValidator())
        self.directInput.textEdited.connect(
            partial(self.directInput.setStyleSheet, "background:rgb(0,255,0);"))
        self.directInputLayout = QtGui.QHBoxLayout()

        self.okDirectInput = QtGui.QPushButton("Set", self.nodeFrame)
        self.okDirectInput.clicked.connect(
            partial(self.directInputHandler, 'float',  self.directInput.text))
        width = self.okDirectInput.fontMetrics().boundingRect("Set").width()
        height = self.okDirectInput.fontMetrics().boundingRect("Set").height()
        self.okDirectInput.setMaximumWidth(width + 10)
        self.okDirectInput.setMaximumHeight(height + 5)
        self.lcd.hide()
    if self.directInput != None:
        self.directInputLayout.addWidget(self.directInput)
        self.directInputLayout.addWidget(self.okDirectInput)
        self.nodeLayout.addLayout(self.directInputLayout, self.index + 2, 1)

    self.prepareGeometryChange()
     def setParentNode(self, node):
        '''Set the parent node.'''
        self.setParentItem(node)
        # Repaint the scene
        self.update()

     def delete(self):
        # print "deleting anchor"

        self.nodeLayout.removeWidget(self.lcd)
        self.nodeLayout.removeWidget(self.labelWidget)

        self.labelWidget.deleteLater()
        self.lcd.deleteLater()

        self.setParentItem(None)
        self.scene.removeItem(self)

    def getLabel(self):
        return str(self.label)

    def setLabel(self, text):
        self.label = text
     def validate(self, type, val):
        '''Make sure value is ov certain type'''
        if type == 'float':
                value = float(str(val))
                return value
        return None
    def directInputHandler(self, type,  callback):
        # print "type:", type
        try:
            value = self.validate(type, callback())
        except:
             self.directInput.setStyleSheet( "background:rgb(255,0,0);")
             traceback.print_exc()
             return
        # print "value:", value
        self.directInput.setStyleSheet( "background:rgb(255,255,255);")

        if self.pipe != None and self.type == 'output':
            self.pipe.setData(value)
        else:
            self.directInputData = value
        self.data = directInputData
        self.parentNode().refreshData()
    def getLcd(self):
        return self.lcd
    def refresh(self):
        self.getLcd().display(self.data)
        self.labelWidget.setText(text)
    def setColor(self, color):
        self.nodeBrush = QtGui.QBrush(color)

    def getGlobalLocation(self):
        if self.type == 'output':
            loc =  QtCore.QPoint(self.getLocalLocation().x()+self.scenePos().x(),self.getLocalLocation().y()+self.scenePos().y())
        elif self.type == 'input':
            loc = QtCore.QPoint(self.getLocalLocation().x()+self.scenePos().x(),self.getLocalLocation().y()+self.scenePos().y())
        return loc
    def getLocalLocation(self):
        return QtCore.QPoint(self.posX+10,self.posY+10)
     def paint(self, painter, option, widget):
        if self.type == 'output':
            # Bounding rectangle of the anchor
            self.posX = self.nodeFrame.width()
            
        elif self.type == 'input':
            self.posX = -20
        # print "pipe:", self.pipe
        if self.pipe != None:
            self.nodeBrush = QtGui.QBrush(QtGui.QColor(200,0,0))
        else:
            self.nodeBrush = QtGui.QBrush(QtGui.QColor(*self.node.getColor()))
        self.posY = self.labelWidget.mapToGlobal(self.labelWidget.rect().topLeft()).y()
        
        painter.setBrush(self.nodeBrush)
        painter.setPen(self.textPen)
        painter.setFont(self.font)
        
            
            # self.label = self.getPipe().getLabel()
        # #self.label = self.getLocalLocation
        # if self.label is None:
            # self.label = 'New Pipe'
        
        # painter.drawText(150-self.width, 105+40*self.index, self.label)
        self.rect.moveTo(self.posX, self.posY)
        
        # painter.drawRect(self.rect)
        # print "posX", self.posX
        
        painter.drawEllipse(self.posX,  self.posY, self.anchorSize,  self.anchorSize)
 def boundingRect(self):
        return self.rect

    def mousePressEvent(self, event):
       # print "Anchor clicked!"
        if self.isConnected():
            self.tree.deletePipe(self.pipe)
            if self.directInput != None:
                self.directInput.show()
                self.okDirectInput.show()
                self.lcd.hide()
        else:
            self.tree.connect(self)
            if self.directInput != None:
                self.directInput.hide()
                self.okDirectInput.hide()
                self.lcd.show()
            # print "disconnecting ", self.param

            
        self.update()
        self.setSelected(True)
        QtGui.QGraphicsItem.mousePressEvent(self, event)
    def hoverEnterEvent(self, event):
        self.textPen.setStyle(QtCore.Qt.DotLine)
        QtGui.QGraphicsItem.hoverEnterEvent(self, event)

    def hoverLeaveEvent(self, event):
        self.textPen.setStyle(QtCore.Qt.SolidLine)
        QtGui.QGraphicsItem.hoverLeaveEvent(self, event)
