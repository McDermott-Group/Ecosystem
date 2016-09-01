import MNodeEditor
import MAnchor
import MNodeTree
from MWeb import web

class MNodeEditorHandler:
    def __init__(self, mainGui):
        # Create a nodeTree
        self.nodeTree = MNodeTree.NodeTree()
        # Create a nodeEditor GUI window
        self.nodeEditor = MNodeEditor.NodeGui(mainGui.devices, self.nodeTree)
        # We need a reference to the main gui that allows us to manipulate mView
        #self.mainGui = mainGui
        # Create a new node to represent each device in the node tree
        for device in web.devices:
            devnode = self.nodeTree.newNode(self.nodeTree, device = device,   mode = 'labrad_device')
            # Tell the device's frame what it's node is
            device.getFrame().setNode(devnode)
            # Create nodes representing the tiles in the main mView window
            outnode = self.nodeTree.newNode(self.nodeTree, mode = 'output')
            # An anchor has been created on the device node for each parameter that it
            # has, create a ouput node that is able to connect to all of these
            self.scene = self.nodeTree.getScene()
            
            for devanchor in devnode.getAnchors():
                outanchor = outnode.addAnchor(MAnchor.MAnchor('Gui Readout',self.scene,self.nodeTree, len(outnode.getAnchors()), type = 'input'))
                # Connect the device anchor and output anchor
                self.nodeTree.connect(devanchor, outanchor)
          
            
    def showEditor(self):
        self.nodeEditor.exec_()
    def getTree(self):
        return self.nodeTree
        