from MPipe import MPipe
from MNode import MNode
class NodeTree:
    scene = None
    pipes = []
    nodes = []
    def getPipes(self):
        return self.pipes
        
    def addPipe(self,pipe):
        self.pipes.append(pipe)
        return self.pipes[-1]
        
    def deletePipe(self, pipeToDel):
        '''Delete pipe from tree'''
        # Connect both ends of the pipe to nothing
        pipeToDel.setLabel(None)
        if pipeToDel.getStartAnchor().getType() == 'input':
             pipeToDel.getStartAnchor().setLabel('Output')
        else:
            pipeToDel.getEndAnchor().setLabel('Output')
        pipeToDel.getStartAnchor().connect(None)
        pipeToDel.getEndAnchor().connect(None)
        for i,pipe in enumerate(self.pipes):
            if pipe is pipeToDel:
                pipe.destruct()
                del pipe
                self.pipes[i] = None
                del self.pipes[i]
                
    def setScene(self, scene):
        self.scene = scene
        
    def getScene(self):
        return self.scene
        
    def connect(self, startAnchor, endAnchor):
        '''Connect two anchors with a pipe.'''
        self.pipes.append(MPipe(startAnchor, self.scene))
        self.pipes[-1].connect(endAnchor)
        # If the start anchor of the pipe is and output
        if startAnchor.getType() == 'output':
            print "output label:", startAnchor.getLabel()
            # The pipe label should be the label of the start anchor
            self.pipes[-1].setLabel(startAnchor.getLabel())
            # The end anchor's label should be the same as the pipe's
            endAnchor.setLabel(self.pipes[-1].getLabel())
        else:
            print "output label:", endAnchor.getLabel()
            self.pipes[-1].setLabel(endAnchor.getLabel())
            startAnchor.setLabel(self.pipes[-1].getLabel())
        startAnchor.connect(self.pipes[-1])
        endAnchor.connect(self.pipes[-1])
     
    def newNode(self,  tree, **kwargs):
        newNode = MNode(self.scene, tree, **kwargs)
        self.scene.addItem(newNode)
        self.nodes.append(newNode)
        return newNode
        
    def getNodes(self):
        return self.nodes
    def getGuiNodes(self):
        return [node for node in self.getNodes() if node.getType() == 'output']