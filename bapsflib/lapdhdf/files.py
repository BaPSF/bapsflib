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

from .hdfchecks import hdfCheck
from .hdfreaddata import hdfReadData


class File(h5py.File):
    def __init__(self, name, mode='r', driver=None, libver=None,
                 userblock_size=None, swmr=False, **kwds):
        h5py.File.__init__(self, name, mode, driver, libver,
                           userblock_size, swmr)

        print('Begin HDF5 Quick Report:')
        self.file_checks = hdfCheck(self)

    @property
    def file_map(self):
        return self.file_checks.get_hdf_mapping()

    @property
    def listHDF_files(self):
        """
        Returns a list of strings representing the absolute paths
        (including Group/Dataset name) for each Group and Dataset in
        the HDF5 file.
        """
        some_list = []
        self.visit(some_list.append)
        return some_list

    @property
    def listHDF_file_types(self):
        """
        Returns a list of strings indicating if an HDF5 item is a Group
        or Dataset. This has a one-to-one correspondence to
        listHDF_files.
        """
        some_list = []
        for name in self.listHDF_files:
            class_type = self.get(name, getclass=True)
            some_list.append(class_type.__name__)

        return some_list

    @property
    def tupHDF_fileSys(self):
        """
        zip(listHDF_files, listHDF_file_types)
        """
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

    def read_data(self, board, channel, shots=None, daq=None,
                  config_name=None, output_voltage=True):
        return hdfReadData(self, board, channel, shots=shots, daq=daq,
                           config_name=config_name)
