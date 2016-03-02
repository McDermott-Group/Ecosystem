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
name = Pfeiffer Vacuum MaxiGauge
version = 1.0.15
description = Monitors and controls vacuum system

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

## from utilities import sleep

class PfeifferVacuumControlWrapper(DeviceWrapper):
    @inlineCallbacks
    def connect(self, server, port):
        """Connect to an Pfeiffer Vacuum MaxiGauge."""
        print('Connecting to "%s" on port "%s"...' %(server.name, port))
        self.server = server
        self.ctx = server.context()
        self.port = port
        p = self.packet()
        p.open(port)
        # The following parameters match the default configuration of 
        # the MaxiGauge unit.
        p.baudrate(9600L)
        p.stopbits(1L)
        p.bytesize(8L)
        p.parity('N')
        p.rts(False)
        p.timeout(2 * units.s)
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
        """Write data value to the vacuum control unit."""
        yield self.server.write_line(code, context = self.ctx)

    @inlineCallbacks
    def write(self, code):
        """Write data value to the vacuum control unit."""
        yield self.server.write(code, context = self.ctx)
        
    @inlineCallbacks
    def read_line(self):
        """Read data value from the vacuum control unit."""
        ans = yield self.server.read(context = self.ctx)
        ### print "ans=", ans
        returnValue(ans)

    @inlineCallbacks
    def read(self):
        """Read data value from the vacuum control unit."""
        ans = yield self.server.read(context = self.ctx)
        returnValue(ans)


