# -*- coding: utf-8 -*-

import sys
import os
import importlib
import h5py
import numpy as np

# --- Import the bapsflib Specific HDF5 Package ---
try:
    from bapsflib import lapdhdf
except ModuleNotFoundError:
    PACKAGE_PARENT = 'bapsflib'
    PACKAGE_PARENT_DIR = ''
    CURRENT_DIR = os.getcwd()

    # Find the dir where the package bapsflib resides
    # this is only done if bapsflib is not found in PYTHONPATH
    strIndex = os.getcwd().find(PACKAGE_PARENT)
    PACKAGE_PARENT_DIR = CURRENT_DIR[:strIndex]

    sys.path.append(os.path.normpath(os.path.join(
        PACKAGE_PARENT_DIR, PACKAGE_PARENT)))

    from bapsflib import lapdhdf

# --- Import Required PyQt5 Packages --
import PyQt5.uic as pyuic
from PyQt5 import QtGui, QtWidgets, QtCore, QtChart

# --- Import UI Files Built with Qt Creator ---
try:
    from .UIs import mainwindow, wdgSimplePlotConfig
except (ModuleNotFoundError, ImportError):
    # relative imports don't work from command line execution
    from UIs import mainwindow, wdgSimplePlotConfig


#def rebuildUiFiles():
#    """
#        This is for use during development process so that the .ui files
#        don't have to be recompiled separately before running main.py
#    """
#    pyuic.compileUiDir('UIs/', execute=True)
#    uiModules = ['mainwindow', 'wdgSimplePlotConfig']
#    for modName in sys.modules.keys():
#        for uiName in uiModules:
#            if modName.__contains__(uiName):
#                importlib.reload(sys.modules[modName])
#
#
#rebuildUiFiles()

