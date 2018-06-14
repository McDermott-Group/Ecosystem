import os
import sys
from PyQt4 import QtCore, QtGui
from functools import partial
import pyqtgraph as pg
from time import sleep

from dataChest import *

##mpl.rcParams['agg.path.chunksize'] = 10000

HEX_COLOR_MAP = {'white': '#FFFFFF', 'silver': '#FFFFFF', 'gray': '#808080',
                 'black':'#000000','red':'#FF0000', 'maroon':'#800000',
                 'yellow':'#FFFF00', 'olive':'#808000', 'lime':'#00FF00',
                 'green':'#008000','aqua':'#00FFFF', 'teal':'#008080',
                 'blue':'#0000FF','navy':'#000080', 'fuchsia':'#FF00FF',
                 'purple':'#800080'}

ACCEPTABLE_DATA_CATEGORIES = ["Arbitrary Type 1", "Arbitrary Type 2", "1D Scan", "2D Scan"]



class Grapher(QtGui.QWidget):

    def __init__(self, parent = None):
        super(Grapher, self).__init__(parent)
        self.setWindowTitle('Data Chest Image Browser')
        self.setWindowIcon(QtGui.QIcon('rabi.jpg'))

        self.root = os.environ["DATA_ROOT"]

        self.filters =QtCore.QStringList()
        self.filters.append("*.hdf5")

        self.d = dataChest(None, True)

        hbox = QtGui.QHBoxLayout()

        # Directory browser configuration.
        self.model = QtGui.QFileSystemModel(self)
        self.model.setRootPath(QtCore.QString(self.root))
        self.model.setNameFilterDisables(False)
        self.model.nameFilterDisables()
        self.model.setNameFilters(self.filters)

        self.indexRoot = self.model.index(self.model.rootPath())

        self.directoryBrowserLabel = QtGui.QLabel(self)
        self.directoryBrowserLabel.setText("Directory Browser:")

        self.directoryTree = QtGui.QTreeView(self)
        self.directoryTree.setModel(self.model)
        self.directoryTree.setRootIndex(self.indexRoot)
        self.directoryTree.header().setResizeMode(QtGui.QHeaderView.ResizeToContents)
        self.directoryTree.header().setStretchLastSection(False)
        self.directoryTree.clicked.connect(self.fileBrowserSelectionMade)

        self.dirTreeWidget = QtGui.QWidget(self)
        self.dirTreeLayout = QtGui.QVBoxLayout()
        self.dirTreeWidget.setLayout(self.dirTreeLayout)
        self.dirTreeLayout.addWidget(self.directoryBrowserLabel)
        self.dirTreeLayout.addWidget(self.directoryTree)

        # Plot types drop down list configuration.
        self.plotTypesComboBoxLabel = QtGui.QLabel(self)
        self.plotTypesComboBoxLabel.setText("Available Plot Types:")

        self.plotTypesComboBox = QtGui.QComboBox(self)
        self.plotTypesComboBox.activated[str].connect(self.plotTypeSelected)

        # Configure scrolling widget.
        self.scrollWidget = QtGui.QWidget(self)
        self.scrollLayout = QtGui.QHBoxLayout()
        self.scrollWidget.setLayout(self.scrollLayout)
        self.scrollArea = QtGui.QScrollArea(self)
        self.scrollArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.scrollArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.scrollArea.setWidget(self.scrollWidget)
        self.scrollArea.setWidgetResizable(True) # What happens without?

        self.plotOptionsWidget = QtGui.QWidget(self)
        self.plotOptionsLayout = QtGui.QVBoxLayout()
        self.plotOptionsWidget.setLayout(self.plotOptionsLayout)
        self.plotOptionsLayout.addWidget(self.plotTypesComboBoxLabel)
        self.plotOptionsLayout.addWidget(self.plotTypesComboBox)
        self.plotOptionsLayout.addWidget(self.scrollArea)

        self.splitterVertical = QtGui.QSplitter(QtCore.Qt.Vertical) #, self)
        self.splitterVertical.addWidget(self.dirTreeWidget)
        self.splitterVertical.addWidget(self.plotOptionsWidget)

        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')
        pg.setConfigOptions(antialias=True)

        self.graphicsLayout = pg.GraphicsLayoutWidget(self)
        self.graphicsLayout.setMinimumHeight(740)

        self.graphsWidget = QtGui.QWidget(self)

        self.graphsLayout = QtGui.QVBoxLayout()
        self.graphsWidget.setLayout(self.graphsLayout)
        self.graphsLayout.addWidget(self.graphicsLayout)

        self.graphScrollArea = QtGui.QScrollArea(self)
        self.graphScrollArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.graphScrollArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.graphScrollArea.setWidget(self.graphsWidget)
        self.graphScrollArea.setWidgetResizable(True) # What happens without?

        self.splitterHorizontal = QtGui.QSplitter(QtCore.Qt.Horizontal)
        self.splitterHorizontal.addWidget(self.splitterVertical)
        self.splitterHorizontal.addWidget(self.graphScrollArea)

        hbox.addWidget(self.splitterHorizontal)
        self.setLayout(hbox)
        QtGui.QApplication.setStyle(QtGui.QStyleFactory.create('Cleanlooks'))

        self.groupVarsWithCommonUnits = True

        self.plotType = None # redundant
        self.plotTypeOptionsDict = {}
        #self.varsToIgnore = []

        self.selectedFile = ''
        self.lastModDate = 0
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.checkFileForUpdates)
        self.timer.start(1000)

    @QtCore.pyqtSlot(QtCore.QModelIndex)
    def fileBrowserSelectionMade(self, index):
        # Called when a directory tree selection is made.
        indexItem = self.model.index(index.row(), 0, index.parent())
        fileName = str(self.model.fileName(indexItem))
        filePath = str(self.model.filePath(indexItem))
        if ".hdf5" in filePath:
            self.selectedFile = filePath
            filePath = filePath[:-(len(fileName)+1)] #strip fileName from path
            filePath = self.convertPathToArray(filePath)
            filePath = filePath[3:]
            currentFileName = self.d.getDatasetName()
            currentFilePath = self.convertPathToArray(self.d.pwd())
            if currentFileName != fileName or currentFilePath != filePath:
                self.plotFile = fileName, filePath
                self.plotData(fileName, filePath)



    def checkFileForUpdates(self):
        if self.selectedFile != '':
            modDate = os.stat(self.selectedFile).st_mtime
            if self.lastModDate != modDate:
                print('OH JEEZ GOTTA UPDATE')
                self.lastModDate = modDate
                self.plotData(*self.plotFile)

    def plotData(self, fileName, filePath):
        d = self.d
        d.cd(filePath)
        d.openDataset(fileName)

        self.datasetVariables = d.getVariables()
        self.datasetName = d.getDatasetName()
        indepVarsList = self.datasetVariables[0]
        depVarsList = self.datasetVariables[1]
        datasetCategory = d.getDataCategory()
        d.cd("")

        if datasetCategory not in ACCEPTABLE_DATA_CATEGORIES:
            print "Unknown category."
            return

        if datasetCategory == "Arbitrary Type 1":
            data = [d.getData().T]
        elif datasetCategory == "Arbitrary Type 2":
            data = d.getData()
        # extract scan part of data so it is a complete, normal data set
        elif datasetCategory == "1D Scan" or datasetCategory == "2D Scan":
            data = d.getData()
            l = depVarsList[0][1][0] # len of first dim in shape of first dep var
            scanType = d.getParameter("Scan Type", bypassIOError=True)
            for j in range(len(data)):
                row = data[j]
                for i in range(len(indepVarsList)):
                    if indepVarsList[i][1] == [1]:
                        data[j][i] = [row[i]]*l
                    elif indepVarsList[i][1] == [2]:
                        start,stop = row[i]
                        if scanType is None:
                            print "Scan Type Not Found.  Assuming Linear."
                            data[j][i] = np.linspace(start, stop, num = l)
                        elif scanType == "Linear":
                            data[j][i] = np.linspace(start, stop, num = l)
                        elif scanType == "Logarithmic":
                            data[j][i] = np.logspace(np.log10(start), np.log10(stop), num = l)
            if datasetCategory == "2D Scan":
                data = [np.concatenate(data, axis=1)]

        data = np.array(data[0])

        self.selectedData = data
        if len(indepVarsList) == 1:
            self.plot1D(data, self.plotTypeOptionsDict)
        elif len(indepVarsList) == 2:
            self.plot2D()

    def extractIndepData(self, data):
        """
        Take the data and turn it into two arrays:
          indepData is a list of dep vars ranges (ranges are sorted by value)
          depData is the associated vector of values associated with the dep vars
        This is done by first skimming off the indep vars, sorting them, and then
        going through the rows of data and setting the value of each spot in the
        vector.  The data must be in the form where each column is a point in the
        dataset (Type 2 data).
        """
        indepVarsList = self.datasetVariables[0]
        depVarsList = self.datasetVariables[1]
        indepData = [np.unique(np.array(data[i])) for i in range(len(indepVarsList))]
        indepShape = [len(v) for v in indepData]
        depData = [np.full(indepShape, np.nan) for _ in range(len(depVarsList))]
        for row in data.T:    # go though each row and fill data
            indepVals = row[:len(indepData)]
            indepIndicies = tuple([np.where(indepData[i]==indepVals[i])[0][0] for i in range(len(indepVals))])
            for i in range(len(depData)):
                depData[i][indepIndicies] = row[i+len(indepVarsList)]
        return indepData, depData

    def plot1D(self, data, plotTypeOptionsDict):
        indepVarsList = self.datasetVariables[0]
        depVarsList = self.datasetVariables[1]
        varsWithCommonUnitsDict = self.getVarsWithCommonUnitsDict(depVarsList)
        plotType = self.supportedPlotTypes("1D")[0] # defaults
        self.clearGraphicsLayout()
        print "varsWithCommonUnitsDict=", varsWithCommonUnitsDict
        print "depVarsList=", depVarsList
        if plotType =="1D":
            if self.groupVarsWithCommonUnits == True:
                for commonUnit in varsWithCommonUnitsDict.keys():
                    commonUnitsData = []
                    commonNamesData = []
                    commonUnitsData.append(data[0])
                    for varName in varsWithCommonUnitsDict[commonUnit]:
                        for ii in range(0, len(depVarsList)):
                            #print "depVarsList[ii][0]=", depVarsList[ii][0]
                            #if ii == 0:
                            #    commonUnitsData.append(data[0])
                            if depVarsList[ii][0] == varName:
                                print "matched"
                                print "depVarsList[ii][0]=", depVarsList[ii][0]
                                print "varName=", varName
                                commonUnitsData.append(data[ii+1])
                                commonNamesData.append(varName)
                                plotTypeOptionsDict[varName] = self.initializeBasic1DPlotOptions(self.datasetName,
                                                                                                 indepVarsList[0][0],
                                                                                                 indepVarsList[0][3],
                                                                                                 varName, commonUnit)
                    self.basic1DPlot(self.graphicsLayout, commonUnitsData, commonNamesData, plotTypeOptionsDict)

    def plot2D(self):
        (xVals, yVals), depGrids = self.extractIndepData(self.selectedData)
        self.graphicsLayout.clear()
        p1 = self.graphicsLayout.addPlot(title="Test Title", size='22pt')
        p1.titleLabel.setText("Test Title", size ='22pt')
        indepVarsList = self.datasetVariables[0]
        p1.setLabel('bottom', indepVarsList[0][0], units=indepVarsList[0][3])
        p1.setLabel('left', indepVarsList[1][0], units=indepVarsList[1][3])
        p1.addLegend()
        img = pg.ImageItem()
        img.setImage(depGrids[0])
        p1.addItem(img)
        pixelX = (xVals[-1]-xVals[0])/len(xVals)
        pixelY = (yVals[-1]-yVals[0])/len(yVals)
        img.translate(xVals[0],yVals[0])
        img.scale(pixelX,pixelY)

        # bipolar colormap
        pos = np.array([0., 1., 0.5, 0.25, 0.75])
        color = np.array([[0,255,255,255], [255,255,0,255], [0,0,0,255], (0, 0, 255, 255), (255, 0, 0, 255)], dtype=np.ubyte)
        cmap = pg.ColorMap(pos, color)
        lut = cmap.getLookupTable(0.0, 1.0, 256)
        img.setLookupTable(lut)

        p1.autoRange()

    def initializeBasic1DPlotOptions(self, datasetName, xVarName, xUnits, yVarName, yUnits):
        plotOptions = {}
        plotOptions["X Scale"] = "Linear"
        plotOptions["X Label"] = xVarName
        plotOptions["X Units"] = xUnits
        plotOptions["Y Scale"] = "Linear"
        plotOptions["Y Label"] = yVarName
        plotOptions["Y Units"] = yUnits
        plotOptions["Title"] = datasetName
        plotOptions["Color"] = None
        plotOptions["Marker Style"] = None
        plotOptions["Enable Grid"] = False
        plotOptions["Hide Variable"] = False
        return plotOptions


    def basic1DPlot(self, graphicsLayout, commonUnitsData, commonNamesData, plotTypeOptionsDict):
        #graphicsLayout.clear()
        for ii in range(0, len(commonNamesData)):
            #p1 = graphicsLayout.addPlot(title=plotTypeOptionsDict[commonNamesData[ii]]["Y Label"], size='22pt') #title="Common Unit 1"
            if ii == 0:
                p1 = graphicsLayout.addPlot(title=plotTypeOptionsDict[commonNamesData[ii]]["Title"], size='22pt')
                p1.titleLabel.setText(plotTypeOptionsDict[commonNamesData[ii]]["Title"], size ='22pt')
                p1.addLegend()
            #print "commonUnitsData[ii]=", commonUnitsData[ii+1]
            p1.plot(x=commonUnitsData[0], y=commonUnitsData[ii+1], name = plotTypeOptionsDict[commonNamesData[ii]]["Y Label"], pen=pg.mkPen(HEX_COLOR_MAP['blue']))
            #p1.plot(x=xdataPlot1, y=ydata2Plot1, name = 'dset2', pen=pg.mkPen(HEX_COLOR_MAP['green']))

            ylabelStyle = {'color': HEX_COLOR_MAP['black'], 'font-size': '22px'}
            p1.setLabel('left', 'Volts [V]', **ylabelStyle) # units = 'V'

            xlabelStyle = {'color': HEX_COLOR_MAP['black'], 'font-size': '22px'}
            p1.setLabel('bottom', 'Time [s]', **xlabelStyle) #units = 's'

    def plotTypeSelected(self, plotType):
        # Called when a plotType selection is made from drop down.
        # self.plotTypesComboBox.adjustSize()
        return "Grape Fruit"
