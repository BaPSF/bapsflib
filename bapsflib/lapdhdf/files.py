# This file is part of the bapsflib package, a Python toolkit for the
# BaPSF group at UCLA.
#
# http://plasma.physics.ucla.edu/
#
# Copyright 2017 Erik T. Everson and contributors
#
# License: Standard 3-clause BSD; see "LICENSES/LICENSE.txt" for full
#   license terms and contributor agreement.
#
import h5py

from .hdfchecks import hdfCheck
from .hdfreaddata import hdfReadData
from .hdfreadcontrol import hdfReadControl


class File(h5py.File):
    """
    Open a HDF5 File.

    see :py:mod:`h5py` documentation for :py:class:`h5py.File` details:
    http://docs.h5py.org/en/latest/

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
        # TODO: add keyword save_report
        # - this will save the hdfChecks report to a text file alongside
        #   the HDF5 file
        # TODO: add keyword silent_report
        # - this will prevent the report from printing to screen, but
        #   does not affect save_report
        #
        h5py.File.__init__(self, name, mode, driver, libver,
                           userblock_size, swmr)

        print('Begin HDF5 Quick Report:')
        self.__file_checks = hdfCheck(self)

    # @property
    # def file_checks(self):
    #    """
    #    :return: an instance of :py:class:`lapdhdf.hdfchecks.hdfCheck`
    #    """
    #    return self.__file_checks

    @property
    def file_map(self):
        """
        :return: an instance of the
            :py:class:`bapsflib.lapdhdf.hdfmappers.hdfMap` file
            mappings.
        """
        return self.__file_checks.get_hdf_mapping()

    @property
    def listHDF_files(self):
        """
        :return: a list of strings representing the absolute paths
            (including Group/Dataset name) for each Group and Dataset in
            the HDF5 file.
        """
        some_list = []
        self.visit(some_list.append)
        return some_list

    @property
    def list_msi(self):
        """
        :return: a list of strings naming the MSI diagnostics found in
            the HDF5 file
        :rtype: list(str)
        """
        return list(self.file_map.msi)

    @property
    def list_digitizers(self):
        """
        :return: a list of strings naming the digitizers found in the
            HDF5 file
        :rtype: list(str)
        """
        return list(self.file_map.digitizers)

    @property
    def list_controls(self):
        """
        :return: a list of strings naming the controls found in the
            HDF5 file
        :rtype: list(str)
        """
        return list(self.file_map.controls)

    @property
    def listHDF_file_types(self):
        """
        :return: a list of strings indicating if an HDF5 item is a Group
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
        :return: `zip(listHDF_files, listHDF_file_types)`
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

    def read_data(self, board, channel, index=None, shotnum=None,
                  digitizer=None, adc=None, config_name=None,
                  keep_bits=False, add_controls=None,
                  intersection_set=True, silent=False, **kwargs):
        """
        :param int board: desired board number
        :param int channel: desired channel number
        :param index:
        :type index: list(int)
        :param str digitizer: name of desired digitizer
        :param str adc: name of desired analog-digital converter
        :param str config_name: name of data configurations
        :param bool keep_bits: :code:`True` for output in bits,
            :code:`False` (default) for output in voltage
        :param bool silent: Defualt :code:`False`. Set :code:`True` to
            suppress any warning print outs when data is constructed.
            Exceptions are still raise when necessary.
        :return: instance of
            :class:`~bapsflib.lapdhdf.hdfreaddata.hdfReadData`
        """
        # TODO: write docstrings
        # consider adding keyword output_voltage
        return hdfReadData(self, board, channel,
                           index=index,
                           shotnum=shotnum,
                           digitizer=digitizer,
                           adc=adc,
                           config_name=config_name,
                           keep_bits=keep_bits,
                           add_controls=add_controls,
                           intersection_set=intersection_set,
                           silent=silent,
                           **kwargs)

    def read_controls(self, controls,
                      index=None, shotnum=None, intersection_set=True,
                      silent=False, **kwargs):
        return hdfReadControl(self, controls,
                              index=index,
                              shotnum=shotnum,
                              intersection_set=intersection_set,
                              silent=silent,
                              **kwargs)
