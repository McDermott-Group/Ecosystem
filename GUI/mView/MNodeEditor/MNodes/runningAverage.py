from MNodeEditor.MNode import MNode
from MNodeEditor.MAnchor import MAnchor
import numpy as np
import traceback
import time


class runningAverage(MNode):
    def __init__(self, *args, **kwargs):
        super(runningAverage, self).__init__(None, *args, **kwargs)
        self.begin()
        self.window = 3
        self.data = []

    def begin(self, *args, **kwargs):
        super(runningAverage, self).begin()
        self.input = self.addAnchor(name='data', type='input', data='float')
        self.output = self.addAnchor(
            name='running avg', type='output', data='float')
        # print "added anchor:", self.input
        # print "added anchor:", self.output
        self.setTitle("Running Avg")

    def setWindowWidth(self, width):
        self.window = width

    def onRefreshData(self):
        # print "Running average refreshingData"
        # traceback.print_stack()
        t1 = time.time()
        # print "here a"
        self.data.append(self.input.getData())
        self.data = self.data[-self.window::]
        # print "self.data in running average:", self.data
        # print "here b"

        # data1 = [del elem if elem == np.nan else elem for elem in data1 ]
        window = self.window
        # print "here c"
        #data2 = list(filter(lambda a: a is not np.nan, data1[-window*2::]))
        # print "here d"

        try:
            ret = self.movingaverage(self.data, window)
            oldMeta = self.input.getMetaData()
            if oldMeta != None:
                self.output.setMetaData((oldMeta[0], oldMeta[1], ret))
            self.output.setData(list(ret)[0])
        except:
            traceback.print_exc()

        # ret = [5]
        # print "here e"

        t2 = time.time()
        # print "time to refreshData in runningAverage:", t2-t1

    def movingaverage(self, interval, window_size):

        # print "here d a"
        window = np.ones(int(window_size)) / float(window_size)
        # print "here d b"
        return np.convolve(interval, window, mode='valid')
        # print "here d c"
