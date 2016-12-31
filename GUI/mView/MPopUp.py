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
__version__ = "2.0.2"
__maintainer__ = "Noah Meltzer"
__status__ = "Beta"

from PyQt4 import QtCore, QtGui


class PopUp(QtGui.QDialog):
    """Small class for a popup window which displays a message
    and allows the user to select OK or Cancel."""
    # Property 'consent' holds the user's decision.
    consent = None
    def __init__(self, message, parent=None):
        """Initialize the pop-up."""
        # The user gives a message to display.
        self.msg = message
        # Initialize the rest of the widget.
        QtGui.QWidget.__init__(self, parent)
        self.setupUi(self)
        
    def setupUi(self, Dialog):
        """Configure the look and function of the popup."""
        self.setObjectName("Warning")
        # Create a new label that will display the message.
        self.warning = QtGui.QLabel()
        self.warning.setText(self.msg)
        
        HBox = QtGui.QHBoxLayout()
        HBox.addWidget(self.warning)
        mainVBox = QtGui.QVBoxLayout()
        mainVBox.addWidget(self.warning)
        mainVBox.addLayout(HBox)
        self.setLayout(mainVBox)

        self.warning.setWordWrap(True)
        self.warning.setAlignment(QtCore.Qt.AlignCenter)
        # Create an 'OK' button at the bottom of the screen.
        self.okButton = QtGui.QPushButton(Dialog)
        HBox.addStretch(0)
        HBox.addWidget(self.okButton)
        self.okButton.setText("OK")
        self.okButton.clicked.connect(self.okClicked)
        self.cancelButton = QtGui.QPushButton(Dialog)
        HBox.addWidget(self.cancelButton)
        self.cancelButton.setText("Cancel")
        self.cancelButton.clicked.connect(self.cancelClicked)
        self.setWindowTitle('Warning')

    def okClicked(self):
        """Called when the ok button is clicked."""
        # The user has given consent.
        self.consent = True
        # Close the popup.
        self.close()

    def cancelClicked(self):
        """Called when the cancel button is clicked."""
        # The user has not given consent.
        self.consent = False
        # Close the popup.
        self.close()