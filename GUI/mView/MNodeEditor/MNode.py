from PyQt4 import QtGui, QtCore
from MAnchor import MAnchor
import threading
import traceback
from MWeb import web
class MNode(QtGui.QGraphicsItem):
    def __init__(self, parent = None, *args, **kwargs):
        QtGui.QGraphicsItem.__init__(self,parent)
        #default color
        self.title = "New MNode"
        self.color = (50,50,50)
    def begin(self,   **kwargs):
        ''' Create a new node'''
        print "self.scene:",self.scene
        # Get keyword args from constructor
        self.scene.addItem(self)
        nodeLayout = QtGui.QGraphicsGridLayout()
        #self.setLayout(nodeLayout)
        self.font = QtGui.QFont()
        self.font.setPointSize(15)
        
        nodeFrame = QtGui.QFrame()
        nodeLayout = QtGui.QVBoxLayout(nodeFrame)
        self.label = QtGui.QLabel(self.title,nodeFrame)
        self.label.setFont(self.font)
        nodeLayout.addWidget(self.label)
        nodeLayout.addWidget(QtGui.QCheckBox(nodeFrame))
        nodeFrame.setLayout(nodeLayout)
        nodeFrame.setStyleSheet("background:rgba(0, 0, 88, 0)")
        pProxy = QtGui.QGraphicsProxyWidget(self)
        pProxy.setWidget(nodeFrame)
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
        self.rect = QtCore.QRectF(0, 0, 180, 180)
        self.rect2 = QtCore.QRectF(-20, -20, 220,220)
        # The pen, for painting the borders
        self.textPen = QtGui.QPen()

        self.textPen.setWidth(2)
        self.textPen.setColor(QtGui.QColor(189, 195, 199))
        
        self.nodeBrush = QtGui.QBrush(QtGui.QColor(*self.color))
        # Based on the mode, set up the node
       
         
    
        # self.nodeThread = threading.Thread(target = self.refreshData, args=[])
        # # If the main thread stops, stop the child thread
        # self.nodeThread.daemon = True
        # # Start the thread
        # self.nodeThread.start()
    def setColor(self,r, g, b):
            self.color = (r, g, b)
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
            anchor = MAnchor(name, self.scene, self.tree, len(self.anchors)-1, type = type)
        self.anchors.append(anchor)
        self.anchors[-1].setParentNode(self)
        self.anchorAdded(anchor)
        return self.anchors[-1]
        
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
        
        painter.setBrush(self.nodeBrush)
        painter.setPen(self.textPen)
        painter.setFont(self.font)
        painter.drawRect(self.rect)
        #painter.drawText(5, 30, self.title)
        
    def getType(self):
        raise notimplementederror("MNode->getType must be implemented.")