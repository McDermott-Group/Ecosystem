from PyQt4 import QtCore, QtGui
import sys

class Editor(QtGui.QWidget):

    def __init__(self):

        QtGui.QWidget.__init__(self)

        self.data = {
                    'example2': {'float': 1.2, 'other': (4, 8)},
                    'example0': {},
                    'example1': {'int': 14, 'str': {'Alex': {'Kong': 14.6}},
                    'listex': [2, 'three', (4,4), {"NOAH":{"EMAIL":"noah"}, "Another List":["Blah", "blah", "BLAH"]}]}
                    }

        self.mainVBox = QtGui.QVBoxLayout()
        self.setLayout(self.mainVBox)

        self.rawDictDisp = QtGui.QLabel(str(self.data), wordWrap=True)
        self.mainVBox.addWidget(self.rawDictDisp)

        self.tree = QtGui.QTreeView()
        self.mainVBox.addWidget(self.tree)

        self.constructTreeHelper(self.data)

    def constructTreeHelper(self, data):
        #parent = []
        parent = QtGui.QStandardItem("Dict")

        self.tree.setAlternatingRowColors(True)
        self.tree.setSortingEnabled(True)
        standardModel = QtGui.QStandardItemModel()
        rootNode = standardModel.invisibleRootItem()
        self.tree.setModel(standardModel)
        self.tree.setSelectionBehavior(QtGui.QAbstractItemView.SelectItems)
        self.tree.model().setHorizontalHeaderLabels(['Parameter', 'Value'])
        self.constructTree(rootNode, self.data)
        self.tree.model().appendRow(parent)
        self.tree.expandAll()
        self.tree.model().itemChanged.connect(self.itemChanged)

    def constructTree(self, rootNode, data, key=None):
        """ Recursive function forms tree which we display.  Lists are turned
        into dicts with their indicies as their keys. """
        modData = data
        isList = False
        if type(data) is list or type(data) is tuple:
            modData = dict(enumerate(data))
            isList = True
        if type(modData) is dict:
            for key, val in sorted(modData.iteritems()):
                newRoot = QtGui.QStandardItem(str(key))
                if isList:
                    newRoot.setEditable(False)
                newRoot.data = data
                newRoot.key = key
                newRoot.change = 'key'
                newRoot.val = QtGui.QStandardItem()
                rootNode.appendRow([newRoot,newRoot.val])
                self.constructTree(newRoot,val)
        else:
            newRoot = rootNode.val
            newRoot.setText(str(data))
            newRoot.data = rootNode.data
            newRoot.key = rootNode.key
            newRoot.change = 'val'

    def itemChanged(self, item):
        """ Basically just inserts the new data into the old data tree and
        remakes the tree.  Note that new data is cast as the old data type,
        except that ints become floats in case decimals are added. """
        if item.change == 'key':
            dataType = type(item.key)
            if dataType == int:
                dataType = float
            val = item.data[item.key]
            item.data[dataType(item.text())] = val
            del item.data[item.key]
        elif item.change == 'val':
            dataType = type( item.data[item.key] )
            if dataType == int:
                dataType = float
            try:
                item.data[item.key] = dataType(item.text())
            except TypeError as e:
                print str(e)
        self.constructTreeHelper(self.data)
        self.rawDictDisp.setText( str(self.data) )


if __name__ == '__main__':

    app=QtGui.QApplication(sys.argv)
    e = Editor()
    e.show()
    sys.exit(app.exec_())
