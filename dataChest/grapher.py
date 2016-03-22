import os
import numpy as np
from PyQt4 import QtCore, QtGui
from matplotlib.figure import Figure
import matplotlib.cm as cm
from matplotlib.backends.backend_qt4agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar)
from dataChest import *


class Main(QtGui.QWidget):
    
    def __init__(self, parent=None):
        #print "__init__ called"
        super(Main, self).__init__(parent)

    
        self.pathRoot=QtCore.QString('Z:\mcdermott-group\DataChest')

        self.filters =QtCore.QStringList()
        self.filters.append("*.hdf5")
        
        self.dataChest = dataChest()
        #self.fig_dict = {}

        self.setWindowTitle('Data Chest Image Browser')
        self.setWindowIcon(QtGui.QIcon('rabi.jpg')) #add in rabi plot


        self.model = QtGui.QFileSystemModel(self)
        self.model.setRootPath(self.pathRoot)
        self.model.setNameFilterDisables(False)
        self.model.nameFilterDisables()
        self.model.setNameFilters(self.filters)

        self.indexRoot = self.model.index(self.model.rootPath())

        self.directoryBrowserLabel = QtGui.QLabel(self)
        self.directoryBrowserLabel.setText("Directory Browser:")
        
        self.directoryTree = QtGui.QTreeView(self)
        self.directoryTree.setModel(self.model)
        self.directoryTree.setRootIndex(self.indexRoot)
        self.directoryTree.clicked.connect(self.directoryTreeClicked)


        self.plotTypesListLabel = QtGui.QLabel(self)
        self.plotTypesListLabel.setText("Available Plot Types:")

        self.plotTypesList =QtGui.QListWidget(self)
        self.mplwindow =QtGui.QWidget(self)


        self.mplvl = QtGui.QVBoxLayout(self.mplwindow)

        self.plotTypesList.itemClicked.connect(self.changePlotType)

        self.gridLayout = QtGui.QGridLayout(self)
        self.gridLayout.addWidget(self.directoryBrowserLabel, 0,0)
        self.gridLayout.addWidget(self.directoryTree, 1,0)

        self.gridLayout.addWidget(self.plotTypesListLabel, 2,0)
        self.gridLayout.addWidget(self.plotTypesList, 3,0)
        
        self.gridLayout.addWidget(self.mplwindow, 0,1,5,1) 

        self.currentFig = Figure()
        self.addFigureToCanvas(self.currentFig)

        self.filePath =""
        self.fileName =""

    def convertWindowsPathToDvPathArray(self, windowsPath):
        
        #print "convertWindowsPathToDvPathArray"
        #print "windowsPath=", windowsPath
        #Z:/mcdermott-group/DataChest
        if 'Z:/mcdermott-group/DataChest/' in windowsPath:
            windowsPath = windowsPath.replace('Z:/mcdermott-group/DataChest/', '')
        elif 'Z:/mcdermott-group/DataChest' in windowsPath:
            windowsPath = windowsPath.replace('Z:/mcdermott-group/DataChest', '')
        windowsPath = windowsPath.replace('.dir', '')
        return windowsPath.split('/')
        
    def changePlotType(self, item):
        #print "changePlotType called"
        plotType = str(item.text())
        print "plotType=", plotType
        print "self.fileName=", self.fileName
##        if self.fileName != fileName: #**log plot type now
        self.removeCurrentFig()
        self.currentFig = self.figFromFileInfo(self.dvPath, self.fileName, plotType)
        self.addFigureToCanvas(self.currentFig)
