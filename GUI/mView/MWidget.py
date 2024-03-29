# -*- coding: utf-8 -*-
"""
Created on Fri Apr 07 12:35:35 2017

@author: Noah
"""
from PyQt4 import QtGui, QtCore


class MWidget(QtGui.QFrame):
    def __init__(self, device, parent=None):
        QtGui.QWidget.__init__(self, parent)
        #        self.setStyleSheet("background: rgb(52, 73, 94);"
        #        "margin:0px; border:2px solid rgb(0, 0, 0);")
        #        self.setStyleSheet("QFrame{background-color: rgb(80,120,88); "
        #                "margin:0px; border:2px solid rgb(0, 0, 0);}")
        self.hbox = QtGui.QHBoxLayout()

        self.setLayout(self.hbox)

    def getHBox(self):
        return self.hbox
