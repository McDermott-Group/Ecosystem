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
name = Omega Ratemeter
version = 1.0.16
description = Monitors water flow

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
# on a time interval.
from twisted.internet.task import LoopingCall
from twisted.internet.reactor import callLater
from twisted.internet.defer import inlineCallbacks, returnValue

from labrad.devices import DeviceServer, DeviceWrapper
from labrad.server import setting
import labrad.units as units
from labrad import util

from utilities import sleep


class OmegaRatemeterWrapper(DeviceWrapper):
    @inlineCallbacks
    def connect(self, server, port):
        """Connect to an Omega rate monitor."""
        print('Connecting to "%s" on port "%s"...' %(server.name, port))
        self.server = server
        self.ctx = server.context()
        self.port = port
        p = self.packet()
        p.open(port)
        # The following parameters match the default configuration of the
        # serial device.
        p.baudrate(9600L)
        p.stopbits(1L)
        p.bytesize(7L)
        p.parity('E')
        p.rts(False)
        p.timeout(5 * units.s)
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
        """Write data value to the rate monitor."""
        yield self.server.write_line(code, context=self.ctx)

    @inlineCallbacks
    def read_line(self):
        """Read data value from the rate monitor."""
        ans = yield self.server.read(context=self.ctx)
        returnValue(ans)


class OmegaRatemeterServer(DeviceServer):
    deviceName = 'Omega Ratemeter'
    name = 'Omega Ratemeter'
    deviceWrapper = OmegaRatemeterWrapper
    
    @inlineCallbacks
    def initServer(self):
        """Initializes the server"""
        print("Server Initializing...")        
        self.reg = self.client.registry()
        yield self.loadConfigInfo()
        yield DeviceServer.initServer(self)
        # Set the maximum acceptible flow rate.
        self.thresholdMax = 5 * units.galUS / units.min
        # Set the minimum acceptible flow rate.
        self.thresholdMin = 1.5* units.galUS / units.min
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
    def startServer(self, c):
        """Initialize the repeated flow rate measurement."""
        self.dev = self.selectedDevice(c)
        callLater(0.1, self.startRefreshing)
        return True
    
    @setting(10, 'Set Thresholds', low='v[ml/min]', high='v[ml/min]')
    def setThresholds(self, ctx, low, high):
        """
        This setting configures the trigger thresholds.
        If a threshold is exceeded, then an alert is sent.
        """
        if low >= high:
            return "The minimum threshold cannot be greater than the maximum\
                    threshold"
        self.thresholdMax = units.WithUnit(high,' ml / min')
        self.thresholdMin = units.WithUnit(low,' ml / min')
        return True
   
    @setting(11, 'Set Alert Interval', interval='v[s]')
    def setAlertInterval(self, ctx, interval):
        """Configure the alert interval."""
        self.alertInterval = interval['s']
    
    @setting(12, 'Get Rate', returns='?')
    def rateSetting(self, ctx):
        """Setting that returns rate"""
        self.dev = self.selectedDevice(ctx)
        rate = yield self.getRate(self.dev)
        if rate is None:
            rate = 0 * units.galUS/units.min
        returnValue(rate)
        
    @inlineCallbacks
    def getRate(self, dev):
        """Get flow rate."""
        # The string '@U?V' asks the device for the current reading
        # The '\r' at the end is the carriage return letting the device
        # know that it was the end of the command.
        #print("getting rate")
        yield dev.write_line("@U?V\r")
        yield sleep(0.5)
        reading = yield dev.read_line()
        # Instrument randomly decides not to return, here's a hack.
        if not reading:
            returnValue(None)
        else:
            # Get the last number in the string.
            reading.rsplit(None, 1)[-1]
            # Strip the 'L' off the string.
            reading = float(reading.lstrip("L"))
            # Convert the reading to the correct units.
            gal = units.WithUnit(1, 'gal')
            output = reading * gal / units.min
            returnValue(output)

    @inlineCallbacks
    def checkMeasurements(self):
        """Make sure the flow rate is within range."""
        rate = yield self.getRate(self.dev)
        if rate:
            if rate > self.thresholdMax:
                self.sendAlert(rate,
                        "Flow rate above maximum threshold of {0}.".format(
                        str(self.thresholdMax)))
            elif rate < self.thresholdMin:
                self.sendAlert(rate,
                        "Flow rate below minimum threshold of {0}.".format(
                        str(self.thresholdMin)))
        
    @inlineCallbacks
    def loadConfigInfo(self):
        """Load configuration information from the registry."""
        reg = self.reg
        yield reg.cd(['', 'Servers', 'Omega Ratemeter', 'Links'], True)
        dirs, keys = yield reg.dir()
        p = reg.packet()
        for k in keys:
            p.get(k, key=k)
        ans = yield p.send()
        self.serialLinks = dict((k, ans[k]) for k in keys)

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
            # Store the last time an alert was sent in the form of
            # seconds since the epoch (1/1/1970).
            self.t2 = self.t1
            print("{0}\n\t{1}\n\t{2}".format(message,
                                             time.ctime(self.t1),
                                             str(measurement)))

    @inlineCallbacks    
    def findDevices(self):
        """Find available devices from a list stored in the registry."""
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


__server__ = OmegaRatemeterServer()


if __name__ == '__main__':
    util.runServer(__server__)
