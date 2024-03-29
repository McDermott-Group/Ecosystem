# Copyright (C) 2019 Chuanhong (Vincent) Liu
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


# To do
# 1. Need to make  "yield dev.write("LISN 3\r\n")" more general. This means I am now talking to
#   the sr560 whose address of unit is 3.

"""
### BEGIN NODE INFO
[info]
name = SR560
version = 1.0.0
description = Remote control the front panel of sr560 low-noise preamplifier

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
from twisted.internet.task import LoopingCall
from twisted.internet.reactor import callLater
from twisted.internet.defer import inlineCallbacks, returnValue

from labrad.devices import DeviceServer, DeviceWrapper
from labrad.server import setting
import labrad.units as units
from labrad import util


class SR560Wrapper(DeviceWrapper):
    @inlineCallbacks
    def connect(self, server, port):
        """Connect to an SR560 Amplifier."""
        print(('Connecting to "%s" on port "%s"...' % (server.name, port)))
        self.server = server
        self.ctx = server.context()
        self.port = port
        p = self.packet()
        p.open(port)
        # The following parameters match the default configuration of
        # the SR560 unit.
        p.baudrate(9600)
        p.stopbits(2)
        p.bytesize(8)
        p.parity("N")
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
    def write(self, code):
        """Write data value to the SR560 unit."""
        yield self.server.write(code, context=self.ctx)

    @inlineCallbacks
    def read(self):
        """Read data value from the SR560 unit."""
        ans = yield self.server.read(context=self.ctx)
        returnValue(ans)

    # you may need read_line and write_line


class SR560Server(DeviceServer):
    """Provides direct access to serial devices."""

    deviceName = "SR560"
    name = "SR560"
    deviceWrapper = SR560Wrapper

    @inlineCallbacks
    def initServer(self):
        self.mydevices = {}
        yield self.loadConfigInfo()
        yield DeviceServer.initServer(self)
        # start refreshing only after we have started serving
        # this ensures that we are added to the list of available
        # servers before we start sending messages

    @inlineCallbacks
    def loadConfigInfo(self):
        """Load configuration information from the registry."""
        reg = self.client.registry()
        yield reg.cd(["", "Servers", "SR560", "Links"], True)
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
            devName = "{} - {}".format(server, port)
            devs += [(name, (server, port))]
        returnValue(devs)

    @setting(8, "operate_amplifier_blanking", blanking="s", returns="s")
    def operate_amplifier_blanking(self, c, blanking=None):
        blanking_dict = {"Not Blanked": 0, "Blanked": 1}
        blanking_number = blanking_dict[blanking]
        dev = self.selectedDevice(c)
        yield dev.write("LISN 3\r\n")
        yield dev.write("BLINK {}\r\n".format(blanking_number))
        returnValue("Blanking has been set to {}".format(blanking))

    @setting(9, "set_input_coupling", coupling="s", returns="s")
    def set_input_coupling(self, c, coupling=None):
        coupling_dict = {"GND": 0, "DC": 1, "AC": 2}
        coupling_number = coupling_dict[coupling]
        dev = self.selectedDevice(c)
        yield dev.write("LISN 3\r\n")
        yield dev.write("CPLG {}\r\n".format(coupling_number))
        returnValue("Input coupling has been set to {}".format(coupling))

    @setting(10, "set_dynamic_reserve", dynamic_reserve="s", returns="s")
    def set_dynamic_reserve(self, c, dynamic_reserve=None):
        dynamic_reserve_dict = {"low noise": 0, "high DR": 1, "calibration gains": 2}
        dynamic_reserve_number = dynamic_reserve_dict[dynamic_reserve]
        dev = self.selectedDevice(c)
        yield dev.write("LISN 3\r\n")
        yield dev.write("DYNR {}\r\n".format(dynamic_reserve_number))
        returnValue("Dynamic reserve has been set to {}".format(dynamic_reserve))

    @setting(11, "set_filter", filter="s", returns="s")
    def set_filter(self, c, filter=None):
        filter_dict = {
            "bypass": 0,  # This corresponds to DC
            "6dB low pass": 1,
            "12dB low pass": 2,
            "6dB high pass": 3,
            "12dB high pass": 4,
            "bandpass": 5,  # This enables both of the 6dB low/high pass
        }
        filter_number = filter_dict[filter]
        dev = self.selectedDevice(c)
        yield dev.write("LISN 3\r\n")
        yield dev.write("FLTM {}\r\n".format(filter_number))
        returnValue("Filter mode has been set to {}".format(filter))

    @setting(12, "set_gain", gain="s", returns="s")
    def set_gain(self, c, gain=None):
        gain_dict = {
            "1": 0,
            "2": 1,
            "5": 2,
            "10": 3,
            "20": 4,
            "50": 5,
            "100": 6,
            "200": 7,
            "500": 8,
            "1000": 9,
            "2000": 10,
            "5000": 11,
            "10000": 12,
            "20000": 13,
            "50000": 14,
        }
        gain_number = gain_dict[gain]
        dev = self.selectedDevice(c)
        yield dev.write("LISN 3\r\n")
        yield dev.write("GAIN {}\r\n".format(gain_number))
        returnValue("Gain has been set to {}".format(gain))

    @setting(13, "set_highpass_filter", highpass_filter="s", returns="s")
    def set_highpass_filter(self, c, highpass_filter=None):
        # If the filter has been set to bandpass mode, lowpass should always be higher than highpass
        highpass_filter_dict = {
            "0.03": 0,
            "0.1": 1,
            "0.3": 2,
            "1": 3,
            "3": 4,
            "10": 5,
            "30": 6,
            "100": 7,
            "300": 8,
            "1k": 9,
            "3k": 10,
            "10k": 11,
        }
        highpass_filter_number = highpass_filter_dict[highpass_filter]
        dev = self.selectedDevice(c)
        yield dev.write("LISN 3\r\n")
        yield dev.write("HFRQ {}\r\n".format(highpass_filter_number))
        returnValue("Highpass filter has been set to {} Hz".format(highpass_filter))

    @setting(14, "set_signal_invert_sense", signal_invert_sense="s", returns="s")
    def set_signal_invert_sense(self, c, signal_invert_sense=None):
        signal_invert_sense_dict = {"non-inverted": 0, "inverted": 1}
        signal_invert_sense_number = signal_invert_sense_dict[signal_invert_sense]
        dev = self.selectedDevice(c)
        yield dev.write("LISN 3\r\n")
        yield dev.write("INVT {}\r\n".format(signal_invert_sense_number))
        returnValue(
            "Signal invert sense has been set to {}".format(signal_invert_sense)
        )

    @setting(15, "set_lowpass_filter", lowpass_filter="s", returns="s")
    def set_lowpass_filter(self, c, lowpass_filter=None):
        # If the filter has been set to bandpass mode, lowpass should always be higher than highpass
        lowpass_filter_dict = {
            "0.03": 0,
            "0.1": 1,
            "0.3": 2,
            "1": 3,
            "3": 4,
            "10": 5,
            "30": 6,
            "100": 7,
            "300": 8,
            "1k": 9,
            "3k": 10,
            "10k": 11,
            "30k": 12,
            "100k": 13,
            "300k": 14,
            "1M": 15,
        }
        lowpass_filter_number = lowpass_filter_dict[lowpass_filter]
        dev = self.selectedDevice(c)
        yield dev.write("LISN 3\r\n")
        yield dev.write("LFRQ {}\r\n".format(lowpass_filter_number))
        returnValue("Lowpass filter has been set to {} Hz".format(lowpass_filter))

    @setting(16, "set_overload", returns="s")
    def reset_overload(self, c):
        dev = self.selectedDevice(c)
        yield dev.write("LISN 3\r\n")
        yield dev.write("ROLD\r\n")
        returnValue("Overload has been reset for 1/2 second")

    @setting(17, "set_input_source", input_source="s", returns="s")
    def reset_input_source(self, c, input_source=None):
        input_source_dict = {"A": 0, "A-B": 1, "B": 2}
        input_source_number = input_source_dict[input_source]
        dev = self.selectedDevice(c)
        yield dev.write("LISN 3\r\n")
        yield dev.write("SRCE {}\r\n".format(input_source_number))
        returnValue("Input source has been set to {}".format(input_source))

    @setting(18, "set_vernier_gain_status", vernier_gain_status="s", returns="s")
    def set_vernier_gain_status(self, c, vernier_gain_status=None):
        vernier_gain_status_dict = {"cal'd gain": 0, "vernier gain": 1}
        vernier_gain_status_number = vernier_gain_status_dict[vernier_gain_status]
        dev = self.selectedDevice(c)
        yield dev.write("LISN 3\r\n")
        yield dev.write("UCAL {}\r\n".format(vernier_gain_status_number))
        returnValue(
            "Vernier gain status has been set to {}".format(vernier_gain_status)
        )

    @setting(19, "set_vernier_gain", vernier_gain="s", returns="s")
    def set_vernier_gain(self, c, vernier_gain=None):
        """Sets the vernier gian to i%. i = 0 to 100."""
        dev = self.selectedDevice(c)
        yield dev.write("LISN 3\r\n")
        yield dev.write("UCGN {}\r\n".format(vernier_gain))
        returnValue("Vernier gain has been set to {}%".format(vernier_gain))

    @setting(100, "reset", returns="s")
    def reset(self, c):
        """Recalls default settings."""
        dev = self.selectedDevice(c)
        yield dev.write("LISN 3\r\n")
        yield dev.write("*RST")
        returnValue("Recalls default settings")


__server__ = SR560Server()


if __name__ == "__main__":
    util.runServer(__server__)
