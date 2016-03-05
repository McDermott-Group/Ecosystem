# Copyright (C) 2016 Noah Meltzer, Alexander Opremcak
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
### BEGIN NODE INFO
[info]
name = Omega Temperature Monitor Server
version = 1.0.15
description = Monitors temperature

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
"""

import time
# The LoopingCall function allows a function to be called periodically
# on a time interval
from twisted.internet.task import LoopingCall
from twisted.internet.reactor import callLater
from twisted.internet.defer import inlineCallbacks, returnValue

from labrad.devices import DeviceServer, DeviceWrapper
from labrad.server import setting
import labrad.units as units
from labrad import util

from utilities import sleep


class OmegaTempMonitorWrapper(DeviceWrapper):
    @inlineCallbacks
    def connect(self, server, port):
        """Connect to an Omega temperature monitor."""
        print('Connecting to "%s" on port "%s"...' %(server.name, port))
        self.server = server
        self.ctx = server.context()
        self.port = port
        p = self.packet()
        p.open(port)
        # The following parameters match the default configuration of the
        # temperature monitor.
        p.baudrate(9600L)
        p.stopbits(1L)
        p.bytesize(7L)
        p.parity('O')
        p.timeout(1 * units.s)
        # Clear out the read buffer. This is necessary for some devices.
        p.read_line()
        yield p.send()
        
    def packet(self):
        """Create a packet in our private context."""
        return self.server.packet(context=self.ctx)
    
    def shutdown(self):
        """Disconnect from the serial port when we shut down."""
        return self.packet().close().send()
    
    @inlineCallbacks
    def write_line(self, code):
        """Write a data value to the temperature monitor."""
        yield self.server.write_line(code, context=self.ctx)

    @inlineCallbacks
    def read_line(self):
        """Read a data value to the temperature monitor."""
        ans = yield self.server.read(context=self.ctx)
        returnValue(ans)
   
            
class OmegaTempMonitorServer(DeviceServer):
    deviceName = 'Omega Temp Monitor Server'
    name = 'Omega Temp Monitor Server'
    deviceWrapper = OmegaTempMonitorWrapper
            
    @inlineCallbacks
    def initServer(self):
        """Initialize the Temperature Monitor Server"""
        print "Server Initializing"
        self.reg = self.client.registry()
        yield self.loadConfigInfo()
        yield DeviceServer.initServer(self)
        # Set the maximum acceptible temperature.
        self.thresholdMax = 50 * units.degF
        # Set the minimum acceptible temperature.
        self.thresholdMin = 30 * units.degF
        self.alertInterval = 10 # seconds
        self.t1 = 0
        self.t2 = 0

    def startRefreshing(self):
        """
        Start periodically refreshing the list of devices.
        The start call returns a deferred which we save for later.
        When the refresh loop is shutdown, we will wait for this
        deferred to fire to indicate that it has terminated.
        """
        self.refresher = LoopingCall(self.checkMeasurements)
        self.refresherDone = self.refresher.start(5.0, now=True)
       
    @inlineCallbacks
    def stopServer(self):
        """Kill the device refresh loop and wait for it to terminate."""
        if hasattr(self, 'refresher'):
            self.refresher.stop()
            yield self.refresherDone
            
    @setting(9, 'Start Server', returns='b')
    def start_server(self, c):
        """Initialize the repeated temperature measurement."""
        self.dev = self.selectedDevice(c)
        callLater(0.1, self.startRefreshing)
        return True

    @setting(10, 'Set Thresholds', low='v[degF]', high='v[degF]')
    def setThresholds(self, ctx, low, high):
        """
        This setting configures the trigger thresholds.
        If a threshold is exceeded, then an alert is sent.
        """
        if low >= high:
            return "The minimum threshold cannot be greater than the maximum\
                    threshold"
        self.thresholdMax = units.WithUnit(high, 'degF')
        self.thresholdMin = units.WithUnit(low, 'degF')
        return True

    @setting(11, 'Set Alert Interval', interval='v[s]')
    def setAlertInterval(self, ctx, interval):
        """Configure the alert interval."""
        self.alertInterval = interval['s']
        
    @inlineCallbacks
    def getTemperature(self, dev):
        """
        Query the thermometer for the temperature via serial
        communication.
        """
        # The string '*X01' asks the device for the current reading.
        yield dev.write_line("*X01")
        yield time.sleep(0.5)
        reading = yield dev.read_line()
        # Instrument randomly decides not to return, here's a hack.
        if not reading:
            returnValue(None)
        else:
            # Get last number in string.
            reading.rsplit(None, 1)[-1]
            # Strip the 'X01' off the returned string.
            reading = float(reading.lstrip("X01"))
            # Add correct units.
            output = reading * units.degF
            returnValue(output)

    @inlineCallbacks
    def checkMeasurements(self):
        """Make sure measured values are within acceptable range."""
        temperature = yield self.getTemperature(self.dev)
        if temperature:
            if temperature > self.thresholdMax:
                    self.sendAlert(temperature,
                    "Temperature is above {0}.".format(str(self.thresholdMax)))
            elif temperature < self.thresholdMin:
                    self.sendAlert(temperature,
                    "Temperature is below {0}.".format(str(self.thresholdMin)))
                
    def sendAlert(self, measurement, message):
        """
        Deal with an out-of-bounds measurement by calling this method,
        it accepts the meausurement, and an error message. It sends an
        email containing the measurements and the error message.
        """
        # If the amount of time specified by the alertInterval has elapsed,
        # then send another alert.
        self.t1 = time.time()
        if (self.t1 - self.t2) > self.alertInterval:
            # Store the last time an alert was sent in the form
            # seconds since the epoch (1/1/1970).
            self.t2 = self.t1
            print("{0}\n\t{1}\n\t{2}".format(message,
                                             time.ctime(self.t1),
                                             str(measurement)))
        return
    
    @inlineCallbacks
    def loadConfigInfo(self):
        """Load configuration information from the registry."""
        reg = self.reg
        yield reg.cd(['', 'Servers', 'Omega Temperature Monitor',
                'Links'], True)
        dirs, keys = yield reg.dir()
        p = reg.packet()
        for k in keys:
            p.get(k, key=k)
        ans = yield p.send()
        self.serialLinks = dict((k, ans[k]) for k in keys)
    
    @inlineCallbacks    
    def findDevices(self):
        """Find available devices from list stored in the registry."""
        devs = []
        for name, (server, port) in self.serialLinks.items():
            if server not in self.client.servers:
                continue
            server = self.client[server]
            ports = yield server.list_serial_ports()
            if port not in ports:
                continue
            devName = '{} - {}'.format(server, port)
            devs += [(name, (server, port))]
        returnValue(devs)


__server__ = OmegaTempMonitorServer()


if __name__ == '__main__':
    util.runServer(__server__)
