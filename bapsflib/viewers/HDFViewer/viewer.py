# -*- coding: utf-8 -*-

import sys

from PyQt5 import QtGui, QtWidgets, QtCore, QtChart
try:
    from .UIs import mainwindow, wdgSimplePlotConfig
except ModuleNotFoundError:
    # relative imports don't work from command line execution
    from UIs import mainwindow, wdgSimplePlotConfig


class Viewer(QtWidgets.QMainWindow, mainwindow.Ui_MainWindow):
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
