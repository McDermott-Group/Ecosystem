# Copyright (C) 2015 Guilhem Ribeill
#               2015, 2016 Ivan Pechenezhskiy
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
name = Lab Brick Attenuators
version = 2.0.1
description =  Gives access to Lab Brick attenuators.
instancename = %LABRADNODE% Lab Brick Attenuators

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
from labrad.units import dB, s
from labrad import util

MAX_NUM_ATTEN = 64      # Maximum number of connected attenuators.
MAX_MODEL_NAME = 32     # Maximum length of Lab Brick model name.


class LBAttenuatorServer(LabradServer):
    name = '%LABRADNODE% Lab Brick Attenuators'
    refreshInterval = 60 * s

   # # @inlineCallbacks
    # def getRegistryKeys(self):
        # """Get registry keys for the Lab Brick Attenuator Server."""
        # #reg = self.client.registry()
		# a = 10
		# area51_root = os.path.join(os.environ['REPOSITORY_ROOT'], 'area51')
		# self.DLL_path = os.path.join(area51_root, '\instruments\labbricks\VNX_atten.dll')
		# self.autoRefresh = True
        # # if 'Lab Brick Attenuator Server Autorefresh' not in keys:
            # # self.autoRefresh = False
        # # else:
            # # self.autoRefresh = yield reg.get('Lab Brick Attenuator '
                                             # # 'Server Autorefresh')
        # print("Lab Brick Attenuator Server Autorefresh is set to %s"
              # % self.autoRefresh)

    @inlineCallbacks
    def initServer(self):
        """Initialize the Lab Brick Attenuator Server."""
        area51_root = os.path.join(os.environ['REPOSITORY_ROOT'], 'area51')
        self.DLL_path = os.path.join(area51_root, 'instruments\\labbricks\\VNX_atten.dll')
        self.autoRefresh = True
        try:
            self.VNXdll = yield ctypes.CDLL(self.DLL_path)
        except Exception:
            raise Exception('Could not find Lab Brick Attenuator DLL')

        # Disable attenuator DLL test mode.
        self.VNXdll.fnLDA_SetTestMode(ctypes.c_bool(False))

        # Number of the currently connected devices.
        self._num_devs = 0
        # Create a dictionary that maps serial numbers to device IDs.
        self._SN2DID = {}
        # Create a dictionary that keeps track of last set attenuation.
        self._last_attn = {}
        # Dictionary to keep track of min/max attenuations.
        self._min_attn = {}
        self._max_attn = {}

        # Create a context for the server.
        self._pseudo_ctx = {}
        if self.autoRefresh:
            callLater(0.1, self.startRefreshing)
        else:
            yield self.refreshAttenuators()

    def startRefreshing(self):
        """Start periodically refreshing the list of devices.

        The start call returns a deferred which we save for later.
        When the refresh loop is shutdown, we will wait for this
        deferred to fire to indicate that it has terminated.
        """
        self.refresher = LoopingCall(self.refreshAttenuators)
        self.refresherDone = \
            self.refresher.start(self.refreshInterval['s'],
                                 now=True)

    @inlineCallbacks
    def stopServer(self):
        """Kill the device refresh loop and wait for it to terminate."""
        if hasattr(self, 'refresher'):
            self.refresher.stop()
            yield self.refresherDone
        self.killAttenuatorConnections()

    def killAttenuatorConnections(self):
        for DID in self._SN2DID.values():
            try:
                yield self.VNXdll.fnLDA_CloseDevice(ctypes.c_uint(DID))
            except Exception:
                pass

    @inlineCallbacks
    def refreshAttenuators(self):
        """Refresh attenuator list."""
        n = yield self.VNXdll.fnLDA_GetNumDevices()
        if n == self._num_devs:
            pass
        elif n == 0:
            print('Lab Brick attenuators disconnected')
            self._num_devs = n
            self._SN2DID.clear()
            self._last_attn.clear()
            self._min_atten.clear()
            self._max_atten.clear()
        else:
            self._num_devs = n
            DIDs = (ctypes.c_uint * MAX_NUM_ATTEN)()
            DIDs_ptr = ctypes.cast(DIDs, ctypes.POINTER(ctypes.c_uint))
            yield self.VNXdll.fnLDA_GetDevInfo(DIDs_ptr)
            for idx in range(n):
                SN = yield self.VNXdll.fnLDA_GetSerialNumber(DIDs_ptr[idx])
                self._SN2DID.update({SN: DIDs_ptr[idx]})
                self.select_device(self._pseudo_ctx, SN)
                model = yield self.model(self._pseudo_ctx)
                attn = yield self.attenuation(self._pseudo_ctx)
                min_attn = yield self.min_attenuation(self._pseudo_ctx)
                max_attn = yield self.max_attenuation(self._pseudo_ctx)
                self._last_attn.update({SN: attn})
                self._min_attn.update({SN: min_attn})
                self._max_attn.update({SN: max_attn})
                print('Found a %s Lab Brick Attenuator, serial '
                      'number: %d, current attenuation: %s'
                      % (model, SN, self._last_attn[SN]))

    def getDeviceDID(self, c):
        if 'SN' not in c:
            raise DeviceNotSelectedError('No Lab Brick Attenuator '
                                         'serial number is selected')
        if c['SN'] not in self._SN2DID.keys():
            raise Exception('Cannot find Lab Brick Attenuator with '
                            'serial number %s' % c['SN'])
        return self._SN2DID[c['SN']]

    @setting(1, 'Refresh Device List')
    def refresh_device_list(self, c):
        """Manually refresh attenuator list."""
        yield self.refreshAttenuators()

    @setting(2, 'List Devices', returns='*w')
    def list_devices(self, c):
        """Return list of attenuator serial numbers."""
        return sorted(self._SN2DID.keys())

    @setting(5, 'Select Device', SN='w', returns='')
    def select_device(self, c, SN):
        """
        Select attenuator by its serial number. Since the serial
        numbers are unique by definition, no extra information is
        necessary to select a device.
        """
        c['SN'] = SN

    @setting(6, 'Deselect Device', returns='')
    def deselect_device(self, c):
        """Deselect attenuator."""
        if 'SN' in c:
            del c['SN']

    @setting(10, 'Attenuation', attn='v[dB]', returns='v[dB]')
    def attenuation(self, c, attn=None):
        """Get or set attenuation."""
        if attn is not None:
            if attn['dB'] < self._min_attn[c['SN']]['dB']:
                attn = self._min_attn[c['SN']]
            elif attn['dB'] > self._max_attn[c['SN']]['dB']:
                attn = self._max_attn[c['SN']]
            # Check whether the attenuation needs to be changed.
            if self._last_attn[c['SN']] == attn:
                returnValue(attn)

        # Set the attenuation (if requested) and read it back.
        DID = ctypes.c_uint(self.getDeviceDID(c))
        yield self.VNXdll.fnLDA_InitDevice(DID)
        if attn is not None:
            attn_value = ctypes.c_int(int(4. * attn['dB']))
            yield self.VNXdll.fnLDA_SetAttenuation(DID, attn_value)
        attn = .25 * (yield self.VNXdll.fnLDA_GetAttenuation(DID)) * dB
        self._last_attn[c['SN']] = attn
        yield self.VNXdll.fnLDA_CloseDevice(DID)
        returnValue(attn)

    @setting(21, 'Max Attenuation', returns='v[dB]')
    def max_attenuation(self, c):
        """Return maximum attenuation."""
        DID = ctypes.c_uint(self.getDeviceDID(c))
        yield self.VNXdll.fnLDA_InitDevice(DID)
        max_attn = yield self.VNXdll.fnLDA_GetMaxAttenuation(DID)
        max_attn = .25 * max_attn * dB
        yield self.VNXdll.fnLDA_CloseDevice(DID)
        returnValue(max_attn)

    @setting(22, 'Min Attenuation', returns='v[dB]')
    def min_attenuation(self, c):
        """Return minimum attenuation."""
        DID = ctypes.c_uint(self.getDeviceDID(c))
        yield self.VNXdll.fnLDA_InitDevice(DID)
        min_attn = yield self.VNXdll.fnLDA_GetMinAttenuation(DID)
        min_attn = .25 * min_attn * dB
        yield self.VNXdll.fnLDA_CloseDevice(DID)
        returnValue(min_attn)

    @setting(30, 'Model', returns='s')
    def model(self, c):
        """Return attenuator model name."""
        DID = ctypes.c_uint(self.getDeviceDID(c))
        model = ctypes.create_string_buffer(MAX_MODEL_NAME)
        name_length = yield self.VNXdll.fnLDA_GetModelName(DID, model)
        returnValue(model.raw[0:name_length])


__server__ = LBAttenuatorServer()


if __name__ == '__main__':
    util.runServer(__server__)