##        self.fileName = fileName
            
    #def addfig(self, name, fig):
        #self.fig_dict[name] = fig
        #self.plotTypesList.addItem(name)

    def addFigureToCanvas(self, fig):
        #print "addFigureToCanvas called"
        self.canvas = FigureCanvas(fig)
        self.mplvl.addWidget(self.canvas)
        self.canvas.draw()
        self.toolbar = NavigationToolbar(self.canvas, 
                self.mplwindow, coordinates=True)
        self.mplvl.addWidget(self.toolbar)

    def removeCurrentFig(self):
        #print "removeCurrentFig called"
        self.mplvl.removeWidget(self.canvas)
        self.canvas.close()
        self.mplvl.removeWidget(self.toolbar)
        self.toolbar.close()
        self.currentFig.clf()
        
    @QtCore.pyqtSlot(QtCore.QModelIndex)
    def directoryTreeClicked(self, index):
        #print "directoryTreeClicked called"
        indexItem = self.model.index(index.row(), 0, index.parent())
        fileName = str(self.model.fileName(indexItem))
        #print "fileName=", fileName
        filePath = str(self.model.filePath(indexItem))
        #print "filePath=", filePath
        
        if ".hdf5" in filePath: #removes fileName from path if file is chosen
            filePath = filePath[:-(len(fileName)+1)]
            
        if self.fileName != fileName or self.filePath != filePath: #if an actual change occurs update
            self.dvPath = self.convertWindowsPathToDvPathArray(filePath)
            self.filePath = filePath
            self.fileName = fileName

            if ".hdf5" in fileName: #i.e. not a directory else leave as is til a file is selected
                self.removeCurrentFig() #removes old figure, needs garbage collection too 
                self.currentFig = self.figFromFileInfo(self.dvPath, self.fileName) #figFromFileInfo
                self.addFigureToCanvas(self.currentFig)
                    
    def updatePlotTypesList(self, plotTypes):
        self.plotTypesList.clear()
        for element in plotTypes:
            #print "element=", element
            if ".dir" not in str(element) and ".ini" not in str(element):
                item = QtGui.QListWidgetItem(str(element),self.plotTypesList)    

    def categorizeDataset(self, variables):
        indepVarsList = variables[0]
        numIndepVars = len(indepVarsList)
        if numIndepVars == 1:
            return "1D"
        elif numIndepVars == 2:
            return "2D"
        else:
            return (str(numIndepVars)+"D")

    def supportedPlotTypes(self, dimensionality):
        if dimensionality == "1D":
            plotTypes = ["1D", "Histogram"]
        elif dimensionality == "2D":
            plotTypes = ["2D"]
        else:
            plotTypes = []
        return plotTypes

    def plot1D(self, dataset, variables, plotType):
        if plotType == None:
            plotType = self.supportedPlotTypes("1D")[0] #defaults
        elif plotType not in self.supportedPlotTypes("1D"):
            print "Unrecognized plot type was provided"
            #return bum fig
            
        fig = Figure(dpi=100)
        ax = fig.add_subplot(111)
        indepVars = variables[0]
        depVars = variables[1]
        xlabel = self.dataChest.getParameter("xlabel")
        if xlabel is None:
            xlabel = indepVars[0][0]
        ylabel = self.dataChest.getParameter("ylabel") #for data with more than one dep, recommend ylabel
        if ylabel is None:
            ylabel = self.dataChest.getDatasetName()
        ax.set_xlabel(xlabel+" "+"("+indepVars[0][3]+")")
        ax.set_ylabel(ylabel+" "+"("+depVars[0][3]+")") #for multiple deps with different units this is ambiguous
        plotTitle = self.dataChest.getParameter("PlotTitle")
        if plotTitle is None:
            plotTitle = self.dataChest.getDatasetName()
        ax.set_title(plotTitle)
        if plotType =="1D":
            for ii in range(0, len(depVars)):
                for rowIndex in range(0,len(dataset)):
                    if rowIndex == 0:
                        x = []
                        x = x + dataset[rowIndex][0]
                        y = []
                        y = y + dataset[rowIndex][1+ii]
                ax.plot(x, y, label = depVars[ii][0])                
            ax.legend()
        elif plotType == "Histogram": #adjust bin size
            for ii in range(0, len(depVars)):
                for rowIndex in range(0,len(dataset)):
                    if rowIndex == 0:
                        x = []
                        x = x + dataset[rowIndex][0]
                        y = []
                        y = y + dataset[rowIndex][1+ii]
                ax.hist(y, 100, normed=1, alpha=0.5, label = depVars[ii][0]) 
            ax.legend()
        return fig
            
    def figFromFileInfo(self, dvPath, fileName, selectedPlotType = None):
        #print "figFromFileInfo called"
        #print "dvPath=", dvPath
        self.dataChest.cd(dvPath) 
        self.dataChest.openDataset(fileName) 
        variables = self.dataChest.getVariables()
        dataCategory = self.categorizeDataset(variables)
        #otherwise refer to dataset name needs to be implemented
        dataset = self.dataChest.getData()
        if dataCategory == "1D":
            self.updatePlotTypesList(self.supportedPlotTypes(dataCategory))
            fig = self.plot1D(dataset, variables, selectedPlotType)
        elif dataCategory =="2D": #was "2D Sweep"
            fig = Figure(dpi=100)
            self.updatePlotTypesList(self.supportedPlotTypes(dataCategory)) #Trajectory
