from PyQt4 import QtGui, QtCore
import sys
import time

app = QtGui.QApplication([])


class nodeGui(QtGui.QDialog):
    def __init__(self, devices, parent = None):
        super(nodeGui, self).__init__(parent)
        
        mainLayout = QtGui.QVBoxLayout()
        lbl = QtGui.QLabel()
        lbl.setText("Logic Editor")
        mainLayout.addWidget(lbl)
        scene = QtGui.QGraphicsScene()
        
        self.devices = devices
        
        view = QtGui.QGraphicsView(scene)
        view.ViewportUpdateMode(2)
        view.setInteractive(True)
        self.backgroundBrush = QtGui.QBrush(QtGui.QColor(70, 80, 88))
        view.setBackgroundBrush(self.backgroundBrush)
        for device in self.devices:
            scene.addItem(MNode(device, mode = 'labrad_device'))
            scene.addItem(MNode(device, mode = 'output'))
        mainLayout.addWidget(view)
        self.setLayout(mainLayout)
       # view.show()
class MNode(QtGui.QGraphicsItem):
    def __init__(self, device, parent = None,  **kwargs):
        print kwargs
        print kwargs.get('mode', 'operator')
        self.mode = kwargs.get('mode', 'operator')
        QtGui.QGraphicsItem.__init__(self,parent)
        self.inputAnchors = []
        self.outputAnchors = []
        self.setFlag(QtGui.QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QtGui.QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QtGui.QGraphicsItem.ItemIsFocusable, True)
        self.setAcceptsHoverEvents(True)
        
        self.device = device
        self.rect = QtCore.QRectF(0, 0, 180, 180)
        self.rect2 = QtCore.QRectF(-20, -20, 220,220)
        self.textPen = QtGui.QPen()
        #self.textPen.setStyle(2)
        self.textPen.setWidth(2)
        self.textPen.setColor(QtGui.QColor(189, 195, 199))
        if self.mode == 'labrad_device':
            self.title = device.getFrame().getTitle()
            self.nodeBrush = QtGui.QBrush(QtGui.QColor(52, 73, 94))
            
            for i,param in enumerate(self.device.getFrame().getNicknames()):
                self.inputAnchors.append(anchor(param,i, type = 'input'))  
        elif self.mode == 'output':
            self.title = 'Output'
            self.nodeBrush = QtGui.QBrush(QtGui.QColor(52, 94, 73))
            self.outputAnchors.append(anchor('Gui Readout',0, type = 'output'))
            #this = outputAnchor('Gui Readout', painter)
       
            
    def hoverEnterEvent(self, event):
        self.prepareGeometryChange()
        self.textPen.setStyle(QtCore.Qt.DotLine)
        print self.pos().x()
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
        print "input"
        print "pos: ", event.pos().x(), event.pos().y()
        for anchor in self.inputAnchors:
            print anchor.contains(event.pos())
            if(anchor.contains(event.pos())):
                anchor.setColor(QtGui.QColor(255, 73, 94))
            else:
                anchor.setColor(QtGui.QColor(52, 73, 94))
        for anchor in self.outputAnchors:
            print anchor.contains(event.pos())
            if(anchor.contains(event.pos())):
                anchor.setColor(QtGui.QColor(255, 73, 94))
            else:
                anchor.setColor(QtGui.QColor(52, 73, 94))
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
        # painter.drawRect(self.rect)
        # #painter.setBrush(self.textBrush)
       
        # painter.drawText(5, 20, self.title)
        painter.drawRect(self.rect)
        painter.drawText(5, 30, self.title)
        for anchor in self.inputAnchors:
            anchor.paint(painter, option, widget)
        for anchor in self.outputAnchors:
            anchor.paint(painter, option, widget)
        
   
            # self.e = painter.drawEllipse(QtCore.QPoint(185,40+40*i), 10, 10)
            # 
            # width = QtGui.QFontMetrics(self.font).boundingRect(paramLabel).width()
            # painter.drawText(150-width, 45+40*i, paramLabel)

class anchor(QtGui.QGraphicsItem):
    def __init__(self, name, index,  parent = None, **kwargs):
        self.type = kwargs.get('type', 'input')
        
        print self.type
        QtGui.QGraphicsItem.__init__(self,parent)
        self.index = index
        # self.setFlag(QtGui.QGraphicsItem.ItemIsMovable, True)
        # self.setFlag(QtGui.QGraphicsItem.ItemIsSelectable, True)
        # self.setFlag(QtGui.QGraphicsItem.ItemIsFocusable, True)
        # self.setAcceptsHoverEvents(True)
        i = index
        if self.type == 'input':
            self.nodeBrush = QtGui.QBrush(QtGui.QColor(52, 73, 94))
            self.rect = QtCore.QRectF(175, 40+40*i,20, 20)
        elif self.type == 'output':
            self.nodeBrush = QtGui.QBrush(QtGui.QColor(52, 73, 94))
            self.rect = QtCore.QRectF(-10, 40+40*i,20, 20)
        self.textPen = QtGui.QPen()
        self.textPen.setStyle(2);
        self.textPen.setWidth(3)
        self.textPen.setColor(QtGui.QColor(189, 195, 199))
        self.param = name
        paramLabel = QtCore.QString(self.param)
        #self.prepareGeometryChange()
        self.font = QtGui.QFont()
        self.font.setPointSize(10)
            

        self.paramLabel = QtCore.QString(self.param)
        self.width = QtGui.QFontMetrics(self.font).boundingRect(paramLabel).width()
        self.update(self.rect)
    def setColor(self, color):
        self.nodeBrush = QtGui.QBrush(color)
    def boundingRect(self):
        self.prepareGeometryChange()
        return self.rect
    def getName(self):
        return self.name
   
    def paint(self, painter, option, widget):
        #print "painting"
        painter.setBrush(self.nodeBrush)
        painter.setPen(self.textPen)
        painter.setFont(self.font)

        painter.drawText(150-self.width, 55+40*self.index, self.paramLabel)
        #painter.drawRect(self.rect)
        if self.type == 'input':
            self.e = painter.drawEllipse(QtCore.QPoint(185,50+40*self.index), 10, 10)
        elif self.type == 'output':
            self.e = painter.drawEllipse(QtCore.QPoint(0,50+40*self.index), 10, 10)
# class outputAnchor:
    # def __init__(self, name, painter,  parent = MNode):
       
        # self.nodeBrush = QtGui.QBrush(QtGui.QColor(52, 73, 94))
        # self.textPen = QtGui.QPen()
        # self.textPen.setStyle(2);
        # self.textPen.setWidth(3)
        # self.textPen.setColor(QtGui.QColor(189, 195, 199))
        # self.param = name
        # paramLabel = QtCore.QString(self.param)
        # #self.prepareGeometryChange()
        # self.font = QtGui.QFont()
        # self.font.setPointSize(10)
        
        
        
        # painter.setBrush(self.nodeBrush)
        # painter.setPen(self.textPen)
        # painter.setFont(self.font)
        # self.e = painter.drawEllipse(QtCore.QPoint(0,50+40), 10, 10)
        # paramLabel = QtCore.QString(self.param)
        # width = QtGui.QFontMetrics(self.font).boundingRect(paramLabel).width()
        # painter.drawText(10, 55+40, paramLabel)
        
    # def getName(self):
        # return self.name
# #app.exec_()
# #time.sleep(2)
# #sys.exit()