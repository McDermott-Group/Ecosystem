#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (C) 2016 Chris Wilen
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sys, os
from PyQt4 import QtGui, QtCore
import numpy as np
import datetime

import labrad
from labrad.server import inlineCallbacks
from labrad import units
from dataChest import dataChest

class ProbeStation(QtGui.QWidget):

    def __init__(self, cxn):
        super(ProbeStation, self).__init__()
        self.cxn = cxn
        self.dmm = self.cxn.keithley_2000_dmm
        p = self.dmm.packet()
        p.select_device()
        p.set_auto_range_status(False)
        p.return_to_local()
        p.send()

        self.areaString = '1,1,1'
        self.innerDiameter = 65
        self.odd = False
        self.pitchX = 6.25
        self.pitchY = 6.25
        self.fileDir = []
        self.measurements = {} # {die: {index:[resistances]}}
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

        innderDiaField = QtGui.QLineEdit(str(self.innerDiameter))
        innderDiaField.setValidator(QtGui.QDoubleValidator())
        innderDiaField.setMaxLength(8)
        innderDiaField.setFixedWidth(100)
        innderDiaField.textChanged.connect(self.setInnerDiameter)
        waferSetupLayout.addWidget(innderDiaField)

        waferSetupLayout.addStretch(1)

        # x,y pitch fields
        dieSetupLayout.addWidget( QtGui.QLabel("Pitch (x,y) [mm]:") )

        pitchXField = QtGui.QLineEdit(str(self.pitchX))
        pitchXField.setValidator(QtGui.QDoubleValidator())
        pitchXField.setMaxLength(8)
        pitchXField.setFixedWidth(70)
        pitchXField.textChanged.connect(self.setPitchX)
        dieSetupLayout.addWidget(pitchXField)

        pitchYField = QtGui.QLineEdit(str(self.pitchY))
        pitchYField.setValidator(QtGui.QDoubleValidator())
        pitchYField.setMaxLength(8)
        pitchYField.setFixedWidth(70)
        pitchYField.textChanged.connect(self.setPitchY)
        dieSetupLayout.addWidget(pitchYField)

        # odd/even radio buttons
        self.oddRadio = QtGui.QRadioButton("Odd")
        self.oddRadio.setChecked(self.odd)
        self.oddRadio.toggled.connect(lambda:self.setOdd(True))
        dieSetupLayout.addWidget(self.oddRadio)

        self.evenRadio = QtGui.QRadioButton("Even")
        self.oddRadio.setChecked(not self.odd)
        self.evenRadio.toggled.connect(lambda:self.setOdd(False))
        dieSetupLayout.addWidget(self.evenRadio)

        # layouts
        dieSetupLayout.addStretch(1)

        layout.addLayout(waferSetupLayout)
        layout.addLayout(dieSetupLayout)

        # file button
        self.fileButton = QtGui.QPushButton("Select File")
        self.fileButton.clicked.connect(self.selectFile)
        layout.addWidget(self.fileButton)

        self.areaView = AreaDisplay()
        self.areaView.setAreasString(self.areaString)
        layout.addWidget(self.areaView)

        layout.addWidget(self.waferMap)

        self.setLayout(layout)

        self.show()

    def selectFile(self):
        fileDialog = QtGui.QFileDialog()
        fileDialog.setNameFilters( [self.tr('HDF5 Files (*.hdf5)'), self.tr('All Files (*)')] )
        fileDialog.setDefaultSuffix( '.hdf5' )
        baseDirList = ['Z:','mcdermott-group','Data']
        baseDir = os.path.join( *(baseDirList+self.fileDir) )
        fileDialog.setDirectory( baseDir )
        filePath = str(fileDialog.getSaveFileName(self, 'Save File', options=QtGui.QFileDialog.DontConfirmOverwrite))
        print( 'save file: ' + filePath )
        if filePath is not '':
            filePath = filePath.replace(baseDir, '') # remove base path
            if filePath[-5:] == '.hdf5':
                filePath = filePath[:-5]
            fileArray = filePath.split('/')
            for elem in baseDirList:
                fileArray.remove(elem)
            self.fileDir = fileArray[:-1]
            fileName = fileArray[-1]
            self.resDataChest = dataChest( self.fileDir )
            try:
                self.resDataChest.openDataset(fileName, modify=True)
                self.setOdd(self.resDataChest.getParameter("Odd"))
                self.setPitchX(self.resDataChest.getParameter("Pitch X"))
                self.setPitchY(self.resDataChest.getParameter("Pitch Y"))
                self.setInnerDiameter(self.resDataChest.getParameter("Inner Diameter"))
                oldData = self.resDataChest.getData()
                for die,index,_,__,resistance in oldData:
                    if die not in self.measurements:
                        self.measurements[die] = {}
                    if index not in self.measurements[die]:
                        self.measurements[die][index] = []
                    self.measurements[die][index].append(resistance)
                print( 'opened old dataset' )
            except Exception:
                self.resDataChest.createDataset(fileName,
                        [('die',[1],'string',''),('index',[1],'uint8',''),
                         ('area',[1],'float64','um**2'),
                            ('DMM range',[1],'float64','Ohm')],
                        [('resistance',[1],'float64','Ohms')])
                self.resDataChest.addParameter("Odd", self.odd)
                self.resDataChest.addParameter("Pitch X", self.pitchX)
                self.resDataChest.addParameter("Pitch Y", self.pitchY)
                self.resDataChest.addParameter("Inner Diameter", self.innerDiameter)
                self.resDataChest.addParameter("Date Measured", str(datetime.datetime.utcnow()))
            self.waferMap.initGrid()
            self.areaView.setAreasIndex(0)
        self.fileButton.setText('End Measurement')
        self.fileButton.clicked.disconnect(self.selectFile)
        self.fileButton.clicked.connect(self.endMeasurement)

    def endMeasurement(self):
        self.fileDir = []
        self.resDataChest = None
        self.fileButton.setText('Select File')
        self.fileButton.clicked.disconnect(self.endMeasurement)
        self.fileButton.clicked.connect(self.selectFile)

    def setOdd(self, odd):
        self.waferMap.setOdd(bool(odd))
        self.odd = bool(odd)
        self.areaView.setAreasIndex(0)
        try:
            self.resDataChest.addParameter("Odd", bool(self.odd), overwrite=True)
        except AttributeError:
            pass # if file has not been created yet

    def setInnerDiameter(self, dia):
        self.waferMap.setInnerDiameter(float(dia))
        self.innerDiameter = float(dia)
        self.areaView.setAreasIndex(0)
        try:
            self.resDataChest.addParameter("Inner Diameter", self.innerDiameter, overwrite=True)
        except AttributeError:
            pass # if file has not been created yet

    def setPitchX(self, pitch):
        self.pitchX = float(pitch)
        self.waferMap.setPitchX(float(pitch))
        self.areaView.setAreasIndex(0)
        try:
            self.resDataChest.addParameter("Pitch X", self.pitchX, overwrite=True)
        except AttributeError:
            pass # if file has not been created yet

    def setPitchY(self, pitch):
        self.pitchY = float(pitch)
        self.waferMap.setPitchY(float(pitch))
        self.areaView.setAreasIndex(0)
        try:
            self.resDataChest.addParameter("Pitch Y", self.pitchY, overwrite=True)
        except AttributeError:
            pass # if file has not been created yet

    def mousePressEvent(self, event):
        QtGui.QApplication.focusWidget().clearFocus()

    @inlineCallbacks
    def keyPressEvent(self, event):
        key = event.key()
        if key == QtCore.Qt.Key_Up:
            self.waferMap.changeSelectedDie(0,-1)
            self.areaView.setAreasIndex(0)
        elif key == QtCore.Qt.Key_Down:
            self.waferMap.changeSelectedDie(0,1)
            self.areaView.setAreasIndex(0)
        elif key == QtCore.Qt.Key_Left:
            self.waferMap.changeSelectedDie(-1,0)
            self.areaView.setAreasIndex(0)
        elif key == QtCore.Qt.Key_Right:
            self.waferMap.changeSelectedDie(1,0)
            self.areaView.setAreasIndex(0)
        elif key == QtCore.Qt.Key_A:
            self.areaView.decreaseAreasIndex()
        elif key == QtCore.Qt.Key_D:
            self.areaView.increaseAreasIndex()
        elif key == QtCore.Qt.Key_Space:
            die = self.waferMap.getSelectedDie()
            area = float(self.areaView.getCurrentArea())
            index = self.areaView.getIndex()
            res = yield self.dmm.get_fw_resistance()
            dmmRange = yield self.dmm.get_fw_range()
            yield self.dmm.return_to_local()
            self.resDataChest.addData( [[die, index, area, dmmRange['Ohm'], res['Ohm']]] )
            if die not in self.measurements:
                self.measurements[die] = {}
            if index not in self.measurements[die]:
                self.measurements[die][index] = []
            self.measurements[die][index].append(res['Ohm'])
            self.waferMap.setDieProgress(len(self.measurements[die]))
            print [die, area, dmmRange['Ohm'], res['Ohm']]
            self.areaView.increaseAreasIndex()
        elif (key == QtCore.Qt.Key_Delete
           or key == QtCore.Qt.Key_Backspace):
            self.areaString = self.areaString[:-1]
            self.areaView.setAreasString(self.areaString)
        else:
            try:
                newText = str(self.areaString + event.text())
                [float(x) for x in newText.strip(',').split(',')]
                self.areaString = newText
                self.areaView.setAreasString(self.areaString)
            except ValueError:
                pass
        die =  self.waferMap.getSelectedDie()
        if die in self.measurements:
            self.areaView.setResistances(self.measurements[die])
        else:
            self.areaView.setResistances({})
        self.areaView.refreshUI()
        print die

