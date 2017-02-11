from PyQt4 import QtGui, QtCore
from PyQt4.QtGui import (QApplication, QColumnView, QFileSystemModel,
                         QSplitter, QTreeView)
from PyQt4.QtCore import QDir, Qt
import sys
class MFileTree(QtGui.QWidget):
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
        views = []
        view = QTreeView(self)
        view.setModel(model)
        view.setRootIndex(model.index(root))
        view.header().setStyleSheet("background:rgb(70, 80, 88);")
        # for ViewType in (QColumnView, QTreeView):
            # # Create the view in the splitter.
            # view = ViewType(splitter)
            # # Set the model of the view.
            # view.setModel(model)
            # # Set the root index of the view as the user's home directory.
            # view.setRootIndex(model.index(QDir.homePath()))
        # # Show the splitter.
        # splitter.show()
        layout = QtGui.QHBoxLayout()
        layout.addWidget(view)
        self.setLayout(layout)
        # Maximize the splitter.
        splitter.setWindowState(Qt.WindowMaximized)
        # Start the main loop.
    