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
Module for the Discharge MSI Diagnostic mapper
`~bapsflib._hdf.maps.msi.magneticfield.HDFMapMSIMagneticField`.
"""
__all__ = ["HDFMapMSIMagneticField"]

import h5py
import numpy as np

from warnings import warn

from bapsflib._hdf.maps.msi.templates import HDFMapMSITemplate
from bapsflib.utils.exceptions import HDFMappingError


class HDFMapMSIMagneticField(HDFMapMSITemplate):
    """
    Mapping class for the 'Magnetic field' MSI diagnostic.

    Simple group structure looks like:

    .. code-block:: none

        +-- Magnetic field
        |   +-- Magnet power supply currents
        |   +-- Magnetic field profile
        |   +-- Magnetic field summary
    """

    def __init__(self, group: h5py.Group):
        """
        :param group: the HDF5 MSI diagnostic group
        :type group: :class:`h5py.Group`
        """
        # initialize
        HDFMapMSITemplate.__init__(self, group)

        # populate self.configs
        self._build_configs()

    def _build_configs(self):
        """Builds the :attr:`configs` dictionary."""
        # look for required datasets
        for dset_name in [
            "Magnet power supply currents",
            "Magnetic field profile",
            "Magnetic field summary",
        ]:
            if dset_name not in self.group:
                why = f"dataset '{dset_name}' not found"
                raise HDFMappingError(self.info["group path"], why=why)

        # initialize general info values
        pairs = [("calib tag", "Calibration tag"), ("z", "Profile z locations")]
        for pair in pairs:
            try:
                val = self.group.attrs[pair[1]]
                if isinstance(val, (list, tuple, np.ndarray)):
                    self._configs[pair[0]] = val
                else:
                    self._configs[pair[0]] = [val]
            except KeyError:
                self._configs[pair[0]] = []
                warn(
                    f"Attribute '{pair[1]}' not found for MSI diagnostic "
                    f"'{self.device_name}', continuing with mapping"
                )

        # initialize 'shape'
        # - this is used by HDFReadMSI
        self._configs["shape"] = ()

        # initialize 'shotnum'
        self._configs["shotnum"] = {
            "dset paths": (),
            "dset field": ("Shot number",),
            "shape": (),
            "dtype": np.int32,
        }

        # initialize 'signals'
        # - there are two signal fields
        #   1. 'magnet ps current'
        #   2. 'magnetic field'
        #
        self._configs["signals"] = {
            "magnet ps current": {
                "dset paths": (),
                "dset field": (),
                "shape": (),
                "dtype": np.float32,
            },
            "magnetic field": {
                "dset paths": (),
                "dset field": (),
                "shape": (),
                "dtype": np.float32,
            },
        }

        # initialize 'meta'
        self._configs["meta"] = {
            "shape": (),
            "timestamp": {
                "dset paths": (),
                "dset field": ("Timestamp",),
                "shape": (),
                "dtype": np.float64,
            },
            "data valid": {
                "dset paths": (),
                "dset field": ("Data valid",),
                "shape": (),
                "dtype": np.int8,
            },
            "peak magnetic field": {
                "dset paths": (),
                "dset field": ("Peak magnetic field",),
                "shape": (),
                "dtype": np.float32,
            },
        }

        # ---- update configs related to 'Magnetic field summary'   ----
        # - dependent configs are:
        #   1. 'shotnum'
        #   2. all of 'meta'
        #
        dset_name = "Magnetic field summary"
        dset = self.group[dset_name]

        # define 'shape'
        expected_fields = [
            "Shot number",
            "Timestamp",
            "Data valid",
            "Peak magnetic field",
        ]
        if dset.ndim == 1 and all(field in dset.dtype.names for field in expected_fields):
            self._configs["shape"] = dset.shape
        else:
            why = "'/Magnetic field summary' does not match expected shape"
            raise HDFMappingError(self.info["group path"], why=why)

        # update 'shotnum'
        self._configs["shotnum"]["dset paths"] = (dset.name,)
        self._configs["shotnum"]["shape"] = dset.dtype["Shot number"].shape

        # update 'meta/timestamp'
        self._configs["meta"]["timestamp"]["dset paths"] = (dset.name,)
        self._configs["meta"]["timestamp"]["shape"] = dset.dtype["Timestamp"].shape

        # update 'meta/data valid'
        self._configs["meta"]["data valid"]["dset paths"] = (dset.name,)
        self._configs["meta"]["data valid"]["shape"] = dset.dtype["Data valid"].shape

        # update 'meta/peak magnetic field'
        self._configs["meta"]["peak magnetic field"]["dset paths"] = (dset.name,)
        self._configs["meta"]["peak magnetic field"]["shape"] = dset.dtype[
            "Peak magnetic field"
        ].shape

        # update configs related to 'Magnet power supply currents'  ----
        # - dependent configs are:
        #   1. 'signals/magnet ps current'
        #
        dset_name = "Magnet power supply currents"
        dset = self.group[dset_name]
        self._configs["signals"]["magnet ps current"]["dset paths"] = (dset.name,)

        # check 'shape'
        _build_success = True
        if dset.dtype.names is not None:
            # dataset has fields (it should not have fields)
            _build_success = False
        elif dset.ndim == 2:
            if dset.shape[0] == self._configs["shape"][0]:
                self._configs["signals"]["magnet ps current"]["shape"] = (dset.shape[1],)
            else:
                _build_success = False
        else:
            _build_success = False
        if not _build_success:
            why = "'/Magnet power supply currents' does not match expected shape"
            raise HDFMappingError(self.info["group path"], why=why)

        # update configs related to 'Magnetic field profile'        ----
        # - dependent configs are:
        #   1. 'signals/magnetic field'
        #
        dset_name = "Magnetic field profile"
        dset = self.group[dset_name]
        self._configs["signals"]["magnetic field"]["dset paths"] = (dset.name,)

        # check 'shape'
        _build_success = True
        if dset.dtype.names is not None:
            # dataset has fields (it should not have fields)
            _build_success = False
        elif dset.ndim == 2:
            if dset.shape[0] == self._configs["shape"][0]:
                self._configs["signals"]["magnetic field"]["shape"] = (dset.shape[1],)
            else:
                _build_success = False
        else:
            _build_success = False
        if not _build_success:
            why = "'/Magnetic field profile' does not match expected shape"
            raise HDFMappingError(self.info["group path"], why=why)
