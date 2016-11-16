#some text
"""
### BEGIN NODE INFO
[info]
name = Tektronix CSA Server
version = 1.0
description = 
[startup]
cmdline = %PYTHON% %FILE%
timeout = 20
[shutdown]
message = 987654321
timeout = 5
### END NODE INFO
"""

from labrad.server import setting
from labrad.gpib import GPIBManagedServer, GPIBDeviceWrapper
from twisted.internet.defer import inlineCallbacks, returnValue
import numpy
from numpy import *


class TektronixTDS2014CWrapper(GPIBDeviceWrapper):
    
    @inlineCallbacks
    def getDataSourceStr(self):  #returns the channels that will return data when the scope is queried for waveform data
        result = yield self.query('DATa:SOUrce?')
        returnValue(result)

    @inlineCallbacks
    def setDataSourceStr(self, channelNum): # sets which channels will return data when the scope is queried for waveform data
        if channelNum in [1,2,3,4]:
            yield self.write('DATa:SOUrce CH' + str(channelNum))
            result = yield self.getDataSourceStr()
            returnValue(result)
        else:
            returnValue(-1)
            
    @inlineCallbacks
    def idnStr(self): #asks scope who it is
        result = yield self.query('*IDN?')
        returnValue(result)

    @inlineCallbacks
    def encASCIIstr(self): #sets data encoding to ascii (note: this is the most inefficient/convenient way to return data)
        yield self.write('DATa:ENCdg ASCi')
        result = yield self.write('DATa:ENCdg?')
        returnValue(result)

    @inlineCallbacks
    def getXzeroStr(self): #gets trigger time
        result = yield self.query('WFMOutpre:XZEro?')
        returnValue(float(result))

    @inlineCallbacks
    def getXincrStr(self): #gets amount of time between adjacent data points
        result = yield self.query('WFMOutpre:XINcr?')
        returnValue(float(result))
        
    @inlineCallbacks
    def getYmultStr(self): 
        result = yield self.query('WFMOutpre:YMUlt?')
        returnValue(float(result))

    @inlineCallbacks
    def getYoffsetStr(self): #get Yoffset
        result = yield self.query('WFMOutpre:YOFf?')
        returnValue(float(result))

    @inlineCallbacks
    def getYzeroStr(self): #get Y0
        result = yield self.query('WFMOutpre:YZEro?')
        returnValue(float(result))

    @inlineCallbacks
    def getChannelOffset(self, channelNum):
        if channelNum in [1,2,3,4]:
            result = yield self.query('CH'+str(channelNum)+':'+'OFFSET?')
            returnValue(float(result))
        else:
            returnValue(-1)

    @inlineCallbacks
    def setChannelOffset(self, channelNum, chanOffset):
        if channelNum in [1,2,3,4]:
            yield self.write('CH'+str(channelNum)+':'+'OFFSET '+str(chanOffset))
            result = yield self.getChannelOffset(channelNum)
            returnValue(float(result))
        else:
            returnValue(-1)

    @inlineCallbacks
    def getChannelPosition(self, channelNum): #Sets or returns the channel vertical position (note: this is not the same as offset)
        if channelNum in [1,2,3,4]:
            result = yield self.query('CH'+str(channelNum)+':POSITION?')
            returnValue(float(result))
        else:
            returnValue(-1)
        
    @inlineCallbacks
    def getVoltsPerDivision(self, channelNum):
        if channelNum in [1,2,3,4]:
            result = yield self.query('CH'+str(channelNum)+':'+'SCALE?')
            returnValue(float(result))
        else:
            returnValue(-1)

    @inlineCallbacks
    def getDataStartIndex(self): #gets the number of elements sent by oscilloscope
        result = yield self.query('DATa:START?')
        returnValue(int(result))

    @inlineCallbacks
    def setDataStartIndex(self, startIndex): #gets the number of elements sent by oscilloscope
        self.write('DATa:START '+str(startIndex))
        result = yield self.getDataStartIndex()
        returnValue(int(result))

    @inlineCallbacks
    def getDataStopIndex(self): #gets the number of elements sent by oscilloscope
        result = yield self.query('DATa:STOP?')
        returnValue(int(result))

    @inlineCallbacks
    def setDataStopIndex(self, startIndex): #gets the number of elements sent by oscilloscope
        self.write('DATa:STOP '+str(startIndex))
        result = yield self.getDataStartIndex()
        returnValue(int(result))

    @inlineCallbacks
    def getRecLength(self): #gets the number of elements sent by oscilloscope
        result = yield self.query('HORizontal:RECOrdlength?')
        returnValue(int(result))

    @inlineCallbacks
    def setRecLength(self, numPts): #gets the number of elements sent by oscilloscope
        yield self.write('HORizontal:RECOrdlength '+str(numPts))
        result = yield self.getRecLength()
        returnValue(int(result))
        
    ###
    @inlineCallbacks
    def getSamplingMode(self):
        result = yield self.query('ACQuire:SAMPLingmode?')  #RT ==> Real-Time, IT ==> Interpolated-Time, ET ==> equivalent time (this server assumes RT)
        returnValue(result)
        
    @inlineCallbacks
    def setRealTimeSamplingMode(self): #turns on aquisition
        yield self.write('ACQuire:SAMPLingmode RT')
        result = yield self.getSamplingMode()
        returnValue(result)

    @inlineCallbacks
    def setChannelState(self, channelNum, state): #turns on aquisition
        if channelNum in [1,2,3,4] and (state.lower() == 'on' or 'off'):
            yield self.write('SELect:CH'+str(channelNum)+' '+state)
            result = yield self.getChannelState(channelNum, False)
            returnValue(result)
        else:
            returnValue(-1)

    @inlineCallbacks
    def getChannelState(self, channelNum, allChannelsFlag): #turns on aquisition
        if allChannelsFlag is False:
            if channelNum in [1,2,3,4]:
                result = yield self.query('SELECT:CH'+str(channelNum)+'?')
                returnValue(result)
            else:
                returnValue('Error')
        else:
            for chan in [1,2,3,4]:
                if chan ==1:
                    queryAllChannelsString = 'SELECT:CH'+str(chan)+'?'
                else:
                    queryAllChannelsString =queryAllChannelsString+";:"+'SELECT:CH'+str(chan)+'?'
            print "queryAllChannelsString=", queryAllChannelsString
            result = yield self.query(queryAllChannelsString)
            print "result=", result
            returnValue(result)
            
    @inlineCallbacks
    def getTimePerDivision(self):
        result = yield sell.query('HORizontal:SCAle?')
        returnValue(result)

    @inlineCallbacks
    def setTimePerDivision(self, timePerDiv): ## depends on number of channels that are on, if single channel 1/(20e9) min, if two 1/(10e9) if 3 or 4 1/(5e9)
        result = yield self.getChannelState(1, True)
        numChansOn = result.count('1')
        
        if numChansOn ==1 and timePerDiv >= (50e-12):
            yield self.write('HORizontal:SCAle '+str(timePerDiv))
            result = yield self.getTimePerDivision()
        elif numChanOn ==2 and timePerDiv >= (100e-12):
            yield self.write('HORizontal:SCAle '+str(timePerDiv))
            result = yield self.getTimePerDivision()
        elif numChanOn >=3 and timePerDiv >= (200e-12):
            yield self.write('HORizontal:SCAle '+str(timePerDiv))
            result = yield self.getTimePerDivision()
        returnValue(str(result))
            
            
    @inlineCallbacks
    def getSamplingRate(self):
        result = yield self.query('HORizontal:MAIn:SAMPLERate?')
        returnValue(float(result))
        
    @inlineCallbacks
    def getTriggerState(self): # there is no corresponding way to set trigger
        result = yield self.write('TRIGger:STATE?')
        returnValue(result)

    @inlineCallbacks
    def configureEdgeTrigger(self, triggerChanNum, slope, level):
        if slope == 'Rise' or slope == 'Fall':
            yield self.write('TRIGger:A:TYPe EDGE')
            yield self.write('TRIGger:A:EDGE:SOUrce CH'+str(triggerChanNum))
            yield self.write('TRIGger:A:EDGE:SLOPE '+slope)
            yield self.write('TRIGger:A:LEVel:CH'+str(triggerChanNum)+' '+str(level))
            returnValue(1)                
        else:
            returnValue(-1)

    @inlineCallbacks
    def checkUnitStr(self): 
        result = yield self.query('MEASUrement:IMMed:UNIts?')
        returnValue(result)

    @inlineCallbacks
    def getWaveFormDataStr(self): #gets current displayed waveform data
        result = yield self.query('WAVFRM?')
        returnValue(result)

    @inlineCallbacks
    def getTriggerStateStr(self): #gets the trigger state of the instrument
        result = yield self.query('TRIGger:STATE?')
        returnValue(result)
