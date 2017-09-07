import os
import sys
import time
from twisted.internet.task import LoopingCall
from twisted.internet.reactor import callLater
from twisted.internet.defer import inlineCallbacks, returnValue

from labrad.devices import DeviceServer, DeviceWrapper
from labrad.server import setting
import labrad.units as units
from labrad import util

class LK211Wrapper(DeviceWrapper):
    @inlineCallbacks
    def connect(self, server, port):
        """Connect to an lk211 """
        print('Connecting to "%s" on port "%s"...' %(server.name, port))
        self.server = server
        self.ctx = server.context()
        print(self.ctx)
        self.port = port
        p = self.packet()
        p.open(port)
        # The following parameters match the default configuration of the
        # lakeshore 211
        p.baudrate(9600L)
        p.stopbits(1L)
        p.bytesize(7L)
        p.parity('O')
        p.rts(False)
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
        """Write data value to the rate monitor."""
        yield self.server.write_line(code, context=self.ctx)

    @inlineCallbacks
    def read_line(self):
        """Read information from lakeshore211."""
        ans = yield self.server.read_line(context=self.ctx)
        returnValue(ans)


class LK211Server(DeviceServer):
    deviceName = 'Lakeshore 211'
    name = 'Lakeshore 211'
    deviceWrapper = LK211Wrapper

    @inlineCallbacks
    def initServer(self):
        """Initializes the server"""
        print("Server Initializing...")
        self.reg = self.client.registry()
        yield self.loadConfigInfo()
        yield DeviceServer.initServer(self)
        time.sleep(1)
        print(self.devices)
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
        self.refresher = LoopingCall(self.findDevices)
        self.refresherDone = self.refresher.start(5.0, now=True)

    @inlineCallbacks
    def stopServer(self):
        """Kill the device refresh loop and wait for it to terminate."""
        if hasattr(self, 'refresher'):
            self.refresher.stop()
            yield self.refresherDone

    @setting(9, 'Start Server', returns='b')
    def startServer(self, c):
        """Initialize the temperature measurement."""
        self.dev = self.selectedDevice(c)
        callLater(0.1, self.startRefreshing)
        return True

    @setting(10, 'Load Context', returns='?')
    def loadContext(self,c):
        print("Load context")
        for key, value in c:
            line = 10
            print([key, value])
            returnValue(line)

    @setting(11, 'Set Alert Interval', interval='v[s]')
    def setAlertInterval(self, ctx, interval):
        """Configure the alert interval."""
        self.alertInterval = interval['s']

    @setting(12, 'Get Temperature', returns='v[]')
    def tempSetting(self, ctx):
        """Setting that returns rate"""
        self.dev = self.selectedDevice(ctx)
        temp = yield self.getTemp(self.dev)
        temp = temp.strip("+")
        temp = float(temp)
        returnValue(temp)

    @inlineCallbacks
    def getTemp(self, dev):
        """Get temperature. See lakeshore211 manual for other query options
        KRDG? queries temperature in Kelvin"""
        yield dev.write_line("KRDG?")
        time.sleep(0.2)
        reading = yield dev.read_line()
        # Instrument randomly decides not to return, here's a hack.
        if not reading:
            returnValue(None)
        else:
            returnValue(reading)

    @inlineCallbacks
    def loadConfigInfo(self):
        """Load configuration information from the registry."""
        """ Make sure that the registry is configured as such """

        print(" Load config info ")
        reg = self.reg
        yield reg.cd(['', 'Servers', 'LK211', 'Links'], True)
        dirs, keys = yield reg.dir()
        p = reg.packet()
        for k in keys:
            p.get(k, key=k)
        ans = yield p.send()
        self.serialLinks = dict((k, ans[k]) for k in keys)

    @inlineCallbacks
    def findDevices(self):
        """Find available devices from a list stored in the registry."""
        devs = []
        print(" Find devices")
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


__server__ = LK211Server()


if __name__ == '__main__':
    util.runServer(__server__)
