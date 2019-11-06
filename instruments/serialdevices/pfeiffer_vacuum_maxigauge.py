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
version = 1.1.0
description = Monitors vacuum system

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
"""

import os
import sys
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

if __file__ in [f for f in os.listdir('.') if os.path.isfile(f)]:
    SCRIPT_PATH = os.path.dirname(os.getcwd())
else:
    SCRIPT_PATH = os.path.dirname(__file__)
LOCAL_PATH = SCRIPT_PATH.rsplit('instruments', 1)[0]
INSTRUMENTS_PATH = os.path.join(LOCAL_PATH, 'instruments')
if INSTRUMENTS_PATH not in sys.path:
    sys.path.append(INSTRUMENTS_PATH)

from utilities.gpib_device_wrapper import ReadRawGPIBDeviceWrapper
from utilities.sleep import sleep

mbar = units.Unit('mbar')


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
        yield self.server.write_line(code, context=self.ctx)

    @inlineCallbacks
    def write(self, code):
        """Write data value to the vacuum control unit."""
        yield self.server.write(code, context=self.ctx)
        
    @inlineCallbacks
    def read_line(self):
        """Read data value from the vacuum control unit."""
        ans = yield self.server.read(context=self.ctx)
        returnValue(ans)

    @inlineCallbacks
    def read(self):
        """Read data value from the vacuum control unit."""
        ans = yield self.server.read(context=self.ctx)
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
        # Index 0 of thresholdMax corresponds to the maximum acceptible
        # value of sensor 1 and index 5, sensor 6. Likewise, index 0 of
        # thresholdMin corresponds to sensor 1.
        # These values can be left as is (default) or they can be changed
        # using the set_thresholds setting.
        # In order to use the setting, type:
        #   [instance name].set_thresholds([low], [high])
        # As an example:
        #   vacuum.set_thresholds([0, 0, 0, 5E-5, 5E-5, 5E-5],
        #                         [0, 0, 0, 5E-4, 5E-4, 5E-4])
        # It is a good idea to allow for a wide range of values if you
        # know that a sensor is not connected because the unit sometimes
        # misreports status codes. This makes it seem as though a sensor
        # is connected, and a 'don't-care' value is treated as an error.
        self.thresholdMax = [1500, 1500, 1500, 5e-4, 5e-4, 1e-1] * mbar
        # Set the minimum acceptible pressures.
        self.thresholdMin = [0, 0, 0, 5E-5, 5E-5, 5E-5] * mbar
        self.alertInterval = 10 # seconds
        self.measurements = [0, 0, 0, 0, 0, 0] * mbar
        self.statusCodes = [0, 0, 0, 0, 0, 0]
        self.t1 = [0,0,0,0,0,0]
        self.t2 = [0,0,0,0,0,0]
    
    def startRefreshing(self):
        """
        Start periodically refreshing the list of devices.
        The start call returns a deferred which we save for later.
        When the refresh loop is shutdown, we will wait for this
        deferred to fire to indicate that it has terminated.
        """
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

    @setting(10, 'Set Thresholds', low='*v[mbar]', high='*v[mbar]')
    def setThresholds(self, ctx, low, high):
        """
        This setting configures the trigger thresholds.
        If a threshold is exceeded, then an alert is sent.
        """
        if not (len(low) == 6) or not (len(high) == 6):
            raise Exception("The 'low' and 'high' parameters must be "
                    "lists of exactly 6 elements.")
        for i in range(6):
            if low[i] > high[i]:
                raise Exception("The minimum threshold cannot be "
                        "greater than the maximum threshold for "
                        "sensor %d." %(i + 1))
            self.thresholdMax[i] = high[i]
            self.thresholdMin[i] = low[i]
        return True

    @setting(11, 'Set Alert Interval', interval='v[s]')
    def setAlertInterval(self, ctx, interval):
        """Configure the alert interval."""
        self.alertInterval = interval['s']
    
    @setting(12, 'Get Pressures', returns='*v[mbar]')
    def pressure(self, c):
        """Setting that returns an array of pressures"""
        t1 = time.time()
        self.dev = self.selectedDevice(c)
        yield self.getPressures(self.dev)
        returnValue(self.measurements)
        
    @inlineCallbacks
    def getPressures(self, dev):
        """Read sensor data."""
        # Iterate through sensors 1 to 6.
        for i in range(4, 7):
            # The serial command 'PRx' tells the device that we are
            # talking about sensor x.
            yield self.dev.write("PR{0}\r\n".format(i))
            # Give the device time to receive and process the request.
            yield sleep(0.1)
            # The device responds with an acknowledge, discard it.
            yield self.dev.read()
            # Deferred at 0x52d0170, which i guess is a time    #Liu
            yield sleep(0.1)
            # Write the 'enquire' code to the serial bus. This tells the
            # device that we want a reading.
            yield self.dev.write("\x05\r\n")
            yield sleep(0.1)
            response = yield self.dev.read()
            # The reading is formatted in the following way:
            # 'status,measurement.'
            # Separate the status code from the measurement.
            response = response.rsplit(',')
            print("response is", response)
            pressure = response[1].strip().split('\r\n\x15')[0]
            status = response[0]
            self.measurements[i - 1] = float(pressure) * mbar
            self.statusCodes[i-1] = response[0]
        
    @inlineCallbacks
    def checkMeasurements(self):
        """Make sure the pressure is within range."""
        # Update the measuremets list by calling the getPressures method.
        yield self.getPressures(self.dev)
        for i in range(6):
            if not self.statusCodes[i] == '5':
                if self.measurements[i] > self.thresholdMax[i]:                    
                    self.sendAlert(str(self.measurements[i]),
                            "Sensor {0} pressure is above {1}."
                            .format(i+1, str(self.thresholdMax[i])), i)
                elif self.measurements[i] < self.thresholdMin[i]:
                    self.sendAlert(str(self.measurements[i]),
                            "Sensor {0} pressure is below {1}."
                            .format(i+1, str(self.thresholdMin[i])), i)

    def sendAlert(self, measurement, message, sensor):
        """
        Deal with an out-of-bounds measurement by calling this method,
        it accepts the meausurement, and an error message. It sends an
        email containing the measurements and the error message.
        """
        # If the amount of time specified by the alertInterval has elapsed,
        # then send another alert.
        self.t1[sensor] = time.time()
        if self.t1[sensor] - self.t2[sensor] > self.alertInterval:
            # Store the last time an alert was sent in the form of 
            # seconds since the epoch (1/1/1970).
            # NOTE: the sensor variable is 0 indexed.
            self.t2[sensor] = self.t1[sensor]
            print("{0}\n\t{1}\n\t{2}".format(message,
                                             time.ctime(self.t1[sensor]),
                                             str(measurement)))
        return
    
    @inlineCallbacks
    def loadConfigInfo(self):
        """Load configuration information from the registry."""
        reg = self.reg
        yield reg.cd(['', 'Servers', 'PfeifferVacuumControlServer', 'Links'], True)
        dirs, keys = yield reg.dir()
        p = reg.packet()
        for k in keys:
            p.get(k, key=k)
        ans = yield p.send()
        self.serialLinks = {k: ans[k] for k in keys}

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
