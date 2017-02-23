from PyQt4 import QtGui, QtCore
from MPipe import MPipe
from MWeb import web
import time
from functools import partial
import traceback
from MReadout import MReadout
class MAnchor(QtGui.QGraphicsItem):
    def __init__(self, name, node, index,  parent = None, **kwargs):
        # Get the keyword arguments
        self.type = kwargs.get('type', 'output')
        self.suggestedDataType = kwargs.get('data', None)
        self.node = node
        # get the tree
        self.tree = node.tree
        self.nodeLayout = node.getNodeLayout()
        self.nodeFrame= node.getNodeWidget()
        # Initialize the base class
        super(MAnchor, self).__init__()
        # Anchor is not connected to any pipe by default
        self.pipe = None
        self.setFlag(QtGui.QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QtGui.QGraphicsItem.ItemIsFocusable, True)
        self.setAcceptsHoverEvents(True)
        # What number the anchor is in the node
        self.index = index
        # The QGraphics scene
        self.scene  = node.scene
        # Add the anchor to the scene
        self.scene.addItem(self)
        # Configure the anchor based on its type
        self.setParentItem(node)
        self.parent = node
        # Configure the brush
        self.nodeBrush = QtGui.QBrush(QtGui.QColor(*node.getColor()))
        self.data = None
        self.posY = 70+30*self.index
        self.directInput = None
        self.okDirectInput = None
        self.directInputLayout = None
        self.directInputData = 0
        if self.type == 'output':
            # Bounding rectangle of the anchor
            self.posX = self.nodeFrame.width()
          
        elif self.type == 'input':
            self.posX = -20


        #print "self.posX", self.posX
        #print "width:", self.nodeFrame.width()
        self.anchorSize = int(8*web.ratio)
        self.rect = QtCore.QRectF(self.posX,  self.posY, self.anchorSize,  self.anchorSize)
        
        #print "posX1", self.posX

       
        # The QPen
        self.textPen = QtGui.QPen()
        self.textPen.setStyle(2);
        self.textPen.setWidth(2)
        self.textPen.setColor(QtGui.QColor(189, 195, 199))
        # Name displayed next to the anchor
        self.param = name
        label = QtCore.QString(self.param)
        self.font = QtGui.QFont()
        self.font.setPointSize(10)
        self.label = QtCore.QString(self.param)
        self.width = QtGui.QFontMetrics(self.font).boundingRect(label).width()
        #self.update(self.rect)
        self.labelWidget = QtGui.QLabel(self.label, self.nodeFrame)
        self.labelWidget.setStyleSheet("color:rgb(189, 195, 199)")
        self.nodeLayout.addWidget(self.labelWidget, self.index+2, 0)
        self.lcd = MReadout(self.nodeFrame)
        
        self.lcd.setStyleSheet("color:rgb(189, 195, 199);\n")
        self.nodeLayout.addWidget(self.lcd, self.index+2, 1)
        if self.suggestedDataType == 'float':
           
            self.directInput = QtGui.QLineEdit(str(self.directInputData),self.nodeFrame)
            self.directInput.setValidator(QtGui.QDoubleValidator())
            self.directInput.textEdited.connect(partial(self.directInput.setStyleSheet, "background:rgb(0,255,0);"))
            self.directInputLayout = QtGui.QHBoxLayout()
            
            self.okDirectInput = QtGui.QPushButton("Set", self.nodeFrame)
            self.okDirectInput.clicked.connect(partial(self.directInputHandler, 'float',  self.directInput.text))
            width = self.okDirectInput.fontMetrics().boundingRect("Set").width()
            height = self.okDirectInput.fontMetrics().boundingRect("Set").height()
            self.okDirectInput.setMaximumWidth(width+10)
            self.okDirectInput.setMaximumHeight(height+5)
            self.lcd.hide()
        if self.directInput != None:
            self.directInputLayout.addWidget(self.directInput)
            self.directInputLayout.addWidget(self.okDirectInput)
            self.nodeLayout.addLayout(self.directInputLayout, self.index+2, 1)
        


        self.prepareGeometryChange()
    def validate(self, type, val):
        if type == 'float':
                value = float(str(val))
                return value
        return None
    def directInputHandler(self, type,  callback):
        print "type:", type
        try:
            value = self.validate(type, callback())
        except:
             self.directInput.setStyleSheet( "background:rgb(255,0,0);")
             traceback.print_exc()
             return
        print "value:", value
        self.directInput.setStyleSheet( "background:rgb(255,255,255);")

        if self.pipe != None and self.type == 'output':
            self.pipe.setData(value)
        else:
            self.directInputData = value
        self.data = directInputData
        self.parentNode().refreshData()
    def getLcd(self):
        return self.lcd
    def parentNode(self):
        return self.parent
    def setParentNode(self, node):
        self.setParentItem(node)
        self.parent  = node
    def getLabel(self):
        return str(self.label)
    def setLabel(self, text):
        self.label = text
        self.labelWidget.setText(text)
        # Repaint the scene
        self.update()
    def getType(self):
        '''Get the anchor type'''
        return self.type
    def getPipe(self):
        '''Get the pipe connected to the anchor'''
        return self.pipe
    def pipeConnected(self, pipe):
        print "anchor->pipeConnected:", self.data
        self.setPipe(pipe)
        if self.getType() == 'output':
            self.setData(self.data)
        else:
            self.data = pipe.getData()
    def update(self):
        #self.parentNode().refreshData()
        if self.parentNode().isDevice:
                self.parentNode().getDevice().updateContainer()
        self.getLcd().display(self.data)
    def getData(self):
        pipe = self.getPipe()
        if pipe != None:
            return self.getPipe().getData()
        else:
            return self.data 
            
            
    def setData(self, data):
        pipe = self.getPipe()
        if pipe != None and self.type == 'output':
            pipe.setData(data)
        elif self.parentNode().isDevice:
            self.parentNode().getDevice().updateContainer()
        self.data = data
        self.lcd.display(data)
    def setPipe(self, pipe):
        self.pipe = pipe
    def delete(self):
        print "deleting anchor"
        

        
        self.nodeLayout.removeWidget(self.lcd)
        self.nodeLayout.removeWidget(self.labelWidget)
        
        self.labelWidget.deleteLater()
        self.lcd.deleteLater()
        
        self.setParentItem(None)
        self.scene.removeItem(self)
    def disconnect(self):
        '''Disconnect and delete the pipe'''
        #self.parentNode().pipeDisconnected(self, self.pipe)
        self.tree.deletePipe(self.pipe)
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
    def connect(self, pipe):
        print "connect function called"
        self.pipe = pipe
        self.update()

    def isConnected(self):
        return not self.getPipe() == None
        
    def paint(self, painter, option, widget):
        if self.type == 'output':
            # Bounding rectangle of the anchor
            self.posX = self.nodeFrame.width()
            
        elif self.type == 'input':
            self.posX = -20
        #print "pipe:", self.pipe
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
        
        #painter.drawText(150-self.width, 105+40*self.index, self.label)
        self.rect.moveTo(self.posX, self.posY)
        
        #painter.drawRect(self.rect)
        #print "posX", self.posX
        
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
            #print "disconnecting ", self.param

            
        self.update()
        self.setSelected(True)
        QtGui.QGraphicsItem.mousePressEvent(self, event)
    def hoverEnterEvent(self, event):
        self.textPen.setStyle(QtCore.Qt.DotLine)
        QtGui.QGraphicsItem.hoverEnterEvent(self, event)

    def hoverLeaveEvent(self, event):
        self.textPen.setStyle(QtCore.Qt.SolidLine)
        QtGui.QGraphicsItem.hoverLeaveEvent(self, event)