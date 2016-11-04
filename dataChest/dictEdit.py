from PyQt4 import QtCore, QtGui
import sys
import ast
import traceback
import time
# ast.literal_eval("blah")
class Editor(QtGui.QMainWindow):
    def __init__(self, parent = None):
    
        self.data = {'example2': {'float': 1.2, 'other': (4, 8)}, 'example0': {}, 'example1': {'int': 14, 'str': {'Alex': {'Kong': 14.6}}, 'listex': [2, 'three', (4,4), {"NOAH":{"EMAIL":"noah"}, "Another List":["Blah", "blah", "BLAH"]}]}}

        
        QtGui.QWidget.__init__(self, parent)
        app.setActiveWindow(self)
        self.main_widget = QtGui.QWidget()
        self.mainVBox = QtGui.QVBoxLayout()
        self.main_widget.setLayout(self.mainVBox)
        self.setCentralWidget(self.main_widget)
        
        self.rawDictDisp = QtGui.QLabel(str(self.data))
        self.mainVBox.addWidget(self.rawDictDisp)

        self.tree = QtGui.QTreeView()
        self.mainVBox.addWidget(self.tree)
        
        
        

        self.constructTreeHelper(self.data)
    def constructTreeHelper(self, data):
        #parent = []
        parent = QtGui.QStandardItem("Dict")

        self.tree.setAlternatingRowColors(True)
        self.tree.setSortingEnabled(True)
        self.tree.setModel(QtGui.QStandardItemModel())
        self.tree.setSelectionBehavior(QtGui.QAbstractItemView.SelectItems)
        self.tree.model().setHorizontalHeaderLabels(['Parameter', 'Value'])
        self.tree.model().itemChanged.connect(self.handleItemChanged)
        #print [(x,y)  for x,y in self.data.iteritems()]
        #for key, value in self.data.iteritems():
        self.constructTree("dict",self.data, parent)
        self.tree.model().appendRow(parent)
        self.tree.expandAll()
        
    def constructTree(self, key, value, parent):

        if type(value) is dict:
            for key, data in value.iteritems():
                if type(data) is dict or  type(data) is list:
                    parent.appendRow([self.constructTree(key, data, QtGui.QStandardItem(str(key))),None])
                    parent.setFlags(QtCore.Qt.NoItemFlags |
                        QtCore.Qt.ItemIsEnabled)
                else:
                    self.appendRow(key, data, parent)

        elif type(value) is list:
 
            for i,elem in enumerate(value):
                if type(elem) is dict:
                    
                    #print key, elem
                   
                    parent.appendRow([self.constructTree(elem.keys()[0], elem[elem.keys()[0]], QtGui.QStandardItem(elem.keys()[0])),None])
                    parent.setFlags(QtCore.Qt.NoItemFlags |
                            QtCore.Qt.ItemIsEnabled)
                elif type(elem) is list:
                    parent.appendRow([self.constructTree(key, elem, QtGui.QStandardItem(str(key))),None])
                    parent.setFlags(QtCore.Qt.NoItemFlags |
                            QtCore.Qt.ItemIsEnabled)
                else:
                        self.appendRow('['+str(i)+'] :', elem, parent)
        else:
            #self.appendRow(key, value, parent)
            pass
        return parent
    def appendRow(self, key, value, parent):
            child0 = QtGui.QStandardItem(str(key))
            child0.setFlags(QtCore.Qt.NoItemFlags |
                                QtCore.Qt.ItemIsEnabled)
            child1 = QtGui.QStandardItem(str(value))
            child1.setFlags(QtCore.Qt.ItemIsEnabled |
                                QtCore.Qt.ItemIsEditable |
                                ~ QtCore.Qt.ItemIsSelectable)
            #parent.removeRow(parent.rowCount()-1)
            parent.appendRow([child0, child1])
            parent.setFlags(QtCore.Qt.NoItemFlags |
                QtCore.Qt.ItemIsEnabled)
    def handleItemChanged(self, item):
        #print item.parent().text()
        #print item.parent().child(item.row(), 0).text()
        try:
            print self.data
            parent = self.data[str(item.parent().text())]
            
            key = item.parent().child(item.row(), 0).text()
            #print type(parent[str(key)])(str(item.text()))
            #parent[str(key)] = type(parent[str(key)])(str(item.text()))
            parent[str(key)] =ast.literal_eval(str(item.text()))
        except:
            #item.parent().child(item.row(), 1).setText(str(parent[str(key)]))
            traceback.print_exc()
            print "type error"
            
        try:
            self.tree.model().removeRows(0,  self.tree.model().rowCount())
           # self.tree.model().reset()
            self.tree.setModel(QtGui.QStandardItemModel())
            self.constructTreeHelper(self.data)
            self.rawDictDisp.setText(str(self.data))
        except:
            print 'failed'
            traceback.print_exc()
if __name__ == '__main__':
    
    app=QtGui.QApplication(sys.argv)
    e = Editor()
    e.show()
    sys.exit(app.exec_())