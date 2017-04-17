from dataChest import dataChest
from labrad import units

class labradDataChest(dataChest):

    def createDataset(self, *args, **kwargs):
        super(labradDataChest, self).createDataset(*args, **kwargs)

    def addData(self, data):
        indepVars, depVars = self.getVariables()
        unitsList = [var[3] for var in indepVars + depVars]
        for row in data:
            row = [row[i][unitsList[i]] for i in range(len(row))]
        super(labradDataChest, self).addData(data)

    def getData(self, *args, **kwargs):
        super(labradDataChest, self).addData(*args, **kwargs)
        indepVars, depVars = self.getVariables()
        unitsList = [var[3] for var in indepVars + depVars]
        for row in data:
            row = [units.Value(row[i], unitsList[i]) for i in range(len(row))]

    def addParameter(self, paramName, paramValue, overwrite=False):
        try:
            units = paramValue.units
            value = paramValue[units]
        except AttributeError:
            units = None
            value = paramValue
        super(labradDataChest, self).addParameter(paramName, value, paramUnits=units, overwrite=overwrite)

    def getParameter(self, paramName, **kwargs):
        resp = super(labradDataChest, self).getParameter(paramName, **kwargs)
        if self.getParameterUnits(paramName) is not None:
            return units.Value(*resp)
        else:
            return resp
