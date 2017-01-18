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
        
        grid = QtGui.QGridLayout(self)
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

        buttonLayout = QtGui.QHBoxLayout(self)
        buttons = device.getFrame().getButtons()

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
                lcdHBox = QtGui.QHBoxLayout(self)
                lcdHBox.addStretch(0)
                lcdHBox.addWidget(lcd)
                grid.addLayout(lcdHBox, y, 1)
        if device.getFrame().isPlot():
            dc = MGrapher.mGraph(device)
            yPos = len(self.nicknames)+1
            device.getFrame().setPlot(dc)
            grid.addWidget(dc, yPos,0,yPos,3)
        
    def update(self):
        #print "updating frame"
        frame = self.device.getFrame()
        #print "updating data 1",self.device.getFrame().getTitle()
        frame.getNode().refreshData()
        #print "updating data 2",self.device.getFrame().getTitle()

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
                for y in range(len(nicknames)):
                    try:
                        format = "%." + str(int(precisions[y])) + "f"
                        if not math.isnan(readings[y]):
                            self.lcds[y].display(format %readings[y])
                        else:
                            self.lcds[y].display("---")
                    except TypeError:
                        pass
                   # print "len(self.unitLabels)>y", len(self.unitLabels)>y
                    if len(self.unitLabels)>y:
                        #print "getting units:", frame.getUnits()
                        unit = frame.getUnits()[y]
                        if unit != None:
                            self.unitLabels[y].setText(unit)
                        #self.unitLabels[y].setFont(self.font)
            else:
                for lcd in self.lcds:
                    lcd.display("-")
