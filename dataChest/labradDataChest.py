from dataChest import dataChest
from labrad import units

class labradDataChest(dataChest):

    def createDataset(self):
        pass

    def addData(self, data):
        pass

    def getData(self, startIndex = np.nan, stopIndex = np.nan):
        pass

    def addParameter(self, paramName, paramValue, overwrite=False):
        try:
            units = paramValue.units
            value = paramValue[units]
        except AttributeError:
            units = None
            value = paramValue
        super(dataChest, self).addParameter(paramName, value, paramUnits=units, overwrite)

    def getParameter(self, *args, **kwargs):
        resp = super(dataChest, self).getParameter(args, kwargs)
