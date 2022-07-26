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
Module for the Gas Pressure MSI Diagnostic mapper
`~bapsflib._hdf.maps.msi.gaspressure.HDFMapMSIGasPressure`.
"""
__all__ = ["HDFMapMSIGasPressure"]

import h5py
import numpy as np

from warnings import warn

from bapsflib._hdf.maps.msi.templates import HDFMapMSITemplate
from bapsflib.utils.exceptions import HDFMappingError


class HDFMapMSIGasPressure(HDFMapMSITemplate):
    """
    Mapping class for the 'Gas pressure' MSI diagnostic.

    Simple group structure looks like:

    .. code-block:: none

        +-- Gas pressure
        |   +-- Gas pressure summary
        |   +-- RGA partial pressures

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
        for dset_name in ["Gas pressure summary", "RGA partial pressures"]:
            if dset_name not in self.group:
                why = f"dataset '{dset_name}' not found"
                raise HDFMappingError(self.info["group path"], why=why)

        # initialize general info values
        pairs = [
            ("RGA AMUs", "RGA AMUs"),
            ("ion gauge calib tag", "Ion gauge calibration tag"),
            ("RGA calib tag", "RGA calibration tag"),
        ]
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
        # - there is only one signal fields
        #   1. 'partial pressures'
        #
        self._configs["signals"] = {
            "partial pressures": {
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
            "data valid - ion gauge": {
                "dset paths": (),
                "dset field": ("Ion gauge data valid",),
                "shape": (),
                "dtype": np.int8,
            },
            "data valid - RGA": {
                "dset paths": [],
                "dset field": ("RGA data valid",),
                "shape": (),
                "dtype": np.int8,
            },
            "fill pressure": {
                "dset paths": (),
                "dset field": ("Fill pressure",),
                "shape": (),
                "dtype": np.float32,
            },
            "peak AMU": {
                "dset paths": (),
                "dset field": ("Peak AMU",),
                "shape": (),
                "dtype": np.float32,
            },
        }

        # ---- update configs related to 'Gas pressure summary'     ----
        # - dependent configs are:
        #   1. 'shape'
        #   2. 'shotnum'
        #   3. all of 'meta'
        #
        dset_name = "Gas pressure summary"
        dset = self.group[dset_name]

        # define 'shape'
        expected_fields = [
            "Shot number",
            "Timestamp",
            "Ion gauge data valid",
            "RGA data valid",
            "Fill pressure",
            "Peak AMU",
        ]
        if dset.ndim == 1 and all(field in dset.dtype.names for field in expected_fields):
            self._configs["shape"] = dset.shape
        else:
            why = "'/Gas pressure summary' does not match expected shape"
            raise HDFMappingError(self.info["group path"], why=why)

        # update 'shotnum'
        self._configs["shotnum"]["dset paths"] = (dset.name,)
        self._configs["shotnum"]["shape"] = dset.dtype["Shot number"].shape

        # update 'meta/timestamp'
        self._configs["meta"]["timestamp"]["dset paths"] = (dset.name,)
        self._configs["meta"]["timestamp"]["shape"] = dset.dtype["Timestamp"].shape

        # update 'meta/data valid - ion gauge'
        self._configs["meta"]["data valid - ion gauge"]["dset paths"] = (dset.name,)
        self._configs["meta"]["data valid - ion gauge"]["shape"] = dset.dtype[
            "Ion gauge data valid"
        ].shape

        # update 'meta/data valid - RGA'
        self._configs["meta"]["data valid - RGA"]["dset paths"] = (dset.name,)
        self._configs["meta"]["data valid - RGA"]["shape"] = dset.dtype[
            "RGA data valid"
        ].shape

        # update 'meta/fill pressure'
        self._configs["meta"]["fill pressure"]["dset paths"] = (dset.name,)
        self._configs["meta"]["fill pressure"]["shape"] = dset.dtype[
            "Fill pressure"
        ].shape

        # update 'meta/peak AMU'
        self._configs["meta"]["peak AMU"]["dset paths"] = (dset.name,)
        self._configs["meta"]["peak AMU"]["shape"] = dset.dtype["Peak AMU"].shape

        # ---- update configs related to 'RGA partial pressures'   ----
        # - dependent configs are:
        #   1. 'signals/partial pressures'
        #
        dset_name = "RGA partial pressures"
        dset = self.group[dset_name]
        self._configs["signals"]["partial pressures"]["dset paths"] = (dset.name,)

        # check 'shape'
        _build_success = True
        if dset.dtype.names is not None:
            # dataset has fields (it should not have fields)
            _build_success = False
        elif dset.ndim == 2:
            if dset.shape[0] == self._configs["shape"][0]:
                self._configs["signals"]["partial pressures"]["shape"] = (dset.shape[1],)
            else:
                _build_success = False
        else:
            _build_success = False
        if not _build_success:
            why = "'/RGA partial pressures' does not match expected shape"
            raise HDFMappingError(self.info["group path"], why=why)