##
##    @inlineCallbacks
##    def getValueStr(self): 
##        result = yield self.query('MEASUrement:IMMed:VALue?')
##        returnValue(result)
##
##    @inlineCallbacks
##    def setSingleTriggerStr(self): #stops aqu. after single trigger
##        result = yield self.query('ACQuire:STOPAfter SEQuence')
##        returnValue(result)

##    @inlineCallbacks
##    def getreadystr(self): #asks if Osc is ready to trigger
##        result = yield self.query('ACQuire:STATE?')  #TRIGger:STATE?
##        returnValue(result)

##    @inlineCallbacks
##    def setReadyStr(self): #turns on aquisition
##        result = yield self.write('ACQuire:STATE ON')
##        returnValue(result)
      
class TektronixTDSServer(GPIBManagedServer):
    #Provides basic control for Tektronix 2014C Oscilloscope
    name = 'CSA7404B'
    deviceName = 'TEKTRONIX CSA7404B'
    deviceWrapper = TektronixTDS2014CWrapper

    
    @setting(101, 'Identify', returns='s')
    def Identify(self, c):
        '''Ask current instrument to identify itself'''
        dev = self.selectedDevice(c)
        answer = yield dev.idnStr()
        returnValue(answer)

    @setting(103, 'setchannel',channelNum='i' , returns='s')
    def setchannel(self,c,channelNum):
        '''Set the Channel you want to take data from'''
        dev = self.selectedDevice(c)
        answer = yield dev.setDataSourceStr(channelNum)
        returnValue(answer)
       
    @setting(106, 'checkunits', returns='s')
    def checkunits(self,c):
        dev = self.selectedDevice(c)
        answer = yield dev.checkUnitStr()
        returnValue(answer)
    
    @setting(108, 'getVoltsPerDivision',channelNum='i', returns='v')
    def getVoltsPerDivision(self, c, channelNum):
        dev = self.selectedDevice(c)
        answer = yield dev.getVoltsPerDivision(channelNum)
        returnValue(answer)

    @setting(109, 'getChannelOffset',channelNum='i', returns='v')
    def getChannelOffset(self, c, channelNum):
        dev = self.selectedDevice(c)
        answer = yield dev.getChannelOffset(channelNum)
        returnValue(answer)

    @setting(110, 'getChannelPosition',channelNum='i', returns='v')
    def getChannelPosition(self, c, channelNum):
        dev = self.selectedDevice(c)
        answer = yield dev.getChannelPosition(channelNum)
        returnValue(answer)

    @setting(111, 'configureEdgeTrigger',triggerChanNum='i', slope ='s', level = 'v', returns='v')
    def configureEdgeTrigger(self, c, triggerChanNum, slope, level):  #configureEdgeTrigger(self, triggerChanNum, slope, level)
        dev = self.selectedDevice(c)
        answer = yield dev.configureEdgeTrigger(triggerChanNum, slope, level)
        returnValue(answer)

    @setting(112, 'getChannelState', channelNum ='i', allChannelsFlag ='b', returns='s')#def getChannelState(self, channelNum, allChannelsFlag = None)
    def getChannelState(self, c, channelNum, allChannelsFlag = False):
        dev = self.selectedDevice(c)
        answer = yield dev.getChannelState(channelNum, allChannelsFlag)
        returnValue(answer)

    @setting(210, 'getRecordLength', returns='w')#def getChannelState(self, channelNum, allChannelsFlag = None)
    def getRecordLength(self, c):
        dev = self.selectedDevice(c)
        recordLength = yield dev.getRecLength()
        returnValue(recordLength)

    @setting(113, 'getWaveFormData', returns='?')
    def getWaveFormData(self, c): #waveforms should only be output upon trig ready
        dev = self.selectedDevice(c)
        yield dev.encASCIIstr()
        start = yield dev.setDataStartIndex(1)
        recordLength = yield dev.getRecLength()
        stop = yield dev.setDataStopIndex(recordLength)
        #trigState = yield dev.getTriggerStateStr()
        numActiveWaveforms = len((yield dev.getDataSourceStr()).split(','))
        splitWaveformData = (yield dev.getWaveFormDataStr()).split(';') # elements 0 - 17 make up first wave form, elements 18-35 make up the second waveform, ...
        print "len(splitWaveformData)=", len(splitWaveformData)
        print "numActiveWaveforms=", numActiveWaveforms
        if len(splitWaveformData) < numActiveWaveforms*18:
            print splitWaveformData
        data = ()
        for ii in range (0, numActiveWaveforms):
            wfID = splitWaveformData[5+ii*18]
            dataStr = splitWaveformData[17+ii*18]
            numPts = int(splitWaveformData[6+ii*18])  # stays fixed
            xUnits = splitWaveformData[8+ii*18]
            dx = float(splitWaveformData[9+ii*18])
            xZero = float(splitWaveformData[10+ii*18])
            yUnits = splitWaveformData[12+ii*18]
            yMult = float(splitWaveformData[13+ii*18])
            yOffset = float(splitWaveformData[14+ii*18])
            yZero = float(splitWaveformData[15+ii*18])
            numFrames = int(splitWaveformData[16+ii*18]) # tells when to split data
            voltageArray = numpy.fromstring(dataStr, sep=',')  # needs to be subparsed
            voltageArray =(voltageArray-yOffset)*yMult+yZero
            timeArray = xZero + dx*numpy.linspace(1, numPts, num = numPts)
            intarr = numpy.vstack((timeArray,voltageArray))
            intarr = intarr.transpose()
            data = data+(intarr,)
        returnValue(data)

