from MNodeEditor.MNode import MNode
from MNodeEditor.MAnchor import MAnchor

class MCompare(MNode):

    def __init__(self, *args, **kwargs):
        super( MCompare, self).__init__(None, *args, **kwargs)
        self.setColor(94, 94, 54)
        
    def begin(self, *args, **kwargs):
        super( MCompare, self).begin()
        self.addAnchor(name = 'A', type = 'input', data = 'float')
        self.addAnchor(name = 'B', type = 'input', data = 'float')
        self.addAnchor(name = 'A > B', type = 'output')
        self.setTitle("Comparator")
        
    def refreshData(self):
        print "refreshing data"
        anchors = self.getAnchors()
        goodToGo = True
        

       
        data1 = anchors[0].getData()
        data2 = anchors [1].getData()

        if data1 > data2:
                anchors[2].setData(1)

        else:
            anchors[2].setData(0)

            
            
