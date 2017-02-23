from PyQt4 import QtCore, QtGui
from MNodeEditor.MNode import MNode
from MNodeEditor.MAnchor import MAnchor
from MDevices.MVirtualDevice import MVirtualDevice
from MWeb import web
from functools import partial
class MVirtualDeviceNode(MNode):
    def __init__(self, *args, **kwargs):
       
        super( MVirtualDeviceNode, self).__init__(None, *args, **kwargs)
        self.setColor(52, 94, 73)
        self.title = 'Output'
        
    def begin(self, *args, **kwargs):
        super( MVirtualDeviceNode, self).begin()
        #print "initializing MVirtualDeviceNode"
        self.addAnchor(name = 'Self', type = 'output')
        self.addAnchor(name = 'New Input', type = 'input')
        self.setTitle("Virtual Device")
        #print "creating new virtual device named", self.getTitle()
        self.associatedDevice = MVirtualDevice(self.getTitle())
        self.setDevice(self.associatedDevice)
        self.associatedDevice.addPlot()
        self.associatedDevice.addParameter(self.getAnchors()[0].getLabel())
        self.associatedDevice.getFrame().setNode(self)
        editButton = QtGui.QPushButton("Edit")
        self.showOnGui = QtGui.QCheckBox("Show", self.nodeFrame)
        self.showOnGui.setStyleSheet("color:rgb(189,195,199);\n background:rgb(52,94,73,0)")
        self.showOnGui.setChecked(True)
        self.nodeLayout.addWidget(editButton, 0, 1)
        self.nodeLayout.addWidget(self.showOnGui, 1, 0)
        editButton.clicked.connect(self.openVirtualDeviceGui)
        web.gui.color = (52,94,73)
        web.gui.addDevice(self.associatedDevice)
        self.showOnGui.clicked.connect(partial(self.associatedDevice.getFrame().getContainer().visible))

    def refreshData(self):
        #print "virtual device refreshing data"
        
        reading = []
        #print "anchors:", self.getAnchors()
        for anchor in self.getAnchors():
            if anchor.getPipe():
                reading.append(anchor.getPipe().getData())
          #  anchor.getLcd().display(reading[-1])
        
        self.getDevice().retrieveFromNode(reading)
        
    def pipeConnected(self, anchor, pipe):
        '''called when a pipe is added'''
        print "pipeConnected called"
        if anchor.getType() == 'input':
            self.addAnchor(name = 'New Input', type = 'input')
            self.associatedDevice.addParameter(self.getAnchors()[-1].getLabel())
        elif anchor.getLabel() == 'Self':
            anchor.setData(self.getDevice())
        pass
    def pipeDisconnected(self):
       print "pipeDisconnected called"
       self.removeAnchor()
       
    def openVirtualDeviceGui(self):
        dialog = MVirtualDeviceGui(self.associatedDevice, self)
        dialog.exec_()
        
class MVirtualDeviceGui(QtGui.QDialog):
    def __init__(self,associatedDevice,node,  parent = None):
        super(MVirtualDeviceGui, self).__init__(parent)
        self.node = node
        self.associatedDevice = associatedDevice
        layout = QtGui.QFormLayout()
        self.btns = []
        for i, nickname in enumerate(self.associatedDevice.getFrame().getNicknames()):
            btn = QtGui.QPushButton("Edit")
            lbl = QtGui.QLabel(nickname)
            btn.clicked.connect(partial(self.getName, "New Name:", i, lbl))
            layout.addRow(lbl, btn)
            self.btns.append(btn)
        closebtn = QtGui.QPushButton("close")
        closebtn.clicked.connect(self.close)
        layout.addRow(closebtn)
        self.setLayout(layout)
        
    def getName(self, name, index, label, anchor):
        text, ok = QtGui.QInputDialog.getText(self, "Virtual Device Name Editor", name)
        if ok:
            nicknames = self.associatedDevice.getFrame().getNicknames()
            nicknames[index] = text
            self.associatedDevice.getFrame().setNicknames(nicknames)
            self.associatedDevice.getContainer().nicknameLabels[index].setText(text)
            self.node.getAnchors()[index].setLabel(text)
            label.setText(text)
        return text
        