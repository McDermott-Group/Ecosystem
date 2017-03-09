from PyQt4 import QtGui, QtCore
class MReadout(QtGui.QWidget):
    def __init__(self, parent= None):
        QtGui.QWidget.__init__(self, parent)
        self.parent = parent
        self.lcd = QtGui.QLCDNumber(parent)
        self.lcd.setSegmentStyle(QtGui.QLCDNumber.Flat)
        self.label = QtGui.QLabel('', self.parent)
        self.layout = QtGui.QHBoxLayout(parent)
        self.layout.addWidget(self.lcd)
        self.layout.addWidget(self.label)
        self.setLayout(self.layout)
        self.isLCD = True
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Minimum)
        self.setSizePolicy(sizePolicy)
        self.lcd.setSizePolicy(sizePolicy)
        self.label.setSizePolicy(sizePolicy)
        #self.label.hide()
        #self.lcd.hide()
        self.layout.setContentsMargins(0,0,0,0)
    def getLCD(self):
        return self.lcd
    def getLabel(self):
        return self.label
    def setLabelSize(self, size):
        font = QtGui.QFont()
        font.setPointSize(size)
        self.label.setFont(font)
    def display(self, data):
        try:
            self.lcd.display(data)
            self.lcd.show()
            self.label.hide()  
        except:
     
            self.lcd.hide()
            self.label.show()
            self.label.setText(str(str(data)))