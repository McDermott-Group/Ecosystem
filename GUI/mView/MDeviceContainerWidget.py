from PyQt4 import QtGui, QtCore
from MWeb import web
import MGrapher
import math
from functools import partial
class MDeviceContainerWidget(QtGui.QFrame):

    def __init__(self, device, parent = None):
        QtGui.QWidget.__init__(self, parent)
        device.updateSignal.connect(self.update)

        device.setContainer(self)
        
        self.nicknameLabels = []
        self.unitLabels = []
        self.lcds = []
        self.device = device
        self.dc = None
        
        grid = QtGui.QGridLayout(self)
        self.grid = grid
        self.setLayout(grid)
        
        self.frameSizePolicy = QtGui.QSizePolicy()
        self.frameSizePolicy.setVerticalPolicy(4)
        self.frameSizePolicy.setHorizontalPolicy(QtGui.QSizePolicy.Preferred)
        self.setSizePolicy(self.frameSizePolicy)
        self.setStyleSheet("background: rgb(52, 73, 94)")
        self.setFrameShape(QtGui.QFrame.Panel)
        self.setFrameShadow(QtGui.QFrame.Plain)
        self.setLineWidth(web.ratio)
        grid.setSpacing(10)
        grid.setColumnStretch(0,1)
        
        self.font = QtGui.QFont()
        self.font.setBold(False)
        self.font.setWeight(50)
        self.font.setKerning(True)
        self.font.setPointSize(12)
        
        self.fontBig = QtGui.QFont()
        self.fontBig.setBold(False)
        self.fontBig.setWeight(50)
        self.fontBig.setKerning(True)
        self.fontBig.setPointSize(18)

        
        titleWidget = QtGui.QLabel(device.getFrame().getTitle())
        titleWidget.setFont(self.fontBig)
        titleWidget.setStyleSheet("color:rgb(189, 195, 199);")
        grid.addWidget(titleWidget,0,0)

        buttonLayout = QtGui.QHBoxLayout()
        buttons = device.getFrame().getButtons()
        
        self.hidden = False
        
        for button in buttons:
            if button != []:

                button.append(QtGui.QPushButton(button[0], self))
                button[-1].setStyleSheet("color:rgb(189, 195, 199); "
                            "background:rgb(70, 80, 88)")
                button[-1].setFont(self.font)   
                buttonLayout.addWidget(button[-1])
                button[-1].clicked.connect(partial(device.prompt, button))

        grid.addLayout(buttonLayout, 0, 1, 1 , 2)

        self.nicknames = device.getFrame().getNicknames()
        for i, nickname in enumerate(self.nicknames):
            if nickname != None:
                y = i+1
                label = QtGui.QLabel(nickname, self)
                label.setFont(self.font)
                label.setWordWrap(True)
                label.setStyleSheet("color:rgb(189, 195, 199);")
                grid.addWidget(label, y, 0)
                self.nicknameLabels.append(label)
                
              
                units = QtGui.QLabel('')
                grid.addWidget(units, y, 2)
                units.setFont(self.fontBig)
                self.unitLabels.append(units)
                
                lcd = QtGui.QLCDNumber(self)
                self.lcds.append(lcd)
                lcd.setNumDigits(11)
                lcd.setSegmentStyle(QtGui.QLCDNumber.Flat)
                lcd.display("-")
                lcd.setFrameShape(QtGui.QFrame.Panel)
                lcd.setFrameShadow(QtGui.QFrame.Plain)
                lcd.setLineWidth(web.ratio)
                lcd.setMidLineWidth(100)
                lcd.setStyleSheet("color:rgb(189, 195, 199);\n")
                lcd.setFixedHeight(web.scrnHeight / 30)
                lcd.setMinimumWidth(web.scrnWidth / 7)
                lcdHBox = QtGui.QHBoxLayout()
                lcdHBox.addStretch(0)
                lcdHBox.addWidget(lcd)

                grid.addLayout(lcdHBox, y, 1)
        self.topHBox = QtGui.QHBoxLayout()
        yPos = len(self.nicknames)
        grid.addLayout(self.topHBox, yPos+1, 0, yPos+1, 3)
        if device.getFrame().isPlot():
            self.dc = MGrapher.mGraph(device)
            yPos = len(self.nicknames)+2
            device.getFrame().setPlot(self.dc)
            grid.addWidget(self.dc, yPos,0,yPos,3)
        self.bottomHBox = QtGui.QHBoxLayout()
      
        
        grid.addLayout(self.bottomHBox, yPos+1, 0, yPos+1, 3)
    def getBottomHBox(self):
        return self.BottomHBox
    def getTopHBox(self):
        return self.topHBox
    def addParameter(self):
        label = QtGui.QLabel('Untitled', self)
        label.setFont(self.font)
        label.setWordWrap(True)
        label.setStyleSheet("color:rgb(189, 195, 199);")
        self.grid.addWidget(label,self.grid.rowCount(), 0)
        self.nicknameLabels.append(label)
        
      
        units = QtGui.QLabel('')
        self.grid.addWidget(units, self.grid.rowCount()-1, 3)
        
        units.setFont(self.fontBig)
        self.unitLabels.append(units)
        lcd = QtGui.QLCDNumber(self)
        self.lcds.append(lcd)
        lcd.setNumDigits(11)
        lcd.setSegmentStyle(QtGui.QLCDNumber.Flat)
        lcd.display("-")
        lcd.setFrameShape(QtGui.QFrame.Panel)
        lcd.setFrameShadow(QtGui.QFrame.Plain)
        lcd.setLineWidth(web.ratio)
        lcd.setMidLineWidth(100)
        lcd.setStyleSheet("color:rgb(189, 195, 199);\n")
        lcd.setFixedHeight(web.scrnHeight / 30)
        lcd.setMinimumWidth(web.scrnWidth / 7)
        lcdHBox = QtGui.QHBoxLayout(self)
        lcdHBox.addStretch(0)
        lcdHBox.addWidget(lcd)

        self.grid.addLayout(lcdHBox, self.grid.rowCount()-1, 1)

        if self.dc != None:
            self.grid.removeWidget(self.dc)
            self.grid.addWidget(self.dc, self.grid.rowCount(), 0, 1, 3)
        
    def visible(self, show = None):
        if self.hidden:
            self.show()
            self.hidden = False
            print "showing"
        else:
            self.hide()
            self.hidden = True
            print "hidden"
    def update(self):
        #print "updating frame"
        frame = self.device.getFrame()
        #print "updating data 1",self.device.getFrame().getTitle()
        frame.getNode().refreshData()
        #print "updating data 2",self.device.getFrame().getTitle()
        if self.device.getFrame().isPlot():
            self.device.getFrame().getPlot().plot(time = 'last_valid')
        if not frame.isError():
            readings = frame.getReadings()
            #print "readings:", readings
            precisions = frame.getPrecisions()
            if readings is not None:
                outOfRange = frame.getOutOfRangeStatus()
                nicknames = frame.getNicknames()
                for y in range(len(outOfRange)):
                    key = frame.getTitle()+":"+nicknames[y]
                    if outOfRange[key]:
                        color = "color:rgb(200, 100, 50);\n"
                    else:
                        color = "color:rgb(189, 195, 199);\n"
                    self.lcds[y].setStyleSheet(color)
                    if len(self.unitLabels)>y:
                        self.unitLabels[y].setStyleSheet(color)
                    self.nicknameLabels[y].setStyleSheet(color)
                    self.nicknameLabels[y].setText(nicknames[y])
                while len(readings) > len(self.lcds):
                        self.addParameter()
                        
                for y in range(len(readings)):
                   
                    try:
                        format = "%." + str(int(precisions[y])) + "f"
                        #print "readings:",readings
                        if not math.isnan(readings[y]):
                            self.lcds[y].display(format %readings[y])
                        else:
                            self.lcds[y].display("---")
                    except TypeError:
                        pass
                    if len(self.unitLabels)>y:
                        unit = frame.getUnits()[y]
                        if unit != None:
                            self.unitLabels[y].setText(unit)
            else:
                for lcd in self.lcds:
                    lcd.display("-")