class Viewer(QtWidgets.QMainWindow, mainwindow.Ui_MainWindow):
    _hdfFilename = ''
    _strDefaultRootParentLabel = 'Root Parent'
    _strDefaultSelectedItemLabel = 'Item Selected'
    _selected_hdf_item_path = ''
    _selected_hdf_item = None

    def __init__(self):
        super(self.__class__, self).__init__()
        self.setupUi(self)

        # Add Plot Config Widget to MainWindow
        self.wdgSimplePlotConfig = simplePlotConfig()
        self.framePlotConfig.layout().addWidget(
            self.wdgSimplePlotConfig)
        self.wdgSimplePlotConfig.setVisible(False)

        # Condition/Initialize Item Selected Title Bar
        self.labelShowRows.setVisible(False)
        self.cboxStartRow.setVisible(False)
        self.labelTo.setVisible(False)
        self.cboxStopRow.setVisible(False)
        self.btnDisplayDataTable.setVisible(False)
        self.cboxStartRow.setInsertPolicy(QtWidgets.QComboBox.NoInsert)
        self.cboxStopRow.setInsertPolicy(QtWidgets.QComboBox.NoInsert)
        self.cboxStartRow.setDuplicatesEnabled(False)
        self.cboxStopRow.setDuplicatesEnabled(False)

        # Opening HDF5 File
        self.actionOpen_HDF5.triggered.connect(self.getFile)
        self.pushOpenHDF.clicked.connect(self.getFile)
        self.textFilenameContainer.textChanged.connect(self.openHDF)

        # QTreeView
        # Condition treeView s.t. horizontal scrollbar will show
        self.treeView.header().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeToContents)
        self.treeView.pressed.connect(self.getHDFItemPath)
        self.buildTreeContextMenu()
        self.treeView.customContextMenuRequested.connect(
            self.treeContextMenu)

        # Condition Splitter Widgets
        #  In order for these to be well-behaved the sum needs to be
        #  greater than 100. Also, set the QPolicySize stretch options
        #  to zero and, I found, to prevent awkward snapping of the
        #  splitter handle then one should set the appropriate
        #  minimumWidth/minimumHeight to 1.
        #
        #        self.splitterLV.setSizes([150, 50])
        self.splitterRV.setSizes([50, 150])
        #        self.splitter.setStretchFactor(0,0)
        #        self.splitter.setStretchFactor(1,1)
        #        self.splitter.setSizes([60, 140])

        # Condition Data Display Area (Data Tables and Plots)
        #print(self.scrollAreaDataDisplay.layout())
        _translate = QtCore.QCoreApplication.translate
        self.stackedlayoutDataDisplay = QtWidgets.QStackedLayout(
            self.scrollAreaDataDisplay)
        #self.stackedlayoutDataDisplay.setContentsMargins(0,0,0,0)

        self.wdgEmptyDataDisplay = QtWidgets.QWidget()
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Preferred,
            QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        self.wdgEmptyDataDisplay.setSizePolicy(sizePolicy)
        self.wdgEmptyDataDisplay.setObjectName('wdgEmptyDataDisplay')

        self.simpleDataPlot = formSimpleDataPlot()

        self.stackedlayoutDataDisplay.addWidget(
            self.wdgEmptyDataDisplay)
        self.stackedlayoutDataDisplay.addWidget(
            self.simpleDataPlot.view)

        self.wdgSimplePlotConfig.cboxPlotRow.setInsertPolicy(
            QtWidgets.QComboBox.NoInsert)
        self.wdgSimplePlotConfig.cboxXAxes.setInsertPolicy(
            QtWidgets.QComboBox.NoInsert)
        self.wdgSimplePlotConfig.cboxYAxes.setInsertPolicy(
            QtWidgets.QComboBox.NoInsert)

        self.wdgSimplePlotConfig.cboxPlotRow.currentIndexChanged.connect(
            self.simpleDataPlot.selectRow)
        self.wdgSimplePlotConfig.cboxXAxes.currentTextChanged.connect(
            self.simpleDataPlot.setXAxis)
        self.wdgSimplePlotConfig.cboxYAxes.currentTextChanged.connect(
            self.simpleDataPlot.setYAxis)

        self.wdgSimplePlotConfig.btnPlot.clicked.connect(
            self.toggleDataDisplay)

        # Connect Signals between PlotConfig and DataPlotDisplay
        self.simpleDataPlot.needRefresh.connect(
            self.wdgSimplePlotConfig.btnPlotState)

        # Clean if 'Clear' Requested
        self.pushClear.clicked.connect(self.cleanup)
        self.actionExit.triggered.connect(self.cleanup)

    def addTreeItem(self, itemPath, itemType):
        """
            Adds a single HDF5 item to the QTreeView.
        """
        # Define QIcon's for the HDF Tree
        iconFolder = QtWidgets.QApplication.style().standardIcon(
            QtWidgets.QStyle.SP_DirIcon)
        iconSDataset = QtGui.QIcon("icons/SidebarGenericFile.png")
        iconCDataset = QtGui.QIcon("icons/SidebarDocumentsFolder.png")
        # iconSDataset = QtWidgets.QApplication.style().standardIcon(
        #            QtWidgets.QStyle.SP_FileIcon)

        rootParent = self.modelTree.invisibleRootItem()

        elements = itemPath.split('/')
        noElems = elements.__len__()

        # Add Items to HDF Tree
        for ii in range(noElems):
            if ii == 0:
                newParent = rootParent
            else:
                newParent = childObj

            noOfChildren = newParent.rowCount()
            if noOfChildren != 0:
                # grab children
                dictChildren = {}
                for jj in range(noOfChildren):
                    newChild = newParent.child(jj)
                    dictChildren[newChild.text()] = newChild

                # Grab Child and Add to Parent
                if elements[ii] in list(dictChildren.keys()):
                    childObj = dictChildren[elements[ii]]
                else:
                    # Add child instance to parent
                    childObj = QtGui.QStandardItem(elements[ii])
                    newParent.appendRow(childObj)

                    # Place Tree Group Icons
                    childHDFItem = self.f.getItem(
                        '/'.join(elements[:ii + 1]))
                    if isinstance(childHDFItem, h5py.Group):
                        childObj.setIcon(iconFolder)

                    # Place Tree Dataset Icons
                    if isinstance(childHDFItem, h5py.Dataset):
                        if childHDFItem.dtype.isbuiltin == 0:
                            # compound dataset
                            childObj.setIcon(iconCDataset)
                        else:
                            # scalar dataset
                            childObj.setIcon(iconSDataset)
            else:
                # Add child instance to parent
                childObj = QtGui.QStandardItem(elements[ii])
                newParent.appendRow(childObj)

                # Place Tree Group Icons
                childHDFItem = self.f.getItem(
                    '/'.join(elements[:ii + 1]))
                if isinstance(childHDFItem, h5py.Group):
                    childObj.setIcon(iconFolder)

                # Place Tree Dataset Icons
                if isinstance(childHDFItem, h5py.Dataset):
                    if childHDFItem.dtype.isbuiltin == 0:
                        # compound dataset
                        childObj.setIcon(iconCDataset)
                    else:
                        # scalar dataset
                        childObj.setIcon(iconSDataset)

    def buildAttrTable(self):
        """
            Builds and displays the table of attributes for a given HDF
            Group/Dataset.
        """
        # Determine Table Dimensions
        noRows = 2
        noCols = self._selected_hdf_item.attrs.values().__len__()

        # Initialize Table Model and Asign
        modelAttrTable = QtGui.QStandardItemModel()
        self.tableItemAttr.setModel(modelAttrTable)
        modelAttrTable.setRowCount(noRows)
        modelAttrTable.setColumnCount(noCols)

        # Populate Table
        dictAttrs = dict(self._selected_hdf_item.attrs.items())
        for ii, key in enumerate(dictAttrs):
            index = modelAttrTable.index(0, ii)
            modelAttrTable.setData(index, key)

            index = modelAttrTable.index(1, ii)
            if isinstance(dictAttrs[key], bytes):
                modelAttrTable.setData(index,
                                       dictAttrs[key].decode('UTF-8'))
            else:
                modelAttrTable.setData(index, dictAttrs[key].__repr__())

        # Resize Cells of Table
        self.tableItemAttr.resizeColumnsToContents()
        self.tableItemAttr.resizeRowsToContents()

        # set gridline color to black
        self.tableItemAttr.setStyleSheet('gridline-color: balck;')

    def buildSimplePlotConfig(self):
        # Pass Dataset to formSimpleDataPlot()
        self.simpleDataPlot.setDataset(self._selected_hdf_item)

        # Disconnect Signals While Initializing
        self.wdgSimplePlotConfig.cboxXAxes.currentTextChanged.disconnect()
        self.wdgSimplePlotConfig.cboxYAxes.currentTextChanged.disconnect()

        # Turn On and Populate Simple Plot Config
        self.wdgSimplePlotConfig.setVisible(True)
        self.wdgSimplePlotConfig.cboxPlotRow.clear()
        self.wdgSimplePlotConfig.cboxXAxes.clear()
        self.wdgSimplePlotConfig.cboxYAxes.clear()

        if self._selected_hdf_item.dtype.isbuiltin == 0:
            # Compound Dataset
            self.wdgSimplePlotConfig.cboxPlotRow.setCurrentText('n/a')
            self.wdgSimplePlotConfig.cboxPlotRow.setDisabled(True)
        else:
            # Scalar Dataset
            self.wdgSimplePlotConfig.cboxPlotRow.setCurrentText('')
            self.wdgSimplePlotConfig.cboxPlotRow.setEnabled(True)

            # Populate Combo Box and set Current Index
            cboxRowList = self.simpleDataPlot.listOfRows()
            self.wdgSimplePlotConfig.cboxPlotRow.addItems(cboxRowList)
            self.wdgSimplePlotConfig.cboxPlotRow.setCurrentIndex(0)

        # Populate and Set X-Axis ComboBox
        cboxAxesList = self.simpleDataPlot.getValidAxes()
        self.wdgSimplePlotConfig.cboxXAxes.addItems(cboxAxesList)
        self.wdgSimplePlotConfig.cboxXAxes.setCurrentText(
            self.simpleDataPlot.getCurrentXAxis())
        self.wdgSimplePlotConfig.txtXAxisTitle.setText(
            self.simpleDataPlot.getXAxisTitle())

        # Populate and Set Y-Axis ComboBox
        self.wdgSimplePlotConfig.cboxYAxes.addItems(cboxAxesList)
        self.wdgSimplePlotConfig.cboxYAxes.setCurrentText(
            self.simpleDataPlot.getCurrentYAxis())
        self.wdgSimplePlotConfig.txtYAxisTitle.setText(
            self.simpleDataPlot.getYAxisTitle())

        # Re-connect Signals
        # X-Axis
        self.wdgSimplePlotConfig.cboxXAxes.currentTextChanged.connect(
            self.simpleDataPlot.setXAxis)
        self.wdgSimplePlotConfig.cboxXAxes.currentTextChanged.connect(
            self.simpleDataPlot.setXAxisTitle)
        self.simpleDataPlot.xAxisTitleChanged.connect(
            self.wdgSimplePlotConfig.txtXAxisTitle.setText)
        self.wdgSimplePlotConfig.txtXAxisTitle.textChanged.connect(
            self.simpleDataPlot.setXAxisTitle)
        self.wdgSimplePlotConfig.btnXAxisTitleReset.clicked.connect(
            self.simpleDataPlot.resetXAxisTitle)
        # Y-Axis
        self.wdgSimplePlotConfig.cboxYAxes.currentTextChanged.connect(
            self.simpleDataPlot.setYAxis)
        self.wdgSimplePlotConfig.cboxYAxes.currentTextChanged.connect(
            self.simpleDataPlot.setYAxisTitle)
        self.simpleDataPlot.yAxisTitleChanged.connect(
            self.wdgSimplePlotConfig.txtYAxisTitle.setText)
        self.wdgSimplePlotConfig.txtYAxisTitle.textChanged.connect(
            self.simpleDataPlot.setYAxisTitle)
        self.wdgSimplePlotConfig.btnYAxisTitleReset.clicked.connect(
            self.simpleDataPlot.resetYAxisTitle)

    def buildTreeContextMenu(self):
        # Initialize Context Menu
        _translate = QtCore.QCoreApplication.translate
        self.treeMenu = QtWidgets.QMenu()

        # Define Action Items
        self.actionCollapseAll = QtWidgets.QAction()
        self.actionCollapseAll.setObjectName('actionCollapseAll')
        self.actionCollapseAll.setText(
            _translate('Viewer', 'Collapse All'))
        self.actionExpandAll = QtWidgets.QAction()
        self.actionExpandAll.setObjectName('actionExpandAll')
        self.actionExpandAll.setText(_translate('Viewer', 'Expand All'))

        # Connect Signals
        self.actionCollapseAll.triggered.connect(
            self.treeView.collapseAll)
        #self.actionCollapseAll.triggered.connect(
        #   self.treeView.clearSelection)
        self.actionExpandAll.triggered.connect(self.treeView.expandAll)

        # Add Actions to Context Menu
        self.treeMenu.addAction(self.actionCollapseAll)
        self.treeMenu.addAction(self.actionExpandAll)

    def getFile(self):
        """
            Calls system's file dialog to select desired HDF5 file and
            define HDF5 file path.
        """
        fname = QtWidgets.QFileDialog.getOpenFileName(
            filter='HDF5 Files (*.hdf5)')
        if fname[0] != self._hdfFilename and fname[0] != '':
            if self._hdfFilename != '':
                self.cleanup()

            self._hdfFilename = fname[0]
            self.textFilenameContainer.setPlainText(self._hdfFilename)

    def getHDFItemPath(self):
        """
            Generates the path structure to the highlighted item in the
            QTreeView
        """
        treeList = []
        selectedIndex = self.treeView.selectedIndexes()[0]
        treeList.append(selectedIndex.model().data(selectedIndex))

        parentIndex = selectedIndex.model().parent(selectedIndex)
        while parentIndex.isValid():
            treeList.append(parentIndex.model().data(parentIndex))
            parentIndex = parentIndex.model().parent(parentIndex)

        treeList.reverse()
        self._selected_hdf_item_path = '/'.join(treeList)
        self.openHDFItem()

    def openHDF(self):
        """
            Opens selected HDF5 file.
        """
        if self._hdfFilename != '':
            self.f = lapdhdf.File(self._hdfFilename)
            self.updateRootParentAttrDisplay()
            self.updateTree()

    @QtCore.pyqtSlot(QtCore.QPoint)
    def treeContextMenu(self, pos):
        self.treeMenu.popup(self.treeView.mapToGlobal(pos))

    def toggleDataDisplay(self):
        if self.stackedlayoutDataDisplay.currentIndex() != 1:
            self.stackedlayoutDataDisplay.setCurrentIndex(1)

        self.simpleDataPlot.refreshPlotData()

    def toggleDataRowSelection(self):
        """
            Toggle the controls for selecting and displaying rows of a
            dataset.
        """
        if (isinstance(self._selected_hdf_item, h5py.Group) and
                self.btnDisplayDataTable.isVisible()):
            self.labelShowRows.setVisible(False)
            self.cboxStartRow.setVisible(False)
            self.labelTo.setVisible(False)
            self.cboxStopRow.setVisible(False)
            self.btnDisplayDataTable.setVisible(False)

        if (isinstance(self._selected_hdf_item, h5py.Dataset) and
                self.btnDisplayDataTable.isHidden()):
            self.labelShowRows.setVisible(True)
            self.cboxStartRow.setVisible(True)
            self.labelTo.setVisible(True)
            self.cboxStopRow.setVisible(True)
            self.btnDisplayDataTable.setVisible(True)

    def toggleSimplePlotConfig(self):
        """
            Toggle the Simple Plot Configuration panel such that
            controls are only visible when a dataset is selected.
        """
        if isinstance(self._selected_hdf_item, h5py.Group):
            self.wdgSimplePlotConfig.setVisible(False)
        else:
            self.buildSimplePlotConfig()

    def updateRootParentAttrDisplay(self):
        """
            Updates the GUI text display for the root parent attributes
            (i.e. HDF5 file name and LaPD HDF5 version).
        """
        strRootParentLabel = (self._strDefaultRootParentLabel + '  --  '
                              + self._hdfFilename.split('/')[-1]
                              + '  --  ' + self.f.getAttrKeys[0] + ' '
                              + self.f.getAttrValues[0].decode('UTF-8'
                                                               ))
        self.labelRootParent.setText(strRootParentLabel)

    def updateTree(self):
        """
            Update the GUI File Tree with the hierarchical items of the
            HDF5 file.
        """
        self.modelTree = QtGui.QStandardItemModel()
        self.treeView.setModel(self.modelTree)

        # tubHDF_FileSys[0] = item path string
        # tubHDF_FileSys[1] = item class (e.g. Group or Dataset)
        for item in self.f.tupHDF_fileSys:
            self.addTreeItem(item[0], item[1])

    def openHDFItem(self):
        """
            Require/Open the selected item from the file tree.
            f.getItem(path) will appropriately grab either a Group or
            Dataset object.
        """
        try:
            self._selected_hdf_item.name
        except AttributeError:
            newSelection = True
        else:
            newSelection = (self._selected_hdf_item.name
                            != '/' + self._selected_hdf_item_path)

        # Only open Group/Dataset if new selection is made
        if newSelection:
            self._selected_hdf_item = self.f.getItem(
                self._selected_hdf_item_path)
            self.updateItemAttrDisplay()
            self.toggleSimplePlotConfig()

    def updateItemAttrDisplay(self):
        """
            Updates the GUI text display for the selected HDF5 item in
            the file tree.
        """
        # Display Selected Item
        strSelectedItemLabel = (
            self._strDefaultSelectedItemLabel + '  --  '
            + self._selected_hdf_item_path.split('/')[-1])
        self.labelSelectedItem.setText(strSelectedItemLabel)

        # Toggle Data Row Selection for Dataset vs Group
        self.toggleDataRowSelection()

        # Initialize Data Row Start and Stop Combo Boxes
        if isinstance(self._selected_hdf_item, h5py.Dataset):
            noOfRows = self._selected_hdf_item.shape[0]
            cboxRowList = []
            for ii in range(noOfRows):
                cboxRowList.append(ii.__str__())

            # Set Start Row Combo Box
            self.cboxStartRow.clear()
            self.cboxStartRow.addItems(cboxRowList)
            self.cboxStartRow.setCurrentIndex(0)

            # Set Stop Row Combo Box
            self.cboxStopRow.clear()
            self.cboxStopRow.addItems(cboxRowList)
            self.cboxStopRow.setCurrentIndex(
                cboxRowList.index(cboxRowList[-1]))

        # Display General Attributes
        itemType = self.f.getItemType(self._selected_hdf_item_path)
        strAttrDisplay = (
            'Type:  {}\n'.format(itemType)
            + 'Path:  {}\n'.format(self._selected_hdf_item.parent.name))

        if isinstance(self._selected_hdf_item, h5py.Group):
            memItems = list(self._selected_hdf_item.values())
            noGroups = 0
            noDatasets = 0
            for name in memItems:
                if isinstance(name, h5py.Group):
                    noGroups += 1
                if isinstance(name, h5py.Dataset):
                    noDatasets += 1

            strAttrDisplay += (
                "{0}{1}{2}".format('Members: {} total\n'.format(
                    self._selected_hdf_item.__len__()),
                    '    {0:3} Groups\n'.format(noGroups),
                    '    {0:3} Datasets'.format(noDatasets)))

        if isinstance(self._selected_hdf_item, h5py.Dataset):
            strAttrDisplay += '\nDataspace:\n'
            strRecLength = '    '
            if self._selected_hdf_item.dtype.isbuiltin == 0:
                strAttrDisplay += '  Data Type:  Compound Dataset\n'
                strRecLength += 'No. of Fields:  {}'.format(
                    self._selected_hdf_item.value[0].__len__())
            if self._selected_hdf_item.dtype.isbuiltin == 1:
                strAttrDisplay += '  Data Type:  Scalar Dataset\n'
                strRecLength += 'Length of Recordings: {}'.format(
                    self._selected_hdf_item.shape[1])

            strAttrDisplay += (
                "{0}{1}{2}".format(
                    '  No. of Dims:  {}\n'.format(
                        self._selected_hdf_item.ndim),
                    '    No. of Recordings:  {}\n'.format(
                        self._selected_hdf_item.shape[0]),
                    strRecLength))

        # Adjust Size of General Attribute Display
        font = self.textItemGeneral.document().defaultFont()
        fontMetrics = QtGui.QFontMetrics(font)
        txtSize = fontMetrics.size(0, strAttrDisplay)
        currentSize = self.textItemGeneral.size()
        txtWidth = txtSize.width() + 20
        if txtSize.height() <= 0.9 * currentSize.height():
            txtHeight = txtSize.height() + 20
        else:
            txtHeight = currentSize.height()
        self.textItemGeneral.setMinimumSize(txtWidth, txtHeight)
        self.textItemGeneral.resize(txtWidth, txtHeight)

        # Update General Attribute Display
        self.textItemGeneral.setPlainText(strAttrDisplay)

        # Build and Display Attribute Table
        self.buildAttrTable()

    def cleanup(self):
        """
            Cleanup necessary objects if cleanup is request or window is
            closed.
        """
        if self._hdfFilename != '':
            self._hdfFilename = ''
            self.modelTree.clear()
            self.textFilenameContainer.clear()
            self.textItemGeneral.clear()
            self.wdgSimplePlotConfig.setVisible(False)
            self.stackedlayoutDataDisplay.setCurrentIndex(0)
            self.labelRootParent.setText(
                self._strDefaultRootParentLabel)
            self.labelSelectedItem.setText(
                self._strDefaultSelectedItemLabel)
            self.f.close()


