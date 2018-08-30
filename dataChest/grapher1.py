# TODO: add units to colorbar label!

import os
import sys
from PyQt4 import QtCore, QtGui
from functools import partial
import pyqtgraph as pg
import pyqtgraph.exporters
from time import sleep, time
import datetime
from dateutil import tz

from dataChest import *

##mpl.rcParams['agg.path.chunksize'] = 10000

HEX_COLOR_MAP = {'white': '#FFFFFF', 'silver': '#FFFFFF', 'gray': '#808080',
                 'black':'#000000','red':'#FF0000', 'maroon':'#800000',
                 'yellow':'#FFFF00', 'olive':'#808000', 'lime':'#00FF00',
                 'green':'#008000','aqua':'#00FFFF', 'teal':'#008080',
                 'blue':'#0000FF','navy':'#000080', 'fuchsia':'#FF00FF',
                 'purple':'#800080'}

ACCEPTABLE_DATA_CATEGORIES = ["Arbitrary Type 1", "Arbitrary Type 2", "1D Scan", "2D Scan"]

STYLE_DEFAULTS = {
    'font-size': '22pt',
    'font-color': 'black'}


class TimeAxisItem(pg.AxisItem):
    def __init__(self, *args, **kwargs):
        #  super().__init__(*args, **kwargs)
        super(TimeAxisItem, self).__init__(*args, **kwargs)
        self.autoSIPrefix = False

    def tickStrings(self, values, scale, spacing):
        # PySide's QTime() initialiser fails miserably and dismisses args/kwargs
        # return [QTime().addMSecs(value).toString('mm:ss') for value in values]
        return [(datetime.datetime.utcfromtimestamp(value)
                                  .replace(tzinfo=tz.tzutc())
                                  .astimezone(tz.tzlocal())
                                  .strftime("%H:%M:%S")) for value in values]


