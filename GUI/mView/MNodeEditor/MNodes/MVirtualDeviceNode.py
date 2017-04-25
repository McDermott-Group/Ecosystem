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

__author__ = "Noah Meltzer"
__copyright__ = "Copyright 2016, McDermott Group"
__license__ = "GPL"
__version__ = "0.0.1"
__maintainer__ = "Noah Meltzer"
__status__ = "Beta"


from PyQt4 import QtCore, QtGui
from MNodeEditor.MNode import MNode
from MNodeEditor.MAnchor import MAnchor
from MDevices.MVirtualDevice import MVirtualDevice
from MWeb import web
from functools import partial


class MVirtualDeviceNode(MNode):
    def __init__(self, name, *args, **kwargs):

        super(MVirtualDeviceNode, self).__init__(None, *args, **kwargs)
        self.name = name
        self.setColor(52, 94, 73)
        self.associatedDevice = None
        self.device = None
        self.keywordArgs = kwargs

    def begin(self, *args):
        super(MVirtualDeviceNode, self).begin()
        # print "initializing MVirtualDeviceNode"
        #self.addAnchor(name = 'Self', type = 'output')
        # self.propogateData(False)
        #self.setTitle("Virtual Device")
        # print "creating new virtual device named", self.getTitle()
        self.associatedDevice = MVirtualDevice(self.name, **self.keywordArgs)
        self.setDevice(self.associatedDevice)
        self.associatedDevice.addPlot()
        #self.associatedDevice.addParameter(str(self.getAnchors()[0]), None, None, show = False)
        self.associatedDevice.getFrame().setNode(self)
        editButton = QtGui.QPushButton("Edit")

        #self.showOnGui = QtGui.QCheckBox("Show", self.nodeFrame)
        #self.showOnGui.setStyleSheet("color:rgb(189,195,199);\n background:rgb(52,94,73,0)")
        # self.showOnGui.setChecked(True)
        #self.nodeLayout.addWidget(editButton, 0, 1)
        #self.nodeLayout.addWidget(self.showOnGui, 1, 0)
        # editButton.clicked.connect(self.openVirtualDeviceGui)
        #web.gui.color = (52,94,73)

        # self.showOnGui.clicked.connect(partial(self.associatedDevice.getFrame().getContainer().visible))
    def onLoad(self):
        web.gui.addDevice(self.associatedDevice)

    def setDevice(self, device):
        self.device = device

    def refreshData(self):
        # print "virtual device refreshing data"

        reading = []
        units = []
        paramNames = []
        precisions = []
        for i, anchor in enumerate(self.getAnchors()[0::]):
           # print "anchor:", anchor
            metadata = anchor.getMetaData()
            data = anchor.getData()
            if metadata != None:
                units.append(metadata[1])
                precisions.append(None)
               # paramNames.append(metadata[0])
            else:
                # print self.associatedDevice, "units",
                # self.associatedDevice.getFrame().getUnits()
                units.append(self.associatedDevice.getUnit(str(anchor)))

                precisions.append(None)
            paramNames.append(self.associatedDevice.getFrame().nicknames[i])
            # print "data:", data
            if type(data) is list:
                # print "its a tuple, saving", data[2][-1]

                reading.append(data[-1])

            else:
                reading.append(data)
          #  anchor.getLcd().display(reading[-1])
        # print "setting virt dev readings:", reading
        self.associatedDevice.getFrame().setUnits(units)

        self.associatedDevice.getFrame().nicknames = paramNames
        self.associatedDevice.setReadings(reading)
        self.associatedDevice.setPrecisions(precisions)
    # def onAddAnchor(self, anchor, **kwargs):
        #
        #

    def anchorAdded(self, anchor, **kwargs):
        # print "---------Adding parameter"
        self.associatedDevice.addParameter(str(anchor), None, None)

    def pipeConnected(self, anchor, pipe):
        '''called when a pipe is added'''

        # if anchor.getType() == 'input':
        #newAnchor = self.addAnchor(name = 'New Input', type = 'input')
        #self.associatedDevice.addParameter(str(newAnchor), None, None)
        # elif anchor.getLabel() == 'Self':
        # anchor.setData(self.getDevice())
        pass

    def pipeDisconnected(self):

        self.removeAnchor()

    def openVirtualDeviceGui(self):
        dialog = MVirtualDeviceGui(self.associatedDevice, self)
        dialog.exec_()


class MVirtualDeviceGui(QtGui.QDialog):
    def __init__(self, associatedDevice, node,  parent=None):
        super(MVirtualDeviceGui, self).__init__(parent)
        self.node = node
        self.associatedDevice = associatedDevice
        layout = QtGui.QFormLayout()
        self.btns = []
        for i, nickname in enumerate(self.associatedDevice.getFrame().getNicknames()):
            btn = QtGui.QPushButton("Edit")
            lbl = QtGui.QLabel(nickname)
            btn.clicked.connect(partial(self.getName, "New Name:", i, lbl))
            layout.addRow(lbl, btn)
            self.btns.append(btn)
        closebtn = QtGui.QPushButton("close")
        closebtn.clicked.connect(self.close)
        layout.addRow(closebtn)
        self.setLayout(layout)

    def getName(self, name, index, label, anchor):
        text, ok = QtGui.QInputDialog.getText(
            self, "Virtual Device Name Editor", name)
        if ok:
            nicknames = self.associatedDevice.getFrame().getNicknames()
            nicknames[index] = text
            self.associatedDevice.getFrame().setNicknames(nicknames)
            self.associatedDevice.getContainer(
            ).nicknameLabels[index].setText(text)
            self.node.getAnchors()[index].setLabel(text)
            label.setText(text)
        return text
