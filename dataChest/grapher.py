import sys
from PyQt4 import QtCore, QtGui
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt4agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar)
from dataChest import *
from functools import partial

class Main(QtGui.QWidget):
    
    def __init__(self, parent = None):
        super(Main, self).__init__(parent)
        self.root = 'Z:/mcdermott-group/DataChest'
        self.pathRoot=QtCore.QString('Z:\mcdermott-group\DataChest')

        self.filters =QtCore.QStringList()
        self.filters.append("*.hdf5")

        self.dataChest = dataChest()

        self.setWindowTitle('Data Chest Image Browser')
        self.setWindowIcon(QtGui.QIcon('rabi.jpg')) #add in rabi plot


        #directory browser configuration
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
        self.directoryTree.clicked.connect(self.dirTreeSelectionMade)
        
        #plot types drop down list configuration
        self.plotTypesComboBoxLabel = QtGui.QLabel(self)
        self.plotTypesComboBoxLabel.setText("Available Plot Types:")

        self.plotTypesComboBox = QtGui.QComboBox(self)
        self.plotTypesComboBox.activated[str].connect(self.plotTypeSelected)

        #configures scrolling widget
        self.scrollWidget = QtGui.QWidget(self)
        self.scrollLayout = QtGui.QHBoxLayout(self)
        self.scrollWidget.setLayout(self.scrollLayout)
        self.scrollArea = QtGui.QScrollArea(self)
        self.scrollArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn) #QtCore.Qt.ScrollBarAsNeeded
        self.scrollArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.scrollArea.setWidget(self.scrollWidget)
        self.scrollArea.setWidgetResizable(True) #what happens without???
        #self.scrollArea.setEnabled(True) #what happens without???

        
        vbox = QtGui.QVBoxLayout()
        vbox.addWidget(self.directoryBrowserLabel)
        vbox.addWidget(self.directoryTree)
        vbox.addWidget(self.plotTypesComboBoxLabel)
        vbox.addWidget(self.plotTypesComboBox)
        vbox.addWidget(self.scrollArea)

        #self.setLayout(vbox)

        self.mplwindow =QtGui.QWidget(self)
        self.mplvl = QtGui.QVBoxLayout(self.mplwindow)

        hbox = QtGui.QHBoxLayout()
        hbox.addLayout(vbox)
        hbox.addWidget(self.mplwindow)
        self.setLayout(hbox)

        self.currentFig = Figure()
        self.addFigureToCanvas(self.currentFig)
        
        self.filePath = None
        self.fileName = None
        self.plotType = None
        self.varsToIgnore = []

    def plotTypeSelected(self, plotType):
        #self.plotTypesComboBox.adjustSize()
        if plotType != self.plotType:
            self.removeFigFromCanvas()
            self.currentFig = self.figFromFileInfo(self.filePath, self.fileName, selectedPlotType = plotType)
            self.addFigureToCanvas(self.currentFig)
            self.updatePlotTypeOptions(plotType)
            self.plotType = plotType
            self.varsToIgnore = [] ##when is best time to do this??
        else:
            print "Nothing new"

    def updatePlotTypeOptions(self, plotType):
        
        self.clearLayout(self.scrollLayout)
        if plotType == "1D" or "Histogram":
            headerList = ["Dep Var:", "Status:"]
            widgetTypeList = ["QLabel", "QCheckBox"]
            depVarList = [row[0] for row in self.dataChest.getVariables()[1]]
            for ii in range(0,len(headerList)):
                optionsSlice = QtGui.QVBoxLayout()
                label = QtGui.QLabel(self) #widget to log
                label.setText(headerList[ii])
                optionsSlice.addWidget(label)
                for depVar in depVarList:
                    if widgetTypeList[ii] =="QLabel":
                        label = QtGui.QLabel(self) #widget to log
                        label.setText(depVar)
                        optionsSlice.addWidget(label)
                    elif widgetTypeList[ii] =="QCheckBox":
                        checkBox = QtGui.QCheckBox('', self)  #widget to log
                        checkBox.setCheckState(QtCore.Qt.Checked)
                        checkBox.stateChanged.connect(partial(self.varStateChanged, depVar))
                        optionsSlice.addWidget(checkBox)
                optionsSlice.addStretch(1)
                self.scrollLayout.addLayout(optionsSlice)
            self.scrollLayout.addStretch(1)
            #print "clearing"
            #self.clearLayout(self.scrollLayout)
            
    #def removeOldPlotTypeWidgets(
    def clearLayout(self, layout):
        for i in reversed(range(layout.count())):
            item = layout.itemAt(i)
            
            if isinstance(item, QtGui.QWidgetItem):
                item.widget().close()
            elif not isinstance(item, QtGui.QSpacerItem):
                self.clearLayout(item.layout())

            # remove the item from layout
            layout.removeItem(item) 
            
    def varStateChanged(self, name, state): #when status check box is selected this is called
        if state == QtCore.Qt.Checked:
            self.varsToIgnore.remove(name)
            self.removeFigFromCanvas() #removes old figure, needs garbage collection too
            self.currentFig = self.figFromFileInfo(self.filePath, self.fileName, varsToIgnore =self.varsToIgnore)
            self.addFigureToCanvas(self.currentFig)
        else: #unchecked
            if name not in self.varsToIgnore:
                self.varsToIgnore.append(name)
            self.removeFigFromCanvas() #removes old figure, needs garbage collection too
            self.currentFig = self.figFromFileInfo(self.filePath, self.fileName, varsToIgnore =self.varsToIgnore)
            self.addFigureToCanvas(self.currentFig)

    def convertWindowsPathToDvPathArray(self, windowsPath): #lets see what happens on a mac ???
        if 'Z:/mcdermott-group/DataChest/' in windowsPath:
            windowsPath = windowsPath.replace('Z:/mcdermott-group/DataChest/', '')
        elif 'Z:/mcdermott-group/DataChest' in windowsPath:
            windowsPath = windowsPath.replace('Z:/mcdermott-group/DataChest', '')
        windowsPath = windowsPath.replace('.dir', '')
        return windowsPath.split('/')
        
    def addFigureToCanvas(self, fig):

        self.canvas = FigureCanvas(fig)
        self.mplvl.addWidget(self.canvas)
        self.canvas.draw()
        self.toolbar = NavigationToolbar(self.canvas, 
                self.mplwindow, coordinates=True)
        self.mplvl.addWidget(self.toolbar)

    def removeFigFromCanvas(self):

        self.mplvl.removeWidget(self.canvas)
        self.canvas.close()
        self.mplvl.removeWidget(self.toolbar)
        self.toolbar.close()
        self.currentFig.clf()
        
    @QtCore.pyqtSlot(QtCore.QModelIndex)
    def dirTreeSelectionMade(self, index): #logical flow could be improved

        indexItem = self.model.index(index.row(), 0, index.parent())
        fileName = str(self.model.fileName(indexItem))
        filePath = str(self.model.filePath(indexItem))

        if ".hdf5" in filePath: #removes fileName from path if file is chosen
            filePath = filePath[:-(len(fileName)+1)]

        if self.fileName != fileName or self.filePath != filePath: #if an actual change occurs update check what happens for just a folder
            self.filePath = filePath # is there a point in storing this?
            self.fileName = fileName
            
            if ".hdf5" in fileName: #i.e. not a directory else leave as is til a file is selected
                self.removeFigFromCanvas() #removes old figure, needs garbage collection too 
                self.currentFig = self.figFromFileInfo(self.filePath, self.fileName)
                self.addFigureToCanvas(self.currentFig)
                variables = self.dataChest.getVariables() #fine
                dataCategory = self.categorizeDataset(variables) #fine
                self.updatePlotTypesList(self.supportedPlotTypes(dataCategory)) #fine: updates list
                self.updatePlotTypeOptions(self.supportedPlotTypes(dataCategory)[0])
                self.plotType = self.supportedPlotTypes(dataCategory)[0]
                self.varsToIgnore = [] ##when is best time to do this??
            else:
                self.fileName = None
                           
    def updatePlotTypesList(self, plotTypes):
        self.plotTypesComboBox.clear()
        for element in plotTypes:
            if ".dir" not in str(element) and ".ini" not in str(element):
                self.plotTypesComboBox.addItem(str(element))
   
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

    #some shape checking needs to go into this function to ensure 1D array inputs
    def plot1D(self, dataset, variables, plotType, dataClass, varsToIgnore = []): #shorten this monstrosity
        #print "varsToIgnore=", varsToIgnore
        if plotType == None:
            plotType = self.supportedPlotTypes("1D")[0] #defaults
        elif plotType not in self.supportedPlotTypes("1D"):
            print "Unrecognized plot type was provided"
            #return bum fig with something cool, maybe a gif
        if plotType =="1D":
            fig = self.basic1DPlot(dataset, variables, varsToIgnore)
        elif plotType == "Histogram": #adjust bin size
            fig = self.basic1DHistogram(dataset, variables, varsToIgnore)
        return fig

    def basic1DPlot(self, dataset, variables, varsToIgnore):
        #print " basic1DPlot varsToIgnore=", varsToIgnore
        fig = Figure(dpi=100)
        ax = fig.add_subplot(111)
        indepVars = variables[0]
        depVars = variables[1]
        xlabel = self.dataChest.getParameter("X Label")
        if xlabel is None:
            xlabel = indepVars[0][0]
        ylabel = self.dataChest.getParameter("Y Label") 
        if ylabel is None: #for data with more than one dep, recommend ylabel
            ylabel = depVars[0][0]
        plotTitle = self.dataChest.getParameter("Plot Title")
        if plotTitle is None:
            plotTitle = self.dataChest.getDatasetName()
        ax.set_title(plotTitle)
        dataset = np.asarray(dataset)
        ax.set_xlabel(xlabel+" "+"("+indepVars[0][3]+")")
        ax.set_ylabel(ylabel+" "+"("+depVars[0][3]+")") #for multiple deps with different units this is ambiguous
        for ii in range(0, len(depVars)):
            if depVars[ii][0] not in varsToIgnore:
                x = dataset[::,0].flatten()
                y = dataset[::,1+ii].flatten()
                ax.plot(x, y, label = depVars[ii][0])
        ax.legend()
        return fig

    def basic1DHistogram(self, dataset, variables, varsToIgnore):
        fig = Figure(dpi=100)
        ax = fig.add_subplot(111)
        indepVars = variables[0]
        depVars = variables[1]
        xlabel = self.dataChest.getParameter("X Label")
        if xlabel is None:
            xlabel = indepVars[0][0]
        ylabel = self.dataChest.getParameter("X Label") 
        if ylabel is None: #for data with more than one dep, recommend ylabel
            ylabel = depVars[0][0]
        plotTitle = self.dataChest.getParameter("Plot Title")
        if plotTitle is None:
            plotTitle = self.dataChest.getDatasetName()
        ax.set_title(plotTitle)
        dataset = np.asarray(dataset)
        ax.set_xlabel(xlabel+" "+"("+indepVars[0][3]+")")
        ax.set_ylabel(ylabel+" "+"("+depVars[0][3]+")") #for multiple deps with different units this is ambiguous
        for ii in range(0, len(depVars)):
            if depVars[ii][0] not in varsToIgnore:
                x = dataset[::,0].flatten()
                y = dataset[::,1+ii].flatten()
                ax.hist(y, 100, normed=1, alpha=0.5, label = depVars[ii][0])
        ax.legend()
        return fig

    #def plot2D(self, dataset, variables, plotType, dataClass):
            
    def figFromFileInfo(self, filePath, fileName, selectedPlotType = None, varsToIgnore =[]):
        relPath = self.convertWindowsPathToDvPathArray(filePath)
        self.dataChest.cd(relPath)
        self.dataChest.openDataset(fileName) 
        variables = self.dataChest.getVariables()
        dataCategory = self.categorizeDataset(variables)
        #otherwise refer to dataset name needs to be implemented
        dataset = self.dataChest.getData()
        if dataCategory == "1D":
            #self.updatePlotTypesList(self.supportedPlotTypes(dataCategory))
            fig = self.plot1D(dataset, variables, selectedPlotType, None, varsToIgnore = varsToIgnore) #plot1D(self, dataset, variables, plotType, dataClass, varsToIgnore = [])
        elif dataCategory =="2D": #was "2D Sweep"
            fig = Figure(dpi=100)
            #self.updatePlotTypesList(self.supportedPlotTypes(dataCategory)) #Trajectory
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
        self.dataChest.cd("")
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