class AreaDisplay(QtGui.QWidget):

    def __init__(self):
        super(AreaDisplay, self).__init__()

        self.areaString = ''
        self.areaLabels = []
        self.resistances = {} # {index,[resistances]}
        self.index = 0

        # self.setFixedHeight(55)
        self.setSizePolicy(QtGui.QSizePolicy.Minimum,
                     QtGui.QSizePolicy.Maximum)
        
        container = QtGui.QVBoxLayout()
        
        self.areaView = QtGui.QHBoxLayout()
        
        self.resView = QtGui.QHBoxLayout()

        container.addLayout(self.areaView)
        container.addLayout(self.resView)

        self.setLayout(container)
        self.initUI()

    def initUI(self):
        self.show()

    def refreshUI(self):
        # delete all the old labels
        for l in self.areaLabels:
            self.areaView.removeWidget(l)
            l.deleteLater()
            l.setParent(None)

        #create all the new labels
        self.areaLabels = []
        index = 0
        areaList = self.areaString.strip(',').split(',')
        self.index = self.index%len(areaList)
        for a in areaList:
            l = QtGui.QLabel(a) # area line
            l.setAlignment(QtCore.Qt.AlignCenter)
            l.setFont(QtGui.QFont("Arial",36))

            if index in self.resistances:
                l.setStyleSheet('color: green')
                resList = ['{:.0f}'.format(r) for r in self.resistances[index]]
                r = QtGui.QLabel('\n'.join(resList)) # resistances below
            else:
                r = QtGui.QLabel('')
            r.setAlignment(QtCore.Qt.AlignCenter)
            # r.setAlignment(QtCore.Qt.AlignTop)
            r.setFont(QtGui.QFont("Arial",12))

            if index == self.index:
                l.setStyleSheet('color: red')

            index += 1
            l.setFixedHeight(50)
            self.areaLabels.append(l)
            self.areaLabels.append(r)
            self.areaView.addWidget(l)
            self.resView.addWidget(r)
            if index < len(areaList) or self.areaString[-1] is ',':
                commaLabel = QtGui.QLabel(',')
                commaLabel.setAlignment(QtCore.Qt.AlignCenter)
                commaLabel.setFont(QtGui.QFont("Arial",36))
                commaLabel.setStyleSheet('color: grey')
                commaLabel.setFixedWidth(10)
                commaLabel.setFixedHeight(50)
                self.areaLabels.append(commaLabel)
                self.areaView.addWidget(commaLabel)

    def setAreasString(self, string):
        self.areaString = string
        self.refreshUI()

    def setResistances(self, resistances):
        self.resistances = resistances # {index: [res]}

    def setAreasIndex(self, index):
        self.index = index
        self.refreshUI()

    def getIndex(self):
        return self.index

    def getCurrentArea(self):
        areaList = self.areaString.strip(',').split(',')
        return areaList[self.index%len(areaList)]

    def increaseAreasIndex(self):
        self.index += 1
        self.refreshUI()

    def decreaseAreasIndex(self):
        self.index -= 1
        self.refreshUI()

