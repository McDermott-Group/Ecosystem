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
name = SignalCore RF Generators
version = 1.1
description =  Gives access to SignalCore RF generators.
instancename = %LABRADNODE% SignalCore RF Generators

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
"""

import os
from ctypes import (
    CDLL,
    Structure,
    POINTER,
    byref,
    c_float,
    c_ubyte,
    c_ulonglong,
    c_void_p,
    c_char_p,
    c_uint8,
    c_uint64,
    c_bool,
    create_string_buffer,
    addressof,
)

from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.internet.reactor import callLater
from twisted.internet.task import LoopingCall

from labrad.server import LabradServer, setting
from labrad.errors import DeviceNotSelectedError
from labrad.units import Hz, dBm, s
from labrad import util

MAX_NUM_RFGEN = 8  # Maximum number of connected RF generators. this is just a guess
MAX_MODEL_NAME = 8  # Size of the SN. not a guess

# SC5503b specs
MIN_FREQ = 50e6 * Hz
MAX_FREQ = 10e9 * Hz

MIN_POW = -60 * dBm
MAX_POW = +17 * dBm


class RFParams(Structure):
    _fields_ = [
        ("frequency", c_ulonglong),
        ("powerLevel", c_float),
    ] + [
        (name, c_ubyte)
        for name in (
            "rfEnable",
            "alcOpen",
            "autoLevelEnable",
            "fastTune",
            "tuneStep",
            "referenceSetting",
        )
    ]


class DeviceStatus(Structure):
    _fields_ = [
        (name, c_ubyte)
        for name in (
            "tcxoPllLock",
            "vcxoPllLock",
            "finePllLock",
            "coarsePllLock",
            "sumPllLock",
            "extRefDetected",
            "refClkOutEnable",
            "extRefLockEnable",
            "alcOpen",
            "fastTuneEnable",
            "standbyEnable",
            "rfEnable",
            "pxiClkEnable",
        )
    ]


class SCRFGenServer(LabradServer):
    name = "%LABRADNODE% SignalCore RF Generators"
    refreshInterval = 60 * s

    @inlineCallbacks
    def initServer(self):
        """Initialize the SignalCore RF Generator Server."""
        # yield self.getRegistryKeys()
        area51_root = os.path.join(os.environ["REPOSITORY_ROOT"], "area51")
        self.DLL_path = os.path.join(
            area51_root, "instruments\\SignalCore\\sc5503b_usb.dll"
        )
        self.autoRefresh = True
        try:
            self.SCdll = yield CDLL(self.DLL_path)
        except Exception:
            raise Exception("Could not find SignalCore RF Generator DLL")

        # Number of the currently connected devices.
        self._num_devs = 0
        # Create dictionaries that keep track of the last set power and
        # frequency.
        self._last_freq = {}
        self._last_pow = {}
        self._SNdict = (
            {}
        )  # Create serial number dictionary, keys are SN strings, values are C objects
        self._status = 0  # running status

        # Set argtypes and restypes
        self.SCdll.sc5503b_OpenDevice.argtypes = [c_char_p, POINTER(c_void_p)]
        self.SCdll.sc5503b_CloseDevice.argtypes = [c_void_p]
        self.SCdll.sc5503b_SetFrequency.argtypes = [c_void_p, c_ulonglong]
        self.SCdll.sc5503b_SetPowerLevel.argtypes = [c_void_p, c_float]
        self.SCdll.sc5503b_SetRfOutput.argtypes = [c_void_p, c_bool]
        self.SCdll.sc5503b_GetRfParameters.argtypes = [c_void_p, POINTER(RFParams)]
        self.SCdll.sc5503b_GetDeviceStatus.argtypes = [c_void_p, POINTER(DeviceStatus)]
        self.SCdll.sc5503b_SetClockReference.argtypes = [
            c_void_p,
            c_bool,
            c_bool,
            c_bool,
            c_bool,
        ]
        self._handle = c_void_p()

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
        self.disconnect(self._pseudo_ctx)
        self.killRFGenConnections()

    @inlineCallbacks
    def killRFGenConnections(self):
        try:
            yield self.SCdll.sc5503b_CloseDevice(handle)
        except Exception:
            pass

    @inlineCallbacks
    def refreshRFGenerators(self):
        """Refresh RF generators list."""
        SNs_new = [create_string_buffer(MAX_MODEL_NAME) for i in range(MAX_NUM_RFGEN)]
        SNs_ptr = (c_char_p * MAX_MODEL_NAME)(*map(addressof, SNs_new))
        n = yield self.SCdll.sc5503b_SearchDevices(SNs_ptr)
        if n == self._num_devs:
            pass
        elif n == 0:
            print("SignalCore RF Generators disconnected")
            self._num_devs = n
            self._last_freq.clear()
            self._last_pow.clear()
        else:
            self._num_devs = n
            for idx in range(n):
                SN = SNs_new[idx].value.decode()
                if SN not in self._SNdict:
                    self._SNdict[SN] = SNs_new[idx]
                    # Select device
                    self.select_device(self._pseudo_ctx, SN)
                    # get RF params
                    freq = yield self.frequency(self._pseudo_ctx)
                    power = yield self.power(self._pseudo_ctx)
                    state = yield self.output(self._pseudo_ctx)
                    ref = yield self.external_pll(self._pseudo_ctx)
                    self._last_freq.update({SN: freq})
                    self._last_pow.update({SN: power})
                    print(
                        "Found a SignalCore RF generator, serial "
                        "number: %s, current power: %s, current "
                        "frequency: %s, output state: %s, "
                        "external reference: %s" % (SN, power, freq, state, ref)
                    )
                    # disconnect from device
                    self.deselect_device(self._pseudo_ctx)

    def getCObjectSN(self, c):
        if "SN" not in c:
            raise DeviceNotSelectedError(
                "No SignalCore RF Generator " "serial number selected"
            )
        if c["SN"] not in list(self._SNdict.keys()):
            raise Exception(
                "Could not find Lab Brick RF Generator " "with serial number " + c["SN"]
            )
        return self._SNdict[c["SN"]]

    @setting(559, "Get Device Status")
    def get_dev_status(self, c):
        status = DeviceStatus()
        SN_call = self.getCObjectSN(c)
        yield self.SCdll.sc5503b_OpenDevice(SN_call, byref(self._handle))
        yield self.SCdll.sc5503b_GetDeviceStatus(self._handle, status)
        yield self.SCdll.sc5503b_CloseDevice(self._handle)
        returnValue(status)

    @setting(560, "Get RF Parameter List")
    def get_rf_params(self, c):
        rf_params = RFParams()
        status = DeviceStatus()
        SN_call = self.getCObjectSN(c)
        yield self.SCdll.sc5503b_OpenDevice(SN_call, byref(self._handle))
        yield self.SCdll.sc5503b_GetRfParameters(self._handle, rf_params)
        yield self.SCdll.sc5503b_GetDeviceStatus(self._handle, status)
        rf_params.rfEnable = status.rfEnable
        yield self.SCdll.sc5503b_CloseDevice(self._handle)
        returnValue(rf_params)

    @setting(561, "Refresh Device List")
    def refresh_device_list(self, c):
        """Manually refresh RF generator list."""
        self.refreshRFGenerators()

    @setting(562, "List Devices", returns="*s")
    def list_devices(self, c):
        """Return list of RF generator serial numbers."""
        return [s for s in self._SNdict]

    @setting(565, "Select Device", SN="s", returns="")
    def select_device(self, c, SN):
        """
        Select RF generator by its serial number.
        """
        c["SN"] = SN

    @setting(566, "Deselect Device", returns="")
    def deselect_device(self, c):
        """Deselect RF generator."""
        if "SN" in c:
            del c["SN"]

    @setting(568, "External PLL", ext_pll="b", returns="b")
    def external_pll(self, c, ext_pll=None):
        """
        Get or set External PLL (bool). Assumes ref out, HF ref out, and PXI clock will always be set 0. Error code None.
        """
        SN_call = self.getCObjectSN(c)
        yield self.SCdll.sc5503b_OpenDevice(SN_call, byref(self._handle))
        if ext_pll == None:
            rf_params = yield self.get_rf_params(c)
            ext_pll = bool(rf_params.referenceSetting)
        else:
            self._status = yield self.SCdll.sc5503b_SetClockReference(
                self._handle, c_bool(ext_pll), c_bool(0), c_bool(0), c_bool(0)
            )
            if self._status:  # non zero status values indicate error
                raise RuntimeError(
                    "Unable to connect to device, error code " + str(self._status)
                )

        returnValue(ext_pll)
        yield self.SCdll.sc5503b_CloseDevice(self._handle)

    @setting(570, "Output", state="b", returns="b")
    def output(self, c, state=None):
        """Get or set RF generator output state (on/off). state must be either None, True or False. Error code None."""
        SN_call = self.getCObjectSN(c)
        if state == None:
            rf_params = yield self.get_rf_params(c)
            state = bool(rf_params.rfEnable)
        elif state == False or state == True:
            yield self.SCdll.sc5503b_OpenDevice(SN_call, byref(self._handle))
            self._status = yield self.SCdll.sc5503b_SetRfOutput(
                self._handle, c_bool(state)
            )
            if self._status:  # non zero status values indicate error
                raise RuntimeError("Error setting RF output, code " + str(self._status))
                state = None
            yield self.SCdll.sc5503b_CloseDevice(self._handle)
        else:
            raise RuntimeError(
                "Input must be None, True or False!. RF output not changed."
            )
            state = None
        returnValue(state)

    @setting(582, "Frequency", freq="v[Hz]", returns="v[Hz]")
    def frequency(self, c, freq=None):
        """Set or get RF generator output frequency. Error code -1"""
        SN_call = self.getCObjectSN(c)
        if freq is None:
            rf_params = yield self.get_rf_params(c)
            freq = rf_params.frequency * Hz
        else:
            """KNOWN BUG ALERT: when both frequency and power are changed while output is disabled, output is
            is enabled w/out the device becoming aware. Fix: before the frequency is changed, RF output
            is queried, then after the frequency is changed, RF output is changed back to that value.
            """
            if self._last_freq[c["SN"]] == freq:
                returnValue(freq)
            if freq["Hz"] < MIN_FREQ["Hz"]:
                freq = MIN_FREQ
                print(
                    f"Frequency too small! Must be None (to get current frequency) or between {MIN_FREQ} and {MAX_FREQ}. Frequency set to minimum frequency."
                )
            elif freq["Hz"] > MAX_FREQ["Hz"]:
                freq = MAX_FREQ
                print(
                    f"Frequency too large! Must be None (to get current frequency) or between {MIN_FREQ} and {MAX_FREQ}. Frequency set to maximum frequency."
                )
            rf_state = yield self.output(c)

            yield self.SCdll.sc5503b_OpenDevice(SN_call, byref(self._handle))
            self._status = yield self.SCdll.sc5503b_SetFrequency(
                self._handle, c_uint64(int(freq["Hz"]))
            )
            yield self.SCdll.sc5503b_CloseDevice(self._handle)

            if self._status:  # non zero status values indicate error
                raise RuntimeError("Error setting frequency, code " + str(self._status))
                returnValue(-1 * Hz)

            yield self.output(c, rf_state)
        returnValue(freq)
        self._last_freq[c["SN"]] = freq

    @setting(583, "Power", power="v[dBm]", returns="v[dBm]")
    def power(self, c, power=None):
        """Set or get RF generator output power."""
        SN_call = self.getCObjectSN(c)
        if power is None:
            rf_params = yield self.get_rf_params(c)
            power = rf_params.powerLevel * dBm
        else:
            """KNOWN BUG ALERT: when both frequency and power are changed while output is disabled, output is
            is enabled w/out the device becoming aware. Fix: before the power is changed, RF output
            is queried, then after the frequency is changed, RF output is changed back to that value.
            """
            if self._last_pow[c["SN"]] == power:
                returnValue(power)
            if power["dBm"] < MIN_POW["dBm"]:
                power = MIN_POW
                print(
                    f"Power too small! Must be None (to get current power) or between {MIN_POW} and {MAX_POW}. Power set to minimum power."
                )
            elif power["dBm"] > MAX_POW["dBm"]:
                power = MAX_POW
                print(
                    f"Power too large! Must be None (to get current power) or between {MIN_POW} and {MAX_POW}. Power set to maximum power."
                )
            rf_state = yield self.output(c)

            yield self.SCdll.sc5503b_OpenDevice(SN_call, byref(self._handle))
            self._status = yield self.SCdll.sc5503b_SetPowerLevel(
                self._handle, c_float(power["dBm"])
            )
            if self._status:  # non zero status values indicate error
                raise RuntimeError("Error setting power, code " + str(self._status))
            yield self.SCdll.sc5503b_CloseDevice(self._handle)

            yield self.output(c, rf_state)
        returnValue(power)
        self._last_pow[c["SN"]] = power


__server__ = SCRFGenServer()


if __name__ == "__main__":
    util.runServer(__server__)
