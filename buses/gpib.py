# Copyright (C) 2007  Matthew Neeley
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
labrad.gpib

Superclass of GPIB device servers.
"""


from labrad import types as T, constants as C, util, errors
from labrad.devices import DeviceWrapper, DeviceServer, DeviceLockedError
from labrad.server import LabradServer, setting
from labrad.support import MultiDict

from twisted.internet import defer
from twisted.internet.defer import inlineCallbacks, returnValue


class GPIBDeviceWrapper(DeviceWrapper):
    """A wrapper for a gpib device."""

    @inlineCallbacks
    def connect(self, server, address):
        """Connect to this device.

        We set the address and timeout in the context reserved
        for talking to this device.  Then call initialize, which may
        be overridden in subclasses.
        """
        self.gpib = server  # wrapper for the gpib server
        self.addr = address
        self._context = self.gpib.context()  # create a new context for this device
        self._timeout = T.Value(C.TIMEOUT, "s")

        # set the address and timeout in this context
        p = self._packet()
        p.address(self.addr)
        p.timeout(self._timeout)
        yield p.send()

        # do device-specific initialization
        yield self.initialize()

    def _packet(self):
        return self.gpib.packet(context=self._context)

    @inlineCallbacks
    def timeout(self, seconds):
        """Set the GPIB timeout for this device."""
        self._timeout = T.Value(seconds, "s")
        p = self._packet()
        p.timeout(self._timeout)
        yield p.send()

    @inlineCallbacks
    def query(self, query, bytes=None, timeout=None):
        """Query this GPIB device."""
        p = self._packet()
        if timeout is not None:
            p.timeout(timeout)
        p.query(query)
        if timeout is not None:
            p.timeout(self._timeout)
        resp = yield p.send()
        returnValue(resp.query)

    @inlineCallbacks
    def write(self, s, timeout=None):
        """Write a string to the device."""
        p = self._packet()
        if timeout is not None:
            p.timeout(timeout)
        p.write(s)
        if timeout is not None:
            p.timeout(self._timeout)
        resp = yield p.send()
        returnValue(resp.write)

    @inlineCallbacks
    def write_raw(self, s, timeout=None):
        """Write a string to the device."""
        p = self._packet()
        if timeout is not None:
            p.timeout(timeout)
        p.write_raw(s)
        if timeout is not None:
            p.timeout(self._timeout)
        resp = yield p.send()
        returnValue(resp.write_raw)

    @inlineCallbacks
    def read(self, bytes=None, timeout=None):
        """Read a string from the device."""
        p = self._packet()
        if timeout is not None:
            p.timeout(timeout)
        p.read(bytes)
        if timeout is not None:
            p.timeout(self._timeout)
        resp = yield p.send()
        returnValue(resp.read)

    @inlineCallbacks
    def read_raw(self, bytes=None, timeout=None):
        """Read a string from the device."""
        p = self._packet()
        if timeout is not None:
            p.timeout(timeout)
        p.read_raw(bytes)
        if timeout is not None:
            p.timeout(self._timeout)
        resp = yield p.send()
        returnValue(resp.read_raw)

    def initialize(self):
        """Called when we first connect to the device.

        Override this in subclasses to perform device-specific
        initialization and to synchronize the wrapper state with
        the device state.
        """


class GPIBDeviceServer(DeviceServer):
    """A server for a GPIB device.

    Creates a GPIBDeviceWrapper for each device it finds that
    is appropriately named.  Provides standard settings for listing
    devices, selecting a device for the current context, and
    refreshing the list of devices.  Also, allows us to read from,
    write to, and query the selected GPIB device directly.

    2013 October 22 - Daniel Sank
    I'm pretty sure this is obsolte and you should use the GPIBManagedServer
    """

    name = "Generic GPIB Device Server"
    deviceName = "Generic GPIB Device"
    deviceWrapper = GPIBDeviceWrapper

    def serverConnected(self, ID, name):
        """Refresh devices when a gpib server comes on line."""
        if "gpib" in name.lower():
            self.refreshDeviceList()

    def serverDisconnected(self, ID, name):
        """Refresh devices when a gpib server goes off line."""
        if "gpib" in name.lower():
            self.refreshDeviceList()

    @inlineCallbacks
    def findDevices(self):
        """Find all available matching GPIB devices."""
        searches = [
            self._findDevicesForServer(srv) for srv in _gpibServers(self.client)
        ]
        found = []
        for search in searches:
            found += yield search
        returnValue(found)

    @inlineCallbacks
    def _findDevicesForServer(self, srv):
        """Find matching devices on a given server."""
        devices = yield srv.list_devices()
        found = []
        for address, deviceName in zip(devices, ["<UNKNOWN>"] * len(devices)):
            if deviceName == self.deviceName:
                name = _getDeviceName(srv, address)
                found.append((name, (srv, address), {}))
        returnValue(found)

    # server settings

    @setting(1001, "GPIB Write", string="s", returns="*b")
    def gpib_write(self, c, string):
        """Write a string to the device over GPIB."""
        return self.selectedDevice(c).write(string)

    @setting(1002, "GPIB Read", bytes="w", returns="s")
    def gpib_read(self, c, bytes=None):
        """Read a string from the device over GPIB."""
        return self.selectedDevice(c).read(bytes)

    @setting(1003, "GPIB Query", query="s", returns="s")
    def gpib_query(self, c, query):
        """Write a string over GPIB and read the response."""
        return self.selectedDevice(c).query(query)


class ManagedDeviceServer(DeviceServer):
    """Builds off DeviceServer class by adding methods to interface with a
    server that manages different devices.  Devices are broadcast from that
    server and then added here when appropriate.
    """

    name = "Generic Device Server"
    deviceManager = "Device Manager"

    messageID = 21436587

    @inlineCallbacks
    def initServer(self):
        DeviceServer.initServer(self)
        # register a message handler for connect/disconnect messages
        handler = lambda c, data: self.handleDeviceMessage(*data)
        self._cxn.addListener(handler, ID=self.messageID)
        if self.deviceManager in self.client.servers:
            yield self.connectToDeviceManager()

    def makeDeviceName(self, device, server, address):
        return server + " - " + address

    @inlineCallbacks
    def handleDeviceMessage(self, device, server, address, isConnected=True):
        print("Device message:", device, server, address, isConnected)
        name = self.makeDeviceName(device, server, address)
        if isConnected:  # add device
            self.addDevice(
                name, device=device, server=self.client[server], address=address
            )
        else:  # remove device
            yield self.removeDevice(name)

    @inlineCallbacks
    def connectToDeviceManager(self):
        """ """
        yield self.client.refresh()
        manager = self.client[self.deviceManager]
        # If we have a device identification function register it with the device manager
        if hasattr(self, "deviceIdentFunc"):
            yield manager.register_ident_function(self.deviceIdentFunc)
        # Register ourself as a server who cares about devices
        devs = yield manager.register_server(
            list(self.deviceWrappers.keys()), self.messageID
        )
        # the devs list is authoritative any devices we have
        # that are _not_ on this list should be removed
        names = [self.makeDeviceName(*dev[:3]) for dev in devs]
        additions = [self.handleDeviceMessage(*dev) for dev in devs]
        deletions = [
            self.removeDevice(name)
            for name in list(self.device_guids.keys())
            if name not in names
        ]
        yield defer.DeferredList(additions + deletions)

    def serverConnected(self, ID, name):
        if name == self.deviceManager:
            self.connectToDeviceManager()

    def refreshDeviceList(self):
        return


class GPIBManagedServer(ManagedDeviceServer):
    """A server for a GPIB device.

    Creates a GPIBDeviceWrapper for each device it finds that
    is appropriately named.  Provides standard settings for listing
    devices, selecting a device for the current context, and
    refreshing the list of devices.  Also, allows us to read from,
    write to, and query the selected GPIB device directly.
    """

    name = "Generic GPIB Device Server"
    deviceManager = "GPIB Device Manager"
    deviceName = "Generic GPIB Device"
    deviceWrapper = GPIBDeviceWrapper
    # server settings

    @setting(1001, "GPIB Write", string="s", timeout="v[s]", returns="")
    def gpib_write(self, c, string, timeout=None):
        """Write a string to the device over GPIB."""
        return self.selectedDevice(c).write(string, timeout)

    @setting(1002, "GPIB Read", bytes="w", timeout="v[s]", returns="s")
    def gpib_read(self, c, bytes=None, timeout=None):
        """Read a string from the device over GPIB."""
        return self.selectedDevice(c).read(bytes, timeout)

    @setting(1003, "GPIB Query", query="s", timeout="v[s]", returns="s")
    def gpib_query(self, c, query, timeout=None):
        """Write a string over GPIB and read the response."""
        return self.selectedDevice(c).query(query, timeout=timeout)


def _gpibServers(cxn):
    """Get a list of available GPIB servers."""
    gpibs = []
    for name in cxn.servers:
        srv = cxn.servers[name]
        if "gpib_bus" in name and "list_devices" in srv.settings:
            gpibs.append(srv)
    return gpibs


def _getDeviceName(server, deviceID):
    """Create a name for a device on a particular server."""
    return "%s - %s" % (server.name, deviceID)
