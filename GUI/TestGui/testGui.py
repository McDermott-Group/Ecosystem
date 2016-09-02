import sys
sys.dont_write_bytecode = True
import MGui             # Handles all gui operations. Independent of labrad.

#from PyQt4 import QtCore, QtGui

from Device import Device
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
        LeidenDRTemperature.addParameter("Pressure","pressure")
        LeidenDRTemperature.addParameter("Temperature", "temperature")
        #LeidenDRTemperature.selectDeviceCommand("select_device", 0)
        LeidenDRTemperature.addPlot()

        LeidenDRTemperature.setPlotRefreshRate(0.5)
        LeidenDRTemperature.setRefreshRate(1)

        LeidenDRTemperature.setYLabel("Hi", "Custom Units")
        LeidenDRTemperature.begin()
        self.devices.append(LeidenDRTemperature)

        
        # Start the datalogger. This line can be commented
        # out if no datalogging is required.
        self.chest = dataChestWrapper(self.devices)
        
        # Create the gui
        self.gui = MGui.MGui()

        self.gui.setRefreshRate(1)

        self.gui.startGui(self.devices, 'Leiden Gui', 'Leiden Data', tele)

            
# In phython, the main class's __init__() IS NOT automatically called
try:
    viewer = nViewer()  
    viewer.__init__()
except:
    pass