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
        #print "initializing MVirtualDeviceNode"
        self.addAnchor(name = 'input 1', type = 'input')
        self.setTitle("Virtual Device")
        #print "creating new virtual device named", self.getTitle()
        self.associatedDevice = MVirtualDevice(self.getTitle())
        self.setDevice(self.associatedDevice)
        self.associatedDevice.addPlot()
        self.associatedDevice.addParameter(self.getAnchors()[0].getLabel())
        self.associatedDevice.getFrame().setNode(self)
        web.gui.color = (52, 73, 94)
        web.gui.addDevice(self.associatedDevice)
        
    def refreshData(self):
        print "virtual device refreshing data"
        
        reading = []
        for anchor in self.getAnchors():
            reading.append(anchor.getPipe().getData())
            anchor.getLcd().display(reading[-1])
        
        self.getDevice().retrieveFromNode(reading)
        
    def pipeConnected(self, anchor, pipe):
        '''called when a pipe is added'''
        print "pipeConnected called"
        self.addAnchor(name = '', type = 'input')
        pass