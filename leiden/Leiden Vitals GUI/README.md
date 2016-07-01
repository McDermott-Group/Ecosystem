# mView
#### What is mView
mView is a programming framework that allows for the easy creation of GUI applications for use with lab equipment. With Mview, simple control and display elements can be easily configured.
  - Buttons
  - Numerical Readouts
  - Plots
  
More advanced features include
- Datalogging using the Datachest Library
- Email and Text Notifications

#### How to use mView
Configuring a new GUI using mView is easy.
#### Step 1: Importing necessary libraries
```python
from Device import Device
from multiprocessing.pool import ThreadPool
import threading
import labrad
import labrad.units as units
from dataChestWrapper import *
```
If you are not using labrad, do not import the labrad libraries.
#### Step 2: Configuring the custom main class
First, we must create the class that will hold our code. Let's call it 'labOne'.
```python
class labOne:
	gui = None 
	devices =[] # An empty array to hold all devices.
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
	...
```
#### Step 3: Configuring devices
It is time now to add devices to your gui. Each device you attatch to your GUI shown up in it's own section of the gui along with all of its attributes.
We configure all of our devices inside of the main class we created in step 2.

In our lab, we have a helium compressor.
We need to be able to do three things.
1. Read temperature values from the compressor.
2. Tell the compressor to turn on and off.
3. Plot the temperature values.

Let's now create our device.
```python
Compressor = Device("Compressor")
```
What we have done here is instantiate a new labrad Device object named "Compressor" this is the name that will show up in the GUI.
>Note that this device class is specifically for use with labrad server, but a new device class can easily be written.

For labrad devices, we must specify a server name. This is the name of the device's server.
```python
Compressor.setServerName("cp2800_compressor")
```
Now, mView knows where it can find the device.  
As mentioned, we need a way to turn the compressor on or off, we add this functionality using buttons, which show up as clickable buttons on the GUI.  

First let's create a button that turns the compressor on.
```python
Compressor.addButton("Turn On", "You are about to turn the compressor on.", "turn_on", None)
```
Note that there are four aguments passed to this method.
* The first arguement tells the gui that the text shown on the button should be "Turn on." 
* The second arguement says that a warning message should be displayed when the button is clicked. The value 'None' can be used if no warning is to be displayed.
* The third arguement tells the device class which Labrad setting should be called when the button is clicked. 
* The fourth argument allows arguments to be passed with the setting. The default fourth argument is `None`, so it does not need to be specified.  

Now that we have configured the buttons, it is time to move onto the data readouts. In order to add numerical readouts to the GUI, we use the `mView.addParameter()` method. We have four temperatures that we want to read from our compressor. 
>Note: The compressor's server returns an array of data. This is not a problem as we can specify the index of the reading in the array.
```python
Compressor.addParameter("Input Water Temperature", "temperaturesforgui", None, 0)
Compressor.addParameter("Output Water Temperature", "temperaturesforgui", None, 1)
Compressor.addParameter("Helium Temperature", "temperaturesforgui", None, 2)
Compressor.addParameter("Oil Temperature", "temperaturesforgui", None, 3)
```

The `mView.addParameter()` method takes three to four arguments.
* The first argument specifies the label to be shown in front of the readout. This name is also used as the independent variable when plotting and datalogging.
* The second argument specifies the server setting that returns the desired reading.
* The third argument allows arguments to be passed to the setting.
* The fourth argument is **only** used when the specified server setting returns an array.
> Warning: As of writing, mView is able to accept integers and floating point numbers, lists, labrad values with units and labrad lists with units.  

Next, we must specify a name for our Y axis when graphing and datalogging.
```python
Compressor.setYLabel("Temperature")
```
Units will automatically be added.

##### Labrad specific setup:
When using labrad, there are a couple more steps that we must take in order allow mView to properly communicate with the device.
Above, we showed how to create a connection to labrad, now we must use it. We use the `mView.connection()` when passing the `cxn` pointer that we created.
```python
Compressor.connection(cxn)
```
Next, as we do in the command line, we must specify the labrad device index.
```python
Compressor.selectDeviceCommand("select_device", 0)
```

