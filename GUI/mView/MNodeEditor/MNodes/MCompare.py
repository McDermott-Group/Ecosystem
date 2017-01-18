from MNodeEditor.MNode import MNode
from MNodeEditor.MAnchor import MAnchor

class MCompare(MNode):
    def __init__(self, *args, **kwargs):
        super( MCompare, self).__init__(None, *args, **kwargs)
        self.setColor(94, 94, 54)
    def begin(self, *args, **kwargs):
        super( MCompare, self).begin()
        self.addAnchor(name = 'A', type = 'input')
        self.addAnchor(name = 'B', type = 'input')
        self.addAnchor(name = 'A > B', type = 'output')
        self.setTitle("Comparator")
        
    def refreshData(self):
        anchors = self.getAnchors()
        goodToGo = True
        
        if anchors[0] .getPipe() == None:
             goodToGo = False
        if anchors[1] .getPipe() == None:
             goodToGo = False
        if anchors[2] .getPipe() == None:
             goodToGo = False
             
        if goodToGo:
            data1 = anchors[0] .getPipe().getData()
            data2 = anchors [1].getPipe().getData()

            if data1 > data2:
                 anchors[2].getPipe().setData(1)
                 anchors [2].getLcd().display(1)
            else:
                anchors[2].getPipe().setData(0)
                anchors [2].getLcd().display(0)
            
            
