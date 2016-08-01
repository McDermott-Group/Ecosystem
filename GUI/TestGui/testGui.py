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
        ##################################################################
        # How to Use nViewer:    
        ################################################################
        #   nViewer can be used with any labrad server, and given a new device class (it must have a "prompt" function), anything else.
        #   It is meant to be a tool which allows much, much easier creation of straightforward gui's.
        #   To create you own, make a new class in which you establish a connection to labrad, create new
        #   device instances, and start the gui.
        #
        #
        # Here are the steps to create your own gui.
        # 1. Establish LabRad connection
        #       cxn = labrad.connect()
        #
        # 2. Create Device
        #        ex = Device("NAME OF LABRAD SERVER", 
        #                        "TITLE TO BE SHOWN ON GUI", 
        #                        [LIST OF FIELDS TO BE DISPLAYED ON GUI],
        #                        [LIST OF THOSE FIELDS' CORRESPONDING SERVER SETTINGS], 
        #                        [ARGUMENTS TO BE PASSED TO THOSE SETTINGS]
        #                        CONNECTION REFERENCE,
        #                        ["LIST","OF","BUTTONS"], 
        #                        ["SETTINGS", "ACTIVATED", "BY BUTTONS"], 
        #                        ["ALERT TO BE DISPLAYED WITH EACH BUTTON PRESS", "NONE IF NO MESSAGE"]
        #                        ["ARGUMENTS PASSED TO THE SETTINGS TRIGGERED BY THE BUTTONS"]
        #                       "yAxis Label"(OPTIONAL),
        #                       "SELECT DEVICE COMMAND (OPTIONAL FOR SERVERS THAT DO NOT REQUIRE DEVICE SELECTION)", 
        #                        "DEVICE NUMBER",)
        # 3. Start the dataChest datalogger, this line can be commented out
        #   if no datalogging is required.
        #           self.chest = dataChestWrapper(self.devices)
        #   
        # 4. Start nGui and name the window
        #       self.gui = NGui.NGui()
        #       self.gui.startGui(self.devices, Window title)
        #
        # 5. Initialize nViewer OUTSIDE OF THE CLASS
        #       viewer = nViewer()  
        #       viewer.__init__()
        ###################################################################
    
        LeidenDRTemperature = Device("Random")
        LeidenDRTemperature.connection(cxn)

        LeidenDRTemperature.setServerName("my_server")
        LeidenDRTemperature.addParameter("Pressure","pressure", None)
        LeidenDRTemperature.addParameter("Temperature", "temperature", None)
        #LeidenDRTemperature.selectDeviceCommand("select_device", 0)
        LeidenDRTemperature.addPlot()
        LeidenDRTemperature.setPlotRefreshRate(1)
        LeidenDRTemperature.setRefreshRate(0.1)
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
viewer = nViewer()  
viewer.__init__()