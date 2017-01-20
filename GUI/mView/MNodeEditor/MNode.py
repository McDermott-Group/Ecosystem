from PyQt4 import QtGui, QtCore
from MAnchor import MAnchor
import traceback
from MWeb import web
class MNode(QtGui.QGraphicsItem):
    def __init__(self, parent = None, *args, **kwargs):
        QtGui.QGraphicsItem.__init__(self,parent)
        #default color'
        self.nodeFrame = QtGui.QFrame()
        self.title = "New MNode"
        self.color = (50,50,50)
        self.device = parent
        self.isDevice = False
        #self.nodeFrame.setStyleSheet(".QFrame{background:rgba"+str(self.color[0])+','+str(self.color[1])+','+str(self.color[2])+', 20)'+
         #                                                                   "; border:rgba(189, 195, 199)")
    def begin(self,   **kwargs):
        ''' Create a new node'''
        #print "self.scene:",self.scene
        # Get keyword args from constructor
        print "newNode"
        self.scene.addItem(self)
        self.nodeLayout = QtGui.QGridLayout()
        #self.setLayout(nodeLayout)
        self.font = QtGui.QFont()
        self.font.setPointSize(15)
        
       
        #self.nodeLayout = QtGui.QVBoxLayout(self.nodeFrame)
        self.label = QtGui.QLabel(self.title,self.nodeFrame)
        self.label.setFont(self.font)
        self.label.setStyleSheet("color:rgb(189,195,199)")
        self.nodeLayout.addWidget(self.label, 0, 0)
        
       
        #nodeLayout.addWidget(QtGui.QCheckBox(nodeFrame))
        self.nodeFrame.setLayout(self.nodeLayout)
     
        
        
        pProxy = QtGui.QGraphicsProxyWidget(self)
        pProxy.setWidget(self.nodeFrame)
        #self.mode = kwargs.get('mode', 'operator')
        
        # Initialize the parent class
        
        # Variables to hold the anchors, scene, and tree
        self.anchors = []
        #self.scene = scene
        #self.tree = tree
        
        # Tell the gui that the item is moveable, slectable, and focusable and that 
        # it accepts hover events.
        self.setFlag(QtGui.QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QtGui.QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QtGui.QGraphicsItem.ItemIsFocusable, True)
        self.setAcceptsHoverEvents(True)
        # Bounding rectangles
        self.rect = QtCore.QRectF(0, 0, self.nodeFrame.width(),self.nodeFrame.height())
        self.rect2 = QtCore.QRectF(-20, -20, 220,220)
        # The pen, for painting the borders
        self.textPen = QtGui.QPen()

        self.textPen.setWidth(2)
        self.textPen.setColor(QtGui.QColor(189, 195, 199))
        
        self.nodeBrush = QtGui.QBrush(QtGui.QColor(*self.color))

    def getDevice(self):
        return self.device
    def setDevice(self, device):
        self.isDevice = True
        self.device = device
    def getNodeWidget(self):
        return self.nodeFrame
    def getNodeLayout(self):
        return self.nodeLayout
    def setColor(self,r, g, b):
            self.color = (r, g, b)
            self.nodeFrame.setStyleSheet(".QFrame{background:rgba("+str(r)+','+str(g)+','+str(b)+', 20)}')
    def getColor(self):
        return self.color
    def setScene(self, scene):
        self.scene = scene
    def setTree(self, tree):
        self.tree = tree
    def setTitle(self, title): 
        self.title = title
        self.label.setText(title)
    def getTitle(self):
        return self.title
    def refreshData(self):
        raise notimplementederror("MNode->refreshData must be implemented.")
        
    def getAnchors(self):
        return self.anchors
        
    def addAnchor(self, anchor=None, **kwargs):
        
        if anchor == None:
            name = kwargs.get('name', None)
            type = kwargs.get('type', None)
            if name == None or type == None:
                raise RuntimeError("If no anchor is passed to MNode.addAnchor(), then \'name\', \'type\' keyword arguments must be given.")
            anchor = MAnchor(name, self, len(self.anchors), type = type)
            
        self.anchors.append(anchor)
        self.anchorAdded(anchor)
        self.rect = QtCore.QRectF(0, 0, self.nodeFrame.width(),self.nodeFrame.height())
        self.rect2 = QtCore.QRectF(0, 0,self.nodeFrame.width(),self.nodeFrame.height())
        return self.anchors[-1]
    def removeAnchor(self, anchor = None, **kwargs):
        print "specified anchor:", anchor
        if anchor == None:
            print "deleting last anchor"
            self.anchors[-1].delete()
        else:
            anchor.delete()
    def pipeDisconnected(self):
        pass
    def pipeConnected(self, anchor, pipe):
       pass
    def anchorAdded(self, anchor):
        pass
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
        #self.prepareGeometryChange()
        return self.rect2
        
    def paint(self, painter, option, widget):
        # self.prepareGeometryChange()
        self.rect2.setHeight(self.nodeFrame.height())
        self.rect2.setWidth(self.nodeFrame.width())

        painter.setBrush(self.nodeBrush)
        painter.setPen(self.textPen)
        painter.setFont(self.font)
        painter.drawRect(self.rect2)
        #painter.drawRect(self.rect)
    def refreshData(self):
        pass

        #painter.drawText(5, 30, self.title)
        
