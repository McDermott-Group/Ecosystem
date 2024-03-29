import os
import sys
from PyQt4 import QtCore, QtGui
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt4agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar,
)
from matplotlib.dates import DateFormatter, AutoDateLocator, date2num
import matplotlib.cm as cm
import matplotlib as mpl
from functools import partial
from datetime import datetime
from dateutil import tz

from dataChest import *
from dataChest import dateStamp

mpl.rcParams["agg.path.chunksize"] = 10000


class Main(QtGui.QWidget):
    def __init__(self, parent=None):
        super(Main, self).__init__(parent)
        self.setWindowTitle("Data Chest Image Browser")
        # Add in Rabi plot.
        self.setWindowIcon(QtGui.QIcon("rabi.jpg"))

        self.root = os.environ["DATA_ROOT"]
        if "\\" in self.root:
            self.root = self.root.replace("\\", "/")
        self.pathRoot = QtCore.QString(self.root)

        self.filters = QtCore.QStringList()
        self.filters.append("*.hdf5")

        self.dataChest = dataChest("", self.root)

        self.local_tz = tz.tzlocal()
        self.utc = tz.gettz("UTC")

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
        self.directoryTree.clicked.connect(self.dirTreeSelectionMade)

        # Plot types drop down list configuration.
        self.plotTypesComboBoxLabel = QtGui.QLabel(self)
        self.plotTypesComboBoxLabel.setText("Available Plot Types:")

        self.plotTypesComboBox = QtGui.QComboBox(self)
        self.plotTypesComboBox.activated[str].connect(self.plotTypeSelected)

        # Configure scrolling widget.
        self.scrollWidget = QtGui.QWidget(self)
        self.scrollLayout = QtGui.QHBoxLayout(self)
        self.scrollWidget.setLayout(self.scrollLayout)
        self.scrollArea = QtGui.QScrollArea(self)
        self.scrollArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.scrollArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.scrollArea.setWidget(self.scrollWidget)
        self.scrollArea.setWidgetResizable(True)  # What happens without?

        vbox = QtGui.QVBoxLayout()
        vbox.addWidget(self.directoryBrowserLabel)
        vbox.addWidget(self.directoryTree)
        vbox.addWidget(self.plotTypesComboBoxLabel)
        vbox.addWidget(self.plotTypesComboBox)
        vbox.addWidget(self.scrollArea)

        self.mplwindow = QtGui.QWidget(self)
        self.mplvl = QtGui.QVBoxLayout(self.mplwindow)

        hbox = QtGui.QHBoxLayout()
        hbox.addLayout(vbox)
        hbox.addWidget(self.mplwindow)
        self.setLayout(hbox)

        self.currentFig = Figure()
        self.addFigureToCanvas(self.currentFig)

        self.filePath = None  # redundant
        self.fileName = None  # redundant
        self.plotType = None  # redundant
        self.varsToIgnore = []

    def plotTypeSelected(self, plotType):
        # Called when a plotType selection is made from drop down.
        # self.plotTypesComboBox.adjustSize()
        if plotType != self.plotType:
            self.removeFigFromCanvas()
            self.currentFig = self.figFromFileInfo(
                self.filePath, self.fileName, selectedPlotType=plotType
            )
            self.addFigureToCanvas(self.currentFig)
            self.updatePlotTypeOptions(plotType)
            self.plotType = plotType
            # When is best time to do this?
            self.varsToIgnore = []

    def updatePlotTypeOptions(self, plotType, depVarName=None):
        # Update area below plotType, selection drop down (add/remove variables)
        self.clearLayout(self.scrollLayout)
        if plotType == "1D" or plotType == "Histogram":
            headerList = ["Dep Var:", "Status:"]
            widgetTypeList = ["QLabel", "QCheckBox"]
            depVarList = [row[0] for row in self.dataChest.getVariables()[1]]
            for ii in range(0, len(headerList)):
                optionsSlice = QtGui.QVBoxLayout()
                label = QtGui.QLabel(self)  # widget to log
                label.setText(headerList[ii])
                optionsSlice.addWidget(label)
                for depVar in depVarList:
                    if widgetTypeList[ii] == "QLabel":
                        label = QtGui.QLabel(self)  # widget to log
                        label.setText(depVar)
                        optionsSlice.addWidget(label)
                    elif widgetTypeList[ii] == "QCheckBox":
                        checkBox = QtGui.QCheckBox("", self)  # widget to log
                        checkBox.setCheckState(QtCore.Qt.Checked)
                        checkBox.stateChanged.connect(
                            partial(self.varStateChanged, depVar)
                        )
                        optionsSlice.addWidget(checkBox)
                optionsSlice.addStretch(1)
                self.scrollLayout.addLayout(optionsSlice)
            self.scrollLayout.addStretch(1)
        elif plotType == "2D Image":
            headerList = ["Dep Var:", "Status:"]
            widgetTypeList = ["QLabel", "QCheckBox"]
            depVarList = [row[0] for row in self.dataChest.getVariables()[1]]
            if depVarName is None:
                depVarName = depVarList[0]
            for ii in range(0, len(headerList)):
                optionsSlice = QtGui.QVBoxLayout()
                label = QtGui.QLabel(self)  # widget to log
                label.setText(headerList[ii])
                optionsSlice.addWidget(label)
                for depVar in depVarList:
                    if widgetTypeList[ii] == "QLabel":
                        label = QtGui.QLabel(self)  # widget to log
                        label.setText(depVar)
                        optionsSlice.addWidget(label)
                    elif widgetTypeList[ii] == "QCheckBox":
                        checkBox = QtGui.QCheckBox("", self)  # widget to log
                        print("depVarName=", depVarName)
                        if depVar == depVarName:
                            checkBox.setCheckState(QtCore.Qt.Checked)
                        checkBox.stateChanged.connect(
                            partial(self.varStateChanged, depVar)
                        )
                        optionsSlice.addWidget(checkBox)
                optionsSlice.addStretch(1)
                self.scrollLayout.addLayout(optionsSlice)
            self.scrollLayout.addStretch(1)

    def clearLayout(self, layout):
        # Clear the plotType options layout and all widgets therein.
        for i in reversed(list(range(layout.count()))):
            item = layout.itemAt(i)

            if isinstance(item, QtGui.QWidgetItem):
                item.widget().close()
            elif not isinstance(item, QtGui.QSpacerItem):
                self.clearLayout(item.layout())
            # remove the item from layout
            layout.removeItem(item)

    def varStateChanged(self, name, state):
        # Add/remove variables from current displayed plot.
        if state == QtCore.Qt.Checked:
            self.varsToIgnore.remove(name)
            # Remove old figure, needs garbage collection too.
            self.removeFigFromCanvas()
            self.currentFig = self.figFromFileInfo(
                self.filePath,
                self.fileName,
                selectedPlotType=self.plotType,
                varsToIgnore=self.varsToIgnore,
            )
            self.addFigureToCanvas(self.currentFig)
        else:  # unchecked
            if name not in self.varsToIgnore:
                self.varsToIgnore.append(name)
            # Remove old figure, needs garbage collection too.
            self.removeFigFromCanvas()
            self.currentFig = self.figFromFileInfo(
                self.filePath,
                self.fileName,
                selectedPlotType=self.plotType,
                varsToIgnore=self.varsToIgnore,
            )
            self.updatePlotTypeOptions(self.plotType, "")
            self.addFigureToCanvas(self.currentFig)

    def convertPathToArray(self, path):
        if self.root + "/" in path:
            path = path.replace(self.root + "/", "")
        elif self.root in path:
            path = path.replace(self.root, "")
        return path.split("/")

    def addFigureToCanvas(self, fig):
        # Addsmpl fig to the canvas.
        self.canvas = FigureCanvas(fig)
        self.mplvl.addWidget(self.canvas)
        self.canvas.draw()
        self.toolbar = NavigationToolbar(self.canvas, self.mplwindow, coordinates=True)
        self.mplvl.addWidget(self.toolbar)

    def removeFigFromCanvas(self):
        # Remove fig from the canvas.
        self.mplvl.removeWidget(self.canvas)
        self.canvas.close()
        self.mplvl.removeWidget(self.toolbar)
        self.toolbar.close()
        self.currentFig.clf()

    @QtCore.pyqtSlot(QtCore.QModelIndex)  # logical flow could be improved
    def dirTreeSelectionMade(self, index):
        # Called when a directory tree selection is made.
        indexItem = self.model.index(index.row(), 0, index.parent())
        fileName = str(self.model.fileName(indexItem))
        filePath = str(self.model.filePath(indexItem))

        if ".hdf5" in filePath:
            # Removes fileName from path if file is chosen.
            filePath = filePath[: -(len(fileName) + 1)]

        if self.fileName != fileName or self.filePath != filePath:
            # If an actual change occurs update check what happens for
            # just a folder.
            self.filePath = filePath  # Is there a point in storing this?
            self.fileName = fileName

            if ".hdf5" in fileName:
                # fileName is not a directory, otherwise leave as is
                # till a file is selected.
                self.removeFigFromCanvas()
                # Remove old figure, needs garbage collection too.
                self.currentFig = self.figFromFileInfo(self.filePath, self.fileName)
                self.addFigureToCanvas(self.currentFig)
                variables = self.dataChest.getVariables()  # fine
                dataCategory = self.categorizeDataset(variables)  # fine
                self.updatePlotTypesList(
                    self.supportedPlotTypes(dataCategory)
                )  # fine: updates list
                self.updatePlotTypeOptions(self.supportedPlotTypes(dataCategory)[0])
                self.plotType = self.supportedPlotTypes(dataCategory)[0]
                self.varsToIgnore = []  # When is best time to do this?
            else:
                self.fileName = None

    def updatePlotTypesList(self, plotTypes):
        # Update plotTypes list based on selected dataset.
        self.plotTypesComboBox.clear()
        for element in plotTypes:
            if ".dir" not in str(element) and ".ini" not in str(element):
                self.plotTypesComboBox.addItem(str(element))

    def categorizeDataset(self, variables):
        # Categorizes dataset, this is now redundant.
        indepVarsList = variables[0]
        numIndepVars = len(indepVarsList)
        if numIndepVars == 1:
            return "1D"
        elif numIndepVars == 2:
            return "2D"
        else:
            return str(numIndepVars) + "D"

    def supportedPlotTypes(self, dimensionality):
        # Provide list of plotTypes based on datasetType.
        if dimensionality == "1D":
            plotTypes = ["1D", "Histogram"]
        elif dimensionality == "2D":
            plotTypes = ["2D Image"]
        else:
            plotTypes = []
        return plotTypes

    # Some shape checking needs to go into this function to ensure
    # 1D array inputs.
    def plot1D(self, dataset, variables, plotType, dataClass, varsToIgnore=[]):
        # Shorten this monstrosity!
        # print "varsToIgnore=", varsToIgnore
        if plotType == None:
            plotType = self.supportedPlotTypes("1D")[0]  # defaults
        elif plotType not in self.supportedPlotTypes("1D"):
            print("Unrecognized plot type was provided")
            # Return bum fig with something cool, maybe a gif.
        if plotType == "1D":
            fig = self.basic1DPlot(dataset, variables, varsToIgnore)
        elif plotType == "Histogram":
            # Adjust bin size.
            fig = self.basic1DHistogram(dataset, variables, varsToIgnore)
        return fig

    # Some shape checking needs to go into this function to ensure
    # 2D array inputs.
    def plot2D(self, dataset, variables, plotType, dataClass, varsToIgnore=[]):
        # Shorten this monstrosity!
        # print "varsToIgnore=", varsToIgnore
        if plotType == None:
            plotType = self.supportedPlotTypes("2D")[0]  # defaults
        elif plotType not in self.supportedPlotTypes("2D"):
            print("Unrecognized plot type was provided")
            # Return bum fig with something cool, maybe a gif.
        if plotType == "2D Image":
            fig = self.basic2DImage(dataset, variables, varsToIgnore)
        # elif plotType == "Histogram": #adjust bin size
        #    fig = self.basic1DHistogram(dataset, variables, varsToIgnore)
        return fig

    def basic2DImage(self, dataset, variables, varsToIgnore):
        fig = Figure(dpi=100)
        ax = fig.add_subplot(111)
        indepVars = variables[0]
        depVars = variables[1]
        if varsToIgnore == [depVars[ii][0] for ii in range(0, len(depVars))]:
            return fig
        #       dataset = np.asarray(dataset)
        xlabel = self.dataChest.getParameter("X Label", True)
        if xlabel is None:
            xlabel = indepVars[0][0]
        ylabel = self.dataChest.getParameter("Y Label", True)
        if ylabel is None:
            # For data with more than one dep, recommend ylabel.
            ylabel = depVars[0][0]
        plotTitle = self.dataChest.getParameter("Plot Title", True)
        if plotTitle is None:
            plotTitle = self.dataChest.getDatasetName()
        ax.set_title(plotTitle)
        ax.set_xlabel(xlabel + " " + "(" + indepVars[0][3] + ")")
        ax.set_ylabel(ylabel + " " + "(" + depVars[0][3] + ")")
        # For multiple deps with different units this is ambiguous.
        imageType = self.dataChest.getParameter("Image Type", True)
        if imageType is None and self.dataChest.getDataCategory() == "2D Scan":
            imageType = "2D Scan"
        print("imageType=", imageType)

        if imageType is None:
            dataset = np.asarray(dataset)
            # Add or "scatter"
            imageType = "Scatter"
            print("Scatter")
            for ii in range(0, len(depVars)):
                x = dataset[::, 0]
                y = dataset[::, 1]
                z = dataset[::, 2]
                im = ax.tricontourf(
                    x, y, z, 100, cmap=cm.gist_rainbow, antialiased=True
                )
                fig.colorbar(im, fraction=0.15)
                break
        elif imageType == "Pixel":
            xGridRes = self.dataChest.getParameter("X Resolution", True)
            xIncrement = self.dataChest.getParameter("X Increment", True)
            yGridRes = self.dataChest.getParameter("Y Resolution", True)
            yIncrement = self.dataChest.getParameter("Y Increment", True)
            dataset = np.asarray(dataset)
            x = dataset[::, 0].flatten()
            y = dataset[::, 1].flatten()
            z = dataset[::, 2].flatten()
            if len(x) > 1:
                if x[0] == x[1]:
                    sweepType = "Y"
                else:
                    sweepType = "X"
                print("sweepType=", sweepType)
                new = self.makeGrid(
                    x, xGridRes, xIncrement, y, yGridRes, yIncrement, sweepType, z
                )  # makeGrid(self, x, xGridRes, dX, y, yGridRes, dY, sweepType, z)
                X = new[0]
                Y = new[1]
                Z = new[2]
                im = ax.imshow(
                    Z,
                    extent=(X.min(), X.max(), Y.min(), Y.max()),
                    interpolation="nearest",
                    cmap=cm.gist_rainbow,
                    origin="lower",
                )
                fig.colorbar(im, fraction=0.15)
        elif imageType == "2D Scan":
            nx = len(dataset)
            ny = len(dataset[0][2])
            z = []
            for ii in range(0, nx):
                z.append(dataset[ii][2])
            x = [dataset[0][0], dataset[-1][0]]
            x = np.asarray(x)
            y = np.linspace(dataset[0][1][0], dataset[0][1][1], ny)
            z = np.asarray(z)
            z = z.flatten()
            z = z.reshape(nx, ny)
            im = ax.imshow(
                z,
                extent=(x.min(), x.max(), y.min(), y.max()),
                aspect="auto",
                interpolation="nearest",
                cmap=cm.gist_rainbow,
                origin="lower",
            )
            fig.colorbar(im, fraction=0.15)
        elif imageType == "Buffered":
            print("Buffered")
        return fig

    def _utc_to_local(self, utcDatetime):
        localDatetime = utcDatetime.replace(tzinfo=self.utc)
        return localDatetime.astimezone(self.local_tz)

    def basic1DPlot(self, dataset, variables, varsToIgnore):
        fig = Figure(dpi=100)
        ax = fig.add_subplot(111)
        indepVars = variables[0]
        depVars = variables[1]
        containsDatetime = False
        for ii in range(0, len(indepVars)):
            if "utc_datetime" in indepVars[ii]:
                containsDatetime = True

        scanType = self.dataChest.getParameter("Scan Type", True)
        xlabel = self.dataChest.getParameter("X Label", True)
        if xlabel is None:
            xlabel = indepVars[0][0]
        ylabel = self.dataChest.getParameter("Y Label", True)
        if ylabel is None:
            # For data with more than one dep, recommend ylabel.
            ylabel = depVars[0][0]
        plotTitle = self.dataChest.getParameter("Plot Title", True)
        if plotTitle is None:
            plotTitle = self.dataChest.getDatasetName()
        ax.set_title(plotTitle)
        dataset = np.asarray(dataset)
        ax.set_xlabel(xlabel + " " + "(" + indepVars[0][3] + ")")
        ax.set_ylabel(ylabel + " " + "(" + depVars[0][3] + ")")
        # For multiple deps with different units this is ambiguous.
        for ii in range(0, len(depVars)):
            if depVars[ii][0] not in varsToIgnore:
                if scanType is None:
                    x = dataset[::, 0].flatten()
                    # Only works when all dims are same => perform checks.
                    y = dataset[::, 1 + ii].flatten()
                    if containsDatetime:
                        dStamp = dateStamp()
                        dates = []
                        for jj in range(0, len(y)):
                            dates.append(
                                self._utc_to_local(
                                    datetime.strptime(
                                        dStamp.floatToUtcDateStr(x[jj]),
                                        "%Y-%m-%dT%H:%M:%S.%f",
                                    )
                                )
                            )
                        dates = np.asarray(dates)
                        print(dates)
                        dates = date2num(dates)
                        dateFmt = DateFormatter("%m/%d/%Y %H:%M:%S")
                        auto = AutoDateLocator()
                        ax.xaxis.set_major_locator(auto)
                        ax.xaxis.set_major_formatter(dateFmt)
                        ax.tick_params(axis="x", labelsize=9)
                        ax.grid(True)
                        ax.autoscale_view()
                elif scanType == "Lin":
                    y = np.asarray(dataset[0][1 + ii])
                    # Only one row of data for this and log type supported.
                    x = np.linspace(dataset[0][0][0], dataset[0][0][1], num=len(y))
                elif scanType == "Log":
                    y = dataset[0][1 + ii]
                    x = np.logspace(
                        np.log10(dataset[0][0][0]),
                        np.log10(dataset[0][0][1]),
                        num=len(y),
                    )
                    ax.set_xscale("log")
                # ax.plot(x, y, "o", label = depVars[ii][0])
                if containsDatetime:
                    ax.plot_date(
                        dates,
                        y,
                        tz=self.utc,
                        linestyle="-",
                        marker=",",
                        label=depVars[ii][0],
                    )
                    fig.autofmt_xdate()
                    fig.tight_layout()
                else:
                    ax.plot(x, y, label=depVars[ii][0])
        ax.legend(fontsize=10, loc="best")
        return fig

    def basic1DHistogram(self, dataset, variables, varsToIgnore):
        fig = Figure(dpi=100)
        ax = fig.add_subplot(111)
        indepVars = variables[0]
        depVars = variables[1]
        scanType = self.dataChest.getParameter("Scan Type", True)
        xlabel = self.dataChest.getParameter("X Label", True)
        ylabel = self.dataChest.getParameter("Y Label", True)
        if ylabel is None:
            ylabel = depVars[0][0]
            # For data with more than one dep, recommend ylabel.
        plotTitle = self.dataChest.getParameter("Plot Title", True)
        if plotTitle is None:
            plotTitle = self.dataChest.getDatasetName()
        ax.set_title(plotTitle)
        dataset = np.asarray(dataset)
        ax.set_xlabel(ylabel + " " + "(" + depVars[0][3] + ")")
        # For multiple deps with different units this is ambiguous.
        ax.set_ylabel("Statistical Frequency")
        for ii in range(0, len(depVars)):
            if depVars[ii][0] not in varsToIgnore:
                if scanType is None:
                    y = dataset[::, 1 + ii].flatten()
                elif scanType == "Lin":
                    y = dataset[0][1 + ii]
                elif scanType == "Log":
                    y = dataset[0][1 + ii]
                weights = np.ones_like(y) / float(len(y))
                ax.hist(y, 100, weights=weights, alpha=0.5, label=depVars[ii][0])
                # ax.hist(y, 50, normed=1,weights =weights, alpha=0.5, label = depVars[ii][0])
        ax.legend()
        return fig

    def figFromFileInfo(
        self, filePath, fileName, selectedPlotType=None, varsToIgnore=[]
    ):
        relPath = self.convertPathToArray(filePath)
        self.dataChest.cd(relPath)
        self.dataChest.openDataset(fileName)
        variables = self.dataChest.getVariables()
        dataCategory = self.categorizeDataset(variables)
        # otherwise refer to dataset name needs to be implemented
        dataset = self.dataChest.getData()
        if dataCategory == "1D":
            fig = self.plot1D(
                dataset, variables, selectedPlotType, None, varsToIgnore=varsToIgnore
            )
            # plot1D(self, dataset, variables, plotType, dataClass, varsToIgnore = [])
        elif dataCategory == "2D":  # was "2D Sweep"
            fig = self.plot2D(
                dataset, variables, selectedPlotType, None, varsToIgnore=varsToIgnore
            )
        else:
            print(
                (
                    "1D data is the only type currently \r\n"
                    + "supported by this grapher."
                )
            )
            print(("Attempted to plot " + dataCategory + " data."))
            fig = Figure(dpi=100)
        self.dataChest.cd("")
        # yield self.cxn.data_vault.dump_existing_sessions()
        return fig

    def makeGrid(self, x, xGridRes, dX, y, yGridRes, dY, sweepType, z):
        totalNumPts = len(x)

        if sweepType == "Y":
            # Y sweep type ==> fix x, sweep y, then go to x+dx and
            # sweep y again...
            divNmod = divmod(len(x), yGridRes)
            numFullYslices = divNmod[0]
            numPartiallyComplete = divNmod[1]
            if numFullYslices < xGridRes:
                npxRemainder = np.array([])
                npyRemainder = np.array([])
                # What kind of beast is the line below?
                nanArray = np.zeros(
                    shape=(
                        yGridRes * xGridRes
                        - yGridRes * numFullYslices
                        - numPartiallyComplete,
                    )
                )
                nanArray[:] = np.NAN
                # Is this pseudo-23 dimensional space definition?
                npzRemainder = np.concatenate(
                    [
                        z[
                            yGridRes * numFullYslices : yGridRes * numFullYslices
                            + numPartiallyComplete
                        ],
                        nanArray,
                    ]
                )
                for ii in range(numFullYslices, xGridRes):
                    npxRemainder = np.concatenate(
                        [
                            npxRemainder,
                            np.linspace(dX * ii + x[0], dX * ii + x[0], num=yGridRes),
                        ]
                    )
                    npyRemainder = np.concatenate(
                        [
                            npyRemainder,
                            np.linspace(y[0], y[0] + (yGridRes - 1) * dY, num=yGridRes),
                        ]
                    )
            else:
                npxRemainder = np.array([])
                npyRemainder = np.array([])
                npzRemainder = np.array([])

            npx = np.concatenate([x[0 : yGridRes * numFullYslices], npxRemainder])
            npy = np.concatenate([y[0 : yGridRes * numFullYslices], npyRemainder])
            npz = np.concatenate([z[0 : yGridRes * numFullYslices], npzRemainder])

            npx = npx.reshape(xGridRes, yGridRes).T
            npy = npy.reshape(xGridRes, yGridRes).T
            npz = npz.reshape(xGridRes, yGridRes).T
        elif sweepType == "X":
            # X sweep type ==> fix y, sweep x, then go to x+dy and
            # sweep y again...
            divNmod = divmod(len(x), xGridRes)
            numFullXslices = divNmod[0]
            numPartiallyComplete = divNmod[1]
            if numFullXslices < yGridRes:
                npxRemainder = np.array([])
                npyRemainder = np.array([])
                nanArray = np.zeros(
                    shape=(
                        yGridRes * xGridRes
                        - xGridRes * numFullXslices
                        - numPartiallyComplete,
                    )
                )
                nanArray[:] = np.NAN
                npzRemainder = np.concatenate(
                    [
                        z[
                            xGridRes * numFullXslices : xGridRes * numFullXslices
                            + numPartiallyComplete
                        ],
                        nanArray,
                    ]
                )
                for ii in range(numFullXslices, yGridRes):
                    npyRemainder = np.concatenate(
                        [
                            npyRemainder,
                            np.linspace(dY * ii + y[0], dY * ii + y[0], num=xGridRes),
                        ]
                    )
                    npxRemainder = np.concatenate(
                        [
                            npxRemainder,
                            np.linspace(x[0], x[0] + (xGridRes - 1) * dX, num=xGridRes),
                        ]
                    )
            else:
                npxRemainder = np.array([])
                npyRemainder = np.array([])
                npzRemainder = np.array([])
            npx = np.concatenate([x[0 : xGridRes * numFullXslices], npxRemainder])
            npy = np.concatenate([y[0 : xGridRes * numFullXslices], npyRemainder])
            npz = np.concatenate([z[0 : xGridRes * numFullXslices], npzRemainder])

            npx = npx.reshape(xGridRes, yGridRes)
            npy = npy.reshape(xGridRes, yGridRes)
            npz = npz.reshape(xGridRes, yGridRes)
        return (npx, npy, npz)


if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    app.setApplicationName("MyWindow")

    main = Main()
    main.resize(1000, 700)
    main.move(app.desktop().screen().rect().center() - main.rect().center())
    main.show()

    sys.exit(app.exec_())
