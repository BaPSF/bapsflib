# This file is part of the bapsflib package, a Python toolkit for the
# BaPSF group at UCLA.
#
# http://plasma.physics.ucla.edu/
#
# Copyright 2017 Erik T. Everson and contributors
#
# License:
#

import h5py

from .hdfcheck import hdfCheck


class File(h5py.File):
    def __init__(self, name, mode='r', driver=None, libver=None,
                 userblock_size=None, swmr=False, **kwds):
        h5py.File.__init__(self, name, mode, driver, libver,
                           userblock_size, swmr)

        print('Begin HDF5 Quick Report:')
        hdfCheck(self)

    @property
    def listHDF_files(self):
        someList = []
        self.visit(someList.append)
        return someList

    @property
    def listHDF_file_types(self):
        someList = []
        for name in self.listHDF_files:
            class_type = self.get(name, getclass=True)
            someList.append(class_type.__name__)

        return someList

    @property
    def tupHDF_fileSys(self):
        return zip(self.listHDF_files, self.listHDF_file_types)

    @property
    def getAttrItems(self):
        return dict(self.attrs.items())

    @property
    def getAttrKeys(self):
        return list(self.attrs.keys())

    @property
    def getAttrValues(self):
        return list(self.attrs.values())

    def getItemType(self, name):
        return self.get(name, getclass=True).__name__
    
    def getItem(self, name):
        return self.get(name)
