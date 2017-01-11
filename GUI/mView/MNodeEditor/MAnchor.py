from PyQt4 import QtGui, QtCore
from MPipe import MPipe
class MAnchor(QtGui.QGraphicsItem):
    def __init__(self, name, scene, tree, index,  parent = None, **kwargs):
        
        # Get the keyword arguments
        self.type = kwargs.get('type', 'output')
        # get the tree
        self.tree = tree
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
        self.scene  = scene
        # Add the anchor to the scene
        self.scene.addItem(self)
        # Configure the anchor based on its type
        if self.type == 'output':
            # Configure the brush
            self.nodeBrush = QtGui.QBrush(QtGui.QColor(52, 73, 94))
            # Bounding rectangle of the anchor
            self.rect = QtCore.QRectF(175, 90+40*self.index,20, 20)
        elif self.type == 'input':
            self.nodeBrush = QtGui.QBrush(QtGui.QColor(52, 73, 94))
            self.rect = QtCore.QRectF(-10, 90+40*self.index,20, 20)
        # The QPen
        self.textPen = QtGui.QPen()
        self.textPen.setStyle(2);
        self.textPen.setWidth(3)
        self.textPen.setColor(QtGui.QColor(189, 195, 199))
        # Name displayed next to the anchor
        self.param = name
        label = QtCore.QString(self.param)
        self.font = QtGui.QFont()
        self.font.setPointSize(10)
        self.label = QtCore.QString(self.param)
        self.width = QtGui.QFontMetrics(self.font).boundingRect(label).width()
        #self.update(self.rect)
        self.prepareGeometryChange()
    def parentNode(self):
        return self.parent
    def setParentNode(self, node):
        self.setParentItem(node)
        self.parent  = node
    def getLabel(self):
        return self.label
    def setLabel(self, label):
        self.label = label
        # Repaint the scene
        self.update()
    def getType(self):
        '''Get the anchor type'''
        return self.type
    def getPipe(self):
        '''Get the pipe connected to the anchor'''
        return self.pipe
    def connect(self, pipe):
        '''Set the anchor's pipe'''
        self.pipe = pipe
    def disconnect(self):
        '''Disconnect and delete the pipe'''
        self.tree.deletePipe(self.pipe)
        self.pipe = None
    def setColor(self, color):
        self.nodeBrush = QtGui.QBrush(color)
    def getGlobalLocation(self):
        if self.type == 'output':
            loc =  QtCore.QPoint(self.getLocalLocation().x()+self.scenePos().x(),self.getLocalLocation().y()+self.scenePos().y())
        elif self.type == 'input':
            loc = QtCore.QPoint(self.getLocalLocation().x()+self.scenePos().x(),self.getLocalLocation().y()+self.scenePos().y())
        return loc
    def getLocalLocation(self):
        if self.type == 'output':
            loc =  QtCore.QPoint(185,100+40*self.index)
        elif self.type == 'input':
            loc = QtCore.QPoint(0,100+40*self.index)
        return loc
    def connect(self, pipe):
        self.pipe = pipe
        self.update()
    def getPipe(self):
        return self.pipe
    def isConnected(self):
        return not self.getPipe() == None
    def paint(self, painter, option, widget):
        painter.setBrush(self.nodeBrush)
        painter.setPen(self.textPen)
        painter.setFont(self.font)
        if self.isConnected():
            self.label = self.getPipe().getLabel()
        #self.label = self.getLocalLocation
        if self.label is None:
            self.label = 'New Pipe'
        painter.drawText(150-self.width, 105+40*self.index, self.label)
        painter.drawRect(self.rect)
        self.e = painter.drawEllipse(self.getLocalLocation(), 10, 10)
    def boundingRect(self):
        return self.rect

    def mousePressEvent(self, event):
        print "Anchor clicked!"
        if self.isConnected():
            self.disconnect()
            print "disconnecting ", self.param
        elif len(self.tree.getPipes()) == 0:
             self.pipe = self.tree.addPipe(MPipe(self, self.scene))
        else:
            if self.tree.getPipes()[-1].isUnconnected():
                print "using existing pipe"
                self.tree.getPipes()[-1].connect(self)
                self.pipe =  self.tree.getPipes()[-1]
            else:
                self.pipe = self.tree.addPipe(MPipe(self, self.scene))
            self.pipe = self.tree.getPipes()[-1]
            
        self.update()
        self.setSelected(True)
        QtGui.QGraphicsItem.mousePressEvent(self, event)
    def hoverEnterEvent(self, event):
        self.textPen.setStyle(QtCore.Qt.DotLine)
        QtGui.QGraphicsItem.hoverEnterEvent(self, event)

    def hoverLeaveEvent(self, event):
        self.textPen.setStyle(QtCore.Qt.SolidLine)
        QtGui.QGraphicsItem.hoverLeaveEvent(self, event)