#### Step 4: Configuring The GUI
There are a few otherthings that we can do include on the GUI. These are optional, but useful tools.
##### The integrated grapher
If desired, we may add a graphing window to any GUI device. To do this, use the `mView.addPlot()` method.
There are two types of plots that can be displayed, one is a scrolling plot that shows a fixed number of datapoints, the second is a plot to show the entire dataset.  

The following code will add a plot which shows the entire dataset.
```python
Compressor.addPlot()
```
In order to only show a certain number of points, we specify a number of data point
```python
Compressor.addPlot(1000)
```
This will tell the grapher to show only the most recent 1000 points of data.

>WARNING: This implementation will soon change to allow for a more interactive on-screen plotter.

#### Step 5: Enabling Our Device
In order for our device to show up on the gui, we must do two things.
First we must tell the device class to start using the `device.begin()` method. This will start the necessary threads used in communicating with the device. Second, we must add our device to a list of all devices, which will be used when starting the GUI itself.  
In order to start the device, simply type
```python
Compressor.begin()
```
>Warning: This line must come after everything else, as any changes made (i.e. adding a button) after the device has begun will not have any effect.

After Doing this, we must add the device to a list.
```python
self.devices.append(Compressor)
```

##### The result
Our compressor configuration should look something like
```python
Compressor = Device("Compressor")
Compressor.setServerName("cp2800_compressor")
Compressor.addButton("Turn Off", "You are about to turn the compressor off." , "turn_off", None)
Compressor.addButton("Turn On", "You are about to turn the compressor on." , "turn_on", None)
Compressor.addParameter("Input Water Temperature", "temperaturesforgui", None, 0)
Compressor.addParameter("Output Water Temperature", "temperaturesforgui", None, 1)
Compressor.addParameter("Helium Temperature", "temperaturesforgui", None, 2)
Compressor.addParameter("Oil Temperature", "temperaturesforgui", None, 3)
Compressor.addPlot()
Compressor.setYLabel("Temperature")
Compressor.selectDeviceCommand("select_device", 0)
Compressor.connection(cxn)
Compressor.begin()
self.devices.append(Compressor)
```
Congratdulations, you have created a device!
##### Datachest
The GUI also supports datachest datalogging.
Configuring datachest itself will not be covered here as it is explained in Datachest's README. Instead, we will cover how to enable Datachest datalogging in mView. To enable datalogging, simply type
```python
self.chest = dataChestWrapper(self.devices)
```
This will enable datalogging, nothing elsee needs to be done.  
The data that is logged includes ONLY the valid readings that are displayed on the gui. 
>Note: The datasets are stored according to the name of the device, so if the device name changes, a new dataset will be created. Otherwise, previous datasets are added to.
##### Notifier
mViewer is still dependent on the telecomm Labrad server for all of its notifications. This requires labrad AND the telecomm to be running even when the notifier functionality is not being used.  
> NOTE: This will change

At the beginning of the class, we created a variable called `tele` which points to the telecomm server. This was important, and will be used in a later step.


#### Step 6: Finishing up
Lastly, we need to start the GUI. We must pass our list of device, a name for the GUI, a name for the dataset and a reference to the telecomm server.
```python
self.gui = MGui.MGui()
self.gui.startGui(self.devices, 'labOne GUI', 'labOne Data', tele)
```
>WARNING: These **must** be the last two lines in our labOne class. As soon as these lines are called, the main thread is occupied by the GUI and our labOne class will stop running.

In python, a main class's `__init__` function is NOT called by itself, so we must call it **outside** of the class.
```python
viewer = nViewer()	
viewer.__init__()
```
These lines should go at the botton, again they **must** be **outside** the main class.

\\TODO add descriptions of classes and in depth use of writing custom device classes
### Version
1.0.1
