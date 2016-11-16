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

MIN_REFRESH_RATE = 1 * units.s
TIME_CONSTANT_MULTIPLIER = 15

class NRuoxServer(LabradServer):
    """
    Use a multiplexer to scroll through multiple channels and read many
    RuOx temps with the same AC bridge.  Note that the multiplexer
    channel must match the curve index in the AC Bridge.
    """
    name = 'AC Bridge with Multiplexer'
    allDeviceChans = {}    # { device addrs: {context: ctx, chan: temp, currentChan: i} }

    @inlineCallbacks
    def startTakingTemps(self, addrs):
        # if no chans, refresh once a second
        # if one chan, measure once a second
        # if more than one chan, switch, wait, measure, ...
        chanList = self.allDeviceChans[addrs].keys()
        chanList.remove('context')
        chanList.remove('currentChanIndex')
        chanList.remove('deviceAddresses')
        # If no chans, refresh
        if len( chanList ) < 1:
            callLater(MIN_REFRESH_RATE['s'],self.startTakingTemps,addrs)
            return
        # If chan index is out of range, reset to 0
        if self.allDeviceChans[addrs]['currentChanIndex'] >= len(chanList):
            self.allDeviceChans[addrs]['currentChanIndex'] = 0
        # Switch channel -> wait time const -> measure temp.
        index = self.allDeviceChans[addrs]['currentChanIndex']
        chan = chanList[index]
        ctx = self.allDeviceChans[addrs]['context']
        deviceAddresses = self.allDeviceChans[addrs]['deviceAddresses']
        MP = self.client[deviceAddresses[1][0]]
        ACB = self.client[deviceAddresses[0][0]]
        yield MP.channel(chan, context=ctx)
        yield ACB.set_curve(chan, context=ctx)
        t = yield ACB.get_time_constant(context=ctx)
        timeout = max(MIN_REFRESH_RATE['s'], TIME_CONSTANT_MULTIPLIER * t['s']) * units.s
        if len(chanList) > 1: yield util.wakeupCall(timeout['s'])
        else: yield util.wakeupCall(MIN_REFRESH_RATE['s'])
        temp = yield ACB.get_ruox_temperature(context=ctx)
        self.allDeviceChans[addrs][chan] = temp
        self.allDeviceChans[addrs]['currentChanIndex'] += 1
        callLater(0.1,self.startTakingTemps,addrs)

    @setting(101, 'Select Device', addrs='*2s')
    def select_device(self, c, addrs):
        """
        Set the device addresses. Input in form ['server_name',
        'gpib_addr'] for [ac bridge, multiplexer]. Once the devices are
        set, we can start a cycle with period timeconstant, switching
        between the channels and recording temperatures.
        """
        #only add if loop with same device is not already running
        address = str(addrs)
        if address not in self.allDeviceChans.keys():
            ctx = self.client.context()
            MP = self.client[addrs[1][0]]
            yield MP.select_device(addrs[1][1], context=ctx)
            ACB = self.client[addrs[0][0]]
            yield ACB.select_device(addrs[0][1], context=ctx)
            self.allDeviceChans[address] = {'context':ctx, \
                                            'currentChanIndex':0, \
                                            'deviceAddresses':addrs}
            callLater(0.1,self.startTakingTemps,address)
        c['address'] = address # just to identify the device pair

    @setting(102, 'Add Channel', chan='i')
    def add_channel(self, c, chan):
        """Add channel to measure."""
        if 'chans' not in c:
            c['chans'] = []
        if chan not in c['chans']:
            c['chans'].append(chan)
        devChans = self.allDeviceChans[c['address']]
        if chan not in devChans.keys():
            devChans[chan] = np.nan*units.K

    @setting(103, 'Remove Channel', chan='i')
    def remove_channel(self, c, chan):
        """No longer measure this channel."""
        try:
            c['chans'].remove(chan)
            # dont remove chan if it is also in use from another context
            allContexts = [self.contexts[key].data for key in self.contexts]
            alsoUsed = False
            for ctx in allContexts:
                if ctx['address'] == c['address'] and \
                   chan in ctx['chans']:
                    alsoUsed = True
            if not alsoUsed:
                devChans = self.allDeviceChans[c['address']]
                del devChans[chan]
        except ValueError:
            pass # if channel not already there ignore request

    @setting(104, 'Get Ruox Temperature', chan='i', returns='?')
    def get_ruox_temperature(self, c, chan=None):
        """Returns the temperature for the specified channel, or if no
        channel is specified, returns a list of [chan,temp] pairs."""
        tempDict = self.allDeviceChans[c['address']]
        if chan == None: # return [[chan, temp]]
            return [(key,tempDict[key]) for key in tempDict.keys() \
                                      if type(key) is not str \
                                      and key in c['chans']]
        else:
            return tempDict[chan]


__server__ = NRuoxServer()


if __name__ == '__main__':
    util.runServer(__server__)
