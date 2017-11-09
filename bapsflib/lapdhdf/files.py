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

    see :mod:`h5py` documentation for :class:`h5py.File` details:
    http://docs.h5py.org/en/latest/

    :param str name: Name of file (`str` or `unicode`)
    :param str mode: Mode in which to open the file. (default 'r' read-only)
    :param driver: File driver to use
    :param libver: Compatibility bounds
    :param userblock_size: Size (in bytes) of the user block. If
        nonzero, must be a power of 2 and at least 512.
    :param swmr: Single Write, Multiple Read
    :param kwargs: Driver specific keywords
    """
    def __init__(self, name, mode='r', driver=None, libver=None,
                 userblock_size=None, swmr=False, **kwargs):
        # TODO: re-work the argument pass through to h5py.File
        # TODO: add keyword save_report
        # - this will save the hdfChecks report to a text file alongside
        #   the HDF5 file
        # TODO: add keyword silent_report
        # - this will prevent the report from printing to screen, but
        #   does not affect save_report
        #
        h5py.File.__init__(self, name, mode, driver, libver,
                           userblock_size, swmr, **kwargs)

        print('Begin HDF5 Quick Report:')
        self.__file_checks = hdfCheck(self)

    @property
    def file_map(self):
        """
        :return: HDF5 file mappings
        :rtype: :class:`bapsflib.lapdhdf.hdfmappers.hdfMap`
        """
        return self.__file_checks.get_hdf_mapping()

    @property
    def listHDF_files(self):
        """
        :return: list of strings representing the absolute paths
            (base + filename) for each Group and Dataset in the HDF5
            file.
        :rtype: list(str)
        """
        some_list = []
        self.visit(some_list.append)
        return some_list

    @property
    def list_msi(self):
        """
        :return: list of strings naming the MSI diagnostics found in
            the HDF5 file
        :rtype: list(str)
        """
        return list(self.file_map.msi)

    @property
    def list_digitizers(self):
        """
        :return: list of strings naming the digitizers found in the
            HDF5 file
        :rtype: list(str)
        """
        return list(self.file_map.digitizers)

    @property
    def list_controls(self):
        """
        :return: list of strings naming the controls found in the
            HDF5 file
        :rtype: list(str)
        """
        return list(self.file_map.controls)

    @property
    def listHDF_file_types(self):
        """
        :return: list of strings indicating if an HDF5 item is a Group
            or Dataset. This has a one-to-one correspondence to
            listHDF_files.
        :rtype: list(str)
        """
        some_list = []
        for name in self.listHDF_files:
            class_type = self.get(name, getclass=True)
            some_list.append(class_type.__name__)

        return some_list

    @property
    def tupHDF_fileSys(self):
        """
        :return: :code:`zip(listHDF_files, listHDF_file_types)`
        :rtype: iterator of 2-element tuples
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
        Provides access to
        :class:`~bapsflib.lapdhdf.hdfreaddata.hdfReadData` to extract
        data from a specified digitizer dataset in the HDF5 file and,
        if requested, mate control device data to the extracted
        digitizer data. See
        :class:`~bapsflib.lapdhdf.hdfreaddata.hdfReadData` for more
        detail.

        :param int board: digitizer board number
        :param int channel: digitizer channel number
        :param index: dataset row index
        :type index: int, list(int), slice()
        :param shotnum: HDF5 global shot number
        :type shotnum: int, list(int), slice()
        :param str digitizer: name of digitizer
        :param str adc: name of the digitizer's analog-digital converter
        :param str config_name: name of digitizer configuration
        :param bool keep_bits: :code:`True` for output in bits,
            :code:`False` (default) for output in voltage
        :param add_controls: a list of strings and/or 2-element tuples
            indicating control device data to be mated to the digitizer
            data. (see
            :class:`~bapsflib.lapdhdf.hdfreaddata.hdfReadData`
            for details)
        :type add_controls: [str, (str, val), ]
        :param bool intersection_set: :code:`True` (default) forces the
            returned array to only contain shot numbers that are in the
            intersection of :data:`shotnum`, the digitizer dataset, and
            all the control device datasets. (see
            :class:`~bapsflib.lapdhdf.hdfreaddata.hdfReadData`
            for details)
        :param bool silent: :code:`False` (default). Set :code:`True` to
            suppress command line printout of soft-warnings
        :return: extracted data from digitizer (and control devices)
        :rtype: :class:`~bapsflib.lapdhdf.hdfreaddata.hdfReadData`
        """
        #
        # :param add_controls: a list of strings and/or 2-element tuples
        #     indicating control device data to be mated to the
        #     digitizer data. If an element is a string, then that
        #     string is the name of the control device, If an element is
        #     a 2-element tuple, then the 1st element is the name of the
        #     control device and the 2nd element is a unique specifier
        #     for that control device.
        # :param intersection_set: :code:`True` (default) ensures the
        #     returned array only contains shot numbers that are found
        #     in the digitizer dataset and all added control device
        #     datasets. :code:`False` will cause the returned array to
        #     contain shot numbers specified by :data:`shotnum` or, when
        #     :data:`index` is used, the matching shot numbers in the
        #     digitizer dataset specified by :data:`index`
        #
        # TODO: write docstrings
        #
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
        """
        Provides access to
        :class:`~bapsflib.lapdhdf.hdfreadcontrol.hdfReadControl` to
        extract data from specified control device dataset(s) in the
        HDF5 file. See
        :class:`~bapsflib.lapdhdf.hdfreadcontrol.hdfReadControl` for
        more detail.

        :param controls: a list of strings and/or 2-element tuples
            indicating control device data to be extracted. (see
            :class:`~bapsflib.lapdhdf.hdfreadcontrol.hdfReadControl`
            for details)
        :type controls: [str, (str, val), ]
        :param index: row index of the 1st specified control device
            dataset or row index of the array of intersecting shot
            numbers (see
            :class:`~bapsflib.lapdhdf.hdfreadcontrol.hdfReadControl`
            for details)
        :type index: int, list(int), slice()
        :param shotnum: HDF5 global shot number
        :type shotnum: int, list(int), slice()
        :param bool intersection_set: :code:`True` (default) forces the
            returned array to only contain shot numbers that are in the
            intersection of :data:`shotnum` and all the control device
            datasets. (see
            :class:`~bapsflib.lapdhdf.hdfreadcontrol.hdfReadControl`
            for details)
        :param bool silent: :code:`False` (default). Set :code:`True` to
            suppress command line printout of soft-warnings
        :return: extracted data from control device(s)
        :rtype: :class:`~bapsflib.lapdhdf.hdfreadcontrol.hdfReadControl`
        """
        return hdfReadControl(self, controls,
                              index=index,
                              shotnum=shotnum,
                              intersection_set=intersection_set,
                              silent=silent,
                              **kwargs)