class Grapher(QtGui.QWidget):

    def __init__(self, parent = None):
        self.cb = None
        super(Grapher, self).__init__(parent)
        self.setWindowTitle('Data Chest Image Browser')
        self.setWindowIcon(QtGui.QIcon('rabi.jpg'))

        self.numChecked = 0

        self.root = os.environ["DATA_ROOT"]
        self.pluginRoot = os.environ["REPOSITORY_ROOT"]
        self.pluginRoot = os.path.join(self.pluginRoot, "servers", "dataChest", "Plugins")

        self.filters = QtCore.QStringList()
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
        self.directoryTree.hideColumn(2)
        self.directoryTree.header().setResizeMode(QtGui.QHeaderView.ResizeToContents)
        self.directoryTree.header().setStretchLastSection(False)
        self.directoryTree.clicked.connect(self.fileBrowserSelectionMade)

        self.sort = QtGui.QSortFilterProxyModel(self.directoryTree)
        self.sort.setSourceModel(self.model)
        self.directoryTree.setSortingEnabled(True)

        self.dirTreeWidget = QtGui.QWidget(self)
        self.dirTreeLayout = QtGui.QVBoxLayout()
        self.dirTreeWidget.setLayout(self.dirTreeLayout)
        self.dirTreeLayout.addWidget(self.directoryBrowserLabel)
        self.dirTreeLayout.addWidget(self.directoryTree)
        self.dirTreeWidget.installEventFilter(self)

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

        # Configure plugin widget.
        self.pluginTypesList = QtGui.QListWidget(self)
        self.populatePluginList(self)

        self.pluginTypesList.itemClicked.connect(self.listItemClicked)
        self.pluginTypesList.setAlternatingRowColors(True)
        self.pluginTypesWidget = QtGui.QWidget(self)
        self.pluginTypesLayout = QtGui.QVBoxLayout()
        self.pluginTypesWidget.setLayout(self.pluginTypesLayout)
        self.pluginTypesLayout.addWidget(self.pluginTypesList)
        self.pluginTypesLayout.addWidget(self.scrollArea)

        self.plotOptionsWidget = QtGui.QWidget(self)
        self.plotOptionsLayout = QtGui.QVBoxLayout()
        self.plotOptionsWidget.setLayout(self.plotOptionsLayout)
        self.plotOptionsLayout.addWidget(self.plotTypesComboBoxLabel)
        self.plotOptionsLayout.addWidget(self.plotTypesComboBox)
        self.plotOptionsLayout.addWidget(self.scrollArea)

        self.splitterVertical = QtGui.QSplitter(QtCore.Qt.Vertical) #, self)
        self.splitterVertical.addWidget(self.dirTreeWidget)
        self.splitterVertical.addWidget(self.pluginTypesList)
        self.splitterVertical.addWidget(self.plotOptionsWidget)
        self.splitterVertical.setSizes([800, 300, 500])

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

        self.parameterTable = QtGui.QTableWidget(self)
        self.parameterTable.horizontalHeader().setStretchLastSection(False)

        self.splitterHorizontal = QtGui.QSplitter(QtCore.Qt.Horizontal)
        self.splitterHorizontal.addWidget(self.splitterVertical)
        self.splitterHorizontal.addWidget(self.graphScrollArea)
        self.splitterHorizontal.addWidget(self.parameterTable)
        self.splitterHorizontal.setSizes([300,800, 300])

        hbox.addWidget(self.splitterHorizontal)
        self.setLayout(hbox)
        QtGui.QApplication.setStyle(QtGui.QStyleFactory.create('Cleanlooks'))

        self.groupVarsWithCommonUnits = True

        self.filePathStr = ''
        self.filePathArray = []
        self.lastModDate = 0
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.checkFileForUpdates)
        self.timer.start(1000)

        self.indepVarsList = []
        self.datasetName = None
        self.depVarsList = []
        self.selectedData = None

        self.plotType = None
        self.selectedDepVars = []
        self.font = QtGui.QFont()
        self.font.setPixelSize(22)

    def eventFilter(self, QObject, QEvent):
        if (QObject == self.dirTreeWidget and QEvent.type() == QtGui.QKeyEvent.KeyRelease):
            if (QEvent.key() == QtCore.Qt.Key_Up or QEvent.key() == QtCore.Qt.Key_Down):
                self.fileBrowserSelectionMade(self.directoryTree.currentIndex())
                return True

        else:
            return False

    def listItemClicked(self, item):
        if item.checkState() == QtCore.Qt.Checked:
            self.numChecked -= 1
            item.setCheckState(QtCore.Qt.Unchecked)
            pluginRow = self.pluginTypesList.row(item)
            self.pluginTypesList.takeItem(pluginRow)
            self.pluginTypesList.insertItem(self.numChecked, item)
            self.pluginTypesList.setCurrentRow(self.numChecked)
        else:
            self.numChecked += 1
            item.setCheckState(QtCore.Qt.Checked)
            pluginRow = self.pluginTypesList.row(item)
            self.pluginTypesList.takeItem(pluginRow)
            self.pluginTypesList.insertItem(self.numChecked-1, item)
            self.pluginTypesList.setCurrentRow(0)
        pluginPath = os.path.join(self.pluginRoot, str(item.whatsThis()))
        self.applyPlugins()

    def populatePluginList(self, *args):
        for pluginFilename in (os.listdir(self.pluginRoot)):
            plugin = open(os.path.join(self.pluginRoot, pluginFilename), 'r')
            pluginTitle = plugin.readline()
            pluginDescription = plugin.readline()

            if (pluginTitle.startswith('*#TITLE:')):
                pluginTitle = pluginTitle[9:].strip()
                if pluginDescription.startswith('*#DESCR:'):
                    pluginDescription = pluginDescription[9:].strip()
                    listItem = QtGui.QListWidgetItem(pluginTitle + '   |   ' + pluginDescription)
                else:
                    listItem = QtGui.QListWidgetItem(pluginTitle)
            else:
                listItem = QtGui.QListWidgetItem(pluginFilename)

            listItem.setWhatsThis(pluginFilename)
            listItem.setFlags(QtCore.Qt.ItemIsUserCheckable)
            listItem.setCheckState(QtCore.Qt.Unchecked)
            listItem.setFlags(QtCore.Qt.ItemIsEnabled)
            self.pluginTypesList.addItem(listItem)

    @QtCore.pyqtSlot(QtCore.QModelIndex)
    def fileBrowserSelectionMade(self, index):
        # Called when a directory tree selection is made.
        indexItem = self.model.index(index.row(), 0, index.parent())
        fileName = str(self.model.fileName(indexItem))
        filePath = str(self.model.filePath(indexItem))
        if ".hdf5" in filePath:
            self.filePathStr = filePath
            filePath = filePath[:-(len(fileName)+1)] #strip fileName from path
            filePath = self.convertPathToArray(filePath)

            # handle case where filePath starts at dataRoot
            if filePath[0] == "Z:":
                filePath = filePath[3:]

            currentFileName = self.d.getDatasetName()
            currentFilePath = self.convertPathToArray(self.d.pwd())
            if currentFileName != fileName or currentFilePath != filePath:
                self.filePathArray = filePath
                self.filePathArray.append(fileName)
                self.prepareData()

    def checkFileForUpdates(self):
        if self.filePathStr != '':
            modDate = os.stat(self.filePathStr).st_mtime
            if self.lastModDate != modDate:
                self.lastModDate = modDate
                self.prepareData()

    def prepareData(self):
        stime = time()
        d = self.d
        d.cd(self.filePathArray[:-1])
        d.openDataset(self.filePathArray[-1], grapher1 = True)
        datasetVariables = d.getVariables()
        self.parameters = d.getParameterList()
        self.datasetName = d.getDatasetName()
        self.indepVarsList = datasetVariables[0]
        self.depVarsList = datasetVariables[1]
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
            l = self.depVarsList[0][1][0] # len of first dim in shape of first dep var
            scanType = d.getParameter("Scan Type", bypassIOError=True)
            for j in range(len(data)):
                row = data[j]
                for i in range(len(self.indepVarsList)):
                    if self.indepVarsList[i][1] == [1]:
                        data[j][i] = [row[i]] * l
                    elif self.indepVarsList[i][1] == [2]:
                        start, stop = row[i]
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

        self.populateParameterTable()
        self.applyPlugins()

    def populateParameterTable(self):
        d = self.d
        num_units = 0
        for parameter in self.parameters:
            try:
                d.getParameter(str(parameter) + ' Units')
                num_units = num_units + 1
            except:
                pass

        num_parameters = len(self.parameters)
        self.parameterTable.setRowCount(num_parameters - num_units)
        self.parameterTable.setColumnCount(3)
        self.parameterTable.setColumnWidth(0, 120)
        self.parameterTable.setColumnWidth(1, 200)
        self.parameterTable.setColumnWidth(2, 50)
        i = 0
        skip = False
        for parameter in self.parameters:
            if skip == False:
                parameterValueText = str(d.getParameter(str(parameter)))
                parameterValue = QtGui.QTableWidgetItem(parameterValueText)
                parameterValue.setToolTip(parameterValueText)
                try:
                    parameterUnit = d.getParameter(str(parameter) + ' Units')
                    skip = True
                except:
                    parameterUnit = None
                parameterText = str(parameter)
                parameter = QtGui.QTableWidgetItem(parameterText)
                parameter.setToolTip(parameterText)
                self.parameterTable.setItem(i, 0, parameter)
                self.parameterTable.setItem(i, 1, parameterValue)

                if parameterUnit is not None:
                    parameterUnitText = str(parameterUnit)
                    parameterUnit = QtGui.QTableWidgetItem(parameterUnitText)
                    parameterUnit.setToolTip(parameterUnitText)
                    self.parameterTable.setItem(i, 2, parameterUnit)
                i = i+1
            else:
                skip = False

        self.parameterTable.horizontalHeader().setResizeMode(0, QtGui.QHeaderView.Interactive)
        self.parameterTable.horizontalHeader().setResizeMode(1, QtGui.QHeaderView.Stretch)
        self.parameterTable.horizontalHeader().setResizeMode(2, QtGui.QHeaderView.Interactive)

    def applyPlugins(self):
        """This is not implemented yet, but will eventually allow plugins to be
        defined to alter the data."""
        plugins = []
        for i in range(0, int(self.pluginTypesList.__len__())):
            item = self.pluginTypesList.item(i)
            if item.checkState() != 0:
                plugins.append(str(item.whatsThis()))
        self.updatePlotTypeSelector()


    def updatePlotTypeSelector(self):
        """Update plotTypes list based on selected dataset.  Selects currently
        selected type if available."""
        self.plotTypesComboBox.clear()
        listOfTypes = self.getListOfAvailabePlotTypes()
        for element in listOfTypes:
            self.plotTypesComboBox.addItem(str(element))
        if self.plotType in listOfTypes:
            index = self.plotTypesComboBox.findText(self.plotType)
            self.plotTypesComboBox.setCurrentIndex(index)
        else:
            self.plotTypesComboBox.setCurrentIndex(0)
        self.plotTypeSelected(str(self.plotTypesComboBox.currentText()))

    def plotTypeSelected(self, plotType):
        """Called when a plotType selection is made from drop down."""
        self.plotType = plotType
        self.updatePlotTypeOptions(plotType)
        if len(self.indepVarsList) == 1:
            self.plot1D()
        elif len(self.indepVarsList) == 2:
            self.plot2D()

    def updatePlotTypeOptions(self, plotType):
        """Update area below plotType, selection drop down (add/remove variables)"""
        # select first dep variable and all others with same units and shape
        varsWithCommonUnitsDict = self.getVarsWithCommonUnitsDict()
        firstVarList = varsWithCommonUnitsDict.values()[0]
        self.selectedDepVars = self.getVarsWithCommonShapeList(firstVarList, firstVarList[0])
        # populate interface buttons
        self.clearLayout(self.scrollLayout)
        optionsSlice = QtGui.QVBoxLayout()
        self.optionsGroup = QtGui.QButtonGroup()
        if plotType == "1D" or plotType == "Histogram":
            self.optionsGroup.setExclusive(False)
        for var in self.depVarsList:
            if plotType == "1D" or plotType == "Histogram":
                checkBox = QtGui.QCheckBox(var[0], self)  # widget to log
                checkBox.toggled.connect(partial(self.varStateChanged, var[0]))
                if var[0] in self.selectedDepVars:
                    checkBox.setCheckState(QtCore.Qt.Checked)
            elif plotType == '2D Scan':
                checkBox = QtGui.QRadioButton(var[0], self)
                checkBox.toggled.connect(partial(self.varStateChanged, var[0]))
                if var[0] in self.selectedDepVars:
                    checkBox.setChecked(True)
            optionsSlice.addWidget(checkBox)
            self.optionsGroup.addButton(checkBox)
        self.selectedDepVars = [str(button.text()) for button in self.optionsGroup.buttons()
                                                    if button.isChecked()]
        optionsSlice.addStretch(1)
        self.scrollLayout.addLayout(optionsSlice)
        self.scrollLayout.addStretch(1)

    def varStateChanged(self, var):
        if len(self.indepVarsList) == 2:
            self.selectedDepVars = [var]

            # ensures that only one radio button is ever checked
            numChecked = 0
            for button in self.optionsGroup.buttons():
                if button.isChecked():
                    numChecked += 1
            if numChecked != 1:
                for button in self.optionsGroup.buttons():
                    button.setChecked(False)

        elif var in self.selectedDepVars:
            self.selectedDepVars.remove(var)
        else:
            self.selectedDepVars.append(var)
        if len(self.selectedDepVars) > 0:
            if len(self.indepVarsList) == 1:
                self.plot1D()
            elif len(self.indepVarsList) == 2:
                self.plot2D()

    def extractIndepData(self, data):
        """
        Take the data and turn it into two arrays:
          indepData is a list of dep vars ranges (ranges are sorted by value)
          depData is the associated vector of values associated with the dep vars
        This is done by first skimming off the indep vars, sorting them, and then
        going through the rows of data and setting the value of each spot in the
        vector.  The data must be in the form where each column is a point in the
        dataset (Type 2 data).  The first row of each dimension is the indep vals.
        """
        indepData = [np.unique(np.array(data[i])) for i in range(len(self.indepVarsList))]
        indepShape = [len(v) for v in indepData]
        depData = [np.full(indepShape, np.nan) for _ in range(len(self.depVarsList))]
        for row in data.T:    # go though each row and fill data
            indepVals = row[:len(indepData)]
            indepIndicies = tuple([np.where(indepData[i]==indepVals[i])[0][0] for i in range(len(indepVals))])
            for i in range(len(depData)):
                depData[i][indepIndicies] = row[i+len(self.indepVarsList)]
        return indepData, depData

    def plot1D(self):
        stime=time()
        if self.cb is not None:
            self.cb.hide()

        varNames = [var[0] for var in self.depVarsList]
        varUnits = [var[3] for var in self.depVarsList]
        indicies = [varNames.index(var)+1 for var in self.selectedDepVars]
        commonUnit = varUnits[indicies[0]-1]
        yVals = self.selectedData[indicies,:]
        pOptions = {
                "X Scale": "Linear",
                "X Label": self.indepVarsList[0][0],
                "X Units": self.indepVarsList[0][3],
                "Y Scale": "Linear",
                "Y Label": '',
                "Y Units": commonUnit,
                "Title": self.datasetName,
                "Color": None,
                "Marker Style": None,
                "Enable Grid": False,
                "Hide Variable": False}
        self.graphicsLayout.clear()
        # self.clearGraphicsLayout()
        if self.indepVarsList[0][2] == 'utc_datetime':
            axis = {'bottom': TimeAxisItem(orientation='bottom')}
            pOptions['X Units'] = None
        else:
            axis = None
        p = self.graphicsLayout.addPlot(axisItems=axis)
        p.addLegend()
        p.setTitle(pOptions['Title'], size='22pt')
        p.setLabel('bottom', pOptions["X Label"], units=pOptions["X Units"],
                    **STYLE_DEFAULTS)
        p.setLabel('left', pOptions["Y Label"], units=pOptions["Y Units"],
                    **STYLE_DEFAULTS)
        p.getAxis('bottom').setStyle(tickTextOffset=22, tickFont=QtGui.QFont().setPointSize(22))
        p.getAxis('left').setStyle(tickTextOffset=22, tickFont=QtGui.QFont().setPointSize(22))
        for i in range(len(self.selectedDepVars)):
            p.plot( x=self.selectedData[0], y=yVals[i],
                     name = self.selectedDepVars[i],
                     pen=(i,len(self.selectedDepVars)))

        p.getAxis('left').tickFont = self.font
        p.getAxis('bottom').tickFont = self.font


    def plot2D(self):
        stime = time()
        (xVals, yVals), depGrids = self.extractIndepData(self.selectedData)
        varNames = [var[0] for var in self.depVarsList]
        index = varNames.index(self.selectedDepVars[0])
        self.graphicsLayout.clear()
        axis = {}
        for i in range(len(self.indepVarsList)):
            if self.indepVarsList[i][2] == 'utc_datetime':
                axis = {['bottom','left'][i]: TimeAxisItem(orientation=['bottom','left'][i])}
                pOptions[['X Units','Y Units'][i]] = None
        p = self.graphicsLayout.addPlot(axisItems=axis, row=1, col=1)
        p.setTitle(self.datasetName, size='22pt')
        p.setLabel('bottom', self.indepVarsList[0][0], units=self.indepVarsList[0][3], **STYLE_DEFAULTS)
        p.setLabel('left', self.indepVarsList[1][0], units=self.indepVarsList[1][3], **STYLE_DEFAULTS)
        p.getAxis('bottom').setStyle(tickTextOffset=22, tickFont=QtGui.QFont().setPointSize(22))
        p.getAxis('left').setStyle(tickTextOffset=22, tickFont=QtGui.QFont().setPointSize(22))
        img = pg.ImageItem()
        img.setImage(depGrids[index])
        p.addItem(img)
        pixelX = (xVals[-1]-xVals[0])/len(xVals)
        pixelY = (yVals[-1]-yVals[0])/len(yVals)
        img.translate(xVals[0],yVals[0])
        img.scale(pixelX,pixelY)

        # bipolar colormap
        pos = np.array([0., 0.125, 0.375, 0.667, 0.933, 1.])
        color = np.array([[0,0,143,255], [0,0,255,255], [0,255,255,255], (255, 255, 0, 255), (255, 0, 0, 255), (128, 0, 0, 255)], dtype=np.ubyte)
        cmap = pg.ColorMap(pos, color)
        lut = cmap.getLookupTable(0., 1., 256)
        img.setLookupTable(lut)

        min = np.min(depGrids[index])
        max = np.max(depGrids[index])

        # calculate equidistant markers between min and max
        tick_labels = []
        for i in range(0, 5):
            tick_labels.append(str(round((min + ((max - min) * i ) / 4), 3)))

        if self.cb is not None:
            self.cb.hide()

        self.cb = ColorBar(cmap, 10, 200, min, max, label=self.selectedDepVars[0], tick_labels = tick_labels)
        self.cb.translate(170, 90)
        self.cb.setAcceptHoverEvents(True)
        # self.cb.hide()
        # print cb.acceptHoverEvents()

        p.scene().addItem(self.cb)

        axis = p.getAxis('left')
        axis.tickFont = self.font
        axis.setWidth(100)
        axis = p.getAxis('bottom').tickFont = self.font

        p.autoRange()


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
        if self.root + "/" in path:
            path = path.replace(self.root+"/", '')
        elif self.root in path:
            path = path.replace(self.root, '')
        return path.split('/')


    def clearGraphicsLayout(self):
        # Remove all widgets from GraphicsLayoutWidget
        self.graphicsLayout.clear()

    def getListOfAvailabePlotTypes(self, selectedVarsList=None):
        if selectedVarsList is None:
            selectedVarsList = self.depVarsList
        if len(self.indepVarsList) == 1:
            if len(selectedVarsList) >= 2: # 1D Traj Plot Types require 2 selected dependent vars
                return ["1D", "1D Parametric"]
            elif len(selectedVarsList) == 1:
                return ["1D"]
            else:
                return ["Please select at least on variable for plotting"]
        elif len(self.indepVarsList) == 2:
            if len(selectedVarsList) >= 2:
                return ["2D Scan", "3D Surface", "2D Parametric", "Projection"] #3D Parametric for > 3 indeps
            elif len(selectedVarsList) == 1:
                return ["2D Scan", "3D Contour", "Projection"]
        else:
            return ["There are no available plot types for "+str(len(self.indepVarsList))+ " dimensional data."]

    def getVarsWithCommonUnitsDict(self):
        compatibleVarsDict = {}
        for depVar in self.depVarsList:
            # depVar of form (name, shape, dtype, units)
            name = depVar[0]
            units = depVar[3]
            if units not in compatibleVarsDict.keys():
                compatibleVarsDict[units] = [name]
            else:
                compatibleVarsDict[units].append(name)
        return compatibleVarsDict

    def getVarsWithCommonShapeList(self, varsWithSameUnits, selectedVarName):
        varsWithCommonShapeList = []
        for depVar in self.depVarsList:
            # depVar of form (name, shape, dtype, units)
            name = depVar[0]
            shape = depVar[1]
            #units = depVar[3]
            if name == selectedVarName:
                selectedVarShape = shape

        for depVar in self.depVarsList:
            # depVar of form (name, shape, dtype, units)
            name = depVar[0]
            shape = depVar[1]
            if (name in varsWithSameUnits) and shape == selectedVarShape:
                varsWithCommonShapeList.append(name)

        return varsWithCommonShapeList

    # recenter with spacebar
    def keyPressEvent(self, QKeyEvent):
        if QKeyEvent.key() == QtCore.Qt.Key_Space:
            if len(self.indepVarsList) == 1:
                self.plot1D()
            elif len(self.indepVarsList) == 2:
                self.plot2D()
        elif QKeyEvent.key() == QtCore.Qt.Key_Up:
            print 'event triggered'
            print self.directoryTree.indexAbove(self.model)
        # elif QKeyEvent.key() == QtCore.Qt.Key_E:
        #     exporter = pg.exporters.ImageExporter(self.plt.plotItem)
        #     if len(self.indepVarsList) == 1:
        #         exporter.parameters()['width'] = 100
        #         exporter.export('testPlot.png')

