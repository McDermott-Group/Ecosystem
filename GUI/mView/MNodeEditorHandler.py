import MNodeEditor
class MNodeEditorHandler:
    def __init__(self, mainGui):
        self.nodeTree = MNodeEditor.NodeTree()
        self.nodeEditor = MNodeEditor.NodeGui(mainGui.devices, self.nodeTree)
        self.mainGui = mainGui
        
        for device in mainGui.devices:
            devnode = self.nodeTree.newNode(self.nodeTree, device = device,   mode = 'labrad_device')
            device.getFrame().setNode(devnode)
            outnode = self.nodeTree.newNode(self.nodeTree, mode = 'output')
            for devanchor in devnode.getAnchors():
                
                outanchor = outnode.addAnchor()
                self.nodeTree.connect(devanchor, outanchor)
          
            
    def showEditor(self):
        self.nodeEditor.exec_()
    