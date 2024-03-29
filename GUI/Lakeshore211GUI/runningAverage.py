""" This code is slightly modified version of an example code of MView by Noah"""
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
        self.input = self.addAnchor(name="data", type="input", data="float")
        self.output = self.addAnchor(name="running avg", type="output", data="float")
        self.setTitle("Running Avg")

    def setWindowWidth(self, width):
        self.window = width

    def onRefreshData(self):
        t1 = time.time()
        self.data.append(self.input.getData())
        self.data = self.data[-self.window : :]
        # print "window size is: ", self.window
        # print "self.data in running average:", self.data

        window = self.window

        try:
            # Modification to accomodate the initial lack of data for slow measurements
            if len(self.data) < window:
                ret = self.movingaverage(self.data, len(self.data))
            else:
                ret = self.movingaverage(self.data, window)

            oldMeta = self.input.getMetaData()
            if oldMeta != None:
                self.output.setMetaData((oldMeta[0], oldMeta[1], ret))
            self.output.setData(list(ret)[0])
        except:
            traceback.print_exc()

        t2 = time.time()

    def movingaverage(self, interval, window_size):
        window = np.ones(int(window_size)) / float(window_size)
        return np.convolve(interval, window, mode="valid")
