import MDevice
from MWeb import web
import os
from PyQt4 import QtCore, QtGui
from MFileTree import MFileTree
from dataChest import *

class Mhdf5Device(MDevice.MDevice):
    def __init__(self, *args):
         super(Mhdf5Device, self).__init__(*args)
         self.frame.setTitle(args[0])
         web.virtualDevices.append(self)
         self.doNotLog(True)
         
    def onLoad(self):
        self.setupMenus()
    def setupMenus(self):
            root = os.environ['DATA_CHEST_ROOT']
            container = self.getFrame().getContainer()
            HBox = container.getTopHBox()
            filetree = MFileTree(root)
            HBox.addWidget(filetree)
            
    def prompt(self, button):
        '''Called when button is pushed'''
        root = os.environ['DATA_CHEST_ROOT']
        dir = QtGui.QFileDialog.getOpenFileName(None, "Open Data Set...",
                root, "Data Chest Files (*.hdf5)")
        dir = str(dir)
        # Get rid of the file namse, use just the path
        print "before dir:", dir
        path = dir.split("/")[0:-1]
        filename = dir.split("/")[-1]
        dir = '/'.join(path)
        print "selected dir:", dir
        root = root.replace('\\', '/')
        print "datachest root:", root
        
        dir = dir.replace(root, '')
        dir = dir.replace('/','\\')
        relpath = dir.split('\\')
        print "relative path:", dir
        #print "current chest directory:", chest.pwd()
        chest = dataChest(relpath[1])
        chest.cd("")
        if len(relpath)> 2:
            chest.cd(relpath[2::])
        print "current chest directory:", chest.pwd()
        chest.openDataset(filename)
        print "opened dataset:", chest
        self.getFrame().setDataSet(chest)
        
        self.getFrame().getPlot().plot()
    def addButton(self, name):
        '''Add a simple button.'''
        button = []
        button.append(name)
        self.frame.setButtons([button])
        