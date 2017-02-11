from MPipe import MPipe
import os
import sys, inspect
from glob import glob
from MWeb import web

class NodeTree:
    scene = None
    pipes = []
    #def __init__(self):
    nodes = []
    print os.getcwd()
    path = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))) 
    
    os.chdir(path+"\MNodes")
    print os.getcwd()
    for file in glob("*.py"):
        web.nodeFilenames.append(file)
        print file

    def getPipes(self):
        return self.pipes
        
    def addPipe(self,pipe):
        self.pipes.append(pipe)
        return self.pipes[-1]
        
    def deletePipe(self, pipeToDel):
        '''Delete pipe from tree'''
        # Connect both ends of the pipe to nothing
        pipeToDel.setLabel(None)
        start = pipeToDel.getStartAnchor()
        end = pipeToDel.getEndAnchor()
        start.connect(None)
        if end != None:
            end.connect(None)
        self.scene.removeItem(pipeToDel)
        for i,pipe in enumerate(self.pipes):
            if pipe is pipeToDel:
                self.pipes[i] = None
                del self.pipes[i]
        start.parentNode().pipeDisconnected()
        if end != None:
            end.parentNode().pipeDisconnected()
                
    def setScene(self, scene):
        self.scene = scene
        
    def getScene(self):
        return self.scene
        
    def connect(self, anchor, endAnchor = None):
        '''Connect anchors with a pipe.'''
        try:
            print "endAnchor:", endAnchor
            print "anchor:", anchor
            if endAnchor != None:
                self.pipes.append(MPipe(anchor, self.scene))
                self.pipes[-1].connect(endAnchor)
                endAnchor.connect(self.pipes[-1])
            # If the start anchor of the pipe is and output
                endAnchor.parentItem().pipeConnected(endAnchor, self.pipes[-1])
                endAnchor.pipeConnected(self.pipes[-1])
            else:
                if len(self.getPipes()) == 0:
                    self.pipe = self.addPipe(MPipe(anchor, self.scene))
                    
                else:
                    if self.getPipes()[-1].isUnconnected():
                        #print "using existing pipe"
                        self.getPipes()[-1].connect(anchor)
                        self.pipe =  self.getPipes()[-1]
                    else:
                        self.pipe = self.addPipe(MPipe(anchor, self.scene))
                    self.pipe = self.getPipes()[-1]
            anchor.pipeConnected(self.pipe)
            anchor.parentItem().pipeConnected(anchor, self.pipe)
            
            anchor.connect(self.pipes[-1])
        except  ValueError, e:
            print "ERROR:",e
            self.deletePipe(self.pipes[-1])

        
        
        
       
        
    def addNode(self, node):
        #print "adding node to scene:",self.scene
        node.setScene(self.scene)
        node.setTree(self)
        node.begin()
        #newNode = MNode(self.scene, self, **kwargs)
       # print newNode
        self.nodes.append(node)
        
       # print self.nodes[-1]
        return node
        
    def getNodes(self):
        return self.nodes
    def getGuiNodes(self):
        return [node for node in self.getNodes() if node.getType() == 'output']