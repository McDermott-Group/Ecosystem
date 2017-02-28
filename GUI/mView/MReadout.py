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
    def getLCD(self):
        return self.lcd
    def getLabel(self):
        return self.label
    def setLabelSize(self, size):
        font = QtGui.QFont()
        font.setPointSize(size)
        self.label.setFont(font)
    def display(self, data):
      
        if type(data) == float or type(data) == int:
            if not self.isLCD:
                #self.widget.deleteLater()
                self.isLCD = True
                self.lcd.show()
                self.label.hide()

            self.lcd.display(data)
            
            
        else:
            if self.isLCD:
                #self.widget.deleteLater()
                self.lcd.hide()
                self.label.show()
                self.isLCD = False

            
            self.label.setText(str(str(data)))