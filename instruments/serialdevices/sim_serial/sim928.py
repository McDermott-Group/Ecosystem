# this is the worst server don't use this unless you're brad
# this server does NOT:
# a) have good user-error checking
# b) utilise the serial bus server

"""
### BEGIN NODE INFO
[info]
name = SIM928_serial
version = 1.1.0
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
from labrad.devices import DeviceWrapper, DeviceServer
from labrad import units
from exceptions import ValueError
from time import sleep
import visa
from socket import gethostname

TC = "\"xyz\"" # Termination Character
LF = '\r' # Line Feed

class SIM928Wrapper(DeviceWrapper):

    @inlineCallbacks
    def connect(self, server, port):
        print('Connecting to "%s" on port "%s"...' %(server.name, port))
        self.server = server
        self.ctx = server.context()
        self.port = port
        self.rm = visa.ResourceManager()
        p = self.packet()
        self.s = self.rm.open_resource(self.port)
        # p.open(port)
        # p.baudrate(9600L)
        # p.stopbits(1L)
        # p.bytesize(8L)
        # p.parity('N')
        # p.rts(False)
        # p.dtr(False)
        # p.timeout(5 * units.s)
        # p.read_line()
        # yield p.send()
        yield p.send()
    
    def packet(self):
        return self.server.packet(context=self.ctx)
    
    def shutdown(self):
        return self.packet().close().send()
     
    @inlineCallbacks
    def write_line(self, code):
        yield self.s.write(code)
        # yield self.server.write_line(code, context=self.ctx)
        
    @inlineCallbacks    
    def read_line(self):
        ans = yield self.s.read()
        returnValue(ans)

        
class SIM928Server(DeviceServer):
    name = 'sim928_serial'
    deviceName = 'Stanford Research Systems SIM900'
    deviceWrapper = SIM928Wrapper   
    
    @inlineCallbacks
    def initServer(self):
        print('Server initializing...')
        self.reg = self.client.registry()
        # default excitation and range: 30uV, 20kOhm
        yield self.loadConfigInfo()
        yield DeviceServer.initServer(self)
        
    @inlineCallbacks
    def loadConfigInfo(self):
        """Load configuration information from the registry."""
        reg = self.reg
        yield reg.cd(['', 'Servers', 'SIM900 Serial', 'links'], True)
        dirs, keys = yield reg.dir()
        p = reg.packet()
        for k in keys:
            p.get(k, key=k)
        ans = yield p.send()
        b = 0
        hostname = gethostname()
        for ss in ans['Serial Links']:
            if ss[0] == hostname + ' Serial Server':
                self.serialLinks = {ss[0]:ss[1]}
        # self.serialLinks = dict((ans[k][0][0], ans[k][0][1]) for k in keys) 
        print self.serialLinks
        
    @inlineCallbacks    
    def findDevices(self):
        """Find available devices from list stored in the registry."""
        devs = []
        for name in self.serialLinks:
            port = self.serialLinks[name]
            if name not in self.client.servers:
                continue
            server = self.client[name]
            ports = yield server.list_serial_ports()
            print ports
            if port not in ports:
                continue
            devName = '%s - %s' % (name, port)
            devs += [(devName, (server, port))]
        returnValue(devs)
    
    @inlineCallbacks
    def open_comm(self, c, slot_number):
        dev = self.selectedDevice(c)
        yield dev.write_line("CONN " + str(slot_number) + "," +"\"xyz\"")
    
    @inlineCallbacks
    def close_comm(self, c, slot_number):
        dev = self.selectedDevice(c)
        yield dev.write_line('xyz')
        
    @inlineCallbacks   
    def write(self, c, write_str):
        """A write method that addresses a particular slot
           in the SIM 900 mainframe. Connection with the
           instrument (slot) is closed after the message
           is sent."""
        dev = self.selectedDevice(c)
        yield dev.write_line(write_str)
        
    @inlineCallbacks
    def read(self, c):
        dev = self.selectedDevice(c)
        ans = yield dev.read_line()
        returnValue(ans)
        
    @inlineCallbacks   
    def query(self, c, slot_number, query_str):
        """A query method that addresses a particular slot
           in the SIM 900 mainframe. Connection with the
           instrument (slot) is closed after the query is
           finished."""
        dev = self.selectedDevice(c)
        #yield dev.write_line("TERM LF"+LF)
        yield dev.write_line(query_str)
        query_resp = yield dev.read_line()
        returnValue(query_resp)

    def no_selection_msg(self):
        err_msg = "You must first select a slot for the SIM 928."
        return err_msg
        
    def slot_not_found_msg(self, slot_number):
        err_msg = "A SIM 928 on slot # %s was not found." % slot_number
        return err_msg
      
    @inlineCallbacks
    def wait_for_completion(self, c):
        yield None
        # dev = self.selectedDevice(c)
        # yield self.write(c, "*OPC")
        # op_completed = False
        # while op_completed == False:
            # yield self.write(c, "*ESR?[0]")
            # esr = yield self.read(c)
            # op_completed = (1 == esr)
            # yield sleep(0.05)
        
    @setting(8, 'Initialize Mainframe', returns = 'b')
    def initialize_mainframe(self, c):
        """Mainframe initialization method used for resetting
           the SIM 900 once it goes into an error state."""
        dev = self.selectedDevice(c)
        yield dev.write_line("*RST\n")
        self.wait_for_completion(c)
        yield dev.write_line("VERB 127\n")
        self.wait_for_completion(c)
        yield dev.write_line("CEOI ON\n")
        self.wait_for_completion(c)
        yield dev.write_line("EOIX ON\n")
        self.wait_for_completion(c)
        yield dev.write_line("TERM D,LF\n")
        self.wait_for_completion(c)
        
        for ii in range(0, 12):
            yield dev.write_line("BAUD "+str(ii)+",9600\n")
            self.wait_for_completion(c)
        
        yield dev.write_line("FLSH\n")
        self.wait_for_completion(c)
        yield dev.write_line("SRST\n")
        self.wait_for_completion(c)
        returnValue(True)
        
    @setting(9, 'Find Source', slot_number = 'i', returns = 'b')
    def find_source(self, c, slot_number):
        """Determines if a SIM 928 voltage source with the
           specified slot_number is present in the mainframe."""
        dev = self.selectedDevice(c)
        ctcr_string = "CTCR? " + str(slot_number)
        yield self.write(c, ctcr_string)
        module_status = yield self.read(c)
        if module_status[0] == '1':
            returnValue( True )
        else:
            returnValue( False )
            
        # module_status = '{0:b}'.format(int(module_status))[4:-1][::-1]
        # module_status = [bool(int(char)) for char in module_status]
        # for ii in range(0, len(module_status)):
            # if slot_number == ii + 1:
                # if module_status[ii]:
                    # try:
                        # idn_str = yield self.query(c, 
                                                   # slot_number,
                                                   # "*IDN?")
                        # self.wait_for_completion(c)
                    # except:
                        # self.initialize_mainframe(c)
                        # idn_str = yield self.query(c, 
                                                   # slot_number,
                                                   # "*IDN?")
                        # self.wait_for_completion(c)
                    # if 'SIM928' in idn_str:
                        # returnValue(True)
        # returnValue(True)

    @setting(10, 'Select Source', slot_number = 'i', returns = '')
    def select_source(self, c, slot_number):
        """Selects the SIM 928 voltage source you intend to
           communicate with."""
        source_found = yield self.find_source(c, slot_number)
        if source_found:
            c['slot_number'] = slot_number
        else:
           raise ValueError(self.slot_not_found_msg(slot_number))

    @setting(11, 'Get Voltage', returns = 'v[V]')
    def get_voltage(self, c):
        """Gets the SIM 928 voltage output value from the
           selected source."""
        if 'slot_number' in c.keys():
            slot_number = c['slot_number']            
            yield self.open_comm(c, slot_number)
            yield self.write(c, 'VOLT?')
            voltage = yield self.read(c)
            yield self.close_comm(c, slot_number)
            
            try:
                voltage = float(voltage)
            except(ValueError):
                old_voltage = voltage
                voltage = ''.join([i for i in voltage if (i.isdigit() or i == '-' or i == '.')])
                voltage = float(voltage)
                print ('The value ' + old_voltage + ' was returned by the SIM928, this value was automatically converted to ' + voltage + '.')
                        
            value = voltage * units.V
            
            # try:
                # voltage = yield self.query(c,
                                           # slot_number, 
                                           # "VOLT?")
                # try:
                    # voltage = float(voltage)
                # except:
                    # self.initialize_mainframe(c)
                    # voltage = yield self.query(c,
                                               # slot_number,
                                               # "VOLT?")
                    # voltage = float(voltage)
            # except:
                # self.initialize_mainframe(c)
                # voltage = yield self.query(c,
                                           # slot_number,
                                           # "VOLT?")
                # try:
                    # voltage = float(voltage)
                # except:
                    # self.initialize_mainframe(c)
                    # voltage = yield self.query(c,
                                               # slot_number,
                                               # "VOLT?")
                    # voltage = float(voltage)
            # try:
                # value = voltage * units.V
            # except:
                # self.initialize_mainframe(c)
                # voltage = yield self.query(c,
                                           # slot_number,
                                           # "VOLT?")
                # voltage = float(voltage)
                # value = voltage * units.V
        # else:
            # raise ValueError(self.no_selection_msg())
        returnValue(value)
        
    @setting(12, 'Get Slot', returns = 'i')
    def get_slot(self, c):
        """Gets the slot_number of the selected SIM 928 source."""
        if 'slot_number' in c.keys():
            slot_number = c['slot_number']
            return slot_number
        else:
            raise ValueError(self.no_selection_msg())
           
        # returnValue(voltage * units.V)
        
    @setting(13, 'Set Voltage',
             voltage = 'v[V]', returns = '')
    def set_voltage(self, c, voltage):
        """Sets SIM 928 voltage for the selected source."""
        if abs(voltage['V']) < (.00001):
            voltage = 0 * units.V
            
        dev = self.selectedDevice(c)
        if 'slot_number' in c.keys():
            slot_number = c['slot_number']
            self.open_comm(c, slot_number)
            output_state = yield self.get_output_state(c)
            if not output_state:
                try:
                    yield self.set_output_state(c, True)
                except:
                    self.initialize_mainframe(c)
                    yield self.set_output_state(c, True)
            write_str = "VOLT "+ str(voltage['V'])
            try:
                yield self.write(c, write_str)
                self.wait_for_completion(c)
            except:
                self.initialize_mainframe(c)
                yield self.write(c, write_str)
                self.wait_for_completion(c)
            self.close_comm(c, slot_number)
        else:
            raise ValueError(self.no_selection_msg())

    @setting(14, 'Get Output State', returns = 'b')
    def get_output_state(self, c):
        """Gets SIM 928 voltage output state 
           for the selected slot number."""
        if 'slot_number' in c.keys():
            slot_number = c['slot_number']
            if 'output_state' not in c.keys():
                try:
                    output_state = yield self.query(c,
                                                    slot_number,
                                                    "EXON?")
                    self.wait_for_completion(c)
                    output_state = bool(int(output_state))
                    c['output_state'] = output_state  
                except:
                    #self.initialize_mainframe(c)
                    output_state = yield self.query(c,
                                                    slot_number,
                                                    "EXON?")
                    self.wait_for_completion(c)
                    output_state = bool(int(output_state))
                    c['output_state'] = output_state  
        else:
            raise ValueError(self.no_selection_msg())
        returnValue(c['output_state'] )    

    @setting(15, 'Set Output State',
             output_on = 'b', returns = '')
    def set_output_state(self, c, output_on):
        """Sets SIM 928 voltage output state for 
           the selected slot number."""
        if 'slot_number' in c.keys():
            slot_number = c['slot_number']
            if output_on:
                try:
                    output_state = yield self.write(c, "OPON")
                    self.wait_for_completion(c)
                    c['output_state'] = True
                except:
                    self.initialize_mainframe(c)
                    output_state = yield self.write(c, "OPON")
                    self.wait_for_completion(c)
                    c['output_state'] = True
            else:
                try:
                    output_state = yield self.write(c, "OPOF")
                    self.wait_for_completion(c)
                    c['output_state'] = False
                except:
                    self.initialize_mainframe(c)
                    output_state = yield self.write(c, "OPOF")
                    self.wait_for_completion(c)
                    c['output_state'] = False
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