class WaferMap(QtGui.QWidget):

    def __init__(self):
        super(WaferMap, self).__init__()

        self.odd = False
        self.wafer_diameter = 72.6
        self.inner_diameter = 65
        self.pitchX = 6.25
        self.pitchY = 6.25
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
        self.dieMapData = np.zeros((ndieX,ndieY), dtype=bool) # is data taken here
        for x in range(ndieX):
            for y in range(ndieY):
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

    def getSelectedDie(self):
        return 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'[self.selectedDie[0]] + str(int(self.selectedDie[1])+1)

    def setDieProgress(self, numberCompleted):
        self.dieMapData[self.selectedDie[0]][self.selectedDie[1]] = numberCompleted

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
                if [x,y] == self.selectedDie: # red for selected die
                    qp.setBrush(QtGui.QColor(200, 0, 0))
                elif self.dieMapData[x][y]: # green for measured die
                    progress = 1.0*self.dieMapData[x][y]/self.dieMapData.max()
                    qp.setBrush(QtGui.QColor(25, progress*90, 0, 200))
                else: # blue otherwise
                    qp.setBrush(QtGui.QColor(25, 0, 90, 200))
                if self.dieMapMask[x][y]:
                    qp.drawRect(self.width()/2 - minWindowDim/2 + (x+0.05)*pitchX, (y+0.05)*pitchY, dieWidth,dieHeight)


def main():

    app = QtGui.QApplication(sys.argv)
    with labrad.connect() as cxn:
        ps = ProbeStation(cxn)
        sys.exit(app.exec_())


if __name__ == '__main__':
    main()
