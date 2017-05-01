from PyQt4 import QtGui, QtCore
import sys
import os


class MCheckableComboBox(QtGui.QComboBox):
    def __init__(self):
        super(MCheckableComboBox, self).__init__()
        self.view().pressed.connect(self.handleItemPressed)
        self.setModel(QtGui.QStandardItemModel(self))
        self.setStyleSheet("\
                    background-color:rgb(70, 80, 88);\
                    color:rgb(189,195, 199);")

    def handleItemPressed(self, index):
        item = self.model().itemFromIndex(index)
        if item.checkState() == QtCore.Qt.Checked:
            item.setCheckState(QtCore.Qt.Unchecked)
        else:
            item.setCheckState(QtCore.Qt.Checked)

    def isChecked(self, index):
        item = self.model().item(index)
        if item.checkState() == QtCore.Qt.Checked:
            return True
        return False

    def setChecked(self, index, checked):
        item = self.model().item(index)
        item.setCheckState(
            QtCore.Qt.Checked if checked else QtCore.Qt.Unchecked)
