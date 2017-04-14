# -*- coding: utf-8 -*-
"""
Created on Fri Apr 07 19:26:23 2017

@author: Noah
"""

from PyQt4 import QtCore, QtGui
from CustomMViewTiles.tetrix import TetrixWindow as tetrix
class tetris(QtGui.QFrame):
    def __init__(self):
        super(tetris, self).__init__(None)
        self.setObjectName("myParentWidget");
        self.setStyleSheet("QFrame#myParentWidget{background: rgb(52, 73, 94);"
                           "margin:0px; border:2px solid rgb(0, 0, 0);}"
                           "QPushButton{color:rgb(189,195, 199); background: rgb(70,80,88)}"
                           "QLabel{color:rgb(189,195, 199); background: rgb(52, 73, 94)}"
                           )
        self.hidden = True
        self.font = QtGui.QFont()
        self.font.setBold(False)
        self.font.setWeight(50)
        self.font.setKerning(True)
        self.font.setPointSize(20)
        self.label = QtGui.QLabel("Tetris")
        self.label.setStyleSheet("QLabel{color:rgb(189,195, 199); background : rgb(52, 73, 94)}")
        self.label.setFont(self.font)
        self.button = QtGui.QPushButton("Tetris")
        
        self.button.clicked.connect(self.toggleTetris)
        self.layout = QtGui.QHBoxLayout()
        self.vlayout = QtGui.QVBoxLayout()
        self.setLayout(self.vlayout)
        self.vlayout.addWidget(self.label)
        self.buttonLayout = QtGui.QHBoxLayout()
        
        self.buttonLayout.addWidget(self.button)
        self.buttonLayout.addStretch()
        self.vlayout.addLayout(self.buttonLayout)
        self.vlayout.addLayout(self.layout)
        self.tet = tetrix()
        self.tet.hide()
        self.layout.addWidget(self.tet)
        self.layout.addStretch()
        
    def toggleTetris(self):
        if self.hidden:
            self.tet.show()
            self.hidden = False
            self.button.setText("Hide Tetris")
        else:
            self.tet.hide()
            self.hidden = True
            self.button.setText("Show Tetris")
