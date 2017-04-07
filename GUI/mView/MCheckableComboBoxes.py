from PyQt4 import QtGui, QtCore
import sys, os

class MCheckableComboBox(QtGui.QComboBox):
    """
    A dropdown menu whose elements are checkable.
    """
    def __init__(self):
        super(MCheckableComboBox, self).__init__()
        self.view().pressed.connect(self.handleItemPressed)
        self.setModel(QtGui.QStandardItemModel(self))
        self.setStyleSheet("\
                    background-color:rgb(70, 80, 88);\
                    color:rgb(189,195, 199);")       
    def handleItemPressed(self, index):
        """
        Called when an item is selected.
        
        :param index: The index of the selection on the dropdown menu.
        """
        item = self.model().itemFromIndex(index)
        if item.checkState() == QtCore.Qt.Checked:
            item.setCheckState(QtCore.Qt.Unchecked)
        else:
            item.setCheckState(QtCore.Qt.Checked)

    def isChecked(self, index):
        """
        Check if a dropdown item is checked.
        
        :param index: Item to check.
        """
        item = self.model().item(index)
        if item.checkState() == QtCore.Qt.Checked:
            return True
        return False

    def setChecked(self, index, checked):
        """
        Set the check state of a dropdown item.
        
        :param index: The index of the dropdown item.
        :param checked: Boolean: Check state.
        """
        item = self.model().item(index)
        item.setCheckState(QtCore.Qt.Checked if checked else QtCore.Qt.Unchecked)