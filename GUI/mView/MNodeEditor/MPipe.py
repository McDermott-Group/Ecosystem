from PyQt4 import QtGui, QtCore

class MPipe(QtGui.QGraphicsPathItem):
    def __init__(self, startAnchor, scene, parent = None):
        QtGui.QGraphicsPathItem.__init__(self, parent = None)
        self.scene = scene
        self.label = None
        #startAnchor.parentNode().pipeConnected(startAnchor, self)
        # Create a new painter path starting at the location of the first anchor
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
        self.startAnchor = startAnchor
        self.endAnchor = None
        self.inputAnchor = None
        self.outputAnchor = None
        if startAnchor.getType()== 'output':
            self.label = startAnchor.getLabel()
        self.data = None
    def connect(self, endAnchor):
        '''Connect the other end of the pipe.'''
        self.inputAnchor = endAnchor
        self.outputAnchor = self.startAnchor
        #endAnchor.parentNode().pipeConnected(endAnchor, self)
        if endAnchor.getType()== 'output':
            self.label = endAnchor.getLabel()
            self.inputAnchor = self.startAnchor
            self.outputAnchor = self.endAnchor
       # print "on connect, input anchor:", self.inputAnchor
        self.endAnchor = endAnchor
        self.update()
        
    def isUnconnected(self):
        return self.endAnchor == None
        
    def destruct(self):
        '''This is where the pipe destroys itself :(. '''
        self.scene.removeItem(self)
        
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
            
           # painter.drawText(self.startAnchor.getGlobalLocation(), self.label)
            #painter.drawRect(self.bound)
    def getStartAnchor(self):
        return self.startAnchor
        
    def getEndAnchor(self):
        return self.endAnchor
        
    def getLabel(self):
        return self.label
        
    def setLabel(self, label):
        self.label = label
        
    def getData(self):
        return self.data
        
    def setData(self, data):
        self.data = data
        #print "self.inputAnchor:", self.inputAnchor
        if self.inputAnchor != None:
            self.inputAnchor.parentNode().refreshData()
            if self.inputAnchor.parentNode().isDevice:
                self.inputAnchor.parentNode().getDevice().updateContainer()
        if self.inputAnchor != None:
            self.inputAnchor .getLcd().display(self.data)
        if self.outputAnchor != None:
            self.outputAnchor .getLcd().display(self.data)

    def sceneMouseMove(self, event):
        print "Scene mouse move"
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
        