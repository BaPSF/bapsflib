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
"""
Module for defining the main HDF5 file mapper
`~bapsflib._hdf.maps.core.HDFMap`.
"""
__all__ = ["HDFMap"]

import h5py
import numpy as np
import os

from typing import List, Union
from warnings import warn

from bapsflib._hdf.maps.controls import HDFMapControls
from bapsflib._hdf.maps.controls.templates import (
    HDFMapControlCLTemplate,
    HDFMapControlTemplate,
)
from bapsflib._hdf.maps.digitizers import HDFMapDigitizers
from bapsflib._hdf.maps.digitizers.templates import HDFMapDigiTemplate
from bapsflib._hdf.maps.msi import HDFMapMSI
from bapsflib._hdf.maps.msi.templates import HDFMapMSITemplate
from bapsflib.utils import _bytes_to_str

# define type aliases
ControlMap = Union[HDFMapControlTemplate, HDFMapControlCLTemplate]
DigiMap = HDFMapDigiTemplate
MSIMap = HDFMapMSITemplate


class HDFMap(object):
    """
    Constructs a complete file mapping of the HDF5 file.  This is
    utilized by the HDF5 utility classes (in module
    :mod:`bapsflib._hdf.utils`) to manipulate and read data out of
    the HDF5 file.

    The following classes are leveraged to construct the mappings:

        * :class:`~.controls.map_controls.HDFMapControls`.
        * :class:`~.digitizers.map_digis.HDFMapDigitizers`.
        * :class:`~.msi.map_msi.HDFMapMSI`.
    """

    def __init__(
        self, hdf_obj: h5py.File, control_path: str, digitizer_path: str, msi_path: str
    ):
        """
        :param hdf_obj: the HDF5 file object
        :type hdf_obj: :class:`h5py.File`
        :param control_path: internal HDF5 path to group containing
            control devices
        :param digitizer_path: internal HDF5 path to group containing
            digitizers
        :param msi_path: internal HDF5 path to group containing
            MSI diagnostics
        """
        # store an instance of the HDF5 object for HDFMap
        if isinstance(hdf_obj, h5py.File):
            self._hdf_obj = hdf_obj
        else:
            raise TypeError("arg `hdf_file` not an h5py.File object")

        # define paths
        self.DEVICE_PATHS = {
            "control": control_path,
            "digitizer": digitizer_path,
            "msi": msi_path,
        }
        for device, path in self.DEVICE_PATHS.items():
            if path == "":
                self.DEVICE_PATHS[device] = "/"

        # attach the mapping dictionaries
        self.__attach_msi()
        self.__attach_digitizers()
        self.__attach_controls()
        self.__attach_unknowns()

    def __repr__(self):
        filename = self._hdf_obj.filename
        if isinstance(filename, (bytes, np.bytes_)):
            filename = _bytes_to_str(filename)
        filename = os.path.basename(filename)
        rstr = f"<{self.__class__.__name__} of HDF5 file '{filename}'>"
        return rstr

    def __attach_controls(self):
        """
        Attaches the :attr:`__controls` dictionary, which contains all
        the control device mapping objects constructed by
        :class:`~.controls.map_controls.HDFMapControls`.
        """
        control_path = self.DEVICE_PATHS["control"]
        if control_path in self._hdf_obj:
            self.__controls = HDFMapControls(self._hdf_obj[control_path])
        else:
            warn(f"Group for control devices ('{control_path}') does NOT exist.")
            self.__controls = {}

    def __attach_digitizers(self):
        """
        Attaches the :attr:`__digitizers` dictionary, which contains
        all the digitizer mapping objects constructed by
        :class:`~.digitizers.map_digis.HDFMapDigitizers`.
        """
        digi_path = self.DEVICE_PATHS["digitizer"]
        if digi_path in self._hdf_obj:
            self.__digitizers = HDFMapDigitizers(self._hdf_obj[digi_path])
        else:
            warn(f"Group for digitizers ('{digi_path}') does NOT exist.")
            self.__digitizers = {}

    def __attach_msi(self):
        """
        Attaches the :attr:`__msi` dictionary, which contains all MSI
        diagnostic mapping objects constructed by
        :class:`~.msi.map_msi.HDFMapMSI`.
        """
        msi_path = self.DEVICE_PATHS["msi"]
        if msi_path in self._hdf_obj:
            self.__msi = HDFMapMSI(self._hdf_obj[msi_path])
        else:
            warn(f"MSI ('{msi_path}') does NOT exist.")
            self.__msi = {}

    def __attach_unknowns(self):
        """
        Attaches the :attr:`__unknowns` list, which contains all the
        subgroup and dataset paths in the HDF% root group, control
        device group, digitizer group, and MSI group that were not
        mapped.
        """
        # add unknowns (Groups & Datasets) from levels
        # 1. root -- '/'
        # 2. control group -- '/Raw data + config' (typical)
        # 3. digitizer group -- '/Raw data + config' (typical)
        # 4. MSI group -- '/MSI' (typical)
        #
        self.__unknowns = []
        device_paths = [
            self.DEVICE_PATHS["control"],
            self.DEVICE_PATHS["digitizer"],
            self.DEVICE_PATHS["msi"],
        ]
        mapped_devices = [list(self.controls), list(self.digitizers), list(self.msi)]

        # scan through root, Control, Digitizer, and MSI groups
        devices_known = {"/": device_paths.copy()}
        for path, mapped in zip(device_paths, mapped_devices):
            if path in devices_known:
                devices_known[path].extend(mapped)
            else:
                devices_known[path] = mapped.copy()
        for path, devices in devices_known.items():
            if path in self._hdf_obj:
                for item in self._hdf_obj[path]:
                    if item not in devices:
                        self.__unknowns.append(self._hdf_obj[path][item].name)

    @property
    def controls(self) -> Union[dict, HDFMapControls]:
        """
        Dictionary of all the control device mapping objects.

        :Example:

            How to retrieve the mapping object of the control device
            :code:`'6K Compumotor'`::

                fmap = HDFMap(file_obj)
                dmap = fmap.controls['6K Compumotor']
        """
        return self.__controls

    @property
    def digitizers(self) -> Union[dict, HDFMapDigitizers]:
        """
        Dictionary of all the digitizer device mapping objects.

        :Example:

            How to retrieve the mapping object of the digitizer
            :code:`'SIS 3301'`::

                fmap = HDFMap(file_obj)
                dmap = fmap.digitizers['SIS 3301']
        """
        return self.__digitizers

    def get(self, name: str):
        """
        Get an device mapping instance.

        :param name: name of desired device
        :returns: If the specified device is mapped, then an instance
            of the mapping is returned. Otherwise, :code:`None` is
            returned.
        :Example:

            How to retrieve the mapping object for the
            :code:`'SIS 3301'` digitizer::

                >>> fmap = HDFMap(file_obj)
                >>> dmap = fmap.get('SIS 3301')
                >>>
                >>> # which is equivalent to
                >>> dmap = fmap.digitizers['SIS 3301']
        """
        if name in self.controls:
            _map = self.controls[name]
        elif name in self.digitizers:
            _map = self.digitizers[name]
        elif name in self.msi:
            _map = self.msi[name]
        else:
            _map = None

        return _map

    @property
    def main_digitizer(self) -> Union[None, DigiMap]:
        """
        :return: the mapping object for the digitizer that is assumed
            to be the :ibf:`main digitizer` in :attr:`digitizers`

        The main digitizer is determine by scanning through the local
        tuple :const:`possible_candidates` that contains a
        hierarchical list of digitizers. The first digitizer found is
        assumed to be the :ibf:`main digitizer`. ::

            possible_candidates = ('SIS 3301', 'SIS crate')
        """
        # possible_candidates is a hierarchical tuple of all digitizers
        # such that the first found digitizer is assumed to be the main
        # digitizer
        possible_candidates = ("SIS 3301", "SIS crate")
        digi = None
        if len(self.digitizers) == 1:
            digi = self.digitizers[list(self.digitizers)[0]]
        else:
            for key in possible_candidates:
                if key in self.digitizers:
                    digi = self.digitizers[key]
                    break

        return digi

    @property
    def msi(self) -> Union[dict, HDFMapMSI]:
        """
        Dictionary of all the MSI diagnostic mapping objects.

        :Example:

            How to retrieve the mapping object of the
            :code:`'Magnetic field'` MSI diagnostic::

                fmap = HDFMap(file_obj)
                dmap = fmap.msi['Magnetic field']
        """
        return self.__msi

    @property
    def unknowns(self) -> List[str]:
        """
        List of all subgroup and dataset paths in the HDF5 root group,
        control device group, digitizer group, and MSI group that were
        not mapped.
        """
        return self.__unknowns