class simplePlotConfig(QtWidgets.QWidget,
                       wdgSimplePlotConfig.Ui_formPlotConfig):
    def __init__(self):
        super(self.__class__, self).__init__()
        self.setupUi(self)

    @QtCore.pyqtSlot(bool)
    def btnPlotState(self, val):
        if val:
            self.btnPlot.setStyleSheet(
                '.QPushButton{font-weight: bold;}')
        else:
            self.btnPlot.setStyleSheet(
                '.QPushButton{font-weight: normal;}')


class formSimpleDataPlot(QtCore.QObject):
    needRefresh = QtCore.pyqtSignal(bool)
    xAxisTitleChanged = QtCore.pyqtSignal(str)
    yAxisTitleChanged = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        super(formSimpleDataPlot, self).__init__(parent)
        #        formSimplePlot.__init__(self)
        self.plot = QChart()
        self.plot.legend().hide()

        self.view = QChartView(self.plot)

        #        self.tooltipDataPoint = QtWidgets.QToolTip

        # Need to initialize
        # - activeRow
        # - activeXAxis
        # - activeYAxis
        self.validAxes = []
        self.dt = 1.0
        self.xscale = 1.0
        self.yscale = 1.0
        self.xAxisTitle = ''
        self.yAxisTitle = ''
        #        self.activeRow = 0

        # Signals
        self.needRefreshState = True

    def buildValidAxes(self):
        if self.isScalar():
            self.buildValidAxesScalar()
        else:
            self.buildValidAxesCompound()

    def buildValidAxesCompound(self):
        self.validAxes.clear()
        self.validAxes.append('row')

        for field in self.data.dtype.fields:
            if (np.issubdtype(self.data.dtype[field], int) or
                    np.issubdtype(self.data.dtype[field], float)):
                self.validAxes.append(field)

    def buildValidAxesScalar(self):
        self.validAxes.clear()
        self.validAxes.append('index')

        # Check for Timestep Conversion in Parent
        for key, val in self.data.parent.attrs.items():
            if key.casefold() == 'timestep'.casefold():
                self.validAxes.append('time')
                self.dt = val

        self.validAxes.append('DAQ Signal')

    def isCompound(self):
        """
            Retruns True is the Dataset is a compound dataset. False if
            scalar dataset.
        """
        if self.data.dtype.isbuiltin != 0:
            compoundD = False
        else:
            compoundD = True

        return compoundD

    def isScalar(self):
        """
            Retruns True is the Datasat is a scalar dataset. False if
            compound dataset.
        """
        if self.data.dtype.isbuiltin != 0:
            scalarD = True
        else:
            scalarD = False

        return scalarD

    def getCurrentXAxis(self):
        return self.xAxis

    def getCurrentYAxis(self):
        return self.yAxis

    def getValidAxes(self):
        return self.validAxes

    def getXAxisTitle(self):
        return self.xAxisTitle

    def getYAxisTitle(self):
        return self.yAxisTitle

    def listOfRows(self):
        """
            Builds a list of strings naming the number of each row in the
            dataset. This is used to populate the Simple Plot Config
            ComboBox.
        """
        listRows = []
        for ii in range(self.noOfRows()):
            listRows.append(ii.__str__())

        return listRows

    def noOfRows(self):
        return self.data.shape[0]

    def refreshCompound(self):
        # Clear Previous Plot
        self.plot.removeAllSeries()

        # Define X-Axis Data Points
        if self.getCurrentXAxis().casefold() == 'row'.casefold():
            xdata = np.arange(self.data.size)
        else:
            xdata = self.data[self.getCurrentXAxis()]

        # Define Y-Axis Data Points
        if self.getCurrentYAxis().casefold() == 'row'.casefold():
            ydata = np.arange(self.data.size)
        else:
            ydata = self.data[self.getCurrentYAxis()]

        # Build Plot Data for Qt
        pdata = []
        for ii in range(xdata.size):
            pdata.append(QtCore.QPointF(xdata[ii], ydata[ii]))

        # Build and Apply Data Series to Chart
        curve = QScatterSeries()
        curve.append(pdata)
        self.plot.addSeries(curve)
        self.plot.createDefaultAxes()

        # Rename Axes
        self.plot.axisX().setTitleText(self.xAxisTitle)
        self.plot.axisY().setTitleText(self.yAxisTitle)

        # Format X-Axis Tick Labels
        if self.getCurrentXAxis().casefold() == 'row'.casefold():
            self.plot.axisX().setLabelFormat('%i')
        elif np.issubdtype(self.data.dtype[self.getCurrentXAxis()],
                           int):
            self.plot.axisX().setLabelFormat('%i')
        else:
            if (np.log10(self.plot.axisX().max()) >= 3.0 or
                        np.log10(self.plot.axisX().max()) <= -3):
                self.plot.axisX().setLabelFormat('%.2e')
        mmax = self.plot.axisX().max()
        mmin = self.plot.axisX().min()
        pad = 0.05 * (mmax - mmin)
        self.plot.axisX().setMax(mmax + pad)
        self.plot.axisX().setMin(mmin - pad)
        self.plot.axisX().applyNiceNumbers()

        # Format X-Axis Tick Labels
        if self.getCurrentYAxis().casefold() == 'row'.casefold():
            self.plot.axisY().setLabelFormat('%i')
        elif np.issubdtype(self.data.dtype[self.getCurrentYAxis()],
                           int):
            self.plot.axisY().setLabelFormat('%i')
        else:
            if (np.log10(self.plot.axisY().max()) >= 3.0 or
                        np.log10(self.plot.axisY().max()) <= -3):
                self.plot.axisY().setLabelFormat('%.2e')
        mmax = self.plot.axisY().max()
        mmin = self.plot.axisY().min()
        pad = 0.05 * (mmax - mmin)
        self.plot.axisY().setMax(mmax + pad)
        self.plot.axisY().setMin(mmin - pad)
        self.plot.axisY().applyNiceNumbers()

        # Connect Signals
        curve.hovered.connect(self.tooltipDataPointDisplay)

    def refreshPlotData(self):
        """
            Refresh the plot if the necessary attributes are defined. The
            following have to exist:
                self.activeRow
                self.xAxis
                self.yAxis
        """
        try:
            self.activeRow
            self.xAxis
            self.yAxis
        except AttributeError:
            pass
        else:
            if self.isScalar():  # Scalar Dataset
                self.refreshScalar()
            else:
                self.refreshCompound()

            self.needRefreshState = False

        self.needRefresh.emit(self.needRefreshState)

    def refreshScalar(self):
        # Clear previous plot
        self.plot.removeAllSeries()

        # Define X-Axis Data Points
        if self.getCurrentXAxis().casefold() == 'index'.casefold():
            xdata = np.arange(self.data[self.activeRow].size)
        elif self.getCurrentXAxis().casefold() == 'time'.casefold():
            xdata = np.arange(self.data[self.activeRow].size) * self.dt
        else:
            xdata = self.data[self.activeRow]

        # Define Y-Axis Data Points
        if self.getCurrentYAxis().casefold() == 'index'.casefold():
            ydata = np.arange(self.data[self.activeRow].size)
        elif self.getCurrentYAxis().casefold() == 'time'.casefold():
            ydata = np.arange(self.data[self.activeRow].size) * self.dt
        else:
            ydata = self.data[self.activeRow]

        # Build Plot Data for Qt
        pdata = []
        for ii in range(xdata.size):
            pdata.append(QtCore.QPointF(xdata[ii], ydata[ii]))

        # Build and Apply Data Series to Chart
        curve = QLineSeries()
        curve.append(pdata)
        self.plot.addSeries(curve)
        self.plot.createDefaultAxes()

        # Rename Axes
        self.plot.axisX().setTitleText(self.xAxisTitle)
        self.plot.axisY().setTitleText(self.yAxisTitle)

        # Format Axis Tick Labels
        if self.getCurrentXAxis().casefold() == 'index'.casefold():
            self.plot.axisX().setLabelFormat('%i')
        if self.getCurrentYAxis().casefold() == 'index'.casefold():
            self.plot.axisY().setLabelFormat('%i')

        # Connect Signals
        curve.hovered.connect(self.tooltipDataPointDisplay)

    @QtCore.pyqtSlot()
    def resetXAxisTitle(self):
        self.setXAxisTitle(self.xAxis)

    @QtCore.pyqtSlot()
    def resetYAxisTitle(self):
        self.setYAxisTitle(self.yAxis)

    def selectRow(self, row):
        if self.isScalar():
            self.activeRow = row
        else:
            self.activeRow = 'None'

        # emit signal
        self.needRefreshState = True
        self.needRefresh.emit(self.needRefreshState)

    def setDataset(self, data):
        self.data = data

        self.setTitle(self.data.name)

        self.selectRow(0)

        # Build and Set Axes
        #  Note: setting a new axis also sets the associated axis title.
        self.buildValidAxes()
        if self.isScalar():
            self.setXAxis(self.validAxes[0])
            self.setYAxis(self.validAxes[-1])
        else:
            self.setXAxis(self.validAxes[0])
            if self.validAxes.__len__() == 1:
                self.setYAxis(self.validAxes[0])
            else:
                self.setYAxis(self.validAxes[1])

        # emit signal
        self.needRefreshState = True
        self.needRefresh.emit(self.needRefreshState)

    def setTitle(self, title):
        self.plot.setTitle(title)

        # emit signal
        self.needRefreshState = True
        self.needRefresh.emit(self.needRefreshState)

    def setXAxis(self, axis):
        self.xAxis = axis
        self.setXAxisTitle(axis)

        # emit signal
        self.needRefreshState = True
        self.needRefresh.emit(self.needRefreshState)

    def setXAxisTitle(self, title):
        self.xAxisTitle = title
        self.xAxisTitleChanged.emit(title)

        # emit signal
        self.needRefreshState = True
        self.needRefresh.emit(self.needRefreshState)

    def setYAxis(self, axis):
        self.yAxis = axis
        self.setYAxisTitle(axis)

        # emit signal
        self.needRefreshState = True
        self.needRefresh.emit(self.needRefreshState)

    def setYAxisTitle(self, title):
        self.yAxisTitle = title
        self.yAxisTitleChanged.emit(title)

        # emit signal
        self.needRefreshState = True
        self.needRefresh.emit(self.needRefreshState)

    @QtCore.pyqtSlot(QtCore.QPointF, bool)
    def tooltipDataPointDisplay(self, point, state):
        """
            Will display a tooltip containg the (x, y) values of the data
            point that the mouse is hovering over.
        """
        if state:
            strTip = '('
            # format X-coord
            if (
                            self.getCurrentXAxis().casefold() == 'index'.casefold() or
                            self.getCurrentXAxis().casefold() == 'row'.casefold()):
                strTip += '{}'.format(int(point.x()))
            elif (
                            self.getCurrentXAxis().casefold() == 'time'.casefold() or
                            self.getCurrentXAxis().casefold() == 'DAQ Signal'.casefold()):
                if (np.log10(self.plot.axisX().max()) >= 3.0 or
                            np.log10(self.plot.axisX().max()) <= -3):
                    strTip += '{:.2e}'.format(point.x())
                else:
                    strTip += '{:.2f}'.format(point.x())
            elif np.issubdtype(self.data.dtype[self.getCurrentXAxis()],
                               int):
                strTip += '{}'.format(int(point.x()))
            else:
                if (np.log10(self.plot.axisX().max()) >= 3.0 or
                            np.log10(self.plot.axisX().max()) <= -3):
                    strTip += '{:.2e}'.format(point.x())
                else:
                    strTip += '{:.2f}'.format(point.x())
            strTip += ', '

            # format Y-coord
            if (
                            self.getCurrentYAxis().casefold() == 'index'.casefold() or
                            self.getCurrentYAxis().casefold() == 'row'.casefold()):
                strTip += '{}'.format(int(point.y()))
            elif (
                            self.getCurrentYAxis().casefold() == 'time'.casefold() or
                            self.getCurrentYAxis().casefold() == 'DAQ Signal'.casefold()):
                if (np.log10(self.plot.axisY().max()) >= 3.0 or
                            np.log10(self.plot.axisY().max()) <= -3):
                    strTip += '{:.2e}'.format(point.y())
                else:
                    strTip += '{:.2f}'.format(point.y())
            elif np.issubdtype(self.data.dtype[self.getCurrentYAxis()],
                               int):
                strTip += '{}'.format(int(point.y()))
            else:
                if (np.log10(self.plot.axisY().max()) >= 3.0 or
                            np.log10(self.plot.axisY().max()) <= -3):
                    strTip += '{:.2e}'.format(point.y())
                else:
                    strTip += '{:0.2f}'.format(point.y())
            strTip += ')'

            self.view.setToolTip(strTip)
        else:
            self.view.setToolTip('')


def run():
    app = QtWidgets.QApplication(sys.argv)
    form = Viewer()
    form.show()
    app.aboutToQuit.connect(form.cleanup)
    sys.exit(app.exec_())


if __name__ == '__main__':
    run()
