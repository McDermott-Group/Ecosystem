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


# This server can be connected to by adr_client.py or other LabRAD
# clients to control the ADR with a GUI, etc.
# Important note: the registry setting in ADRSettings for "Ruox
# Temperature Monitor" specifies the servers that should be run in
# order to record the temperatures. To turn the GGG monitoring on/off,
# swap the values of the "Ruox Temperature Monitor (with GGG)" and "Ruox
# Temperature Monitor (without GGG)" into "Ruox Temperature Monitor".

ADR_SETTINGS_BASE_PATH = ['','ADR Settings'] # path in registry
DEFAULT_ADR = 'ADR3' # name of ADR in registry
AVAILABLE_ADRS = ['ADR1','ADR2','ADR3']

import numpy
import datetime, struct
from labrad.server import (LabradServer, setting,
                           inlineCallbacks, returnValue)
from labrad.devices import DeviceServer
from labrad import util, units
from labrad.types import Error as LRError
from pyvisa.errors import VisaIOError
from dataChest import dataChest
from dateStamp import dateStamp
import sys, os
import json
from twisted.web.static import File
from twisted.python import log
from twisted.web.server import Site
from twisted.internet import ssl, reactor

from autobahn.twisted.websocket import WebSocketServerFactory, \
    WebSocketServerProtocol, listenWS

from autobahn.twisted.resource import WebSocketResource


def deltaT(dT):
    """
    .total_seconds() is only supported by >py27 :(, so we use this
    to subtract two datetime objects.
    """
    try:
        return dT.total_seconds()
    except:
        return dT.days * 86400 + dT.seconds + dT.microseconds * pow(10,-6)

class NumpyEncoder(json.JSONEncoder):
    """ Special json encoder for numpy types.  Otherwise it fails with float16, etc. """
    def default(self, obj):
        if isinstance(obj, (numpy.int_, numpy.intc, numpy.intp, numpy.int8,
            numpy.int16, numpy.int32, numpy.int64, numpy.uint8,
            numpy.uint16,numpy.uint32, numpy.uint64)):
            return int(obj)
        elif isinstance(obj, (numpy.float_, numpy.float16, numpy.float32, 
            numpy.float64)):
            return float(obj)
        return json.JSONEncoder.default(self, obj)

class MyServerProtocol(WebSocketServerProtocol):
    def onOpen(self):
        self.adrServer = self.factory.register(self)
        print('new connection')
        # probably only need to get the last 30 log messages
        backLogs = self.adrServer.getLog(None,30)
        # initial values
        state = self.adrServer.state
        text = json.dumps({
            'temps': {
                'timeStamps':[deltaT(state['datetime']-datetime.datetime(1970,1,1))],
                't60K': [state['T_60K']['K']],
                't03K': [state['T_3K']['K']],
                'tGGG': [state['T_GGG']['K']],
                'tFAA': [state['T_FAA']['K']]
            },
            'instruments': { name:{'server':status[0],
                                    'connected':status[1] }
                                for (name,status) in self.adrServer.getInstrumentState('bla')},
            'compressorOn':state['CompressorStatus'],
            'pressure': state['Pressure']['torr'],
            'isMaggingUp': state['maggingUp'],
            'isRegulating': state['regulating'],
            'backEMF': state['magnetV']['V'],
            'PSCurrent': state['PSCurrent']['A'],
            'PSVoltage': state['PSVoltage']['V'],
            'log':[{
                'datetime':deltaT(log[0]-datetime.datetime(1970,1,1)),
                'message':log[1],
                'alert':log[2]} for log in backLogs]
        }, cls=NumpyEncoder)
        text = text.replace('NaN','null') # apparently JSON does not support nan
        self.sendMessage(text)

    def connectionLost(self, reason):
        self.factory.unregister(self)
        print('connection lost')

    def onMessage(self, payload, isBinary):
        message = json.loads(payload)
        print(message)
        if   message['command'] == 'Open Heat Switch':
            self.adrServer.openHeatSwitch(None)
        elif message['command'] == 'Close Heat Switch':
            self.adrServer.closeHeatSwitch(None)
        elif message['command'] == 'Mag Up':
            self.adrServer._magUp()
        elif message['command'] == 'Stop Magging Up':
            self.adrServer._cancelMagUp()
        elif message['command'] == 'Regulate':
            try:
                temp = float(message['temp'])
                self.adrServer._regulate(temp)
            except:
                self.adrServer.logMessage('Could not convert input to temperature.',alert=True)
        elif message['command'] == 'Stop Regulating':
            self.adrServer._cancelRegulate()
        elif message['command'] == 'Set Compressor State':
            if message['on']: self.adrServer.startCompressor(None)
            else: self.adrServer.stopCompressor(None)
        elif message['command'] == 'Refresh Instruments':
            self.adrServer.refreshInstruments(None)
        elif message['command'] == 'Add To Log':
            if message['text'] is not None:
                self.adrServer.logMessage(message['text'])
        elif message['command'] == 'Get Temperature Data':
            if message['minutes'] is not None:
                m = int(message['minutes'])
                n = self.adrServer.tempDataChest.getNumRows()
                tempData = self.adrServer.tempDataChest.getData(max(0,n-m*60), None)
                now = deltaT(datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1))
                tempData = [line for line in tempData if line[0] > now-m*60]
                # add blank data so if we restart server, there will not be a
                # big ugly line on the graph where we have a break in time
                timestamp = deltaT(datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1))
                nanRow = [[timestamp] + [numpy.float16(numpy.NaN)]*4]
                tempData = nanRow + tempData + nanRow
                tempData = numpy.array(tempData)
                tempData = tempData.transpose()
                tempData = tempData.tolist()
                text = json.dumps({
                    'temps': {
                        'timeStamps': tempData[0],
                        't60K': tempData[1],
                        't03K': tempData[2],
                        'tGGG': tempData[3],
                        'tFAA': tempData[4]
                    }
                }, cls=NumpyEncoder)
                text = text.replace('NaN','null') # apparently JSON does not support nan
                self.sendMessage(text)


