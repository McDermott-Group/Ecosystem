import sys
import os
from PyQt4 import QtGui, QtCore
import time
import gc


class FilePicker(QtGui.QWidget):
    """
    An example file picker application
    """
    def __init__(self, parent = None):
        super(FilePicker, self).__init__(parent)
        self.root = os.environ["DATA_CHEST_ROOT"]
        self.dialog = QtGui.QFileDialog()
        self.dialog.fileSelected.connect(QtCore.QCoreApplication.instance().quit)
        self.fullFilePath = self.dialog.getOpenFileName(self, 'Open File Up',self.root,"Text files (*.hdf5)")
        self.fullFilePath = str(self.fullFilePath)
        self.dialog.close()
        self.getDatasetName()
        #QtCore.QCoreApplication.instance().quit()
        
    def getDatasetName(self):
        if self.fullFilePath == '':
            return None
        else:
            if self.root not in self.fullFilePath:
                print "The dataChest cannot venture outside of the DATA_CHEST_ROOT path."
                return None
            else:
                self.relativePath = self.fullFilePath.strip(self.root).split("/")[:-1]
                self.selectedFileName = self.fullFilePath.strip(self.root).split("/")[-1]


if __name__ == "__main__":
   app = QtGui.QApplication(sys.argv)
   ex = FilePicker()
