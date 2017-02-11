from PyQt4 import QtGui, QtCore
class MReadout(QtGui.QWidget):
    def __init__(self, parent= None):
        QtGui.QWidget.__init__(self, parent)
        self.parent = parent
        self.widget = QtGui.QLCDNumber(parent)
        self.layout = QtGui.QHBoxLayout(parent)
        self.layout.addWidget(self.widget)
        self.setLayout(self.layout)
        self.isLCD = True
    def display(self, data):
      
        if type(data) == float or type(data) == int:
            if not self.isLCD:
                self.widget.deleteLater()
                self.widget = QtGui.QLCDNumber(self.parent)
                self.isLCD = True
                self.layout.addWidget(self.widget)
            self.widget.display(data)
            self.widget.setSegmentStyle(QtGui.QLCDNumber.Flat)
            
        else:
            if self.isLCD:
                self.widget.deleteLater()
                self.widget = QtGui.QLabel(str(data), self.parent)
                self.isLCD = False
                self.layout.addWidget(self.widget)
            
            self.widget.setText(str(data))