class ColorBar(pg.GraphicsObject):

    def __init__(self, cmap, width, height, min, max, ticks=None, tick_labels=None, label=None, clear = False):
        pg.GraphicsObject.__init__(self)

        # handle args
        label = label or ''
        w, h = width, height
        stops, colors = cmap.getStops('float')
        smn, spp = stops.min(), stops.ptp()
        stops = (stops - stops.min())/stops.ptp()
        if ticks is None:
            ticks = np.r_[0.0:1.0:5j, 1.0] * spp + smn
        tick_labels = tick_labels or ["%0.2g" % (t,) for t in ticks]

        # setup picture
        self.pic = pg.QtGui.QPicture()
        p = pg.QtGui.QPainter(self.pic)

        mintx = 0.0

        # compute rect bounds for underlying mask
        self.br = p.boundingRect(0, 0, 0, 0, pg.QtCore.Qt.AlignRight, label)
        self.zone = mintx - 50, -15.0,  75, h + self.br.height() + 30.0

        p.setPen(pg.QtGui.QColor(255, 255, 255, 0))
        p.setBrush(pg.QtGui.QColor(255, 255, 255, 180))
        p.drawRect(*(self.zone))

        # draw bar with gradient following colormap
        p.setPen(pg.mkPen('k'))
        grad = pg.QtGui.QLinearGradient(w/2.0, 0.0, w/2.0, h*1.0)
        for stop, color in zip(stops, colors):
            grad.setColorAt(1.0 - stop, pg.QtGui.QColor(*[c for c in color]))
        p.setBrush(pg.QtGui.QBrush(grad))
        p.drawRect(pg.QtCore.QRectF(0, 0, w, h))

        # draw ticks & tick labels

        for tick, tick_label in zip(ticks, tick_labels):
            y_ = (1.0 - (tick - smn)/spp) * h
            p.drawLine(0.0, y_, -5.0, y_)
            br = p.boundingRect(0, 0, 0, 0, pg.QtCore.Qt.AlignRight, tick_label)
            if br.x() < mintx:
                mintx = br.x()
            p.drawText(br.x() - 10.0, y_ + br.height() / 4.0, tick_label)

        # draw label
        p.drawText(-self.br.width() / 2.0 - 10, h + self.br.height() + 5.0, label)
        # done
        p.end()

    def paint(self, p, *args):
        # paint underlying mask


        # paint colorbar
        p.drawPicture(0, 0, self.pic)

    def boundingRect(self):
        return pg.QtCore.QRectF(self.pic.boundingRect())

    def mousePressEvent(self, *args, **kwargs):
        self.setOpacity(0.0)

    def mouseReleaseEvent(self, *args, **kwargs):
        self.setOpacity(1.0)


if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    app.setApplicationName('MyWindow')

    main = Grapher()
    main.showMaximized()
    # main.move(app.desktop().screen().rect().center() - main.rect().center())
    main.show()

    sys.exit(app.exec_())