gpib_server
	uses visa to list all devices
	for each device, sends out send_named_message with server and address
GPIBManagedServer
	ManagedDeviceServer
		connectToDeviceManager - registers devices with DeviceManager
		handleDeviceMessage - dev.connect(server, addr)
self.devices - dict of devices

_doRefresh (DeviceServer) and handleDeviceMessage(ManagedDeviceServer) do the same thing, that is:
	dev.connect(server, addr)
	add/remove devices from self.devices

named messages above go to DeviceManager, but then DeviceManager sends appropriate devs back to each server

gpib.py and devices.py within the labrad core code have a lot of duplicate code and inherit from old device code.  I have updated and simplified the classes in these files, and they are now stored here as gpib.py and devices.py.  These should replace the files in the core labrad code to use them.

what does x = defer.DeferredLock() do and x.run(fn)?
