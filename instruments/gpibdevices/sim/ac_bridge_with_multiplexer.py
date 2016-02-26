# Copyright (C) 2015 Chris Wilen
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
name = AC Bridge with Multiplexer
version = 2.2.1
description = Uses the SIM multiplexer and AC bridge to read out multiple RuOx thermometers at once.

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 5
### END NODE INFO
"""

from labrad.server import setting, LabradServer
from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.internet.reactor import callLater
from twisted.internet import threads as twistedThreads
from labrad import units, util
import numpy as np

MIN_REFRESH_RATE = 2 * units.s

class NRuoxServer(LabradServer):
    """
    Use a multiplexer to scroll through multiple channels and read many
    RuOx temps with the same AC bridge.
    """
    name = 'AC Bridge with Multiplexer'
                
    @inlineCallbacks
    def startTakingTemps(self, c):
        if 'currentChan' not in c:
            c['currentChan'] = 0
        chans = c['chans'].keys()
        if len(chans) == 0: 
            # To not take up too many resources if no channels are
            # selected.
            callLater(MIN_REFRESH_RATE['s'],self.startTakingTemps,c)
            return
        # Switch channel -> wait time const -> measure temp.
        if c['currentChan'] >= len(chans): # if we have gone to end of list
            c['currentChan'] = 0
        chan = chans[c['currentChan']]
        yield c['MP'].channel(chan)
        yield c['ACB'].set_curve(chan)
        t = yield c['ACB'].get_time_constant()
        timeout = max(MIN_REFRESH_RATE['s'], 3 * t['s']) * units.s
        yield util.wakeupCall(timeout['s'])
        c['chans'][chan] = yield c['ACB'].get_ruox_temperature()
        c['currentChan'] += 1
        callLater(0.1,self.startTakingTemps,c)
    
    @setting(101, 'Select Device', addrs='*2s')
    def select_device(self, c, addrs):
        """
        Set the device addresses. Input in form ['server_name',
        'gpib_addr'] for [ac bridge, multiplexer]. Once the devices are
        set, we can start a cycle with period timeconstant, switching
        between the channels and recording temperatures.
        """
        c['MP'] = self.client[addrs[1][0]]
        yield c['MP'].select_device(addrs[1][1])
        c['ACB'] = self.client[addrs[0][0]]
        yield c['ACB'].select_device(addrs[0][1])
        if 'chans' not in c:
            c['chans'] = {}
        callLater(0.1,self.startTakingTemps,c)

    @setting(102, 'Add Channel', chan='i')
    def add_channel(self, c, chan):
        """Add channel to measure."""
        if 'chans' not in c:
            c['chans'] = {}
        if chan not in c['chans']:
            c['chans'][chan] = np.nan * units.K
    
    @setting(103, 'Remove Channel', chan='i')
    def remove_channel(self, c, chan):
        """No longer measure this channel."""
        try:
            del c['chans'][chan]
        except KeyError:
            pass
        
    @setting(104, 'Get Ruox Temperature', chan='i', returns='?')
    def get_ruox_temperature(self, c, chan=None):
        if chan == None:
            return [c['chans'][chan] for chan in c['chans']] 
        else:
            return c['chans'][chan]


__server__ = NRuoxServer()


if __name__ == '__main__':
    util.runServer(__server__)