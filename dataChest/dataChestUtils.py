import sys
import os
from PyQt4 import QtGui, QtCore
import time
import gc
from dataChest import *


class FilePicker(QtGui.QWidget):
    """
    An example file picker application
    """
    def __init__(self, parent = None):
        self.app = QtGui.QApplication(sys.argv)
        super(FilePicker, self).__init__(parent)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
        try:
            self.data_root = os.environ["BROWSER_ROOT"]
        except:
            os.environ["BROWSER_ROOT"] = os.environ["DATA_ROOT"]
            self.data_root = os.environ["BROWSER_ROOT"]
        self.relativePath = None
        self.selectedFileName = None
        self.dialog = QtGui.QFileDialog()
        self.dialog.fileSelected.connect(QtCore.QCoreApplication.instance().quit)
        self.fullFilePath = self.dialog.getOpenFileName(self, 'Open File Up',self.data_root,"Text files (*.hdf5)")
        self.fullFilePath = str(self.fullFilePath)
        self.dialog.close()
        self.getDatasetName()
        if self.selectedFileName is not None:
            os.environ['BROWSER_ROOT'] = self.fullFilePath.replace("/", "\\").replace("\\"+self.selectedFileName, "")
    
    def getDataChestObject(self):
        datachest_object = dataChest(self.relativePath)
        datachest_object.openDataset(self.selectedFileName)
        return datachest_object
        
    def getDatasetName(self):
        if self.fullFilePath == '':
            return
        else:
            if os.environ["DATA_ROOT"] not in self.fullFilePath.replace("/", "\\"):
                print "The dataChest shall not venture outside of the DATA_ROOT path."
                return
            else:
                self.relativePath = self.fullFilePath.strip(self.data_root).split("/")[3:-1]
                self.selectedFileName = self.fullFilePath.strip(self.data_root).split("/")[-1]
        return


# if __name__ == "__main__":
   # app = QtGui.QApplication(sys.argv)
   # ex = FilePicker()
