class ManagedDeviceServer(DeviceServer):
    """Builds off DeviceServer class by adding methods to interface with a
    server that manages different devices.  Devices are broadcast from that
    server and then added here when appropriate.
    """
    name = 'Generic Device Server'
    deviceManager = 'Device Manager'

    messageID = 21436587

    @inlineCallbacks
    def initServer(self):
        DeviceServer.initServer(self)
        # register a message handler for connect/disconnect messages
        handler = lambda c, data: self.handleDeviceMessage(*data)
        self._cxn.addListener(handler, ID=self.messageID)
        if self.deviceManager in self.client.servers:
            yield self.connectToDeviceManager()

    def makeDeviceName(self, device, server, address):
        return server + ' - ' + address

    @inlineCallbacks
    def handleDeviceMessage(self, device, server, address, isConnected=True):
        print('Device message:', device, server, address, isConnected)
        name = self.makeDeviceName(device, server, address)
        if isConnected: # add device
            self.addDevice(name, device=device)
        else: # remove device
            yield self.removeDevice(name)

    @inlineCallbacks
    def connectToDeviceManager(self):
        """
        """
        yield self.client.refresh()
        manager = self.client[self.deviceManager]
        #If we have a device identification function register it with the device manager
        if hasattr(self, 'deviceIdentFunc'):
            yield manager.register_ident_function(self.deviceIdentFunc)
        #Register ourself as a server who cares about devices
        devs = yield manager.register_server(list(self.deviceWrappers.keys()), self.messageID)
        # the devs list is authoritative any devices we have
        # that are _not_ on this list should be removed
        names = [self.makeDeviceName(*dev[:3]) for dev in devs]
        additions = [self.handleDeviceMessage(*dev) for dev in devs]
        deletions = [self.removeDevice(name)
                     for name in self.device_guids.keys()
                     if name not in names]
        yield defer.DeferredList(additions + deletions)

    def serverConnected(self, ID, name):
        if name == self.deviceManager:
            self.connectToDeviceManager()

    def refreshDeviceList(self):
        return
