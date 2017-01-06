from PyQt4 import QtGui, QtCore
from MAnchor import MAnchor
import threading
import traceback
from MWeb import web
class MNode(QtGui.QGraphicsItem):
    def __init__(self,  scene, tree, parent = None,  **kwargs):
        ''' Create a new node'''
        # Get keyword args from constructor
        self.mode = kwargs.get('mode', 'operator')
        self.device = kwargs.get('device',None)
        # Initialize the parent class
        QtGui.QGraphicsItem.__init__(self,parent)
        # Variables to hold the anchors, scene, and tree
        self.anchors = []
        self.scene = scene
        self.tree = tree
        
        # Tell the gui that the item is moveable, slectable, and focusable and that 
        # it accepts hover events.
        self.setFlag(QtGui.QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QtGui.QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QtGui.QGraphicsItem.ItemIsFocusable, True)
        self.setAcceptsHoverEvents(True)
        # Set the node tree
        self.NodeTree = tree
        # Bounding rectangles
        self.rect = QtCore.QRectF(0, 0, 180, 180)
        self.rect2 = QtCore.QRectF(-20, -20, 220,220)
        # The pen, for painting the borders
        self.textPen = QtGui.QPen()

        self.textPen.setWidth(2)
        self.textPen.setColor(QtGui.QColor(189, 195, 199))
        # Based on the mode, set up the node
        if self.mode == 'labrad_device':
            # If the node represents a labrad device, then the title displayed on the node
            # should be the same as the title of the device
            self.title = self.device.getFrame().getTitle()
            # The color of a device node is blue
            self.nodeBrush = QtGui.QBrush(QtGui.QColor(52, 73, 94))
            for i,param in enumerate(self.device.getFrame().getNicknames()):
                # Append all anchors to node
                self.anchors.append(MAnchor(param,scene,tree,  i, type = 'output'))  
                # Setting the parents of the anchors to the node is very important.
                self.anchors[-1].setParentItem(self)
       # If the node is an output, configure it as such.
        elif self.mode == 'output':
            self.title = 'Output'
            # Ouput node colors are green.
            self.nodeBrush = QtGui.QBrush(QtGui.QColor(52, 94, 73))
        
        self.nodeThread = threading.Thread(target = self.refreshData, args=[])
        # If the main thread stops, stop the child thread
        self.nodeThread.daemon = True
        # Start the thread
        self.nodeThread.start()
    def refreshData(self):
        index = 0
        try:
            if self.getType() == 'labrad_device':
                for i, anchor in enumerate(self.getAnchors()):
                    if(anchor.getType() == 'output' and anchor.getPipe() is not None):
                        anchor.getPipe().setData(self.device.getFrame().getReadings()[i] )
                        #print anchor.getPipe().getData()
                        index = index + 1
            if web.keepGoing:
                pass
                threading.Timer(1, self.refreshData).start()
        except:
            traceback.print_exc()
    def getAnchors(self):
        return self.anchors
        
    def addAnchor(self, anchor):
        self.anchors.append(anchor)
        self.anchors[-1].setParentItem(self)
        return self.anchors[-1]
            
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
        self.font = QtGui.QFont()
        self.font.setPointSize(15)
        painter.setBrush(self.nodeBrush)
        painter.setPen(self.textPen)
        painter.setFont(self.font)
        painter.drawRect(self.rect)
        painter.drawText(5, 30, self.title)
        
    def getType(self):
        return self.mode