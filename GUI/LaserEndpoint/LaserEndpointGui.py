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
import time
from tendo import singleton
class nViewer:
    gui = None
    devices =[]
    
    def __init__(self, parent = None):
        # Establish a connection to 
        try:
            me = singleton.SingleInstance() # will sys.exit(-1) if other instance is running
        except:
            print("Multiple instances cannot be running")
            time.sleep(2)
            sys.exit(1)
        try:
            cxn = labrad.connect()
        except:
            print("Please start the labrad manager")
            time.sleep(3)
            sys.exit(0)
        try:
            tele = cxn.telecomm_server
        except:
            print("Please start the telecomm server")
            time.sleep(3)
            sys.exit(1)
        
        laser = Device("Laser Endpoint Monitor")
        laser.connection(cxn)

        laser.setServerName("goldstein_s_laser_endpoint_monitor")
        laser.addParameter("Voltage","get_reading", None)
        laser.selectDeviceCommand("select_device", 0)

        laser.addPlot()
        laser.setPlotRefreshRate(0.02)
        laser.setRefreshRate(0.02)
        laser.setYLabel("Strength")
        laser.begin()
        self.devices.append(laser)

        
        # Start the datalogger. This line can be commented
        # out if no datalogging is required.
        self.chest = dataChestWrapper(self.devices)
        
        # Create the gui
        self.gui = MGui.MGui()
        self.gui.setRefreshRate(0.02)
        self.gui.startGui(self.devices, 'Laser Endpoint System Gui', 'Laser Endpoint Data', tele)
        
        
# In phython, the main class's __init__() IS NOT automatically called
viewer = nViewer()  
viewer.__init__()