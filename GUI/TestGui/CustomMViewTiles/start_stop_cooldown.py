# -*- coding: utf-8 -*-
# Copyright (C) 2016 Noah Meltzer
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

"""
Created on Fri Apr 07 12:33:18 2017

@author: Noah
"""
from PyQt4 import QtGui, QtCore
from MWeb import web
from MWidget import MWidget

import time
import re
class MStartStopCooldownWidget(MWidget):
    def __init__(self, cdLoc, stbyLoc):
        super(MStartStopCooldownWidget, self).__init__(None)
        font = QtGui.QFont()
        font.setBold(True)
        font.setPointSize(30)
        font.setWeight(50)
        font.setKerning(True)
        hbox = self.getHBox()
        self.cdButton = QtGui.QPushButton()
        self.cdButton.setFont(font)
       
        self.cdButton.clicked.connect(self.toggleCD)
        hbox.addWidget(self.cdButton)
        self.coolDown = web.persistentData.persistentDataAccess(None, 'cooldown_mode', default = True)
        if not self.coolDown:
             self.cdButton.setStyleSheet("background:rgb(70,88,70);color:rgb(189,195, 199)")
             self.cdButton.setText("Start Cooldown")
        else:
            self.cdButton.setStyleSheet("background:rgb(88,70,70);color:rgb(189,195, 199)")
            self.cdButton.setText("Stop Cooldown")
        self.stbyLoc = stbyLoc
        self.cdLoc = cdLoc
        
    def toggleCD(self):
        if self.coolDown:
            msg = "You are about to stop cooldown data collection."
        else:
            msg = "You are about to start cooldown data collection."
        p = QtGui.QMessageBox()
        p.setText(msg)
        p.setStandardButtons(QtGui.QMessageBox.Ok | QtGui.QMessageBox.Cancel);
        result = p.exec_()
        
        if result == QtGui.QMessageBox.Ok:
            if self.coolDown:
                self.coolDown = False
                web.persistentData.persistentDataAccess(False, 'cooldown_mode')

                loc = self.stbyLoc
                self.cdButton.setStyleSheet("background:rgb(70,88,70);color:rgb(189,195, 199)")
                self.cdButton.setText("Start Cooldown")
            else:
                self.coolDown = True
                web.persistentData.persistentDataAccess(True, 'cooldown_mode')
                loc = self.cdLoc
                self.cdButton.setStyleSheet("background:rgb(88,70,70);color:rgb(189,195, 199)")
                self.cdButton.setText("Stop Cooldown")
            for i,device in enumerate(web.devices):
                 chest = device.getFrame().getDataChestWrapper()
                 path = loc.split('\\')
                 r = re.compile('.{2}_.{2}_.{2}')

                 if not r.match(path[-1]):

                      dateFolderName = time.strftime('%x').replace(' ', '_')
                      dateFolderName = dateFolderName.replace('/','_')
                      loc = loc+'\\'+dateFolderName
                      print "\tNew location:", loc
                 else:
                     print "\tFound location:", loc
                 if chest != None:
                     print str(str(device) + ":\t"), "Switching path to:\t", loc
                     chest.changeLocation(loc, True)
                   
            