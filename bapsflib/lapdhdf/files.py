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
    """
    Open a HDF5 File. (see :py:mod:`h5py` documentation for
    :py:class:`h5py.File` details)

    :param name: Name of file (`str` or `unicode`)
    :param mode: Mode in which to open the file. (default 'r' read-only)
    :param driver: File driver to use
    :param libver: Compatibility bounds
    :param userblock_size: Size (in bytes) of the user block. If
        nonzero, must be a power of 2 and at least 512.
    :param swmr: Single Write, Multiple Read
    :param kwds: Driver specific keywords
    """
    def __init__(self, name, mode='r', driver=None, libver=None,
                 userblock_size=None, swmr=False, **kwds):
        """what should i put here"""
        h5py.File.__init__(self, name, mode, driver, libver,
                           userblock_size, swmr)

        print('Begin HDF5 Quick Report:')
        self.file_checks = hdfCheck(self)

    @property
    def file_map(self):
        """
        Returns an instance of the :py:class:`lapdhdf.hdfmappers.hdfMap`
        file mappings.
        """
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
        `zip(listHDF_files, listHDF_file_types)`
        """
        return zip(self.listHDF_files, self.listHDF_file_types)

    @property
    def getAttrItems(self):
        """
        .. Warning:: Do not use. Will be deprecated.

        :return: dict of `File.attrs.items()`
        """
        return dict(self.attrs.items())

    @property
    def getAttrKeys(self):
        """
        .. Warning:: Do not use. Will be deprecated.

        :return: list of `File.attrs.keys()`
        """
        return list(self.attrs.keys())

    @property
    def getAttrValues(self):
        """
        .. Warning:: Do not use. Will be deprecated.

        :return: list of `File.attrs.values()`
        """
        return list(self.attrs.values())

    def getItemType(self, name):
        """
        .. Warning:: Do not use. Will be deprecated.

        :param name: name of Group/Dataset
        :return: `str` indicating if `name` is a 'Group' of 'Dataset'
        """
        return self.get(name, getclass=True).__name__
    
    def getItem(self, name):
        """
        .. Warning:: Do not use. Will be deprecated.

        :param name: name of Group/Dataset
        :return: `File.get(name)`
        """
        return self.get(name)

    def read_data(self, board, channel, shots=None, adc=None,
                  config_name=None, output_voltage=True):
        return hdfReadData(self, board, channel, shots=shots, adc=adc,
                           config_name=config_name)
