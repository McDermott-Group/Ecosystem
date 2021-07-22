# Copyright (C) 2008  Matthew Neeley
#           (C) 2015  Chris Wilen, Ivan Pechenezhskiy
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
### BEGIN NODE INFO
[info]
name = SIM900 Serial
version = 1.5.0
description = Gives access to GPIB devices in the SIM900 mainframe.

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
"""

import string
import random
from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.internet.reactor import callLater

from labrad import util
from labrad.server import LabradServer, setting
from labrad.errors import DeviceNotSelectedError
import labrad.units as units
from labrad.gpib import ManagedDeviceServer
from labrad.devices import DeviceServer, DeviceWrapper


class SIM900Wrapper(DeviceWrapper):
    @inlineCallbacks
    def connect(self, server, address):
        """Connect the the guage controller."""
        print(('Connecting to "%s" on port "%s"...' %(server.name, address)))
        self.server = server
        self.ctx = server.context()
        self.address = address
        # The following parameters match the default configuration of 
        # the Varian unit.
        p = self.packet()
        p.open(address)
        p.baudrate(9600)
        p.stopbits(1)
        p.bytesize(8)
        p.parity('N')
        p.rts(False)
        p.timeout(2 * units.s)
        # Clear out the read buffer. This is necessary for some devices.
        p.read_line()
        p.close()
        yield p.send()
        
    def packet(self):
        """Create a packet in our private context."""
        return self.server.packet(context=self.ctx)

    def shutdown(self):
        """Disconnect from the serial port when we shut down."""
        return self.packet().close().send()
     
    @inlineCallbacks
    def write_line(self, code):
        code = code + '\n'
        yield self.server.write_line(code, context=self.ctx)
        # yield self.server.write_line(code, context=self.ctx)
        
    @inlineCallbacks    
    def read_line(self):
        ans = yield self.server.read_line(context=self.ctx)
        returnValue(ans)
        
        
class SIM900(DeviceServer):
    """Provides direct access to GPIB-enabled devices."""
    name = 'SIM900 Serial'
    deviceName = 'STANFORD RESEARCH SYSTEMS SIM900'
    deviceWrapper = SIM900Wrapper
    defaultTimeout = 1.0 * units.s
    
    @inlineCallbacks  
    def initServer(self):
        self.mydevices = {}
        yield self.loadConfigInfo()
        yield DeviceServer.initServer(self)
        # start refreshing only after we have started serving
        # this ensures that we are added to the list of available
        # servers before we start sending messages
        callLater(0.1, self.refreshDevices)

    @inlineCallbacks
    def loadConfigInfo(self):
        """Load configuration information from the registry."""
        reg = self.client.registry()
        yield reg.cd(['', 'Servers', 'SIM900 Serial', 'Links'], True)
        dirs, keys = yield reg.dir()
        p = reg.packet()
        for k in keys:
            p.get(k, key=k)
        ans = yield p.send()
        self.serialLinks = {k: ans[k] for k in keys}
        print(self.serialLinks)

    @inlineCallbacks    
    def findDevices(self):
        """Find available devices from a list stored in the registry."""
        devs = []
        for name, (server, port) in list(self.serialLinks.items()):
            if server not in self.client.servers:
                continue
            server = self.client[server]
            ports = yield server.list_serial_ports()
            if port not in ports:
                continue
            devName = '{} - {}'.format(server, port)
            devs += [(name, (server, port))]
        returnValue(devs)
        
    # @inlineCallbacks
    # def handleDeviceMessage(self, *args):
        # """We override this function so that whenever a new SIM900 is
        # added, and a message is sent out, we refresh the devices. This
        # has the benefit of being able to start this server, the
        # GPIB Device Manager, and the GPIB Bus Server, in any order."""
        # yield GPIBManagedServer.handleDeviceMessage(self, *args)
        # if args[0] == self.deviceName:
            # self.refreshDevices()

    @inlineCallbacks
    def refreshDevices(self):
        """
        Refresh the list of known devices (modules) in the SIM900
        mainframe.
        """
        print('Refreshing devices...')
        addresses = []
        IDs, names = self.deviceLists()
        # return
        for SIM900addr in names:
            try:
                dev = self.devices[SIM900addr]
                p = dev.packet()
                # p = self.client[self.name].packet()
            except KeyError as e:
                callLater(0.1, self.refreshDevices)
                return
            p.open(dev.address)
            # p.write_line('*RST')
            p.write_line('*CLS')
            p.write_line('FLSH')#.write_line('SRST')
            p.write_line('CTCR?').pause(0.1*units.s).read_line()
            p.close()
            statusStr = (yield p.send())['read_line']
            # Ask the SIM900 which slots have an active module, and only
            # deal with those.
            statusCodes = [bool(int(x))
                           for x in "{0:016b}".format(int(statusStr))]
            statusCodes.reverse()
            for i in range(1, 9):  # slots 1-8 in rack
                if statusCodes[i]:  # added or changed
                    # Ex: mcdermott5125 GPIB Bus - GPIB0::2[::INSTR]::SIM900::4
                    devName = ('::'.join(SIM900addr.split(' - ')
                                         [-1].split('::')[:-1] +
                                         ['SIM900', str(i)]))
                    devName = '%s::SIM900::%s' % (SIM900addr, str(i))
                    addresses.append(devName)
        additions = set(addresses) - set(self.mydevices.keys())
        deletions = set(self.mydevices.keys()) - set(addresses)
        # Get the visa instruments, changing the read/write/query
        # commands to work for only the correct slot in the SIM900.
        for addr in additions:
            instName = addr.split(' - ')[-1].rsplit('::', 2)[0]
            self.mydevices[addr] = instName
            self.sendDeviceMessage('GPIB Device Connect', addr)
        for addr in deletions:
            del self.mydevices[addr]
            self.sendDeviceMessage('GPIB Device Disconnect', addr)

    def getSocketsList(self):
        """Get a list of all connected devices.

        Return value:
        A list of strings with the names of all connected devices, ready
        for being used to open each of them.
        """
        return self.rm.list_resources()

    def sendDeviceMessage(self, msg, addr):
        print(('%s: %s' % (msg, addr)))
        self.client.manager.send_named_message(msg, (self.name, addr))

    def initContext(self, c):
        c['timeout'] = self.defaultTimeout

    def escapeString(self):
        chars = string.ascii_uppercase + string.ascii_lowercase
        return 'xZy' + ''.join(random.choice(chars) for _ in range(3))

    @setting(19, returns='*s')
    def list_addresses(self, c):
        """Get a list of GPIB addresses on this bus."""
        return sorted(self.mydevices.keys())

    @setting(21, returns='*?')
    def refresh_devices(self, c):
        '''Manually refresh devices.'''
        yield self.refreshDevices()

    @setting(20, addr='s', returns='s')
    def address(self, c, addr=None):
        """Get or set the GPIB address for this context.

        To get the addresses of available devices,
        use the list_devices function.
        """
        if addr is not None:
            c['addr'] = addr
        return c['addr']

    @setting(22, time='v[s]', returns='v[s]')
    def timeout(self, c, time=None):
        """Get or set the GPIB timeout."""
        if time is not None:
            c['timeout'] = time
        return c['timeout']

    @setting(23, data='s', returns='')
    def write(self, c, data):
        """Write a string to the GPIB bus."""
        # print c['addr'], data
        if 'addr' not in c:
            raise DeviceNotSelectedError("No GPIB address selected")
        if c['addr'] not in self.mydevices:
            raise Exception('Could not find device %s' % c['addr'])
        # Ex: mcdermott5125 GPIB Bus - GPIB0::2::SIM900::4
        dev = self.devices[c['addr'].split('::')[0]]
        # gpibBusServName = c['addr'].split(' - ')[0]
        slot = c['addr'][-1]
        p = dev.packet()
        p.open(dev.address)
        p.timeout(c['timeout'])
        escape = self.escapeString()
        p.write_line("CONN %s,'%s'" % (slot, escape))
        p.write_line(data)
        p.write_line(escape)
        p.close()
        p.send()

    @setting(24, bytes='w', returns='s')
    def read_raw(self, c, bytes=None):
        """Read a raw string from the GPIB bus.

        If specified, reads only the given number of bytes.
        Otherwise, reads until the device stops sending.
        """
        if 'addr' not in c:
            raise DeviceNotSelectedError("No GPIB address selected")
        if c['addr'] not in self.mydevices:
            raise Exception('Could not find device %s' % c['addr'])
        # Ex: mcdermott5125 GPIB Bus - GPIB0::2::SIM900::4
        dev = self.devices[c['addr'].split('::')[0]]
        # gpibBusServName = c['addr'].split(' - ')[0]
        slot = c['addr'][-1]
        p = self.client[gpibBusServName].packet()
        p.address(self.mydevices[c['addr']])
        p.timeout(c['timeout'])
        escape = self.escapeString()
        p.write("CONN %s,'%s'" % (str(slot), escape))
        p.read_raw(bytes)
        p.write(escape)
        p.close()
        resp = yield p.send()
        returnValue(resp['read_raw'])

    @setting(25, returns='s')
    def read(self, c):
        """Read from the GPIB bus."""
        if 'addr' not in c:
            raise DeviceNotSelectedError("No GPIB address selected")
        if c['addr'] not in self.mydevices:
            raise Exception('Could not find device %s' % c['addr'])
        # Ex: mcdermott5125 GPIB Bus - GPIB0::2::SIM900::4
        dev = self.devices[c['addr'].split('::')[0]]
        # gpibBusServName = c['addr'].split(' - ')[0]
        slot = c['addr'][-1]
        p = dev.packet()
        p.open(dev.address)
        p.timeout(c['timeout'])
        escape = self.escapeString()
        p.write_line("CONN %s,'%s'" % (slot, escape))
        p.read_line()
        p.write_line(escape)
        p.close()
        resp = yield p.send()
        returnValue(resp['read_line'])

    @setting(26, data='s', returns='s')
    def query(self, c, data):
        """Make a GPIB query.

        This query is atomic. No other communication to the
        device will occur while the query is in progress.
        """
        if 'addr' not in c:
            raise DeviceNotSelectedError("No GPIB address selected")
        if c['addr'] not in self.mydevices:
            raise Exception('Could not find device %s' % c['addr'])
        # Ex: mcdermott5125 GPIB Bus - GPIB0::2::SIM900::4
        dev = self.devices[c['addr'].split('::')[0]]
        # gpibBusServName = c['addr'].split(' - ')[0]
        slot = c['addr'][-1]
        p = dev.packet()
        p.open(dev.address)
        p.timeout(c['timeout'])
        escape = self.escapeString()
        p.write_line("CONN %s,'%s'" % (slot, escape))
        p.write_line(data)
        p.pause(0.1*units.s)
        p.read_line()
        p.write_line(escape)
        p.close()
        resp = yield p.send()
        returnValue(resp['read_line'])


__server__ = SIM900()


if __name__ == '__main__':
    util.runServer(__server__)
