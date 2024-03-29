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


class MStartStopCooldownWidget(MWidget):
    def __init__(self):
        super(Device, self).__init__()
        hbox = self.getHBox()
        label = QtGui.QLabel("HELLO!")
        hbox.addWidget(label)