##            ax = fig.add_subplot(111)
##            ax.set_xlabel(indepVars[0][0]+" "+"("+indepVars[0][1]+")")
##            ax.set_ylabel(indepVars[1][0]+" "+"("+indepVars[1][1]+")")
##            ax.set_title(plotTitle)
##            xGridRes = yield self.cxn.data_vault.get_parameter('X Grid Resolution')
##            dX = yield self.cxn.data_vault.get_parameter('dX')
##            yGridRes = yield self.cxn.data_vault.get_parameter('Y Grid Resolution')
##            dY = yield self.cxn.data_vault.get_parameter('dY')
##            sweepType =yield self.cxn.data_vault.get_parameter('Sweep Type')
##            x = np.asarray(dataset[:,0])
##            y = np.asarray(dataset[:,1])
##            z = np.asarray(dataset[:,2])
##            new = self.makeGrid(x, xGridRes, dX, y, yGridRes, dY, sweepType, z)
##            X = new[0]
##            Y = new[1]
##            Z = new[2]
##            im = ax.imshow(Z, extent=(X.min(), X.max(), Y.min(), Y.max()), interpolation='nearest', cmap=cm.gist_rainbow, origin='lower')
##            fig.colorbar(im, fraction = 0.15)
        else:
            print ("1D and 2D data are the only types currently \r\n"+
                   "supported by this grapher.")
            print ("Attempted to plot "+dataCategory+" data.")
            self.updatePlotTypesList(self.supportedPlotTypes(dataCategory))
            fig = Figure(dpi=100)
        #yield self.cxn.data_vault.cd("") #does this bump us to home?? ********************* why is this here
        #yield self.cxn.data_vault.dump_existing_sessions()
        return fig



##    def makeGrid(self, x, xGridRes, dX, y, yGridRes, dY, sweepType, z):
##        
##        totalNumPts = len(x)
##        divNmod = divmod(len(x), yGridRes)
##        
##        if sweepType =="Y": #Y sweep type ==> fix x, sweep y, then go to x+dx and sweep y again ... 
##            divNmod = divmod(len(x), yGridRes)
##            numFullYslices = divNmod[0]
##            numPartiallyComplete = divNmod[1]
##            if numFullYslices < xGridRes:
##                npxRemainder = np.array([])
##                npyRemainder = np.array([])
##                nanArray = np.zeros(shape = (yGridRes*xGridRes -yGridRes*numFullYslices-numPartiallyComplete,))
##                nanArray[:] = np.NAN
##                npzRemainder = np.concatenate([z[yGridRes*numFullYslices:yGridRes*numFullYslices+numPartiallyComplete], nanArray])
##                for ii in range(numFullYslices, xGridRes):
##                    npxRemainder = np.concatenate([npxRemainder, np.linspace(dX*ii+x[0], dX*ii+x[0], num = yGridRes)])
##                    npyRemainder = np.concatenate([npyRemainder, np.linspace(y[0], y[0]+(yGridRes-1)*dY, num = yGridRes)])
##            else:
##                npxRemainder = np.array([])
##                npyRemainder = np.array([])
##                npzRemainder = np.array([])
##
##                
##            npx = np.concatenate([x[0:yGridRes*numFullYslices], npxRemainder])
##            npy = np.concatenate([y[0:yGridRes*numFullYslices], npyRemainder])
##            npz = np.concatenate([z[0:yGridRes*numFullYslices], npzRemainder])
##
##            npx = npx.reshape(xGridRes, yGridRes).T
##            npy = npy.reshape(xGridRes, yGridRes).T
##            npz = npz.reshape(xGridRes, yGridRes).T
##        elif sweepType =="X": #X sweep type ==> fix y, sweep x, then go to x+dy and sweep y again ...
##            divNmod = divmod(len(x), xGridRes)
##            numFullXslices = divNmod[0]
##            numPartiallyComplete = divNmod[1]
##            if numFullXslices < yGridRes:
##                npxRemainder = np.array([])
##                npyRemainder = np.array([])
##                nanArray = np.zeros(shape = (yGridRes*xGridRes -xGridRes*numFullXslices-numPartiallyComplete,))
##                nanArray[:] = np.NAN
##                npzRemainder = np.concatenate([z[xGridRes*numFullXslices:xGridRes*numFullXslices+numPartiallyComplete], nanArray])
##                for ii in range(numFullXslices, yGridRes):
##                    npyRemainder = np.concatenate([npyRemainder, np.linspace(dY*ii+y[0], dY*ii+y[0], num = xGridRes)])
##                    npxRemainder = np.concatenate([npxRemainder, np.linspace(x[0], x[0]+(xGridRes-1)*dX, num = xGridRes)])
##            else:
##                npxRemainder = np.array([])
##                npyRemainder = np.array([])
##                npzRemainder = np.array([])
##            npx = np.concatenate([x[0:xGridRes*numFullXslices], npxRemainder])
##            npy = np.concatenate([y[0:xGridRes*numFullXslices], npyRemainder])
##            npz = np.concatenate([z[0:xGridRes*numFullXslices], npzRemainder])
##
##            npx = npx.reshape(xGridRes, yGridRes)
##            npy = npy.reshape(xGridRes, yGridRes)
##            npz = npz.reshape(xGridRes, yGridRes)
##                
##        return (npx,npy,npz)


if __name__ == "__main__":
    import sys

    app = QtGui.QApplication(sys.argv)
    app.setApplicationName('MyWindow')

    main = Main()
    main.resize(1000, 700)
    main.move(app.desktop().screen().rect().center() - main.rect().center())
    main.show()

    sys.exit(app.exec_())
