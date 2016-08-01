from PyQt4 import QtGui, QtCore
import sys
import time

app = QtGui.QApplication([])


class NodeGui(QtGui.QDialog):
    pipes = []
    scene = None
    def __init__(self, devices, tree, parent = None):
        super(NodeGui, self).__init__(parent)
        self.setMouseTracking(True)
        mainLayout = QtGui.QVBoxLayout()
        lbl = QtGui.QLabel()
        lbl.setText("Logic Editor")
        mainLayout.addWidget(lbl)
        
        #self.scene = QtGui.QGraphicsScene()
        if(not tree.getScene()is None):
            self.scene = tree.getScene()
        else:
            self.scene = QtGui.QGraphicsScene()
            tree.setScene(self.scene)
        self.devices = devices
        self.tree = tree
        view = QtGui.QGraphicsView(self.scene)
        view.ViewportUpdateMode(0)
        view.setInteractive(True)
        self.backgroundBrush = QtGui.QBrush(QtGui.QColor(70, 80, 88))
        view.setBackgroundBrush(self.backgroundBrush)
        # for device in self.devices:
            # self.scene.addItem(MNode(device, self.scene, mode = 'labrad_device'))
            # self.scene.addItem(MNode(device, self.scene, mode = 'output'))
        mainLayout.addWidget(view)
        self.setLayout(mainLayout)
       # view.show()
class NodeTree:
    scene = NodeGui.scene
    pipes = []
    nodes = []
    def getPipes(self):
        return self.pipes
    def addPipe(self,pipe):
        self.pipes.append(pipe)
    def setScene(self, scene):
        self.scene = scene
    def getScene(self):
        return self.scene
    def connect(self, startAnchor, endAnchor):
        self.pipes.append(MPipe(startAnchor, self.scene))
        self.pipes[-1].connect(endAnchor)
        if startAnchor.getType() == 'output':
            self.pipes[-1].setLabel(startAnchor.getLabel())
            #endAnchor.setLabel(startAnchor)
        elif endAnchor.getType() == 'output':
            self.pipes[-1].setLabel(endAnchor.getLabel())
        startAnchor.pipeConnected(self.pipes[-1])
        endAnchor.pipeConnected(self.pipes[-1])
            #startAnchor.setLabel(endAnchor)
     
    def newNode(self,  tree, **kwargs):
        newNode = MNode(self.scene, tree, **kwargs)
        self.scene.addItem(newNode)
        return newNode
    def getNodes(self):
        return nodes
        
class MPipe(QtGui.QGraphicsPathItem, NodeGui):
    def __init__(self, startAnchor, scene, parent = None):
        QtGui.QGraphicsPathItem.__init__(self, parent = None)
        # self.setFlag(QtGui.QGraphicsItem.ItemIsMovable, True)
        # self.setFlag(QtGui.QGraphicsItem.ItemIsSelectable, True)
        # self.setFlag(QtGui.QGraphicsItem.ItemIsFocusable, True)
        # self.setAcceptsHoverEvents(True)
        self.scene = scene
        self.label = None
        self.path = QtGui.QPainterPath(startAnchor.getGlobalLocation())
        self.pen = QtGui.QPen()
        self.pen.setStyle(2);
        self.pen.setWidth(3)
        self.pen.setColor(QtGui.QColor(189, 195, 199))
        #self.path.addPath( QtGui.QPainterPath())
        #print self.scene
        self.scene.addItem(self)
        self.bound = QtCore.QRectF(0,0,1,1)
        self.startAnchor = startAnchor
        self.endAnchor = None
    def connect(self, endAnchor):
        #print "connecting"
        
        self.endAnchor = endAnchor
        #self.path2.lineTo(endAnchor.scenePos())
        self.update()
        #print "Updated"
    def isUnconnected(self):
        return self.endAnchor == None
    def paint(self, painter, option, widget):
        #print "painting pipe"
        #painter.drawText(5, 30, "test")
        self.prepareGeometryChange()
        if not self.isUnconnected():
            self.setBrush( QtGui.QColor(255, 0, 0) )
            #print self.startAnchor.scenePos().x()
            self.setPath(self.path)
            path2 = QtGui.QPainterPath()
            path2.moveTo(self.startAnchor.getGlobalLocation())
            #path2.cubicTo(100, -20, 40, 90, 20, 20)
            path2.lineTo(self.endAnchor.getGlobalLocation())
            #self.scene.addPath(path2)
            painter.setPen(self.pen)
            painter.drawPath(path2)
            #painter.drawRect(self.bound)
    def getStartAnchor(self):
        return self.startAnchor
    def getEndAnchor(self):
        return self.endAnchor
        
    def mouseMoveEvent(self, event):
        # move object
        #print "moving"
        self.update()
        self.prepareGeometryChange()
        QtGui.QGraphicsPathItem.mouseMoveEvent(self, event)
    def getLabel(self):
        return self.label
    def setLabel(self, label):
        self.label = label
    def boundingRect(self):
        #self.prepareGeometryChange()
        #print self.isUnconnected()
        
        if not self.isUnconnected():
            width = self.endAnchor.getGlobalLocation().x()- self.startAnchor.getGlobalLocation().x()
            height = self.endAnchor.getGlobalLocation().y()- self.startAnchor.getGlobalLocation().y()
            
            if(width<0 and height<0):
               # print 1
                self.bound = QtCore.QRectF(self.startAnchor.getGlobalLocation().x()+width,self.startAnchor.getGlobalLocation().y()+height, width*-1, height*-1 )
            elif(width<0):
                #print 2
                self.bound = QtCore.QRectF(self.startAnchor.getGlobalLocation().x()+width,self.startAnchor.getGlobalLocation().y(), width*-1, height)
            elif(height<0):
               # print 3
                self.bound = QtCore.QRectF(self.startAnchor.getGlobalLocation().x(),self.startAnchor.getGlobalLocation().y()+height, width, height*-1 )
            else:
                self.bound = QtCore.QRectF(self.startAnchor.getGlobalLocation().x(),self.startAnchor.getGlobalLocation().y(), width,height)
            return self.bound
        return self.bound
        
