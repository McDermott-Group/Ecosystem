import sys
from PyQt4 import QtGui

class Example(QtGui.QWidget):
    
    def __init__(self):
        super(Example, self).__init__()
        
        self.initUI()
        
    def initUI(self):

        vbox = QtGui.QVBoxLayout()
        vbox.addStretch(1)

        listOfBoxs = []
        listOfButtons = []
        for ii in range(0, 10):
            qframe = QtGui.QFrame(self)
            qframe.setFrameShape(QtGui.QFrame.Panel)
            hbox = QtGui.QHBoxLayout()
            okButton = QtGui.QPushButton("OK"+str(ii))
            cancelButton = QtGui.QPushButton("Cancel"+str(ii))
            hbox.addWidget(okButton)
            hbox.addWidget(cancelButton)
            qframe.setLayout(hbox)
            vbox.addWidget(qframe)
        self.setLayout(vbox)

        self.setGeometry(300, 300, 300, 150)
        self.setWindowTitle('Buttons')    
        self.show()
            
def main():
    
    app = QtGui.QApplication(sys.argv)
    ex = Example()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
