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
Module for the Cathode Heater MSI Diagnostic mapper
`~bapsflib._hdf.maps.msi.heater.HDFMapMSIHeater`.
"""
__all__ = ["HDFMapMSIHeater"]

import h5py
import numpy as np

from warnings import warn

from bapsflib._hdf.maps.msi.templates import HDFMapMSITemplate
from bapsflib.utils.exceptions import HDFMappingError


class HDFMapMSIHeater(HDFMapMSITemplate):
    """
    Mapping class for the 'Heater' MSI diagnostic.

    Simple group structure looks like:

    .. code-block:: none

        +-- Heater
        |   +-- Heater summary

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
        for dset_name in ["Heater summary"]:
            if dset_name not in self.group:
                why = f"dataset '{dset_name}' not found"
                raise HDFMappingError(self.info["group path"], why=why)

        # initialize general info values
        pairs = [("calib tag", "Calibration tag")]
        for pair in pairs:
            try:
                self._configs[pair[0]] = [self.group.attrs[pair[1]]]
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
        # - there are NO signal fields
        #
        self._configs["signals"] = {}

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
            "current": {
                "dset paths": (),
                "dset field": ("Heater current",),
                "shape": (),
                "dtype": np.float32,
            },
            "voltage": {
                "dset paths": (),
                "dset field": ("Heater voltage",),
                "shape": (),
                "dtype": np.float32,
            },
            "temperature": {
                "dset paths": (),
                "dset field": ("Heater temperature",),
                "shape": (),
                "dtype": np.float32,
            },
        }

        # ---- update configs related to 'Heater summary'           ----
        # - dependent configs are:
        #   1. 'shape'
        #   2. 'shotnum'
        #   3. all of 'meta'
        #
        dset_name = "Heater summary"
        dset = self.group[dset_name]

        # define 'shape'
        expected_fields = [
            "Shot number",
            "Timestamp",
            "Data valid",
            "Heater current",
            "Heater voltage",
            "Heater temperature",
        ]
        if dset.ndim == 1 and all(field in dset.dtype.names for field in expected_fields):
            self._configs["shape"] = dset.shape
        else:
            why = "'/Heater summary' does not match expected shape"
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

        # update 'meta/current'
        self._configs["meta"]["current"]["dset paths"] = (dset.name,)
        self._configs["meta"]["current"]["shape"] = dset.dtype["Heater current"].shape

        # update 'meta/voltage'
        self._configs["meta"]["voltage"]["dset paths"] = (dset.name,)
        self._configs["meta"]["voltage"]["shape"] = dset.dtype["Heater voltage"].shape

        # update 'meta/current'
        self._configs["meta"]["temperature"]["dset paths"] = (dset.name,)
        self._configs["meta"]["temperature"]["shape"] = dset.dtype[
            "Heater temperature"
        ].shape
