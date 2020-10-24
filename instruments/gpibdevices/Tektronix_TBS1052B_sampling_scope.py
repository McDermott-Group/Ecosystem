# Date: 4th November 2019
# Author: Naveen Nehra
#
#...........Server details.........
#
# Module Type - Abstraction server
# Code organization - Divided into Query commands and Set commands

"""
### BEGIN NODE INFO
[info]
name = TBS1052B Sampling Scope
version = 1.0
description = Digital Oscillioscope

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 5
### END NODE INFO
"""

from labrad.server import LabradServer, setting
from twisted.internet.defer import inlineCallbacks, returnValue

from labrad.gpib import GPIBManagedServer


class TBS1052B(GPIBManagedServer):
    name = "TBS1052B Sampling Scope" #Server Name
    deviceName = ['TEKTRONIX TBS 1052B'] # String returned when equipment enquired with *IDN command

############################### Query commands ############################

    @setting(10, 'Get Instrument Name', returns='s')
    def getInstrumentName(self, c):
        """Return the instrument name."""
        dev = self.selectedDevice(c)
        instrumentName = yield dev.query('ID?')
        returnValue(instrumentName)

    @setting(11, 'Get Acquire Mode', returns='s')
    def getAcquireMode(self, c):
        """Returns the instrument acquire mode"""
        dev = self.selectedDevice(c)
        AcquireMode = yield dev.query('ACQuire:MODe?')
        returnValue(AcquireMode)



############################### Set commands ############################






############################### Get commands ############################   
        

__server__ = TBS1052B()

if __name__ == '__main__':
    from labrad import util
    util.runServer(__server__)