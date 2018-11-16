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

what does x = defer.DeferredLock() do and x.run(fn)?