class MNode(QtGui.QGraphicsItem):
    def __init__(self,  scene, tree, parent = None,  **kwargs):
       # print kwargs
       # print kwargs.get('mode', 'operator')
       
        self.mode = kwargs.get('mode', 'operator')
        self.device = kwargs.get('device',None)
        QtGui.QGraphicsItem.__init__(self,parent)
        self.anchors = []
        self.scene = scene
        self.tree = tree
        
        self.setFlag(QtGui.QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QtGui.QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QtGui.QGraphicsItem.ItemIsFocusable, True)
        self.setAcceptsHoverEvents(True)
        self.NodeTree = tree

        self.rect = QtCore.QRectF(0, 0, 180, 180)
        self.rect2 = QtCore.QRectF(-20, -20, 220,220)
        self.textPen = QtGui.QPen()
        #self.textPen.setStyle(2)
        self.textPen.setWidth(2)
        self.textPen.setColor(QtGui.QColor(189, 195, 199))
        #self.pipes = []
        if self.mode == 'labrad_device':
            self.title = self.device.getFrame().getTitle()
            self.nodeBrush = QtGui.QBrush(QtGui.QColor(52, 73, 94))
            
            for i,param in enumerate(self.device.getFrame().getNicknames()):
                self.anchors.append(anchor(param,scene,tree,  i, type = 'output'))  
                self.anchors[-1].setParentItem(self)
        elif self.mode == 'output':
            self.title = 'Output'
            self.nodeBrush = QtGui.QBrush(QtGui.QColor(52, 94, 73))
            
            #this = outputAnchor('Gui Readout', painter)
       
    def getAnchors(self):
        return self.anchors
    def addAnchor(self):
        if self.mode == 'output':
            self.anchors.append(anchor('Gui Readout',self.scene,self.tree, len(self.anchors), type = 'input'))
            self.anchors[-1].setParentItem(self)
            return self.anchors[-1]
        else:
            print "you can't add an anchor to an input node."
            return None
    def hoverEnterEvent(self, event):
        self.prepareGeometryChange()
        self.textPen.setStyle(QtCore.Qt.DotLine)
        #print self.pos().x()
        QtGui.QGraphicsItem.hoverEnterEvent(self, event)
        
    def hoverLeaveEvent(self, event):
        self.prepareGeometryChange()
        self.textPen.setStyle(QtCore.Qt.SolidLine)
        QtGui.QGraphicsItem.hoverLeaveEvent(self, event)
    def mouseMoveEvent(self, event):
        # move object
        
        self.prepareGeometryChange()
        QtGui.QGraphicsItem.mouseMoveEvent(self, event)
    def mousePressEvent(self, event):
        # move object
        #print "input"
        #print "pos: ", event.pos().x(), event.pos().y()
        self.prepareGeometryChange()
        QtGui.QGraphicsItem.mousePressEvent(self, event)
    def boundingRect(self):
        #self.prepareGeometryChange()
        return self.rect2
        
    def paint(self, painter, option, widget):
        # self.prepareGeometryChange()
        self.font = QtGui.QFont()
        self.font.setPointSize(15)
        painter.setBrush(self.nodeBrush)
        painter.setPen(self.textPen)
        painter.setFont(self.font)
        painter.drawRect(self.rect)
        painter.drawText(5, 30, self.title)

