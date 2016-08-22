import sys
sys.dont_write_bytecode = True
from PyQt4 import QtCore, QtGui
from functools import partial
from MWeb import web
import traceback
class ConfigGui(QtGui.QDialog):
    def __init__(self, parent = None):
        super(ConfigGui, self).__init__(parent)
        # Create a tab for update speed settings
        mainTabWidget = QtGui.QTabWidget()
        mainTabWidget.addTab(refreshRateContents(), "Refresh Rates")
        mainLayout = QtGui.QVBoxLayout()
        mainLayout.addWidget(mainTabWidget)
        buttonLayout = QtGui.QHBoxLayout()
        okButton = QtGui.QPushButton(self)
        okButton.setText("Ok")
        buttonLayout.addStretch(0)
        buttonLayout.addWidget(okButton)
        mainLayout.addLayout(buttonLayout)
        self.setLayout(mainLayout)
        self.setWindowTitle("Device Config")
        okButton.clicked.connect(self.close)
        
class refreshRateContents(QtGui.QWidget):
    def __init__(self, parent = None):
        super(refreshRateContents, self).__init__(parent)
        #self.mainGui = mainGui
        mainLayout = QtGui.QVBoxLayout()
        
        self.setLayout(mainLayout) 
        self.refreshTabWidget = QtGui.QTabWidget()
       
        mainLayout.addWidget(self.refreshTabWidget)
        self.refreshTabWidget.addTab(self.guiRefreshConfig(), "Gui")
        
        for device in web.devices:
            self.refreshTabWidget.addTab(devRefRateConfig(device), device.getFrame().getTitle())
            
    def guiRefreshConfig(self):
        guiRefConfig = QtGui.QWidget()
        guiRefLayout = QtGui.QVBoxLayout()
        guiRefLayoutH = QtGui.QHBoxLayout()
        guiRefLayoutH.addWidget(QtGui.QLabel("Gui Refresh period: "))
        guiRefLayoutH.addStretch(0)
        self.refRateEdit = QtGui.QLineEdit()
        self.refRateEdit.setText(str(web.guiRefreshRate))
        guiRefLayoutH.addWidget(self.refRateEdit)
        guiRefLayoutH.addWidget(QtGui.QLabel('s'))
        self.refRateEdit.editingFinished.connect(self.updateMainGuiRefRate)
        
        guiRefLayout.addLayout(guiRefLayoutH)
        guiRefConfig.setLayout(guiRefLayout)
        return guiRefConfig
        
    def updateMainGuiRefRate(self):
       try:
            web.guiRefreshRate = float(self.refRateEdit.text())
       except Exception as e:
            print e
            
class devRefRateConfig(QtGui.QWidget):
    def __init__(self, device, parent = None):
        super(devRefRateConfig, self).__init__(parent)
 
        self.device = device
 
        devRefConfig = QtGui.QWidget()
        devRefLayout = QtGui.QVBoxLayout()
        devRefLayoutH = QtGui.QHBoxLayout()
        devRefLayoutH.addWidget(QtGui.QLabel(device.getFrame().getTitle()+" update period:"))
        devRefLayoutH.addStretch(0)
            
            
        devRefConfig.setLayout(devRefLayout)
        self.devRefRateEdit = QtGui.QLineEdit()
        self.devRefRateEdit.editingFinished.connect(self.updateDevRefRate)
        self.devRefRateEdit.setText(str(device.getFrame().getRefreshRate()))
        devRefLayoutH.addWidget(self.devRefRateEdit)
        devRefLayoutH.addWidget(QtGui.QLabel('s'))
        
        devRefLayout.addLayout(devRefLayoutH)
        
        if device.getFrame().isPlot():
            plotRefLayoutH = QtGui.QHBoxLayout()
            plotRefLayoutH.addWidget(QtGui.QLabel(device.getFrame().getTitle()+" plot refresh rate:"))
            plotRefLayoutH.addStretch(0)
            self.plotRefRateEdit = QtGui.QLineEdit()
            self.plotRefRateEdit.setText(str(device.getFrame().getPlotRefreshRate()))
            self.plotRefRateEdit.editingFinished.connect(self.updateDevPlotRate)
            plotRefLayoutH.addWidget(self.plotRefRateEdit)
            plotRefLayoutH.addWidget(QtGui.QLabel('s'))
            devRefLayout.addLayout(plotRefLayoutH)
        self.setLayout(devRefLayout)
        
    def updateDevPlotRate(self):
        #print self.plotRefRateEdit.text()
        try:
            self.device.getFrame().setPlotRefreshRate(float(self.plotRefRateEdit.text()))
           # print self.self.device.getFrame().getPlotRefreshRate()
        except:
            traceback.print_exc()
            print "["+self.device.getFrame().getTitle()+"] "+self.plotRefRateEdit.text() + " is not a number."
    def updateDevRefRate(self):
        #print self.devRefRateEdit.text()
        try:
            self.device.getFrame().setRefreshRate(float(self.devRefRateEdit.text()))
        except:
            traceback.print_exc()
            print "["+self.device.getFrame().getTitle()+"] "+self.plotRefRateEdit.text() + " is not a number."