class PfeifferVacuumControlServer(DeviceServer):
    deviceName = 'Pfeiffer Vacuum MaxiGauge'
    name = 'Pfeiffer Vacuum MaxiGauge'
    deviceWrapper = PfeifferVacuumControlWrapper
    
    @inlineCallbacks
    def initServer(self):
        """Initializes the server"""
        print("Server initializing")        
        self.reg = self.client.registry()
        yield self.loadConfigInfo()
        yield DeviceServer.initServer(self)
        # Set the maximum acceptible pressures. This is a list
        # of 6 values corresponding to the 6 sensors.
        # TO-DO: These parameters should be moved to the registry.
        # OR EXPLAIN...
        self.thresholdMax = [0, 0, 0, 5E-4, 5E-4, 5E-4] # mbar
        # Set the minimum acceptible pressures.
        self.thresholdMin = [0, 0, 0, 5E-5, 5E-5, 5E-5] # mbar
        self.alertInterval = 10 # seconds
        self.measurements = [0, 0, 0, 0, 0, 0]
        self.statusCodes = [0, 0, 0, 0, 0, 0]
        self.t1 = 0
        self.t2 = 0
    
    def startRefreshing(self):
        """
        Start periodically refreshing the list of devices.
        The start call returns a deferred which we save for later.
        When the refresh loop is shutdown, we will wait for this
        deferred to fire to indicate that it has terminated.
        """
        ### dev = self.dev
        self.refresher = LoopingCall(self.checkMeasurements)
        self.refresherDone = self.refresher.start(5, now=True)

    @inlineCallbacks
    def stopServer(self):
        """Kill the device refresh loop and wait for it to terminate."""
        if hasattr(self, 'refresher'):
            self.refresher.stop()
            yield self.refresherDone
      
    @setting(9, 'Start Server', returns='b')
    def startServer(self, c):
        """Initialize the repeated pressure measurement."""
        self.dev = self.selectedDevice(c)
        callLater(0.1, self.startRefreshing)
        return True

    ## TO-DO: @setting(10, 'Set Thresholds', low='*v[bar]', high='*v[bar]')
    @setting(10, 'Set Thresholds', low='*v', high='*v')
    def setThresholds(self, ctx, low, high):
        """
        This setting configures the trigger thresholds.
        If a threshold is exceeded, then an alert is sent.
        """
        # TO-DO: Check the lengths of 'low' and 'high'.
        # Exlain in the error message the input requirments.
        for i in range(0, 6):
            if low[i] > high[i]:
                print("The minimum threshold cannot be greater than the"
                        " maximum threshold for sensor %s" %str(i+1))
                return False
            self.thresholdMax[i] = high[i]
            self.thresholdMin[i] = low[i]
        return True

    @setting(11, 'Set Alert Interval', interval = 'w')
    def setAlertInterval(self, ctx, interval):
        """Configure the alert interval"""
        self.alertInterval = interval
        
    @inlineCallbacks
    def getPressures(self, dev):
        """Read sensor data."""
        # Iterate through sensors 1 to 6.
        for i in range(1, 7):
            # The serial command 'PRx' tells the device that we are
            # talking about sensor x.
            ### yield self.dev.write("PR"+str(i)+"\r\n")
            ## yield self.dev.write("PR%s\r\n" %str(i))
            ## better: yield self.dev.write("PR%d\r\n" %i)
            # Give the device time to receive and process the request
            ## yield sleep(0.05)
            ### time.sleep(0.05)
            # The device responds with an acknowledge, discard it.
            yield self.dev.read()
            ## yield sleep(0.05)
            ### time.sleep(0.05)
            # Write the 'enquire' code to the serial bus. This tells the
            # device that we want a reading.
            yield self.dev.write("\x05\r\n")
            ## yield sleep(0.05)
            ### time.sleep(0.05)
            response = yield self.dev.read()
            # The reading is formatted in the following way:
            # 'status,measurement.'
            # Separate the status code from the measurement.
            response = response.rsplit(',')
            pressure = response[1]
            status = response[0]
            self.measurements[i-1] = response[1]
            self.statusCodes[i-1] = response[0]
            ## TO-DO: Use units!
            ## self.measurements[i-1] = 1e-3 * float(response[1]) * units.bar
            ## self.statusCodes[i-1] = response[0]
            # A status code of 5 means that no sensor is connected.
            ### if status == '5':
                ### print("Sensor %d: Not Connected" %i)
            ### else:
                # Using rstrip(), strip whitespace and escape characters
                # off the end of the reading
                ### print("sensor "+str(i)+": "+pressure.rstrip())
        # QUESTION: do we need this?
        ## returnValue(None)
        
    @inlineCallbacks
    def checkMeasurements(self):
        """Make sure the pressure is within range."""
        # Update the measuremets list by calling the getPressures method.
        yield self.getPressures(self.dev)
        
        for i in range(0, 6):
            if not self.statusCodes[i] == '5':
                ## TO-DO: Remove float operator.
                if float(self.measurements[i]) > float(self.thresholdMax[i]):
                    ## TO-DO: Improve formating.
                    self.sendAlert(self.measurements[i], "Sensor "+str(i+1)+\
                                  " pressure is above "+str(self.thresholdMax[i]))
                elif(float(self.measurements[i]) < float(self.thresholdMin[i])):
                    self.sendAlert(self.measurements[i], "Sensor "+str(i+1)+\
                                   " pressure is below "+str(self.thresholdMin[i]))

    def sendAlert(self, measurement, message):
        """
        Deal with an out-of-bounds measurement by calling this method,
        it accepts the meausurement, and an error message. It sends an
        email containing the measurements and the error message.
        """
        # If the amount of time specified by the alertInterval has elapsed,
        # then send another alert.
        self.t1 = time.time()
        ## TO-DO: Improve formating.
        if((self.t1-self.t2)>self.alertInterval):
            # Store the last time an alert was sent in the form of 
            # seconds since the epoch (1/1/1970).
            self.t2 = self.t1
            print("\r\n"+message)
            print("\t"+time.ctime(self.t1))
            # No newline character
            print("\t"+str(measurement)+"\r\n")
            # The labrad do not like when you try to append values with
            # units to another string...hence the many print statements.
        return
    
    @inlineCallbacks
    def loadConfigInfo(self):
        """Load configuration information from the registry."""
        reg = self.reg
        # TO-DO: Rename the server name in the registry.
        yield reg.cd(['', 'Servers', 'Leiden Vacuum Monitor', 'Links'], True)
        dirs, keys = yield reg.dir()
        p = reg.packet()
        for k in keys:
            p.get(k, key=k)
        ans = yield p.send()
        ### self.serialLinks = dict((k, ans[k]) for k in keys)
        ## self.serialLinks = {k: ans[k] for k in keys}

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


__server__ = PfeifferVacuumControlServer()


if __name__ == '__main__':
    util.runServer(__server__)