##    def makeDictionaryFromPreamble(self, preamble):
##        preambleDict ={}

##    def createDict(self):
##        d = {}
##        d['X0'] = None #trigger position
##        d['Xinc'] = None #time increment
##        d['Ymulti'] = None #Voltage increment
##        d['Yoff'] = None #Voltage offset
##        d['Y0'] = None # position of 0V
##        d['Datalength'] = None #number of datapoints
##        d['readystate'] = None # boolean 1=ready to trigger, 0= triggered, waiting for next command
##        self.tdsDict = d
##        
##    @inlineCallbacks
##    def populateDict(self, c):
##        dev = self.selectedDevice(c)
##        X0 = yield dev.getXzeroStr() 
##        Xinc = yield dev.getXincrStr()
##        Ymulti = yield dev.getYmultStr()
##        Yoff = yield dev.getYoffsetStr()
##        Y0 = yield dev.getYzeroStr()        
##        Datalength = yield dev.getDataLengthStr()
##        Datasource = yield dev.getDataSourceStr()
##
##        self.createDict()
##
##        self.tdsDict['X0'] = float(X0) 
##        self.tdsDict['Xinc'] = float(Xinc)
##        self.tdsDict['Ymulti'] = float(Ymulti)
##        self.tdsDict['Yoff'] = float(Yoff)
##        self.tdsDict['Y0'] = float(Y0)
##        self.tdsDict['Datalength'] = int(Datalength) 
##        self.tdsDict['Datasource'] = Datasource

