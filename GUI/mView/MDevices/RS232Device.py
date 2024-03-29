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
__copyright__ = "Copyright 2016, Noah Meltzer, McDermott Group"
__license__ = "GPL"
__version__ = "0.0.1"
__maintainer__ = "Noah Meltzer"
__status__ = "Beta"

# Import the parent class
from MDevice import MDevice

# We will use the pyserial class to interface with COM ports.
import serial
import time

# Traceback is good for printing errors and debugging.
import traceback

# Import necessary Qt libraries
from PyQt4 import QtGui


class RS232Device(MDevice):
    def __init__(self, *args, **kwargs):
        """Initialize variables. Most of the device parameters cannot yet be initialized."""
        super(RS232Device, self).__init__(*args, **kwargs)
        # The name of the device is passed as the first argument.
        self.name = args[0]
        # The name of the port (i.e. COMx) is given as the second argument.
        self.portname = args[1]
        # This dictionary will hold basic information about different parameters.
        # This dictionary will just be used by us.
        self.paramInfo = {}
        # This will hold a reference to the pySerial instance that
        # is used to communicate with the device.
        self.port = None
        # Is the device connected?
        self.connected = False
        # The serial timeout, default 10ms.
        self.timeout = kwargs.get("timeout", 10)
        # Default baud rate is 9600.
        self.baud = kwargs.get("baud", 9600)

    def onAddParameter(self, paramName, command, *args, **kwargs):
        # Look for keyword arguments
        precision = kwargs.get("precision", None)
        units = kwargs.get("units", None)
        # Add a key to our dictionary that holds another dictionary.
        self.paramInfo[str(paramName)] = {}
        thisParam = self.paramInfo[str(paramName)]
        # Add some more keys to our dictionary.
        thisParam["name"] = paramName
        thisParam["command"] = command
        thisParam["precision"] = precision
        thisParam["units"] = units

    def addButton(self, text, command, **kwargs):
        # Look for a message keyword argument
        message = kwargs.get("message", None)
        # Build the list.  The QPush button object will be appended to the end
        # of this list.
        button = []
        # We will make the first element of the list hold
        # the text that is displayed on the button.
        button.append(text)
        # The second element will be the command sent to the device
        # if the button is clicked.
        button.append(command)
        # We can include a warning message too.
        button.append(message)
        # Add the button to the gui
        self.addButtonToGui(button)

    def prompt(self, button):
        # We stored the warning message in the 3rd element of the button array.
        # If it is None, do not display a warning message, if it is not, display about
        # warning using the QMessageBox class.
        if button[2] is not None:
            # Create a QMessageBox
            msg = QtGui.QMessageBox()
            # Set the icon to an exclamation point.
            msg.setIcon(QtGui.QMessageBox.Warning)
            # Our warning message text is in the 3rd element of our array.
            msg.setText(button[2])
            # Add ok and cancel buttons.
            msg.setStandardButtons(QtGui.QMessageBox.Ok | QtGui.QMessageBox.Cancel)
            # The window title.
            msg.setWindowTitle("Warning")
            # Execute the class and retrieve the value clicked.
            retval = msg.exec_()
            # If ok was clicked then send the command to the serial device.
            if retval == QtGui.QMessageBox.Ok:
                # The command was put into the 2nd element of the array.
                self.port.write(button[1])
        # If no warning message was given, then just go ahead and send the
        # command.
        else:
            # The command was put into the 2nd element of the array.
            self.port.write(button[1])

    def setPort(self, portname, timeout=10):
        """Set the name of the port. i.e. COMx. Keyword args: timeout = 10."""
        self.portname = portname
        self.timeout = timeout

    def setYLabel(self, yLbl, units=""):
        """Set the label to be displayed on the independent variable axis."""
        self.frame.setYLabel(yLbl, units)

    def onBegin(self):
        """Begin the device."""
        self.connect()

    def connect(self):
        """Open the serial port and try to connect to it."""
        try:
            self.port = serial.Serial(
                self.portname, int(self.baud), timeout=self.timeout, write_timeout=10
            )
            self.connected = True
            return self.port
        except:
            traceback.print_exc()
            self.connected = False
            print("ERROR: port:", self.port, "will try again.")
            return None

    def query(self):
        """The query function is called with a period defined
        by MDevice.frame.getRefreshRate().  At the end it
        should set the readings by calling self.frame.setReadings([readings]).
        Where [readings] is an array of readings.
        """
        try:
            readings = []
            if not self.connected:
                # if not connected, connect.
                self.connect()
            # If self.port is not None.
            if self.port is not None:
                # For each parameter, get readings
                for param in self.getParameters():
                    print("param:", param)
                    # Flush anything that might on the port.
                    self.port.flush()
                    # Write the command to the port.
                    command = self.paramInfo[param]["command"]
                    if command != None:
                        self.port.write(self.paramInfo[param]["command"])
                        # Wait while there is nothing on the port.
                        while not self.port.in_waiting > 0:
                            time.sleep(0.01)
                        # While there is stuff on the port, read it.
                        reading = self.port.readline()
                        # Strip whitespace and newline characters off the
                        # received value.
                        reading = int(reading.strip())
                        # Tell the device what the readings were.
                        self.setReading(param, reading)
        except:
            try:
                self.port.close()
            except:
                pass
            traceback.print_exc()
            self.connected = False
            pass

    def close(self):
        """Stop the device. This includes closing the port."""
        try:
            self.port.close()
        except:
            print("Could not close port.")
