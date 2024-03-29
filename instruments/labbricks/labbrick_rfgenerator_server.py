# Copyright (C) 2015 Guilhem Ribeill
#               2016 Ivan Pechenezhskiy
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
name = Lab Brick RF Generators
version = 2.0.2
description =  Gives access to Lab Brick RF generators.
instancename = %LABRADNODE% Lab Brick RF Generators

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
"""

import os
import ctypes

from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.internet.reactor import callLater
from twisted.internet.task import LoopingCall

from labrad.server import LabradServer, setting
from labrad.errors import DeviceNotSelectedError
from labrad.units import Hz, dBm, s
from labrad import util

MAX_NUM_RFGEN = 64  # Maximum number of connected RF generators.
MAX_MODEL_NAME = 32  # Maximum length of Lab Brick model name.


class LBRFGenServer(LabradServer):
    name = "%LABRADNODE% Lab Brick RF Generators"
    refreshInterval = 60 * s

    @inlineCallbacks
    def initServer(self):
        """Initialize the Lab Brick RF Generator Server."""
        # yield self.getRegistryKeys()
        area51_root = os.path.join(os.environ["REPOSITORY_ROOT"], "area51")
        self.DLL_path = os.path.join(
            area51_root, "instruments\\labbricks\\vnx_fmsynth.dll"
        )
        self.autoRefresh = True
        try:
            self.VNXdll = yield ctypes.CDLL(self.DLL_path)
        except Exception:
            raise Exception("Could not find Lab Brick RF Generator DLL")

        # Disable RF Generator DLL test mode (turn it off).
        self.VNXdll.fnLMS_SetTestMode(ctypes.c_bool(False))

        # Number of the currently connected devices.
        self._num_devs = 0
        # Create dictionaries that keep track of the last set power and
        # frequency.
        self._last_freq = {}
        self._last_pow = {}
        # Dictionary to keep track of min/max powers and frequencies.
        self._min_freq = {}
        self._max_freq = {}
        self._min_pow = {}
        self._max_pow = {}
        # Create a dictionary that maps serial numbers to device IDs.
        self._SN2DID = {}

        # Create a context for the server.
        self._pseudo_ctx = {}
        if self.autoRefresh:
            callLater(0.1, self.startRefreshing)
        else:
            self.refreshRFGenerators()

    def startRefreshing(self):
        """
        Start periodically refreshing the list of devices.

        The start call returns a deferred which we save for later.
        When the refresh loop is shutdown, we will wait for this
        deferred to fire to indicate that it has terminated.
        """
        self.refresher = LoopingCall(self.refreshRFGenerators)
        self.refresherDone = self.refresher.start(self.refreshInterval["s"], now=True)

    @inlineCallbacks
    def stopServer(self):
        """Kill the device refresh loop and wait for it to terminate."""
        if hasattr(self, "refresher"):
            self.refresher.stop()
            yield self.refresherDone
        self.killRFGenConnections()

    @inlineCallbacks
    def killRFGenConnections(self):
        for DID in list(self._SN2DID.values()):
            try:
                yield self.VNXdll.fnLMS_CloseDevice(ctypes.c_uint(DID))
            except Exception:
                pass

    @inlineCallbacks
    def refreshRFGenerators(self):
        """Refresh RF generators list."""
        n = yield self.VNXdll.fnLMS_GetNumDevices()
        if n == self._num_devs:
            pass
        elif n == 0:
            print("Lab Brick RF Generators disconnected")
            self._num_devs = n
            self._SN2DID.clear()
            self._min_freq.clear()
            self._max_freq.clear()
            self._min_pow.clear()
            self._max_pow.clear()
            self._last_freq.clear()
            self._last_pow.clear()
        else:
            self._num_devs = n
            DIDs = (ctypes.c_uint * MAX_NUM_RFGEN)()
            DIDs_ptr = ctypes.cast(DIDs, ctypes.POINTER(ctypes.c_uint))
            yield self.VNXdll.fnLMS_GetDevInfo(DIDs_ptr)
            for idx in range(n):
                SN = yield self.VNXdll.fnLMS_GetSerialNumber(DIDs_ptr[idx])
                self._SN2DID.update({SN: DIDs_ptr[idx]})
                self.select_device(self._pseudo_ctx, SN)
                model = yield self.model(self._pseudo_ctx)
                min_freq = yield self.min_frequency(self._pseudo_ctx)
                max_freq = yield self.max_frequency(self._pseudo_ctx)
                min_pow = yield self.min_power(self._pseudo_ctx)
                max_pow = yield self.max_power(self._pseudo_ctx)
                self._min_freq.update({SN: min_freq})
                self._max_freq.update({SN: max_freq})
                self._min_pow.update({SN: min_pow})
                self._max_pow.update({SN: max_pow})
                freq = yield self.frequency(self._pseudo_ctx)
                power = yield self.power(self._pseudo_ctx)
                state = yield self.output(self._pseudo_ctx)
                ref = yield self.external_reference(self._pseudo_ctx)
                self._last_freq.update({SN: freq})
                self._last_pow.update({SN: power})
                print(
                    (
                        "Found a %s Lab Brick RF generator, serial "
                        "number: %d, current power: %s, current "
                        "frequency: %s, output state: %s, "
                        "external reference: %s" % (model, SN, power, freq, state, ref)
                    )
                )

    def getDeviceDID(self, c):
        if "SN" not in c:
            raise DeviceNotSelectedError(
                "No Lab Brick RF Generator " "serial number selected"
            )
        if c["SN"] not in list(self._SN2DID.keys()):
            raise Exception(
                "Could not find Lab Brick RF Generator "
                "with serial number %d" % c["SN"]
            )
        return self._SN2DID[c["SN"]]

    @setting(561, "Refresh Device List")
    def refresh_device_list(self, c):
        """Manually refresh RF generator list."""
        self.refreshRFGenerators()

    @setting(562, "List Devices", returns="*w")
    def list_devices(self, c):
        """Return list of RF generator serial numbers."""
        return sorted(self._SN2DID.keys())

    @setting(565, "Select Device", SN="w", returns="")
    def select_device(self, c, SN):
        """
        Select RF generator by its serial number. Since the serial
        numbers are unique by definition, no extra information is
        necessary to select a device.
        """
        c["SN"] = SN

    @setting(566, "Deselect Device", returns="")
    def deselect_device(self, c):
        """Deselect RF generator."""
        if "SN" in c:
            del c["SN"]

    @setting(570, "Output", state="b", returns="b")
    def output(self, c, state=None):
        """Get or set RF generator output state (on/off)."""
        DID = ctypes.c_uint(self.getDeviceDID(c))
        yield self.VNXdll.fnLMS_InitDevice(DID)
        if state is not None:
            yield self.VNXdll.fnLMS_SetRFOn(DID, ctypes.c_bool(state))
        outputState = yield self.VNXdll.fnLMS_GetRF_On(DID)
        yield self.VNXdll.fnLMS_CloseDevice(DID)
        returnValue(bool(outputState))

    @setting(575, "External Reference", ref="b", returns="b")
    def external_reference(self, c, ref=None):
        """Get or set RF generator external reference (True/False).
        True corresponds to the external reference, False corresponds
        to the internal.
        """
        DID = ctypes.c_uint(self.getDeviceDID(c))
        yield self.VNXdll.fnLMS_InitDevice(DID)
        if ref is not None:
            yield self.VNXdll.fnLMS_SetUseInternalRef(DID, ctypes.c_bool(not ref))
        ref = yield self.VNXdll.fnLMS_GetUseInternalRef(DID)
        yield self.VNXdll.fnLMS_CloseDevice(DID)
        returnValue(not bool(ref))

    @setting(582, "Frequency", freq="v[Hz]", returns="v[Hz]")
    def frequency(self, c, freq=None):
        """Set or get RF generator output frequency."""
        DID = ctypes.c_uint(self.getDeviceDID(c))
        yield self.VNXdll.fnLMS_InitDevice(DID)
        if freq is None:
            # Synthesizer decided to work in 10 Hz increments
            # f[actual] = 10 * f[returned].
            freq = 10.0 * (yield self.VNXdll.fnLMS_GetFrequency(DID)) * Hz
        else:
            if self._last_freq[c["SN"]] == freq:
                returnValue(freq)
            if freq["Hz"] < self._min_freq[c["SN"]]["Hz"]:
                freq = self._min_freq[c["SN"]]
            elif freq["Hz"] > self._max_freq[c["SN"]]["Hz"]:
                freq = self._max_freq[c["SN"]]
            self._last_freq[c["SN"]] = freq
            yield self.VNXdll.fnLMS_SetFrequency(
                DID, ctypes.c_int(int(0.1 * freq["Hz"]))
            )
        yield self.VNXdll.fnLMS_CloseDevice(DID)
        returnValue(freq)

    @setting(583, "Power", power="v[dBm]", returns="v[dBm]")
    def power(self, c, power=None):
        """Set or get RF generator output power."""
        DID = ctypes.c_uint(self.getDeviceDID(c))
        yield self.VNXdll.fnLMS_InitDevice(DID)
        if power is None:
            power = yield self.VNXdll.fnLMS_GetPowerLevel(DID)
            power = self._max_pow[c["SN"]] - 0.25 * power * dBm
        else:
            if self._last_pow[c["SN"]] == power:
                returnValue(power)
            if power["dBm"] < self._min_pow[c["SN"]]["dBm"]:
                power = self._min_pow[c["SN"]]
            elif power["dBm"] > self._max_pow[c["SN"]]["dBm"]:
                power = self._max_pow[c["SN"]]
            self._last_pow[c["SN"]] = power
            powerSetting = ctypes.c_int(int(4 * power["dBm"]))
            yield self.VNXdll.fnLMS_SetPowerLevel(DID, powerSetting)
        yield self.VNXdll.fnLMS_CloseDevice(DID)
        returnValue(power)

    @setting(591, "Max Power", returns="v[dBm]")
    def max_power(self, c):
        """Return maximum output power."""
        DID = ctypes.c_uint(self.getDeviceDID(c))
        yield self.VNXdll.fnLMS_InitDevice(DID)
        max_pow = 0.25 * (yield self.VNXdll.fnLMS_GetMaxPwr(DID)) * dBm
        yield self.VNXdll.fnLMS_CloseDevice(DID)
        returnValue(max_pow)

    @setting(592, "Min Power", returns="v[dBm]")
    def min_power(self, c):
        """Return minimum output power."""
        DID = ctypes.c_uint(self.getDeviceDID(c))
        yield self.VNXdll.fnLMS_InitDevice(DID)
        min_pow = 0.25 * (yield self.VNXdll.fnLMS_GetMinPwr(DID)) * dBm
        yield self.VNXdll.fnLMS_CloseDevice(DID)
        returnValue(min_pow)

    @setting(593, "Max Frequency", returns="v[Hz]")
    def max_frequency(self, c):
        """Return maximum output frequency."""
        DID = ctypes.c_uint(self.getDeviceDID(c))
        yield self.VNXdll.fnLMS_InitDevice(DID)
        max_freq = 10.0 * (yield self.VNXdll.fnLMS_GetMaxFreq(DID)) * Hz
        yield self.VNXdll.fnLMS_CloseDevice(DID)
        returnValue(max_freq)

    @setting(594, "Min Frequency", returns="v[Hz]")
    def min_frequency(self, c):
        """Return minimum output frequency."""
        DID = ctypes.c_uint(self.getDeviceDID(c))
        yield self.VNXdll.fnLMS_InitDevice(DID)
        min_freq = 10.0 * (yield self.VNXdll.fnLMS_GetMinFreq(DID)) * Hz
        yield self.VNXdll.fnLMS_CloseDevice(DID)
        returnValue(min_freq)

    @setting(595, "Model", returns="s")
    def model(self, c):
        """Return RF generator model name."""
        DID = ctypes.c_uint(self.getDeviceDID(c))
        model = ctypes.create_string_buffer(MAX_MODEL_NAME)
        model_length = yield self.VNXdll.fnLMS_GetModelName(DID, model)
        returnValue(model.raw[0:model_length])


__server__ = LBRFGenServer()


if __name__ == "__main__":
    util.runServer(__server__)
