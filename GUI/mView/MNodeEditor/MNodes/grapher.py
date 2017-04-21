from MNodeEditor.MNode import MNode
from MNodeEditor.MAnchor import MAnchor
from MGrapher import mGraph as MGrapher
from MWeb import web
from PyQt4 import QtGui, QtCore
class grapher(MNode):
    def __init__(self, *args, **kwargs):
        super(grapher, self).__init__(None, *args, **kwargs)
        self.setColor(94, 54, 94)
        self.graph = None
        self.timer = QtCore.QTimer()
        
    def begin(self, *args, **kwargs):
        super(grapher, self).begin()
        self.addAnchor(name = 'Device', type = 'input')
        self.setTitle("Grapher")
    def pipeConnected(self,anchor, pipe):
        #print "device connected to grapher:", anchor.getData()
        self.frame = QtGui.QFrame()
        
        self.frameSizePolicy = QtGui.QSizePolicy()
        self.frameSizePolicy.setVerticalPolicy(4)
        self.frameSizePolicy.setHorizontalPolicy(QtGui.QSizePolicy.Preferred)
        self.frame.setSizePolicy(self.frameSizePolicy)
        self.frame.setStyleSheet("background: rgb(52, 73, 94)")
        self.frame.setFrameShape(QtGui.QFrame.Panel)
        self.frame.setFrameShadow(QtGui.QFrame.Plain)
        self.frame.setLineWidth(web.ratio)
        
        self.layout = QtGui.QHBoxLayout()
        self.graph = MGrapher(anchor.getData(), self.frame)
        self.frame.setLayout(self.layout)
        self.layout.addWidget(self.graph)
        web.gui.addWidget(self.frame)
        self.frame.show()
        self.timer.timeout.connect(self.refreshPlot)
        self.timer.start(2000)

    def refreshPlot(self):
        self.graph.plot(time = 'last_valid')
        
        