##    @setting(104, 'getcurve', returns='*2v')  # ??? why *2v ?
##    def getcurve(self, c):
##        dev = self.selectedDevice(c)
##        yield self.populateDict(c)
##        yield dev.encASCIIstr()
##        datastr = yield dev.getDataStr()
##        dataarray = numpy.fromstring(datastr, sep=',')
##        voltarray =(dataarray-self.tdsDict['Yoff'])*self.tdsDict['Ymulti']+self.tdsDict['Y0']
##        t0=self.tdsDict['X0']
##        dt=self.tdsDict['Xinc']
##        length=self.tdsDict['Datalength']        
##        tarray = t0 + dt*array(range(length))
##        intarr = numpy.vstack((tarray,voltarray))
##        answer = intarr.transpose()
##        returnValue(answer)

##    @setting(105, 'getvalue', returns='v')
##    def getvalue(self, c):
##        dev = self.selectedDevice(c)
##        answer = yield dev.getValueStr()
##        returnValue(answer)

##    @setting(108, 'setrms', returns='')
##    def setrms(self, c):
##        dev = self.selectedDevice(c)
##        answer = yield dev.setRMS()
##        #print 'success'
##        returnValue(answer)

##    @setting(107, 'setpk2pk', returns='')
##    def setpk2pk(self, c):
##        dev = self.selectedDevice(c)
##        answer = yield dev.setPeakToPeakStr()
##        #print 'success'
##        returnValue(answer)

__server__ = TektronixTDSServer()

if __name__ == '__main__':
    from labrad import util
    util.runServer(__server__)
