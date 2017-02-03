# Copyright (C) 2016 Ivan Pechenezhskiy
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

from twisted.internet.defer import inlineCallbacks, returnValue

from labrad.gpib import GPIBDeviceWrapper


class ReadRawGPIBDeviceWrapper(GPIBDeviceWrapper):
    @inlineCallbacks
    def read_raw(self, bytes=None, timeout=None):
        """Read a raw string from the device."""
        p = self._packet()
        if timeout is not None:
            p.timeout(timeout)
        p.read_raw(bytes)
        if timeout is not None:
            p.timeout(self._timeout)
        resp = yield p.send()
        returnValue(resp.read_raw)