# This file is part of the bapsflib package, a Python toolkit for the
# BaPSF group at UCLA.
#
# http://plasma.physics.ucla.edu/
#
# Copyright 2017-2018 Erik T. Everson and contributors
#
# License: Standard 3-clause BSD; see "LICENSES/LICENSE.txt" for full
#   license terms and contributor agreement.
#
import h5py
import numpy as np
import os

from typing import (List, Union)
from warnings import warn

from .controls import HDFMapControls
from .controls.templates import (HDFMapControlTemplate,
                                 HDFMapControlCLTemplate)
from .digitizers import HDFMapDigitizers
from .digitizers.templates import HDFMapDigiTemplate
from .msi import HDFMapMSI
from .msi.templates import HDFMapMSITemplate


# define type aliases
ControlMap = Union[HDFMapControlTemplate, HDFMapControlCLTemplate]
DigiMap = HDFMapDigiTemplate
MSIMap = HDFMapMSITemplate


class HDFMap(object):
    """
    Constructs a complete file mapping of :obj:`hdf_obj` that is
    utilized by :class:`bapsflib.lapd.File` to manipulate and
    read data out of the HDF5 file.

    The following classes are leveraged to construct the mappings:

    * :class:`~.controls.map_controls.HDFMapControls`.
    * :class:`~.digitizers.map_digis.HDFMapDigitizers`.
    * :class:`~.msi.map_msi.HDFMapMSI`.
    """

    def __init__(self,
                 hdf_obj: h5py.File,
                 control_path: str,
                 digitizer_path: str,
                 msi_path: str):
        """
        :param hdf_obj: the HDF5 file object
        :type hdf_obj: :class:`h5py.File`
        """
        # store an instance of the HDF5 object for HDFMap
        if isinstance(hdf_obj, h5py.File):
            self._hdf_obj = hdf_obj
        else:
            raise TypeError("arg `hdf_file` not an h5py.File object")

        # define paths
        self._CONTROL_PATH = '/' if control_path == '' else control_path
        self._DIGITIZER_PATH = '/' if digitizer_path == '' \
            else digitizer_path
        self._MSI_PATH = '/' if msi_path == '' else msi_path

        '''
        # initialize attributes dict
        self._attrs = {'root': dict(hdf_obj.attrs)}

        # populate attributes
        for attr in (self._MSI_PATH, self._DIGITIZER_PATH,
                     self._CONTROL_PATH):
            if attr == '/':
                # root attributes already added
                pass
            elif attr in self._attrs:
                # attributes for this path already added
                pass
            elif attr in hdf_obj:
                # get attributes to add
                attr_update = dict(hdf_obj[attr].attrs)
                for key, val in attr_update.items():
                    if isinstance(val, np.bytes_):
                        attr_update[key] = val.decode('utf-8')

                # update attributes
                self._attrs[attr] = attr_update
        '''

        # attach the mapping dictionaries
        self.__attach_msi()
        self.__attach_digitizers()
        self.__attach_controls()
        self.__attach_unknowns()

    def __repr__(self):
        filename = self._hdf_obj.filename
        if isinstance(filename, (bytes, np.bytes_)):
            filename = filename.decode('utf-8')
        filename = os.path.basename(filename)
        rstr = ("<" + self.__class__.__name__
                + " of HDF5 file '" + filename + "'>")
        return rstr

    def __attach_controls(self):
        """
        Attaches a dictionary (:attr:`__controls`) containing all
        control device mapping objects constructed by
        :class:`~.controls.map_controls.HDFMapControls`.
        """
        if self._CONTROL_PATH in self._hdf_obj:
            self.__controls = HDFMapControls(
                self._hdf_obj[self._CONTROL_PATH])
        else:
            warn("Group for control devices "
                 + "('{}')".format(self._CONTROL_PATH)
                 + " does NOT exist.")
            self.__controls = {}

    def __attach_digitizers(self):
        """
        Attaches a dictionary (:attr:`__digitizers`) containing all
        digitizer mapping objects constructed by
        :class:`~.digitizers.map_digis.HDFMapDigitizers`.
        """
        if self._DIGITIZER_PATH in self._hdf_obj:
            self.__digitizers = HDFMapDigitizers(
                self._hdf_obj[self._DIGITIZER_PATH])
        else:
            warn("Group for digitizers "
                 + "('{}')".format(self._DIGITIZER_PATH)
                 + " does NOT exist.")
            self.__digitizers = {}

    def __attach_msi(self):
        """
        Attaches a dictionary (:attr:`__msi`) containing all MSI
        diagnostic mapping objects constructed by
        :class:`~.msi.map_msi.HDFMapMSI`.
        """
        if self._MSI_PATH in self._hdf_obj:
            self.__msi = HDFMapMSI(self._hdf_obj[self._MSI_PATH])
        else:
            warn("MSI ('{}') does NOT exist.".format(self._MSI_PATH))
            self.__msi = {}

    def __attach_unknowns(self):
        """
        Attaches a list (:attr:`__unknowns`) with the subgroup names of
        all the subgroups in the data group (:attr:`data_gname`) that
        are unknown to the mapping constructors.
        """
        # add unknowns (Groups & Datasets) from levels
        # 1. root -- '/'
        # 2. MSI group -- '/MSI'
        # 3. data group -- '/Raw data + config'
        self.__unknowns = []
        device_paths = [self._CONTROL_PATH, self._DIGITIZER_PATH,
                        self._MSI_PATH]
        mapped_devices = [list(self.controls), list(self.digitizers),
                          list(self.msi)]

        # scan through root, Control, Digitizer, and MSI groups
        devices_known = {'/': device_paths.copy()}
        for path, mapped in zip(device_paths, mapped_devices):
            if path in devices_known:
                devices_known[path].extend(mapped)
            else:
                devices_known[path] = mapped.copy()
        for path, devices in devices_known.items():
            if path in self._hdf_obj:
                for item in self._hdf_obj[path]:
                    if item not in devices:
                        self.__unknowns.append(
                            self._hdf_obj[path][item].name)

        '''
        # scan through root
        check_list = device_paths.copy()
        if self._CONTROL_PATH == '/':
            check_list.extend(list(self.controls))
        if self._DIGITIZER_PATH == '/':
            check_list.extend(list(self.digitizers))
        if self._MSI_PATH == '/':
            check_list.extend(list(self.msi))
        for item in self._hdf_obj:
            if item not in check_list:
                self.__unknowns.append(self._hdf_obj[item].name)
        
        # scan through MSI group
        if self._MSI_PATH == '/':
            # done above
            pass
        elif self._MSI_PATH in self._hdf_obj:
            for item in self._hdf_obj[self._MSI_PATH]:
                if item not in self.msi:
                    self.__unknowns.append(
                        self._hdf_obj[self._MSI_PATH][item].name)

        # scan through control and digitizer group
        devices_known = []
        if self._CONTROL_PATH == self._DIGITIZER_PATH:
            if self._CONTROL_PATH != '/':
                devices_known.append(
                    (self._CONTROL_PATH,
                     list(self.controls) + list(self.digitizers))
                )
        else:
            if self._CONTROL_PATH != '/':
                devices_known.append(
                    (self._CONTROL_PATH, list(self.controls))
                )
            if self._DIGITIZER_PATH != '/':
                devices_known.append(
                    (self._DIGITIZER_PATH, list(self.digitizers))
                )
        for path, devices in devices_known:
            if path in self._hdf_obj:
                for item in self._hdf_obj[path]:
                    if item not in devices:
                        self.__unknowns.append(
                            self._hdf_obj[path][item].name)
        '''

    '''
    @property
    def attrs(self):
        """Dictionary of the 'MSI' and 'Raw data + config' attributes"""
        return self._attrs
    '''

    @property
    def controls(self) -> Union[dict, HDFMapControls]:
        """
        :return: A dictionary containing all control device mapping
            objects.
        :rtype: dict

        For example, to retrieve mappings of the control device
        :code:`'6K Compumotor'` one would call::

            fmap = HDFMap(file_obj)
            mmap = fmap.controls['6K Compumotor']
        """
        return self.__controls

    @property
    def digitizers(self) -> Union[dict, HDFMapDigitizers]:
        """
        :return: A dictionary containing all digitizer mapping objects.
        :rtype: dict

        For example, to retrieve mappings of digitizer
        :code:`'SIS 3301'` one would call::

            fmap = HDFMap(file_obj)
            dmap = fmap.digitizers['SIS 3301']
        """
        return self.__digitizers

    @property
    def main_digitizer(self) -> Union[None, DigiMap]:
        """
        :return: the mapping object for the digitizer that is assumed
            to be the 'main digitizer' in :attr:`digitizers`

        The main digitizer is determine by scanning through the local
        tuple :const:`possible_candidates` that contains a
        hierarchical list of digitizers. The first digitizer found is
        assumed to be the 'main digitizer'.::

            possible_candidates = ('SIS 3301', 'SIS crate')
        """
        # possible_candidates is a hierarchical tuple of all digitizers
        # such that the first found digitizer is assumed to be the main
        # digitizer
        possible_candidates = ('SIS 3301', 'SIS crate')
        digi = None
        try:
            for key in possible_candidates:
                if key in self.__digitizers:
                    digi = self.__digitizers[key]
                    break
        except TypeError:  # pragma: no cover
            # catch if __digitizers is None
            pass

        return digi

    @property
    def msi(self) -> Union[dict, HDFMapMSI]:
        """
        :return: A dictionary containing all MSI diagnostic mappings
            objects.
        :rtype: dict

        For example, to retrieve mappings of LaPD's Magnetic field one
        would call::

            fmap = HDFMap(file_obj)
            bmap = fmap.msi['Magnetic field']
        """
        return self.__msi

    @property
    def unknowns(self) -> List[str]:
        """
        :return: A list containing all the subgroup names for the
            subgroups in the data group (:attr:`data_gname` that are
            unknown to the mapping constructor.
        :rtype: list
        """
        return self.__unknowns
