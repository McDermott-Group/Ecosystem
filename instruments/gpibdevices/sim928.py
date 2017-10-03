# Copyright (C) 2017 Alex Opremcak
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
# along with this program.  If not, see <http://www.gnu.org/licenses/>
  
"""
### BEGIN NODE INFO
[info]
name = SIM 928
version = 1.0.0
description = 
  
[startup]
cmdline = %PYTHON% %FILE%
timeout = 20
  
[shutdown]
message = 987654321
timeout = 5
### END NODE INFO
"""

from twisted.internet.defer import inlineCallbacks, returnValue

from labrad.server import setting
from labrad.gpib import GPIBManagedServer
from labrad import units

TC = "'end'" # Termination Character
LF = '\n' # Line Feed

class SIM928Server(GPIBManagedServer):
    name = 'SIM928_test'
    deviceName = 'STANFORD RESEARCH SYSTEMS SIM900'

    @inlineCallbacks   
    def write(self, c, slot_number, write_str):
        """A SIM specific write method."""
        dev = self.selectedDevice(c)
        yield dev.write("CONN "+str(slot_number)+","+TC+LF)
        yield dev.write("TERM LF"+LF)
        yield dev.write(write_str + LF)
        yield dev.write(TC)
        
    @inlineCallbacks   
    def query(self, c, slot_number, query_str):
        """A SIM specific query method."""
        dev = self.selectedDevice(c)
        yield dev.write("CONN "+str(slot_number)+","+TC+LF)
        yield dev.write("TERM LF"+LF)
        query_resp = yield dev.query(query_str + LF)
        yield dev.write(TC)
        returnValue(query_resp)

    def no_selection_msg(self, slot_number):
        err_msg = "You must first select a slot for the SIM 928."
        return err_msg
        
    def slot_not_found_msg(self, slot_number):
        err_msg = "A SIM 928 on slot # %s was not found." % slot_number
        return err_msg
        
    @setting(9, 'Find Sources', slot_number = 'i', returns = 'b')
    def find_source(self, c, slot_number):
        """Finds all slots with SIM 928s in them."""
        dev = self.selectedDevice(c)
        module_status = yield dev.query("CTCR?\n")
        module_status = '{0:b}'.format(int(module_status))[4:-1][::-1]
        module_status = [bool(int(char)) for char in module_status]
        for ii in range(0, len(module_status)):
            if slot_number == ii + 1:
                if module_status[ii]:
                    idn_str = yield self.query(c, slot_number, "*IDN?")
                    if 'SIM928' in idn_str:
                        returnValue(True)
        returnValue(False)

    @setting(10, 'Select Source', slot_number = 'i', returns = '')
    def select_source(self, c, slot_number):
        """Selects a SIM 928 within the SIM 900 Mainframe."""
        source_found = yield self.find_source(c, slot_number)
        if source_found:
            c['slot_number'] = slot_number
        else:
            raise ValueError(self.slot_not_found_msg(slot_number))

    @setting(11, 'Get Voltage', returns = 'v[V]')
    def get_voltage(self, c):
        """Gets SIM 928 voltage for the selected slot number."""
        if 'slot_number' in c.keys():
            slot_number = c['slot_number']
            voltage = yield self.query(c, slot_number, "VOLT?")
            voltage = float(voltage)
        else:
            raise ValueError(self.no_selection_msg())
           
        returnValue(voltage * units.V)
        
    @setting(12, 'Set Voltage',
             voltage = 'v[V]', returns = '')
    def set_voltage(self, c, voltage):
        """Sets SIM 928 voltage for the selected slot number."""
        if 'slot_number' in c.keys():
            slot_number = c['slot_number']
            output_state = yield self.get_output_state(c)
            if not output_state:
                yield self.set_output_state(c, True)
            write_str = "VOLT "+ str(voltage['V'])
            yield self.write(c, slot_number, write_str)
        else:
            raise ValueError(self.no_selection_msg())

    @setting(13, 'Get Output State', returns = 'b')
    def get_output_state(self, c):
        """Gets SIM 928 voltage output state 
           for the selected slot number."""
        if 'slot_number' in c.keys():
            slot_number = c['slot_number']
            output_state = yield self.query(c, slot_number, "EXON?")
            output_state = bool(int(output_state))
        else:
            raise ValueError(self.no_selection_msg())
        returnValue(output_state)    

    @setting(14, 'Set Output State',
             output_on = 'b', returns = '')
    def set_output_state(self, c, output_on):
        """Sets SIM 928 voltage output state for 
           the selected slot number."""
        if 'slot_number' in c.keys():
            slot_number = c['slot_number']
            if output_on:
                output_state = yield self.write(c, slot_number, "OPON")
            else:
                output_state = yield self.write(c, slot_number, "OPOF")
        else:
            raise ValueError(self.no_selection_msg())      

__server__ = SIM928Server()
  
if __name__ == '__main__':
    from labrad import util
    util.runServer(__server__)
    
##### EXAMPLE #####
#   import labrad
#   from labrad import units
#   cxn = labrad.connect()
#   v1 = cxn.sim928
#   v1.select_device(0) # this argument depends on gpib address
#   v1.select_source(1) # slot number for chose mainframe
#   v1.set_voltage(0.5 * units.V)
#   v1.get_voltage() # returns 0.5 * V
#   v1.get_output_state() #True, turned on by default if voltage is set
#   v1.set_output_state(False)
#   v2 = cxn.sim928
#   v2.select_device(0)
#   v2.select_device(2) # chose another source with different slot num