class MyFactory(WebSocketServerFactory):
    def __init__(self, *args, **kwargs):
        self.adrServer = kwargs['adrServer']
        del kwargs['adrServer']
        super(MyFactory, self).__init__(*args, **kwargs)
        self.clients = {}

    def register(self, client):
        self.clients[client.peer] = client
        return self.adrServer

    def unregister(self, client):
        self.clients.pop(client.peer)

    def sendMessageToAll(self, message):
        text = json.dumps(message, cls=NumpyEncoder)
        text = text.replace('NaN','null') # apparently JSON does not support nan
        for c in self.clients.keys():
            self.clients[c].sendMessage(text)


class ADRServer(DeviceServer):
    """
    Provide a way to control all the instruments that control
    our ADRs.
    """
    name = 'ADR Server'
    deviceName = 'ADR'
    # We no longer use signals.  That way if this server is turned on
    # and off, named_messages still get to clients.
    # This is an example of a signal, however:
    # stateChanged = Signal(1001, 'signal:state_changed', 's')

    def __init__(self, args):
        DeviceServer.__init__(self)
        self.ADRSettingsPath = ADR_SETTINGS_BASE_PATH
        selectedADR = DEFAULT_ADR
        if '-a' in args:    # Use -a to specify ADR
            index = args.index('-a')
            args.pop(index)
            # If we do not pop these off, twisted will complain because
            # this is not an allowed argument.
            selection = str( args.pop(index) )
            if selection in AVAILABLE_ADRS:
                selectedADR = selection
            else:
                print('%s is not a valid ADR selection.' %selection)
        self.ADRSettingsPath.append(selectedADR)
        self.name = selectedADR
        self.deviceName = selectedADR
        print('%s selected.' %selectedADR)
        self.alive = True # to turn off the update state look when server is closed
        self.state = {
                'T_FAA': numpy.NaN * units.K,
                'T_GGG': numpy.NaN * units.K,
                'T_3K' : numpy.NaN * units.K,
                'T_60K': numpy.NaN * units.K,
                'Pressure': numpy.NaN * units.torr,
                'datetime' : datetime.datetime.utcnow(),
                'cycle': 0,
                'magnetV': numpy.NaN * units.V,
                'RuOxChan': 'FAA',
                'RuOxChanSetTime': datetime.datetime.utcnow(),
                'PSCurrent': numpy.NaN * units.A,
                'PSVoltage': numpy.NaN * units.V,
                'maggingUp': False,
                'regulating': False,
                'regulationTemp': 0.1,
                'PID_cumulativeError': 0
        }
        self.lastState = self.state.copy()
        # These are defaults.  They can be overridden in the registry by
        # including a setting with the same name.
        self.ADRSettings = {
                'PID_KP': 0.75,
                'PID_KI': 0,
                'PID_KD': 15,
                'PID_MaxI': 1,
                'magup_dV': 0.003,                #[V/step] How much do we increase the voltage by every second when maggin up? HPD Manual uses 10mV=0.01V, 2.5V/30min=1.4mV/s ==> Let's use a middle rate of 3mV/step. (1 step is about 1s)
                'magnet_voltage_limit': 0.1,      #Back EMF limit in Volts
                'current_limit': 9,               #Max Current in Amps
                'voltage_limit': 2,               #Max Voltage in Volts.  At 9A, we usually get about 2.5-2.7V or 1.69V (with or without the external diode protection box), so this shouldn't need to be more than 3 or 2
                'dVdT_limit': 0.008,              #Keep dV/dt to under this value [V/s]
                'dIdt_magup_limit': 9. / (30*60), #limit on the rate at which we allow current to increase in amps/s (we want 9A over 30 min)
                'dIdt_regulate_limit': 9./(40*60),#limit on the rate at which we allow current to change in amps/s (we want 9A over 40 min)
                'step_length': 1.0,               #How long is each regulation/mag up cycle in seconds.  **Never set this less than 1.0sec.**  The SRS SIM922 only measures once a second and this would cause runaway voltages/currents.
                'magnet_max_temp': 5,
                'FAA MP Chan': 2,
                'GGG MP Chan': 1,
                'Power Supply':['Agilent 6641A PS','addr'],
                'Ruox Temperature Monitor':['SIM921','addr'], #['AC Bridge with Multiplexer',[['SIM921 Server','addr'],['SIM925 Server','addr']]],
                'Diode Temperature Monitor':['SIM922','addr'],
                'Magnet Voltage Monitor':['SIM922','addr'],
                'Heat Switch':['Heat Switch','addr'],
                'Compressor':['CP2800 Compressor','addr'],
                'Pressure Guage':['Varian Guage Controller','addr'],
                'Log Path': ["fridgeLogs"],
                'Start Compressor Datetime': None,
                'Stop Compressor Datetime': None
        }
        self.instruments = {'Power Supply':'None',
                            'Ruox Temperature Monitor':'None',
                            'Diode Temperature Monitor':'None',
                            'Magnet Voltage Monitor':'None',
                            'Heat Switch':'None',
                            'Compressor':'None',
                            'Pressure Guage':'None'}

    @inlineCallbacks
    def initServer(self):
        """
        This method loads default settings from the registry,
        sets up instruments, and sets up listeners for GPIB device
        connect/disconnect messages.
        """
        yield DeviceServer.initServer(self)

        yield self.loadDefaults()

        # init start time, create dataChest, etc.
        # If the compressor was last stopped over 24 hours ago, or if the
        # compressor cannot be started and stopped from the computer,
        # a new file will be created each time the server is opened.  If
        # the compressor has not been stopped, the last file will be
        # appended to.  If the compressor has stopped, but it was less
        # than 24 hours ago, the last file will be appended to.  Starting
        # the compressor creates a new file.
        now = datetime.datetime.utcnow()
        start = self.ADRSettings['Start Compressor Datetime']
        stop = self.ADRSettings['Stop Compressor Datetime']
        if start is None or (stop is not None and deltaT(now - stop) > 24*60*60):
            self.ADRSettings['Start Compressor Datetime'] = now
            reg = self.client.registry
            yield reg.cd(self.ADRSettingsPath)
            yield reg.set('Start Compressor Datetime',now)
        self.initLogFiles()

        # Web Socket Update Stuff:
        log.startLogging(sys.stdout)
        root = File("")

        adrN = int(self.deviceName[-1])
        port = 9879 - adrN

        self.factory = MyFactory(u"wss://127.0.0.1:%i/"%port,adrServer=self)
        self.factory.protocol = MyServerProtocol
        resource = WebSocketResource(self.factory)
        root.putChild(u"ws", resource)

        site = Site(root)
        contextFactory = ssl.DefaultOpenSSLContextFactory('Z:/mcdermott-group/LabRAD/ssl_certificates/adr%i/ssl.key'%adrN,
                                                          'Z:/mcdermott-group/LabRAD/ssl_certificates/adr%i/ssl.crt'%adrN)
        # reactor.listenTCP(port, site, interface='0.0.0.0')
        reactor.listenSSL(port, site, contextFactory, interface='0.0.0.0')

        yield self.initializeInstruments()
        # subscribe to messages
        # the server ones are not used right now, but at some point they could be
        serv_conn_func = lambda c, (s, payload): self.serversChanged(*payload)
        serv_disconn_func = lambda c, (s, payload): self.serversChanged(*payload)
        mgr = self.client.manager
        self._cxn.addListener(serv_conn_func, source=mgr.ID, ID=12)
        self._cxn.addListener(serv_disconn_func, source=mgr.ID, ID=13)
        yield mgr.subscribe_to_named_message('Server Connect', 12, True)
        yield mgr.subscribe_to_named_message('Server Disconnect', 13, True)

        # listen for device connect/disconnect signals
        dev_con_changed = lambda c, payload: self.device_connection_changed(*payload)
        try: # in case the device manager is not running
             # &&& do this whenever device manager starts or something?
            devManager = self.client.gpib_device_manager
            yield devManager.device_connection_changed(self.ID)
            yield devManager.addListener(listener = dev_con_changed,
                                         source = None,
                                         ID = self.ID)
        except Exception as e:
            print str(e)

        self.updateState()

    @inlineCallbacks
    def loadDefaults(self):
        reg = self.client.registry
        yield reg.cd(self.ADRSettingsPath)
        _,settingsList = yield reg.dir()
        for setting in settingsList:
            self.ADRSettings[setting] = yield reg.get(setting)
    
    def initLogFiles(self):
        startDatetime = self.ADRSettings['Start Compressor Datetime']
        self.tempDataChest = dataChest(self.ADRSettings['Log Path'])
        dts = dateStamp()
        iso = startDatetime.isoformat().split('+')[0] # strip timezone (or dateStamp will fail)
        dtstamp = dts.dateStamp(iso)
        try:
            self.tempDataChest.openDataset(dtstamp+'_temperatures', modify=True)
        except Exception as e:
            self.tempDataChest.createDataset("temperatures",
                    [('time',[1],'utc_datetime','')],
                    [('temp60K',[1],'float16','Kelvin'),('temp03K',[1],'float16','Kelvin'),
                     ('tempGGG',[1],'float16','Kelvin'),('tempFAA',[1],'float16','Kelvin')],
                     dateStamp=dtstamp)
            self.tempDataChest.addParameter("X Label", "Time")
            self.tempDataChest.addParameter("Y Label", "Temperature")
            self.tempDataChest.addParameter("Plot Title",
                    startDatetime.strftime("ADR temperature history "
                                                "for run starting on %y/%m/%d %H:%M"))
        self.logMessages = []

    @inlineCallbacks
    def initializeInstruments(self):
        """
        This method creates the instances of all the instruments and
        saves them in self.instruments. It then sends
        set_adr_settings_path and select_device.  If these both go
        through (or are not valid methods, instr.connect is set to True.
        The power supply is also initialized.
        """
        instruments = self.instruments
        settings = self.ADRSettings
        for instrName in instruments:
            self.connectServer(instrName)
            self.connectDevice(instrName)

        # initialize power supply
        if hasattr(instruments['Power Supply'],'connected') \
               and instruments['Power Supply'].connected == True:
            try:
                yield instruments['Power Supply'].initialize_ps()
                self.logMessage('Power Supply initialized.')
            except Exception as e:
                self.logMessage( 'Power Supply could not be initialized.', alert=True)

        # if ruox therms are being read through multiplexer, set the channels
        try:
            instruments['Ruox Temperature Monitor'].add_channel(settings['FAA MP Chan'])
            instruments['Ruox Temperature Monitor'].add_channel(settings['GGG MP Chan'])
        except AttributeError:
            pass # may not have add_channel methods

    @inlineCallbacks
    def connectServer(self, instrName):
        settings = self.ADRSettings[instrName]

        # save server to instruments dict, leave as None if cannot connect
        lastInstr = self.instruments[instrName]
        try:
            instr = self.client[ settings[0] ]
            self.instruments[instrName] = instr
            if lastInstr != self.instruments[instrName]:
                self.logMessage('Server running for '+instrName+'.')
        except KeyError:
            instr = None
            self.instruments[instrName] = instr
            if lastInstr != self.instruments[instrName]:
                message = 'Server not found for '+instrName+'.'
                self.logMessage(message, alert=True)

        # set adr settings path (if the server has that method)
        try:
            yield instr.set_adr_settings_path(self.ADRSettingsPath)
        except AttributeError:
            pass # not all instruments have the set_adr_settings_path setting

    @inlineCallbacks
    def connectDevice(self, instrName):
        settings = self.ADRSettings[instrName]

        # select the device using the address in the registry under the
        # instrument name
        instr = self.instruments[instrName]
        if instr == None:
            return
        if hasattr(instr,'connected'):
            lastStatus = instr.connected
        else:
            lastStatus = None
        try:
            yield instr.select_device( settings[1] )
            instr.connected = True
            if lastStatus != instr.connected:
                self.logMessage(instrName+' connected.')
        except AttributeError as e:
            instr.connected = False # may not have a select_device method (heat switch, for ex)
        except LRError as e:
            if 'NoDevicesAvailableError' in e.msg:
                message = 'No devices connected for %s.'%instrName
            elif 'NoSuchDeviceError' in e.msg:
                message = 'No devices found for %s at address %s.'%(instrName,str(settings[1]))
            else: message = False
            instr.connected = False
            if message and lastStatus != instr.connected:
                self.logMessage(message, alert=True)
        except Exception as e:
            instr.connected = False
            self.logMessage('Could not connect to device for ' +
                    instrName + ': ' + str(e) + '.', alert=True)

    @inlineCallbacks
    def _refreshInstruments(self):
        """We can manually have all gpib buses refresh the list of
        devices connected to them."""
        self.logMessage('Refreshing devices...')
        serverList = yield self.client.manager.servers()
        for serv in [n for s,n in serverList]:
            if 'gpib_bus' in serv \
            or 'GPIB Bus' in serv:# or 'sim900_srs_mainframe' in serv:
                yield self.client[serv].refresh_devices()

    @inlineCallbacks
    def device_connection_changed(self, device, server, channel, isConnected):
        print '%s connected: %s'%(device, isConnected)
        # if instrument added, initialize instrument.  if it is removed,
        # mark it as disconnected.
        for instName in self.instruments.keys():
            instAddress = self.ADRSettings[instName][1]
            if server in instAddress and channel in instAddress:
                if isConnected == False:
                    self.instruments[instName].connected = False
                else:
                    yield util.wakeupCall(0.5) # to give the instrument
                                               # server time to register the device
                    self.connectDevice(instName)

    def serversChanged(self,*args):
        # &&& make this server by server like the device connection
        self.initializeInstruments()

    def logMessage(self, message, alert=False):
        """Applies a time stamp to the message and saves it to a file and an
        array."""
        dt = datetime.datetime.utcnow()
        self.logMessages.append( (dt,message,alert) )
        messageWithTimeStamp = dt.strftime("[%m/%d/%y %H:%M:%S] ") + message
        try:
            fname = os.path.join(os.environ['DATA_CHEST_ROOT'], 
                                    self.tempDataChest.pwd()) + \
                self.ADRSettings['Start Compressor Datetime'].strftime("\\log_%y%m%d_%H%M.txt")
            with open(fname, 'a') as f:
                f.write( messageWithTimeStamp + '\n' )
        except Exception as e:
            print("Could not write to log file: " + str(e) + '.')
        print '[log] '+ message
        self.factory.sendMessageToAll({
            'log': [{
                'datetime':(dt-datetime.datetime(1970,1,1)).total_seconds(),
                'message':message,
                'alert':alert
            }]
        })
        self.client.manager.send_named_message('Log Changed', (dt,message,alert))

    @inlineCallbacks
    def updateState(self):
        """ This takes care of the real time reading of the instruments.
           It starts immediately upon starting the program, and never stops. """
        nan = numpy.nan
        instruments = self.instruments
        while self.alive:
            cycleStartTime = datetime.datetime.utcnow()
            self.lastState = self.state.copy()
            # datetime, cycle
            self.state['datetime'] = datetime.datetime.utcnow()
            self.state['cycle'] += 1
            # compressor
            self.state['CompressorStatus'] = None
            if hasattr(instruments['Compressor'],'connected') \
                    and instruments['Compressor'].connected:
                try:
                    self.state['CompressorStatus'] = yield instruments['Compressor'].status()
                except Exception as e:
                    print 'could not read compressor status', str(e)
            # diode temps
            try:
                temps = yield instruments['Diode Temperature Monitor'].get_diode_temperatures()
                self.state['T_60K'],self.state['T_3K'] = temps
            except Exception as e:
                self.state['T_60K'],self.state['T_3K'] = nan*units.K, nan*units.K
                try:
                    lastState = instruments['Diode Temperature Monitor'].connected
                    instruments['Diode Temperature Monitor'].connected = False
                    if lastState != False:
                        self._refreshInstruments()
                except AttributeError:
                    pass # in case instrument didn't initialize properly and is None
            # ruox temps
            try:
                temps = yield instruments['Ruox Temperature Monitor'].get_ruox_temperature()
                # if there are two returned temps, maps them to GGG and FAA.
                # if only one is returned, assumes it is for the FAA
                try:
                    FAAChan = self.ADRSettings['FAA MP Chan']
                    GGGChan = self.ADRSettings['GGG MP Chan']
                    self.state['T_GGG'] = dict(temps)[GGGChan]
                    self.state['T_FAA'] = dict(temps)[FAAChan]
                except:
                    self.state['T_GGG'],self.state['T_FAA'] = nan*units.K, temps
            except Exception as e:
                self.state['T_GGG'],self.state['T_FAA'] = nan*units.K, nan*units.K
                try:
                    lastState = instruments['Ruox Temperature Monitor'].connected
                    instruments['Ruox Temperature Monitor'].connected = False
                    if lastState != False:
                        self._refreshInstruments()
                except AttributeError:
                    pass # in case instrument didn't initialize properly and is None
            if self.state['T_GGG']['K'] == 20.0:
                self.state['T_GGG'] = nan*units.K
            if self.state['T_FAA']['K'] == 45.0:
                self.state['T_FAA'] = nan*units.K
            # voltage across magnet
            try:
                self.state['magnetV'] = yield instruments['Magnet Voltage Monitor'].get_magnet_voltage()
            except Exception as e:
                self.state['magnetV'] = nan*units.V
                try:
                    lastState = instruments['Magnet Voltage Monitor'].connected
                    instruments['Magnet Voltage Monitor'].connected = False
                    if lastState != False:
                        self._refreshInstruments()
                except AttributeError:
                    pass # in case instrument didn't initialize properly and is None
            # PS current, voltage
            try:
                self.state['PSCurrent'] = yield instruments['Power Supply'].current()
                self.state['PSVoltage'] = yield instruments['Power Supply'].voltage()
            # except LRError as e:
                # if 'VisaIOError' in e.msg:
                    # self.state['PSCurrent'] = nan*units.A
                    # self.state['PSVoltage'] = nan*units.V
                    # try:
                        # lastState = instruments['Power Supply'].connected
                        # instruments['Power Supply'].connected = False
                        # if lastState != False:
                            # self._refreshInstruments()
                    # except AttributeError:
                        # pass # in case instrument didn't initialize properly and is None
                # else:
                    # print str(e)
            except Exception as e:
                self.state['PSCurrent'] = nan*units.A
                self.state['PSVoltage'] = nan*units.V
                try:
                    lastState = instruments['Power Supply'].connected
                    instruments['Power Supply'].connected = False
                    if lastState != False:
                        self._refreshInstruments()
                except AttributeError:
                    pass # in case instrument didn't initialize properly and is None
            # pressure
            try:
                pressures = yield instruments['Pressure Guage'].get_pressures()
                pressure = pressures[0]['torr'] * units.torr
            except Exception as e:
                pressure = numpy.nan * units.torr
            self.state['Pressure'] = pressure
            # update relevant files
            try:
                newTemps = [numpy.float16(self.state[t]['K']) for t in ['T_60K','T_3K','T_GGG','T_FAA']]
                timestamp = deltaT(self.state['datetime'] - datetime.datetime(1970, 1, 1))
                self.tempDataChest.addData( [[timestamp] + newTemps] )
            except Exception as e:
                self.logMessage('Temperature recording failed: %s.\n%s' %(str(e),str([[timestamp] + newTemps])) )
            cycleLength = deltaT(datetime.datetime.utcnow() - cycleStartTime)
            self.factory.sendMessageToAll({
                'temps': {
                    'timeStamps':[(self.state['datetime']-datetime.datetime(1970,1,1)).total_seconds()],
                    't60K': [self.state['T_60K']['K']],
                    't03K': [self.state['T_3K']['K']],
                    'tGGG': [self.state['T_GGG']['K']],
                    'tFAA': [self.state['T_FAA']['K']]
                },
                'instruments': { name:{'server':status[0],
                                        'connected':status[1] }
                                    for (name,status) in self.getInstrumentState('bla')},
                'compressorOn':self.state['CompressorStatus'],
                'pressure':self.state['Pressure']['torr'],
                'isMaggingUp': self.state['maggingUp'],
                'isRegulating': self.state['regulating'],
                'backEMF': self.state['magnetV']['V'],
                'PSCurrent': self.state['PSCurrent']['A'],
                'PSVoltage': self.state['PSVoltage']['V']
            })
            self.client.manager.send_named_message('State Changed', 'state changed')
            yield util.wakeupCall( max(0,self.ADRSettings['step_length']-cycleLength) )

    def _cancelMagUp(self):
        """Cancels the mag up loop."""
        self.state['maggingUp'] = False
        self.logMessage( 'Magging up stopped at a current of ' +
                str(self.state['PSCurrent']) + '.' )
        self.factory.sendMessageToAll({
            'isMaggingUp': self.state['maggingUp']
        })
        self.client.manager.send_named_message('MagUp Stopped', 'cancel')

    @inlineCallbacks
    def _magUp(self):
        """ The magging up method, as per the HPD Manual, involves
        increasing the voltage in steps of MAG_UP_dV volts every cycle
        of the loop.  This cycle happens once every STEP_LENGTH seconds,
        nominally 1s (since the voltage monitor reads once a second).
        Each cycle, the voltage across the magnet is read to get the
        backEMF.  If it is greater than the MAGNET_VOLTAGE_LIMIT, the
        voltage will not be raised until the next cycle for which the
        backEMF < MAGNET_VOLTAGE_LIMIT. """
        instruments = self.instruments
        settings = self.ADRSettings
        if self.state['maggingUp']:
            self.logMessage('Already magging up.')
            return
        if self.state['regulating']:
            self.logMessage('Currently in PID control loop regulation.'
                            ' Please wait until finished.')
            return
        if self.state['T_3K']['K'] > settings['magnet_max_temp']:
            self.logMessage('Temperature too high to mag up.')
            return
        deviceNames = ['Power Supply','Magnet Voltage Monitor']
        deviceStatus = [instruments[name].connected for name in deviceNames]
        if False in deviceStatus:
            message = ('Cannot mag up: At least one of the essential '
                      'devices is not connected.  Connections: %s'
                      %str([deviceNames[i]+':'+str(deviceStatus[i])
                            for i in range(len(deviceNames))]))
            self.logMessage(message, alert=True)
            return
        self.state['maggingUp'] = True
        self.factory.sendMessageToAll({
            'isMaggingUp': self.state['maggingUp']
        })
        self.client.manager.send_named_message('MagUp Started', 'start')
        self.logMessage('Beginning to mag up to ' +
                str(settings['current_limit']) + ' A.')
        while self.state['maggingUp']:
            startTime = datetime.datetime.utcnow()
            dI = self.state['PSCurrent'] - self.lastState['PSCurrent']
            dt = deltaT( self.state['datetime'] - self.lastState['datetime'] )
            if dt == 0:
                dt = 0.0000000001 #to prevent divide by zero error
            if self.state['PSCurrent']['A'] < settings['current_limit']:
                if self.state['magnetV']['V'] < settings['magnet_voltage_limit'] and \
                   abs(dI['A']/dt) < settings['dIdt_magup_limit'] and \
                   self.state['T_FAA']['K'] < settings['magnet_max_temp']:
                    newVoltage = self.state['PSVoltage'] + settings['magup_dV']*units.V
                    if newVoltage['V'] < settings['voltage_limit']:
                        instruments['Power Supply'].voltage(newVoltage) #set new voltage
                    else:
                        instruments['Power Supply'].voltage(settings['voltage_limit']*units.V)
                cycleLength = deltaT(datetime.datetime.utcnow() - startTime)
                yield util.wakeupCall( max(0,settings['step_length']-cycleLength) )
            else:
                self.logMessage( 'Finished magging up. %s reached.'%str(self.state['PSCurrent']) )
                self.state['maggingUp'] = False
                self.factory.sendMessageToAll({
                    'isMaggingUp': self.state['maggingUp']
                })
                self.client.manager.send_named_message('MagUp Stopped', 'done')

    def _cancelRegulate(self):
        """Cancels the PID regulation loop."""
        self.state['regulating'] = False
        self.logMessage( 'PID Control stopped at a current of ' +
                str(self.state['PSCurrent']) + '.' )
        self.factory.sendMessageToAll({
            'isRegulating': self.state['regulating']
        })
        self.client.manager.send_named_message('Regulation Stopped', 'cancel')

    @inlineCallbacks
    def _regulate(self,temp):
        """ This function starts a PID loop to control the temperature.
        The basics of it is that a new voltage V+dV is proposed.  dV is
        then limited as necessary, and the new voltage is set. As with
        magging up, regulate runs a cycle at approximately once per second. """
        print 'REG TEMP',temp
        self.state['regulationTemp'] = temp
        self.logMessage('Setting regulation temperature to %f K.'%temp)
        if self.state['maggingUp'] == True:
            self.logMessage('Currently magging up. Please wait until finished.')
            return
        deviceNames = ['Power Supply',
                       'Diode Temperature Monitor',
                       'Ruox Temperature Monitor',
                       'Magnet Voltage Monitor']
        deviceStatus = [self.instruments[name].connected for name in deviceNames]
        if False in deviceStatus:
            message = ('Cannot regulate: At least one of the essential '
                    'devices is not connected. Connections: %s'
                    %str([deviceNames[i]+':'+str(deviceStatus[i])
                    for i in range(len(deviceNames))]))
            self.logMessage(message, alert=True)
            return
        self.factory.sendMessageToAll({
            'isRegulating': self.state['regulating']
        })
        self.client.manager.send_named_message('Regulation Started', 'start')
        self.logMessage( 'Starting regulation to '+str(self.state['regulationTemp'])
                        +' K from '+str(self.state['PSCurrent'])+'.' )
        self.state['regulating'] = True
        print 'beginning regulation'
        print 'V\tbackEMF\tdV/dT\tdV'
        while self.state['regulating']:
            startTime = datetime.datetime.utcnow()
            dI = self.state['PSCurrent'] - self.lastState['PSCurrent']
            if numpy.isnan(self.state['T_FAA']['K']):
                self.logMessage( 'FAA temperature is not valid. '
                                 'Regulation cannot continue.' )
                self._cancelRegulate()
            # propose new voltage
            T_target = float(self.state['regulationTemp'])*units.K
            dT = deltaT( self.state['datetime'] - self.lastState['datetime'] )
            if dT == 0:
                dT = 0.001 #to prevent divide by zero error
            self.state['PID_cumulativeError'] += (T_target['K']-self.state['T_FAA']['K'])
            self.state['PID_cumulativeError'] = \
                    min(self.state['PID_cumulativeError'],
                        self.ADRSettings['PID_MaxI'],key=abs) # so we dont just build this up during the mag down.
            dV = ( self.ADRSettings['PID_KP']*(T_target['K']-self.state['T_FAA']['K']) \
                 + self.ADRSettings['PID_KI']*self.state['PID_cumulativeError'] \
                 + self.ADRSettings['PID_KD']*(self.lastState['T_FAA']['K'] \
                                             - self.state['T_FAA']['K'])/dT )*units.V
            # hard current limit
            if self.state['PSCurrent'] > self.ADRSettings['current_limit']*units.A:
                if dV>0*units.V:
                    dV=0*units.V
            # hard voltage limit
            if self.state['PSVoltage'] + dV > self.ADRSettings['voltage_limit']*units.V:
                dV = self.ADRSettings['voltage_limit']*units.V - self.state['PSVoltage']
            # steady state limit
            if dV['V'] < 0:
                dV = max(dV, self.state['magnetV'] - \
                             self.ADRSettings['magnet_voltage_limit']*units.V)
                if dV['V'] > 0:
                    dV = 0*units.V
            if dV['V'] > 0:
                dV = min(dV, self.ADRSettings['magnet_voltage_limit']*units.V-self.state['magnetV'])
                if dV['V'] < 0:
                    dV = 0*units.V
            # limit by hard voltage increase limit
            # print str(dV/dT)+'\t',
            if abs(dV/dT) > self.ADRSettings['dVdT_limit']*units.V:
                dV = self.ADRSettings['dVdT_limit']*dT*(dV/abs(dV))*units.V
            # limit by hard current increase limit
            if abs(dI/dT) > self.ADRSettings['dIdt_regulate_limit']*units.A:
                dV = 0*units.V
            # will voltage go negative?
            if self.state['PSVoltage']+dV <= 0*units.V:
                self.instruments['Power Supply'].voltage(0*units.V)
                dV = 0*units.V
            # is current 0?  if so, end regulation
            # if dV > 0, don't end regulation because we are increasing current
            # 0.02 amps is pretty arebitrary, but the PS seemed to stay at 0.018A
            # at 0.02V (the lowest it went)
            if self.state['PSCurrent']['A'] < 0.03 and dV['V'] <= 0:
                runCycleAgain = False
            else:
                runCycleAgain = True
            # print str(dV)
            self.instruments['Power Supply'].voltage(self.state['PSVoltage'] + dV)
            cycleTime = deltaT(datetime.datetime.utcnow() - startTime)
            if runCycleAgain:
                yield util.wakeupCall( max(0,self.ADRSettings['step_length']-cycleTime) )
            else:
                self.logMessage( 'Regulation has completed. Mag up and try again.' )
                self.state['regulating'] = False
                self.factory.sendMessageToAll({
                    'isRegulating': self.state['regulating']
                })
                self.client.manager.send_named_message('Regulation Stopped', 'done')

    @setting(101, 'Get Settings Path', returns=['*s'])
    def getSettingsPath(self,c):
        return self.ADRSettingsPath

    @setting(102, 'Get Start Datetime', returns=['t'])
    def getStartDatetime(self,c):
        return self.ADRSettings['Start Compressor Datetime']

    @setting(103, 'Get Log', n=['v'], returns=['*(t,s,b)'])
    def getLog(self,c, n=0):
        """Get an array of the last n logs."""
        if n==0: n = len(self.logMessages)
        n = int(min(n, len(self.logMessages)))
        return [messageAndAlert for messageAndAlert in self.logMessages[-n:]]

    @setting(104, 'Get State Var', var=['s'], returns=['?'])
    def getStateVar(self,c, var):
        """You can get any arbitrary value stored in the state variable
        by passing its name to this function."""
        return self.state[var]

    @setting(105, 'Get Instrument State', instrNames=['*s'], returns=['?'])
    def getInstrumentState(self,c, instrNames=None):
        """Get the status of instruments in the form [('instrument name',
        (server connected?, device selected?))].  If no instruments are
        passed in, returns an array of all iinstrument statuses"""
        if instrNames==None:
            instrNames = self.instruments.keys()
        states = []
        for name in instrNames:
            if bool(self.instruments[name]):
                state = (True, self.instruments[name].connected)
            else: state = (False,False)
            states.append((name,state))
        return states

    @setting(110, 'PSCurrent', returns=['v'])
    def pscurrent(self,c):
        """Get the current of the power supply."""
        return self.state['PSCurrent']

    @setting(111, 'PSVoltage', returns=['v'])
    def psvoltage(self,c):
        """Get the voltage of the power supply."""
        return self.state['PSVoltage']

    @setting(112, 'MagnetV', returns=['v'])
    def magnetv(self,c):
        """Get the voltage across the magnet (at the magnet leads)."""
        #print 'getting magnet voltage',self.state['magnetV']
        return self.state['magnetV']

    @setting(113, 'cycle', returns=['v'])
    def cycle(self,c):
        """How many measurement cycles have been run?"""
        return self.state['cycle']

    @setting(114, 'time', returns=['t'])
    def time(self,c):
        """Returns the (UTC) time at which the last measurement cycle was run."""
        return self.state['datetime']

    @setting(115, 'Temperatures', returns=['*v'])
    def temperatures(self,c):
        """Returns the measured temperatures in an array: [60K,3K,GGG,FAA]"""
        return [self.state[t] for t in ('T_60K','T_3K','T_GGG','T_FAA')]

    @setting(120, 'Regulate', temp=['v'])
    def regulate(self,c, temp=0.1):
        """Starts the PID Temperature control loop."""
        self._regulate(temp)

    @setting(121, 'Mag Up')
    def magUp(self,c):
        """Slowly increases the current through the magnet to the current limit."""
        self._magUp()

    @setting(122, 'Cancel Regulation')
    def cancelRegulation(self,c):
        """Stop PID regulation cycle."""
        self._cancelRegulate()

    @setting(123, 'Cancel Mag Up')
    def cancelMagUp(self,c):
        """Stop mag up process."""
        self._cancelMagUp()

    @setting(124, 'Refresh Instruments')
    def refreshInstruments(self,c):
        """Manually tell all gpib buses to refresh their list of connected devices."""
        self._refreshInstruments()

    @setting(125, 'Add To Log', message=['s'])
    def addToLog(self,c,message=None):
        """Add message to log."""
        if message is not None:
            self.logMessage(message)

    @setting(126, 'Close Heat Switch')
    def closeHeatSwitch(self,c):
        """Close Heat Switch."""
        try:
            yield self.client.heat_switch.close()
            self.logMessage('Closing Heat Switch.')
        except Exception as e:
            self.logMessage('Closing Heat Switch failed.',alert=True)

    @setting(127, 'Open Heat Switch')
    def openHeatSwitch(self,c):
        """Open Heat Switch."""
        try:
            yield self.client.heat_switch.open()
            self.logMessage('Opening Heat Switch.')
        except Exception as e:
            self.logMessage('Opening Heat Switch failed.',alert=True)

    @setting(128, 'Start Compressor')
    def startCompressor(self,c):
        """Start Compressor."""
        try:
            yield self.client['CP2800 Compressor'].start()
            self.logMessage('Compressor started.')
            # Update start time and refresh files unless compressor was
            # stopped within last 24 hours.
            now = datetime.datetime.utcnow()
            start = self.ADRSettings['Start Compressor Datetime']
            stop = self.ADRSettings['Stop Compressor Datetime']
            if (start is None and stop is None) or \
              (stop is not None and deltaT(now - stop) > 24*60*60):
                self.ADRSettings['Start Compressor Datetime'] = now
                self.ADRSettings['Stop Compressor Datetime'] = None
                reg = self.client.registry
                yield reg.cd(self.ADRSettingsPath)
                yield reg.set('Start Compressor Datetime',now)
                yield reg.set('Stop Compressor Datetime',None)
                self.initLogFiles()
        except Exception as e:
            self.logMessage('Starting Compressor failed.',alert=True)

    @setting(129, 'Stop Compressor')
    def stopCompressor(self,c):
        """Stop Compressor."""
        try:
            yield self.client['CP2800 Compressor'].stop()
            self.logMessage('Compressor stopped.')
            now = datetime.datetime.utcnow()
            self.ADRSettings['Stop Compressor Datetime'] = now
            reg = self.client.registry
            yield reg.cd(self.ADRSettingsPath)
            yield reg.set('Stop Compressor Datetime',now)
        except Exception as e:
            self.logMessage('Stopping Compressor failed.',alert=True)

    @setting(130, 'Set PID KP',k=['v'])
    def setPIDKP(self,c,k):
        """Set PID Proportional Constant."""
        self.ADRSettings['PID_KP'] = k
        self.logMessage('PID_KP has been set to '+str(k))

    @setting(131, 'Set PID KI',k=['v'])
    def setPIDKI(self,c,k):
        """Set PID Integral Constant."""
        self.ADRSettings['PID_KI'] = k
        self.logMessage('PID_KI has been set to '+str(k))

    @setting(132, 'Set PID KD',k=['v'])
    def setPIDKD(self,c,k):
        """Set PID Derivative Constant."""
        self.ADRSettings['PID_KD'] = k
        self.logMessage('PID_KD has been set to '+str(k))

    @setting(133, 'Set PID Max I',max=['v'])
    def setPIDMaxI(self,c,max):
        """Set PID Max Integral Value."""
        self.ADRSettings['PID_MaxI'] = max
        self.logMessage('PID_MaxI has been set to '+str(max))


if __name__ == "__main__":
    __server__ = ADRServer(sys.argv)
    util.runServer(__server__)
