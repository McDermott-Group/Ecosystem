# Copyright (C) 2016 Noah Meltzer
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

__author__ = "Noah Meltzer"
__copyright__ = "Copyright 2016, McDermott Group"
__license__ = "GPL"
__version__ = "0.0.1"
__maintainer__ = "Noah Meltzer"
__status__ = "Beta"


from PyQt4 import QtGui, QtCore


class MReadout(QtGui.QWidget):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.parent = parent
        self.lcd = QtGui.QLCDNumber(parent)
        self.lcd.setSegmentStyle(QtGui.QLCDNumber.Flat)
        self.label = QtGui.QLabel("", self.parent)
        self.layout = QtGui.QHBoxLayout(parent)
        self.layout.addWidget(self.lcd)
        self.layout.addWidget(self.label)
        self.setLayout(self.layout)
        self.isLCD = True
        sizePolicy = QtGui.QSizePolicy(
            QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Minimum
        )
        self.setSizePolicy(sizePolicy)
        self.lcd.setSizePolicy(sizePolicy)
        self.label.setSizePolicy(sizePolicy)
        # self.label.hide()
        # self.lcd.hide()
        self.layout.setContentsMargins(0, 0, 0, 0)

    def setStyle(self, style):
        self.lcd.setStyleSheet(style)
        self.label.setStyleSheet(style)

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
            float(data)
            self.lcd.display(data)
            self.lcd.show()
            self.label.hide()
        except:
            self.lcd.hide()
            self.label.show()
            self.label.setText(str(str(data)))
