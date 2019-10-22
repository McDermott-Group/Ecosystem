"""
### BEGIN NODE INFO
[info]
name = AVS47 Resistance Bridge
version = 1.0.0
description = Monitors DR temperatures

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
"""

import os
import sys
import time
# The LoopingCall function allows a function to be called periodically
# on a time interval.
from twisted.internet.task import LoopingCall
from twisted.internet.reactor import callLater
from twisted.internet.defer import inlineCallbacks, returnValue

from labrad.devices import DeviceServer, DeviceWrapper
from labrad.server import setting
from numpy import log10
import labrad.units as units
from labrad import util
import socket

if __file__ in [f for f in os.listdir('.') if os.path.isfile(f)]:
    SCRIPT_PATH = os.path.dirname(os.getcwd())
else:
    SCRIPT_PATH = os.path.dirname(__file__)
LOCAL_PATH = SCRIPT_PATH.rsplit('instruments', 1)[0]
INSTRUMENTS_PATH = os.path.join(LOCAL_PATH, 'instruments')
if INSTRUMENTS_PATH not in sys.path:
    sys.path.append(INSTRUMENTS_PATH)

from utilities.gpib_device_wrapper import ReadRawGPIBDeviceWrapper
from utilities.sleep import sleep


class AVS47ResistanceBridgeWrapper(DeviceWrapper):

    @inlineCallbacks
    def connect(self, server, port):
        print('Connecting to "%s" on port "%s"...' %(server.name, port))
        self.server = server
        self.ctx = server.context()
        self.port = port
        p = self.packet()
        p.open(port)
        p.baudrate(9600L)
        p.stopbits(1L)
        p.bytesize(8L)
        p.parity('N')
        p.rts(False)
        p.dtr(False)
        p.timeout(5 * units.s)
        p.read_line()
        yield p.send()
    
    def packet(self):
        return self.server.packet(context=self.ctx)
    
    def shutdown(self):
        return self.packet().close().send()
     
    @inlineCallbacks
    def write_line(self, code):
        yield self.server.write_line(code, context=self.ctx)
        
    @inlineCallbacks    
    def read_line(self):
        ans = yield self.server.read(context = self.ctx)
        returnValue(ans)
        
        
