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
except ModuleNotFoundError:
    # relative imports don't work from command line execution
    from UIs import mainwindow, wdgSimplePlotConfig


def rebuildUiFiles():
    '''
        This is for use during development process so that the .ui files
        don't have to be recompiled separately before runing main.py
    '''
    pyuic.compileUiDir('UIs/', execute=True)
    uiModules = ['mainwindow', 'wdgSimplePlotConfig']
    for modName in sys.modules.keys():
        for uiName in uiModules:
            if modName.__contains__(uiName):
                importlib.reload(sys.modules[modName])

rebuildUiFiles()

class Viewer(QtWidgets.QMainWindow, mainwindow.Ui_MainWindow):
    _hdfFile = ''
    _strDefaultRootParentLabel = 'Root Parent'
    _strDefaultSelectedItemLabel = 'Item Selected'

    def __init__(self):
        super(self.__class__, self).__init__()
        self.setupUi(self)


def run():
    app = QtWidgets.QApplication(sys.argv)
    form = Viewer()
    form.show()
    #    app.aboutToQuit(form.cle)
    sys.exit(app.exec_())


if __name__ == '__main__':
    run()
