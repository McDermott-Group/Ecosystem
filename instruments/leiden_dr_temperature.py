# Copyright (C) 2015 Ivan Pechenezhskiy
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
name = Leiden DR Temperature
version = 0.4.2
description =  Gives access to Leiden DR temperatures.
instancename = Leiden DR Temperature

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
"""

import os
import numpy as np
from scipy.signal import medfilt

from twisted.internet.defer import inlineCallbacks
from twisted.internet.reactor import callLater
from twisted.internet.task import LoopingCall

from labrad.server import LabradServer, setting
from labrad.units import mK, K, s
from labrad import util


class LeidenDRPseudoserver(LabradServer):
    """
    This server provides an access to the Leiden DR temperatures by
    reading the corresponding log files on the AFS.
    """
    name = 'Leiden DR Temperature'
    refreshInterval = 15 * s
    
    @inlineCallbacks
    def getRegistryKeys(self):
        """
        Get registry keys for the Leiden DR Temperature Pseudoserver.
        """
        reg = self.client.registry()
        yield reg.cd(['', 'Servers', 'Leiden DR Temperature', os.environ['COMPUTERNAME'].lower()], True)
        dirs, keys = yield reg.dir()
        
        if 'Leiden Log Files Path' in keys:
            self._path = yield reg.get('Leiden Log Files Path')
        
        if ('Leiden Log Files Path' not in keys or 
                not os.path.exists(self._path)):
                self._path = ('Z:\mcdermott-group\Data\DR Log Files\Leiden')
        
        if not os.path.exists(self._path):
            raise Exception("Could not find the Leiden Log Files "
                    "Path: '%s'" %str(self._path))
        print("Leiden Log Files Path is set to '%s'." %str(self._path))

    @inlineCallbacks    
    def initServer(self):
        """Initialize the Leiden DR Temperature Pseudoserver."""
        yield self.getRegistryKeys()
        # Number of bytes to read near the end of the log file.
        self._offset = 1024
        # Number of reading to hold in the memory. The filtering is
        # based on this array.
        array_length = 50
        self._arr_still = np.nan * np.empty(array_length)       # mK
        self._arr_exch = np.nan * np.empty(array_length)        # mK
        self._arr_mix = np.nan * np.empty(array_length)         # mK
        self._arr_mix_pt1000 = np.nan * np.empty(array_length)  # K
        yield self.readTemperatures()
        callLater(0.1, self.startRefreshing)

    def startRefreshing(self):
        """
        Start periodically refreshing the temperatures.

        The start call returns a deferred which we save for later.
        When the refresh loop is shutdown, we will wait for this
        deferred to fire to indicate that it has terminated.
        """
        self.refresher = LoopingCall(self.readTemperatures)
        self.refresherDone = \
                self.refresher.start(self.refreshInterval['s'],
                now=True)
        
    @inlineCallbacks
    def stopServer(self):
        """Kill the device refresh loop and wait for it to terminate."""
        if hasattr(self, 'refresher'):
            self.refresher.stop()
            yield self.refresherDone

    def readTemperatures(self):
        """Read temperatures from a log file."""
        # Get the list of files in the folder and return the one with
        # the most recent name.
        file = sorted([f for f in os.listdir(self._path)
                if os.path.isfile(os.path.join(self._path, f))])[-1]

        # Read the last line in the log file.
        with open(os.path.join(self._path, file), 'rb') as f:
            f.seek(0, os.SEEK_END)
            sz = f.tell()   # Get the size of the file.
            while True:
                if self._offset > sz:
                    self._offset = sz
                f.seek(-self._offset, os.SEEK_END)
                lines = f.readlines()
                if len(lines) > 1 or self._offset == sz:
                    line = lines[-1]
                    break
                self._offset *= 2
            # Extract temperatures.
            fields = line.split('\t')
            raw_still = float(fields[10])         # mK
            raw_exch = float(fields[11])          # mK
            raw_mix = float(fields[12])           # mK
            raw_mix_pt1000 = float(fields[13])    # K
            
            if self._arr_still[-1] != raw_still or \
                    self._arr_exch[-1] != raw_exch or \
                    self._arr_mix[-1] != raw_mix or \
                    self._arr_mix_pt1000[-1] != raw_mix_pt1000:
                
                self._arr_still = np.roll(self._arr_still, -1)
                self._arr_exch = np.roll(self._arr_exch, -1)
                self._arr_mix = np.roll(self._arr_mix, -1)
                self._arr_mix_pt1000 = np.roll(self._arr_mix_pt1000, -1)
                
                self._arr_still[-1] = raw_still
                self._arr_exch[-1] = raw_exch
                self._arr_mix[-1] = raw_mix
                self._arr_mix_pt1000[-1] = raw_mix_pt1000
    
    def filteredTemperature(self, array, lower_threshold,
            upper_threshold):
        if not np.any(np.isfinite(array)):
            return np.nan
        # Raw thresholding.
        array = array[np.isfinite(array)]
        mask = np.logical_and(np.less(array, upper_threshold),
                              np.greater(array, lower_threshold))
        raw = array[mask]
        
        # Median filtering.
        filtered = medfilt(raw, 5)
        
        # Fine thresholding.
        if filtered.size:
            weight = np.exp(-np.linspace(filtered.size / 5., 0,
                                         filtered.size))
            Tmean = np.sum(weight * filtered) / np.sum(weight)
            Tmed = np.median(raw)
            
            if Tmean > 1.3 * Tmed or Tmean < 0.7 * Tmed:
                T = Tmed
            else:
                T = Tmean 
            lower_threshold = np.max([lower_threshold, 0.7 * T])
            upper_threshold = np.min([upper_threshold, 1.3 * T])
            mask = np.logical_and(np.less(array, upper_threshold),
                                  np.greater(array, lower_threshold))
            fine = array[mask]
            if fine.size:
                return fine[-1]
            else:
                return Tmean
        elif raw.size:
            return raw[-1]
        else:
            return np.nan
   
    @setting(1, 'Refresh Temperatures')
    def refresh_temperatures(self, c):
        """Manually refresh the temperatures."""
        self.readTemperatures()
        
    @setting(11, 'Raw Still Temperature', returns='v[mK]')
    def raw_still_temperature(self, c):
        """Return the raw still chamber temperature."""
        return self._arr_still[-1] * mK

    @setting(12, 'Raw Exchange Temperature', returns='v[mK]')
    def raw_exchange_temperature(self, c):
        """Return the raw exchange chamber temperature."""
        return self._arr_ech[-1] * mK
        
    @setting(13, 'Raw Mix Temperature', returns='v[mK]')
    def raw_mix_temperature(self, c):
        """Return the raw mix chamber temperature."""
        return self._arr_mix[-1] * mK
        
    @setting(14, 'Raw Mix Temperature Pt1000', returns='v[K]')
    def raw_mix_temperature_pt1000(self, c):
        """
        Return the raw mix chamber temperature measured with the Pt1000
        thermometer.
        """
        return self._arr_mix_pt1000[-1] * K
        
    @setting(21, 'Still Temperature', returns='v[mK]')
    def still_temperature(self, c):
        """Return the still chamber temperature."""
        return self.filteredTemperature(self._arr_still, 1, 1.1e4) * mK

    @setting(22, 'Exchange Temperature', returns='v[mK]')
    def exchange_temperature(self, c):
        """Return the exchange chamber temperature."""
        return self.filteredTemperature(self._arr_exch, 1, 1.1e4) * mK
        
    @setting(23, 'Mix Temperature', returns='v[mK]')
    def mix_temperature(self, c):
        """Return the mix chamber temperature."""
        return self.filteredTemperature(self._arr_mix, 1, 1.1e4) * mK
        
    @setting(24, 'Mix Temperature Pt1000', returns='v[K]')
    def mix_temperature_pt1000(self, c):
        """
        Return the raw mix chamber temperature measured with the Pt1000
        thermometer.
        """
        return self.filteredTemperature(self._arr_mix_pt1000, 3, 400) * K


__server__ = LeidenDRPseudoserver()


if __name__ == '__main__':
    util.runServer(__server__)