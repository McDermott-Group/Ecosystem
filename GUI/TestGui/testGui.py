import sys
sys.dont_write_bytecode = True
import MGui             # Handles all gui operations. Independent of labrad.
from MWeb import web
#from PyQt4 import QtCore, QtGui

from MDevices.Device import Device
from multiprocessing.pool import ThreadPool
import threading
import labrad
import labrad.units as units
from dataChestWrapper import *

class nViewer:
    gui = None
    devices =[]
    
    def __init__(self, parent = None):
        # Establish a connection to labrad
        try:
            cxn = labrad.connect()
        except:
            print("Please start the labrad manager")
            sys.exit(0)
        try:
            tele = cxn.telecomm_server
        except:
            print("Please start the telecomm server")
            sys.exit(1)
      
        LeidenDRTemperature = Device("Random")
        LeidenDRTemperature.connection(cxn)

        LeidenDRTemperature.setServerName("my_server")
        LeidenDRTemperature.addParameter("Random Pressure","pressure", None, log = False)
        LeidenDRTemperature.addParameter("Random Temperature", "temperature", None)
        #LeidenDRTemperature.selectDeviceCommand("select_device", 0)
        LeidenDRTemperature.addPlot()
        LeidenDRTemperature.setPlotRefreshRate(0.5)
        LeidenDRTemperature.setRefreshRate(0.5)
        LeidenDRTemperature.setYLabel("Hi", "Custom Units")
        LeidenDRTemperature.begin()
        self.devices.append(LeidenDRTemperature)

        localTemp = Device("Local Temperatures")
        localTemp.connection(cxn)
        localTemp.setServerName("my_server2")
        localTemp.addParameter("Outside Temperature", "temperature", None)
        localTemp.addButton("Madison Weather",  None, "changeLocation", 53715)
        localTemp.addButton("St. Paul Weather", None,  "changeLocation", 55118)

        localTemp.addPlot()
        localTemp.setPlotRefreshRate(2)
        localTemp.setRefreshRate(2)
        localTemp.setYLabel("Temperature")
        localTemp.begin()
        self.devices.append(localTemp)
        
        
        # Start the datalogger. This line can be commented
        # out if no datalogging is required.
        #print self.devices
       # self.chest = dataChestWrapper(self.devices)
        
        # Create the gui
        self.gui = MGui.MGui()
        self.gui.setRefreshRate(0.5)
        self.gui.startGui(self.devices, 'Leiden Gui', 'Leiden Data', tele)
        
        
# In phython, the main class's __init__() IS NOT automatically called
viewer = nViewer()  
viewer.__init__()