class AVS47ResistanceBridgeServer(DeviceServer):
    deviceName = 'AVS47 Resistance Bridge'
    name = 'AVS47 Resistance Bridge'
    deviceWrapper = AVS47ResistanceBridgeWrapper
    
    @inlineCallbacks
    def initServer(self):
        print('Server initializing...')
        self.reg = self.client.registry()
        yield self.loadSensorInfo()
        # default excitation and range: 30uV, 20kOhm
        self.excitation = "3"
        self.excitation_values = ['0V', '3uV', '10uV', '30uV', '100uV', '300uV', '1mV', '3mV']
        self.range = "5"
        self.range_values = ['2 Ohm', '20 Ohm', '200 Ohm', '2 kOhm', '20 kOhm', '200 kOhm', '2 MOhm']
        yield self.loadConfigInfo()
        yield self.loadCalibrationInfo()
        yield DeviceServer.initServer(self)
        print self.sensors
   
    @setting(901, 'Get Temperatures', returns='b')
    def getTemperatures(self, c):
    
        self.dev = self.selectedDevice(c)
        temperatures = []
        for i in range(0, 8):
        
            # GET RESISTANCE FROM BRIDGE
            self.dev.write_line("inp1;mux%s;ran%s;exc%s"%(str(i), self.range, self.excitation))
            yield sleep(.1)
            self.dev.write_line("res?")
            yield sleep(.1)
            reading = yield self.dev.read_line()
            reading = reading.rstrip("\r\n")
            print reading
            reading = float(reading)
            
            # GET CALIBRATION FROM FILE
            cal_array = []
            filename = self.calibrations[i]
            if filename != 'NONE':
                file = open(('avs47_calibrations/' + filename), "r")
                index = 1
                exponent = 0.0
                result = 0.0
                
                for line in file:
                    cal_array.insert(0, float(line.strip('\n')))
                
                # CONVERT RESISTANCE TO TEMPERATURE WITH CALIBRATION
                exponent += cal_array.pop()
                while (len(cal_array) != 0):
                    exponent += cal_array.pop() * (log10(reading) ** index)
                    index += 1
               
                result = 10 ** exponent
                temperatures.append(result)
               
            else:
                temperatures.append(0.0)
        
        print temperatures
        returnValue(True)
            
           
    
    @setting(9, 'Start Server', returns='b')
    def startServer(self, c):
        self.dev = self.selectedDevice(c)
        callLater(0.1, self.startRefreshing)
        return True
        
    @setting(10, 'Identify', returns='s')
    def identify(self, c):
        self.dev = self.selectedDevice(c)
        yield self.dev.write_line("*IDN?")
        yield sleep(0.5)
        reading = yield self.dev.read_line()
        reading = yield str(reading.rstrip("\r\n"))
        returnValue(reading)
     
    @setting(11, 'Get Resistances', returns='*v[Ohm]')
    def getResistances(self, c):
        self.dev = self.selectedDevice(c)
        resistances = []
        for i in range(0, 8):
            self.dev.write_line("inp1;mux%s;ran%s;exc%s"%(str(i), self.range, self.excitation))
            yield sleep(.1)
            self.dev.write_line("res?")
            yield sleep(.1)
            reading = yield self.dev.read_line()
            reading = reading.rstrip("\r\n")
            reading = float(reading) * units.Ohm
            resistances.append(reading)
        returnValue(resistances)
        
    @setting(12, 'Set Range', returns='s')
    def setRange(self, c, range):
        """Set range for output values. 
        1..7 = ranges from 2 ohm to 2 Mohm
        """
        if (range > 7 or range < 1):
            return 'Invalid Range\n1..7 = ranges from 2 ohms to 2 Mohms'
        else:
            self.range = range
            return 'Range set to ' + str(self.range_values[range])
            
    @setting(13, 'Set Excitation', returns='s')
    def setExcitation(self, c, excitation):
        """Excitation = the RMS voltage
        across a sensor whose value is half of the selected
        range. Excitation is symmetrical square
        wave -shaped current at about 13.7Hz.
        0 = no excitation
        1..7 = 3uV, 10u, 30uV...3mV"""
        if (excitation > 7 or excitation < 0):
            return 'Invalid excitation\n0 = no excitation\n1..7 = 3uV, 10uV, 30uV...3mV'
        else:
            self.excitation = excitation
            return 'Excitation set to ' + str(self.excitation_values[excitation])  
        
    @inlineCallbacks
    def loadConfigInfo(self):
        """Load configuration information from the registry."""
        reg = self.reg
        yield reg.cd(['', 'Servers', 'AVS47 Resistance Bridge', 'Links'], True)
        dirs, keys = yield reg.dir()
        p = reg.packet()
        for k in keys:
            p.get(k, key=k)
        ans = yield p.send()
        self.serialLinks = dict((k, ans[k]) for k in keys) 
        
    @inlineCallbacks
    def loadCalibrationInfo(self):
        """Load calibration information from the registry."""
        reg = self.reg
        yield reg.cd(['', 'Servers', 'AVS47 Resistance Bridge', 'Calibrations'], True)
        dirs, keys = yield reg.dir()
        p = reg.packet()
        for k in keys:
            p.get(k, key=k)
        ans = yield p.send()
        self.calibrations = ans[keys[0]]
        print self.calibrations        
        
    @inlineCallbacks
    def loadSensorInfo(self):
        reg = yield self.reg
        dir = yield reg.dir()
        print dir
        yield reg.cd(['', 'Servers', 'AVS47 Resistance Bridge'])
        yield reg.cd(['Sensors'])
        data = yield reg.get('dip1')
        print data
        dirs, keys = yield reg.dir()
        p = yield reg.packet()
        key = None
        for k in keys:
            if k == socket.gethostname():
                key = k
        
        if key is not None:
            p.get(key, key=key)
            ans = yield p.send()
            self.sensors = ans[key]
        
    @inlineCallbacks    
    def findDevices(self):
        """Find available devices from a list stored in the registry."""
        devs = []
        for name, (server, port) in self.serialLinks.items():
            if server not in self.client.servers:
                continue
            server = self.client[server]
            ports = yield server.list_serial_ports()
            if port not in ports:
                continue
            devName = '{} - {}'.format(server, port)
            devs += [(name, (server, port))]
        returnValue(devs)

    def startRefreshing(self):
        """
        Start periodically refreshing the list of devices.
        The start call returns a deferred which we save for later.
        When the refresh loop is shutdown, we will wait for this
        deferred to fire to indicate that it has terminated.
        """
        self.refresher = LoopingCall(self.checkMeasurements)
        self.refresherDone = self.refresher.start(5.0, now=True)    
        
__server__ = AVS47ResistanceBridgeServer()


if __name__ == '__main__':
    util.runServer(__server__)