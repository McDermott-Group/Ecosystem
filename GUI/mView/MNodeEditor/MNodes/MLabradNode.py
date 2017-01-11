from MNodeEditor.MNode import MNode
from MNodeEditor.MAnchor import MAnchor
class MLabradNode(MNode):
    def __init__(self,*args, **kwargs):
        super(MLabradNode, self).__init__(None,*args, **kwargs)
        self.setColor (52, 73, 94)

        self.device = args[0]
    def begin(self):
        super(MLabradNode, self).begin()
        
        # If the node represents a labrad device, then the title displayed on the node
        # should be the same as the title of the device
        self.title = self.device.getFrame().getTitle()
        # The color of a device node is blue
       
        for i,param in enumerate(self.device.getFrame().getNicknames()):
            self.addAnchor(MAnchor(param,self.scene,self.tree,  i, type = 'output'))
            
    def refreshData(self):
        index = 0
        try:
            if self.getType() == 'labrad_device':
                for i, anchor in enumerate(self.getAnchors()):
                    if(anchor.getType() == 'output' and anchor.getPipe() is not None):
                        anchor.getPipe().setData(self.device.getFrame().getReadings()[i] )
                        #print anchor.getPipe().getData()
                        index = index + 1
            # if web.keepGoing:
                # pass
                # threading.Timer(1, self.refreshData).start()
        except:
            traceback.print_exc()
            
    def getType(self):
        return self.mode
