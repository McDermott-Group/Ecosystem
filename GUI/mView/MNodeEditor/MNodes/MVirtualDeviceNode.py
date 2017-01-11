from MNodeEditor.MNode import MNode
from MNodeEditor.MAnchor import MAnchor
from MDevices.MVirtualDevice import MVirtualDevice
from MWeb import web
class MVirtualDeviceNode(MNode):
    def __init__(self, *args, **kwargs):
       
        super( MVirtualDeviceNode, self).__init__(None, *args, **kwargs)
        self.setColor(52, 94, 73)
        self.title = 'Output'
        
    def begin(self, *args, **kwargs):
        super( MVirtualDeviceNode, self).begin()
        print "initializing MVirtualDeviceNode"
        self.addAnchor(name = 'input 1', type = 'input')
        self.addAnchor(name = 'input 2', type = 'input')
        self.setTitle("Virtual Device")
        print "creating new virtual device named", self.getTitle()
        self.associatedDevice = MVirtualDevice(self.getTitle())
        self.associatedDevice.addParameter(self.getAnchors()[0].getLabel())
        web.gui.addDevice(self.associatedDevice)
        
    def pipeConnected(self, anchor, pipe):
        '''called when a pipe is added'''
        pass