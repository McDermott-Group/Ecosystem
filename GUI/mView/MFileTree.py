from PyQt4 import QtGui, QtCore
from PyQt4.QtGui import (QApplication, QColumnView, QFileSystemModel,
                         QSplitter, QTreeView)
from PyQt4.QtCore import QDir, Qt
import sys
from MGrapher import mGraph as MGrapher
class MFileTree(QtGui.QTreeView):
    def __init__(self, root, parent = None):
        super(MFileTree, self).__init__(parent)
        self.setStyleSheet("color:rgb(189, 195, 199);")
        # model = QFileSystemModel()
        # model.setRootPath(QDir.rootPath())
        # view = QTreeView(parent)
        # self.show()
        #app = QApplication(sys.argv)
        # Splitter to show 2 views in same widget easily.
        splitter = QSplitter()
        # The model.
        model = QFileSystemModel()
        # You can setRootPath to any path.
        model.setRootPath(root)
        # List of views.
        self.views = []
        #self.view = QTreeView(self)
        #self.itemPressed.connect(self.itemClicked)
        self.setModel(model)
        self.setRootIndex(model.index(root))
        self.header().setStyleSheet("background:rgb(70, 80, 88);")
        # for ViewType in (QColumnView, QTreeView):
            # # Create the view in the splitter.
            # view = ViewType(splitter)
            # # Set the model of the view.
            # view.setModel(model)
            # # Set the root index of the view as the user's home directory.
            # view.setRootIndex(model.index(QDir.homePath()))
        # # Show the splitter.
        # splitter.show()
        self.layout = QtGui.QHBoxLayout()
        #self.layout.addWidget(self)
        
        
        self.setLayout(self.layout)
       
        # Maximize the splitter.
        splitter.setWindowState(Qt.WindowMaximized)
        
        # Start the main loop.
    def resizeColumns(self):
        self.resizeColumnToContents(0)
    def fileSelected(self):
        index = self.selectedIndexes()[0]
        crawler = index.model().itemFromIndex(index)
        print "Selected item:", crawler
        self.callback(crawler)
    def setCallback(self, callback):
        self.callback = callback
    def selectionChanged(self, selected, deselected):
        #col = self.itemFromIndex(modelIndex)
        self.path = self.model().filePath(selected.indexes()[0])
        print "clicked", self.path
        self.callback(self.path)
        self.resizeColumns()
        
        #self.fileSelected()
    def mousePressEvent(self, event):
        QtGui.QTreeView.mousePressEvent(self, event)
        self.resizeColumns()
        