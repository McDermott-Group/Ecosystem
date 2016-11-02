#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
This application allows for easy probing of a wafer of JJs.

author: Chris Wilen
"""

import sys
from PyQt4 import QtGui, QtCore
import numpy as np

class ProbeStation(QtGui.QWidget):

    def __init__(self):
        super(ProbeStation, self).__init__()

        self.areaString = '1,1,1'
        self.areaLabels = []
        self.areaIndex = 0
        self.areaStatus = [False,False,False]
        self.initUI()

    def initUI(self):

        self.setGeometry(200, 100, 600, 800)
        self.setWindowTitle('Probe Wafer')

        layout = QtGui.QVBoxLayout()
        waferSetupLayout = QtGui.QHBoxLayout()
        dieSetupLayout = QtGui.QHBoxLayout()

        self.waferMap = WaferMap()

        # wafer outer diameter field
        waferSetupLayout.addWidget( QtGui.QLabel("Wafer Dia [mm]:") )

        outerDiaField = QtGui.QLineEdit("72.6")
        outerDiaField.setValidator(QtGui.QDoubleValidator())
        outerDiaField.setMaxLength(8)
        outerDiaField.setFixedWidth(100)
        outerDiaField.textChanged.connect(self.waferMap.setOuterDiameter)
        waferSetupLayout.addWidget(outerDiaField)

        # wafer inner diameter field
        waferSetupLayout.addWidget( QtGui.QLabel("Inner Dia [mm]:") )

        innderDiaField = QtGui.QLineEdit("65")
        innderDiaField.setValidator(QtGui.QDoubleValidator())
        innderDiaField.setMaxLength(8)
        innderDiaField.setFixedWidth(100)
        innderDiaField.textChanged.connect(self.waferMap.setInnerDiameter)
        waferSetupLayout.addWidget(innderDiaField)

        waferSetupLayout.addStretch(1)

        # x,y pitch fields
        dieSetupLayout.addWidget( QtGui.QLabel("Pitch (x,y) [mm]:") )

        pitchXField = QtGui.QLineEdit("6.2")
        pitchXField.setValidator(QtGui.QDoubleValidator())
        pitchXField.setMaxLength(8)
        pitchXField.setFixedWidth(70)
        pitchXField.textChanged.connect(self.waferMap.setPitchX)
        dieSetupLayout.addWidget(pitchXField)

        pitchYField = QtGui.QLineEdit("6.2")
        pitchYField.setValidator(QtGui.QDoubleValidator())
        pitchYField.setMaxLength(8)
        pitchYField.setFixedWidth(70)
        pitchYField.textChanged.connect(self.waferMap.setPitchY)
        dieSetupLayout.addWidget(pitchYField)

        # odd/even radio buttons
        self.oddRadio = QtGui.QRadioButton("Odd")
        self.oddRadio.setChecked(True)
        self.oddRadio.toggled.connect(lambda:self.setOdd(True))
        dieSetupLayout.addWidget(self.oddRadio)

        self.evenRadio = QtGui.QRadioButton("Even")
        self.evenRadio.toggled.connect(lambda:self.setOdd(False))
        dieSetupLayout.addWidget(self.evenRadio)

        dieSetupLayout.addStretch(1)

        layout.addLayout(waferSetupLayout)
        layout.addLayout(dieSetupLayout)

        fileButton = QtGui.QPushButton("Select File")
        fileButton.clicked.connect(self.selectFile)
        layout.addWidget(fileButton)

        self.areaView = QtGui.QHBoxLayout()
        self.updateAreaLabels()
        layout.addLayout(self.areaView)

        layout.addWidget(self.waferMap)

        self.setLayout(layout)

        self.show()

    def selectFile(self):
        fileName = QtGui.QFileDialog.getSaveFileName(self, 'Save File')
        # self.resDataChest = dataChest(fileName)
        # self.resDataChest.createDataset("Resistance Measurements",
        #         [('die',[1],'string',''),('area',[1],'float64','um^2'),('DMM range',[1],'float64','Ohms')],
        #         [('resistance',[1],'float64','Ohms')])
        # self.resDataChest.addParameter("X Label", "Time")
        # self.resDataChest.addParameter("Y Label", "Temperature")
        # self.resDataChest.addParameter("Plot Title",
        #         self.startDatetime.strftime("ADR temperature history "
        #                                     "for run starting on %y/%m/%d %H:%M"))

    def setOdd(self, odd):
        self.waferMap.setOdd(odd)
        self.areaIndex = 0
        self.updateAreaLabels()

    def updateAreaLabels(self):
        for l in self.areaLabels:
            self.areaView.removeWidget(l)
            l.deleteLater()
            l.setParent(None)
        self.areaLabels = []
        index = 0
        areaList = self.areaString.strip(',').split(',')
        for a in areaList:
            l = QtGui.QLabel(a)
            l.setAlignment(QtCore.Qt.AlignCenter)
            l.setFont(QtGui.QFont("Arial",36))
            if index == self.areaIndex%len(areaList):
                l.setStyleSheet('color: red')
            index += 1
            l.setFixedHeight(50)
            self.areaLabels.append(l)
            self.areaView.addWidget(l)
        self.update()

    def mousePressEvent(self, event):
        QtGui.QApplication.focusWidget().clearFocus()

    def keyPressEvent(self, event):
        key = event.key()
        if key == QtCore.Qt.Key_Up:
            self.waferMap.changeSelectedDie(0,1)
            self.areaIndex = 0
            self.updateAreaLabels()
        elif key == QtCore.Qt.Key_Down:
            self.waferMap.changeSelectedDie(0,-1)
            self.areaIndex = 0
            self.updateAreaLabels()
        elif key == QtCore.Qt.Key_Left:
            self.waferMap.changeSelectedDie(-1,0)
            self.areaIndex = 0
            self.updateAreaLabels()
        elif key == QtCore.Qt.Key_Right:
            self.waferMap.changeSelectedDie(1,0)
            self.areaIndex = 0
            self.updateAreaLabels()
        elif key == QtCore.Qt.Key_Space:
            res = self.takeMeasurement()
            area = np.fromstring( self.areaString, dtype=float, sep=',' )
            dmmRange = None
            self.waferMap.addMeasurement(res, area, dmmRange)
            self.areaStatus[self.areaIndex%len(self.areaStatus)] = True
            self.areaIndex += 1
            self.updateAreaLabels()
        elif (key == QtCore.Qt.Key_Delete
           or key == QtCore.Qt.Key_Backspace):
            self.areaString = self.areaString[:-1]
            self.updateAreaLabels()
        else:
            try:
                newText = str(self.areaString + event.text())
                [float(x) for x in newText.strip(',').split(',')]
                self.areaString = newText
                self.updateAreaLabels()
            except ValueError:
                pass

    def takeMeasurement(self):
        return 5

class WaferMap(QtGui.QWidget):

    def __init__(self):
        super(WaferMap, self).__init__()

        self.odd = True
        self.wafer_diameter = 72.6
        self.inner_diameter = 65
        self.pitchX = 6.2
        self.pitchY = 6.2
        self.selectedDie = [6,6]
        self.initGrid()
        self.initUI()

    def initGrid(self):
        if self.odd:
            ndieX = int(np.floor(self.inner_diameter/self.pitchX)) + 1
            self.centerDieX = np.floor(ndieX/2.)
            ndieY = int(np.floor(self.inner_diameter/self.pitchY)) + 1
            self.centerDieY = np.floor(ndieY/2.)
        else:
            ndieX = int(np.floor(self.inner_diameter/self.pitchX))
            self.centerDieX = ndieX/2.-0.5
            ndieY = int(np.floor(self.inner_diameter/self.pitchY))
            self.centerDieY = ndieY/2.-0.5
        self.dieMapMask = np.ones((ndieX,ndieY), dtype=bool) # is die on wafer?
        self.dieMapData = np.zeros((ndieX,ndieY)) # actual data stored here
        for x in range(ndieX):
            for y in range(ndieY):
                self.dieMapData[x][y] = np.nan
                x_cent = (x-self.centerDieX)*self.pitchX
                y_cent = (y-self.centerDieY)*self.pitchY
                if np.sqrt(x_cent**2 + y_cent**2) >= self.inner_diameter/2.:
                    self.dieMapMask[x][y] = False

    def initUI(self):
        self.show()

    def changeSelectedDie(self, x, y):
        self.selectedDie[0] += x
        self.selectedDie[1] += y
        self.update()

    def setOdd(self, odd):
        self.odd = odd
        self.initGrid()
        self.update()

    def setInnerDiameter(self, dia):
        self.inner_diameter = float(dia)
        self.initGrid()
        self.update()

    def setOuterDiameter(self, dia):
        self.wafer_diameter = float(dia)
        self.initGrid()
        self.update()

    def setPitchX(self, pitch):
        self.pitchX = float(pitch)
        self.initGrid()
        self.update()

    def setPitchY(self, pitch):
        self.pitchY = float(pitch)
        self.initGrid()
        self.update()

    def addMeasurement(self, res, area, dmmRange):
        self.dieMapData[self.selectedDie[0]][self.selectedDie[1]] = res
        die = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'[self.selectedDie[0]] + str(int(self.selectedDie[1]))
        # self.resDataChest.addData( [die, area, dmmRange, res] )

    def paintEvent(self, e):

        qp = QtGui.QPainter()
        qp.begin(self)
        self.drawWafer(qp)
        qp.end()

    def drawWafer(self, qp):

        color = QtGui.QColor(0, 0, 0)
        color.setNamedColor('#d4d4d4')
        qp.setPen(color)

        nDieX = self.dieMapMask.shape[0]
        nDieY = self.dieMapMask.shape[1]
        minWindowDim = min(self.width(),self.height())
        pitchX = minWindowDim/nDieX
        pitchY = minWindowDim/nDieY
        dieWidth = pitchX*0.9
        dieHeight = pitchY*0.9

        qp.setBrush(QtGui.QColor(10, 10, 10, 200))
        dia = self.wafer_diameter*minWindowDim/(nDieX*self.pitchX)
        qp.drawEllipse(self.width()/2.-dia/2, minWindowDim/2.-dia/2, dia, dia)

        for x in range(nDieX):
            for y in range(nDieY):
                if [x,y] == self.selectedDie:
                    qp.setBrush(QtGui.QColor(200, 0, 0))
                elif not np.isnan(self.dieMapData[x][y]):
                    qp.setBrush(QtGui.QColor(25, 90, 0, 200))
                else:
                    qp.setBrush(QtGui.QColor(25, 0, 90, 200))
                if self.dieMapMask[x][y]:
                    qp.drawRect(self.width()/2 - minWindowDim/2 + (x+0.05)*pitchX, minWindowDim-(y+1)*pitchY, dieWidth,dieHeight)


def main():

    app = QtGui.QApplication(sys.argv)
    ps = ProbeStation()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