class anchor(QtGui.QGraphicsItem):
    def __init__(self, name, scene, tree, index,  parent = None, **kwargs):
        self.type = kwargs.get('type', 'output')
        self.NodeTree = tree
        #print self.type
        #QtGui.QGraphicsItem.__init__()
        super(anchor, self).__init__()
        self.pipe = None
        # self.setFlag(QtGui.QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QtGui.QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QtGui.QGraphicsItem.ItemIsFocusable, True)
        self.pipes = []
        self.setAcceptsHoverEvents(True)
        self.index = index
        self.scene  = scene
        self.scene.addItem(self)
        i = index
        if self.type == 'output':
            self.nodeBrush = QtGui.QBrush(QtGui.QColor(52, 73, 94))
            self.rect = QtCore.QRectF(175, 40+40*i,20, 20)
        elif self.type == 'input':
            self.nodeBrush = QtGui.QBrush(QtGui.QColor(52, 73, 94))
            self.rect = QtCore.QRectF(-10, 40+40*i,20, 20)
        self.textPen = QtGui.QPen()
        self.textPen.setStyle(2);
        self.textPen.setWidth(3)
        self.textPen.setColor(QtGui.QColor(189, 195, 199))
        self.param = name
        label = QtCore.QString(self.param)
        #self.prepareGeometryChange()
        self.font = QtGui.QFont()
        self.font.setPointSize(10)
            

        self.label = QtCore.QString(self.param)
        self.width = QtGui.QFontMetrics(self.font).boundingRect(label).width()
        #self.update(self.rect)
        self.prepareGeometryChange()
    def setColor(self, color):
        self.nodeBrush = QtGui.QBrush(color)
    def boundingRect(self):
       
        return self.rect
    def getLabel(self):
        return self.label
    # def mouseMoveEvent(self, event):
        # # move object
        # QtGui.QGraphicsItem.mouseMoveEvent(self, event)
    def getType(self):
        return self.type
    def mousePressEvent(self, event):
        # select object
        # set item as topmost in stack
        #self.setZValue(self.parent.scene.items()[0].zValue() + 1)
      #  print len(self.NodeTree.getPipes)
        #if(self.contains(event.pos())):
        self.setColor(QtGui.QColor(255, 73, 94))
        if(len(self.NodeTree.getPipes()) == 0 ):
            #print "No pipes exist, adding pipe"
            self.NodeTree.addPipe(MPipe(self, self.scene))
            
        elif self.NodeTree.getPipes()[-1].isUnconnected():
            #print "pipe is unconnected, using existing pipe"
            self.NodeTree.getPipes()[-1].connect(self)
            
        else:
            #print "new unconnected pipe"
            self.NodeTree.addPipe(MPipe(self, self.scene))
        #print self.type
        # if self.type == 'input':
            # #print "its an imput"
            # self.label = self.NodeTree.getPipes()[-1].getLabel()
            
        # elif self.type == 'output':
            # #print "its and outptu"
            # self.NodeTree.getPipes()[-1].setLabel(self.getLabel())
            #print "self.getLabel ", self.getLabel()
            #print "self.NodeTree.getPipes[-1].getLabel() ", self.NodeTree.getPipes[-1].getLabel()
        self.pipe = self.NodeTree.getPipes()[-1]
        # else:
            # anchor.setColor(QtGui.QColor(52, 73, 94))
        #print self.label
        self.update
        self.setSelected(True)
        QtGui.QGraphicsItem.mousePressEvent(self, event)
    def hoverEnterEvent(self, event):
        self.textPen.setStyle(QtCore.Qt.DotLine)
        QtGui.QGraphicsItem.hoverEnterEvent(self, event)

    def hoverLeaveEvent(self, event):
        self.textPen.setStyle(QtCore.Qt.SolidLine)
        QtGui.QGraphicsItem.hoverLeaveEvent(self, event)
    def paint(self, painter, option, widget):
        #print "painting anchor"
        painter.setBrush(self.nodeBrush)
        painter.setPen(self.textPen)
        painter.setFont(self.font)
        if self.pipe is not None:
            painter.drawText(150-self.width, 55+40*self.index, str(self.pipe.getLabel()))
        else:
            painter.drawText(150-self.width, 55+40*self.index, self.label)
        #painter.drawRect(self.rect)
        #if self.type == 'input':
        self.e = painter.drawEllipse(self.getLocalLocation(), 10, 10)
        # elif self.type == 'output':
            # self.e = painter.drawEllipse(QtCore.QPoint(0,50+40*self.index), 10, 10)
    def getGlobalLocation(self):
        if self.type == 'output':
            loc =  QtCore.QPoint(self.getLocalLocation().x()+self.scenePos().x(),self.getLocalLocation().y()+self.scenePos().y())
        elif self.type == 'input':
            loc = QtCore.QPoint(self.getLocalLocation().x()+self.scenePos().x(),self.getLocalLocation().y()+self.scenePos().y())
        return loc
    def getLocalLocation(self):
        if self.type == 'output':
            loc =  QtCore.QPoint(185,50+40*self.index)
        elif self.type == 'input':
            loc = QtCore.QPoint(0,50+40*self.index)
        return loc
    def pipeConnected(self, pipe):
        self.pipe = pipe
    def getPipe(self):
        return self.pipe
    def isConnected(self):
        return not self.getPipe() == None