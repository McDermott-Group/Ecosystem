from PyQt4 import QtGui, QtCore
import sys
import time
import gc
from functools import partial
from MNodes.MVirtualDeviceNode import MVirtualDeviceNode
from MNodes.MCompare import MCompare
from MWeb import web
import importlib
import inspect
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
        # if(not tree.getScene()is None):
            # self.scene = tree.getScene()
        # else:
            # self.scene = QtGui.QGraphicsScene()
            # tree.setScene(self.scene)
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


        addDeviceBtn = QtGui.QPushButton("Add Device")
        addDeviceBtn.clicked.connect(self.addDevice)
        
        mainLayout.addWidget(addDeviceBtn)
        self.setLayout(mainLayout)

    def addDevice(self):
        items = web.nodeFilenames
        formattedItems = []
        for i,item in enumerate(items):
            item  = item.replace(".py","")
            if item == '__init__' or item == 'MLabradNode':
                pass
            else: 
                formattedItems.append(item)
        item, ok = QtGui.QInputDialog.getItem(self, "Add Node", "Select Node:", formattedItems, editable = False)
        
        if ok:  
           #import MNodes.MCompare
           newNodeModule = importlib.import_module(str('MNodeEditor.MNodes.'+str(item)))
           #print "newNodeModule:", newNodeModule
           
           for name, obj in inspect.getmembers(newNodeModule):
                #print obj.__dict__
                if inspect.isclass(obj):
                    #print "looking at:", item, obj.__name__
                    pass
                if inspect.isclass(obj) and item == obj.__name__:
                    newNodeClass = obj
                    #print "obj:", obj
                    self.tree.addNode(obj())
                    #print "importing type:", str(newNodeClass)
                    break

                    