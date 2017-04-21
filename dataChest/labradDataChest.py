from dataChest import dataChest
from labrad import units

class labradDataChest(dataChest):

    def createDataset(self, *args, **kwargs):
        super(labradDataChest, self).createDataset(*args, **kwargs)

    def addData(self, data):
        indepVars, depVars = self.getVariables()
        unitsList = [var[3] for var in indepVars + depVars]
        for row in data:
            for i in range(len(row)):
                if unitsList[i] != '':
                    try:
                        row[i] = [x[unitsList[i]] for x in row[i]]
                    except TypeError:
                        row[i] = row[i][unitsList[i]]
        super(labradDataChest, self).addData(data)

    def getData(self, *args, **kwargs):
        data = super(labradDataChest, self).getData(*args, **kwargs)
        indepVars, depVars = self.getVariables()
        unitsList = [var[3] for var in indepVars + depVars]
        for row in data:
            row = [units.Value(row[i], unitsList[i]) for i in range(len(row))]
        return data

    def addParameter(self, paramName, paramValue, overwrite=False):
        try:
            units = paramValue.units
            value = paramValue[units]
        except AttributeError:
            units = ''
            value = paramValue
        super(labradDataChest, self).addParameter(paramName, value, paramUnits=units, overwrite=overwrite)

    def getParameter(self, paramName, **kwargs):
        resp = super(labradDataChest, self).getParameter(paramName, **kwargs)
        if self.getParameterUnits(paramName) is not None:
            return units.Value(*resp)
        else:
            return resp