##        if plotType != self.plotType:
##            self.clearGraphicsLayout()
##            #self.currentFig = self.figFromFileInfo(self.filePath, self.fileName, selectedPlotType = plotType)
##            #self.addFigureToCanvas(self.currentFig)
##            self.updatePlotTypeOptions(plotType)
##            self.plotType = plotType
##            # When is best time to do this?
##            self.varsToIgnore = []


    def clearLayout(self, layout):
        # Clear the plotType options layout and all widgets therein.
        for i in reversed(range(layout.count())):
            item = layout.itemAt(i)

            if isinstance(item, QtGui.QWidgetItem):
                item.widget().close()
            elif not isinstance(item, QtGui.QSpacerItem):
                self.clearLayout(item.layout())
            # remove the item from layout
            layout.removeItem(item)

    def convertPathToArray(self, path):
        print "self.root=", self.root
        print "path=", path
        if self.root + "/" in path:
            path = path.replace(self.root+"/", '')
        elif self.root in path:
            path = path.replace(self.root, '')
        return path.split('/')


    def clearGraphicsLayout(self):
        # Remove all widgets from GraphicsLayoutWidget
        self.graphicsLayout.clear()

    def getListOfAvailabePlotTypes(self, datasetDimension, datasetCategory, selectedVarsList):
        if datasetDimension == 1:
            if len(selectedVarsList) >= 2: # 1D Traj Plot Types require 2 selected dependent vars
                return ["1D", "1D Parametric"]
            elif len(selectedVarsList) == 1:
                return ["1D"]
            else:
                return ["Please select at least on variable for plotting"]
        elif datasetDimension == 2:
            if len(selectedVarsList) >= 2:
                return ["2D Scan", "3D Surface", "2D Parametric", "Projection"] #3D Parametric for > 3 indeps
            elif len(selectedVarsList) == 1:
                return ["2D Scan", "3D Contour", "Projection"]
        else:
            return ["There are no available plot types for "+str(datasetDimension)+ " dimensional data."]


    def getVarsWithCommonUnitsDict(self, depVarsList):
        compatibleVarsDict = {}
        for depVar in depVarsList:
            # depVar of form (name, shape, dtype, units)
            name = depVar[0]
            units = depVar[3]
            if units not in compatibleVarsDict.keys():
                compatibleVarsDict[units] = [name]
            else:
                compatibleVarsDict[units].append(name)
        return compatibleVarsDict

    def getVarsWithCommonShapeList(self, depVarsList, commonUnitsList, selectedVarName):

        varsWithCommonShapeList = []
        for depVar in depVarsList:
            # depVar of form (name, shape, dtype, units)
            name = depVar[0]
            shape = depVar[1]
            #units = depVar[3]
            if name == selectedVarName:
                selectedVarShape = shape

        for depVar in depVarsList:
            # depVar of form (name, shape, dtype, units)
            name = depVar[0]
            shape = depVar[1]
            if (name in commonUnitsList) and shape == selectedVarShape:
                varsWithCommonShapeList.append(name)

        return varsWithCommonShapeList

    def updatePlotTypesList(self, plotTypeOptionsList):
        # Update plotTypes list based on selected dataset.
        self.plotTypesComboBox.clear()
        for element in plotTypeOptionsList:
            if ".dir" not in str(element) and ".ini" not in str(element):
                self.plotTypesComboBox.addItem(str(element))

    def supportedPlotTypes(self, dimensionality):
        # Provide list of plotTypes based on datasetType.
        if dimensionality == "1D":
            plotTypes = ["1D"] #"Histogram"
        elif dimensionality == "2D":
            plotTypes = ["2D Image"]
        else:
            plotTypes = []
        return plotTypes

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    app.setApplicationName('MyWindow')

    main = Grapher()
    main.resize(1000, 700)
    main.move(app.desktop().screen().rect().center() - main.rect().center())
    main.show()

    sys.exit(app.exec_())
