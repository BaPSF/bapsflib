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
Module for defining the LaPD HDF5 file mapper
`~bapsflib.lapd._hdf.lapdmap.LaPDMap`.
"""
__all__ = ["LaPDMap"]

import h5py
import numpy as np

from typing import Union
from warnings import warn

from bapsflib._hdf import HDFMap
from bapsflib.utils import _bytes_to_str
from bapsflib.utils.warnings import BaPSFWarning


class LaPDMap(HDFMap):
    """
    A specialized version of :class:`~bapsflib._hdf.maps.core.HDFMap`
    which adds attributes that are specific to mapping a HDF5 file
    generated by the LaPD.
    """

    def __init__(
        self,
        hdf_obj: h5py.File,
        control_path="Raw data + config",
        digitizer_path="Raw data + config",
        msi_path="MSI",
    ):
        """
        Parameters
        ----------
        hdf_obj : `h5py.File`
            HDF5 file object

        control_path : `str`, optional
            internal HDF5 path to group containing control devices
            (DEFAULT ``'Raw data + config'``)

        digitizer_path : `str`, optional
            internal HDF5 path to group containing digitizers
            (DEFAULT ``'Raw data + config'``)

        msi_path : `str`, optional
            internal HDF5 path to group containing MSI diagnostics
            (DEFAULT ``'MSI'``)
        """
        super().__init__(
            hdf_obj,
            control_path=control_path,
            digitizer_path=digitizer_path,
            msi_path=msi_path,
        )

        # is HDF5 file generated by the LaPD
        if not self.is_lapd:
            warn(
                f"HDF5 file ('{hdf_obj.filename}') was not generated by the LaPD.",
                BaPSFWarning,
            )

    @property
    def is_lapd(self) -> bool:
        """`True` if HDF5 file was generated by the LaPD"""
        is_lapd = True if "LaPD HDF5 software version" in self._hdf_obj.attrs else False

        return is_lapd

    @property
    def lapd_version(self) -> Union[None, str]:
        """LaPD HDF5 version string."""
        try:
            vers = _bytes_to_str(self._hdf_obj.attrs["LaPD HDF5 software version"])
        except KeyError:
            vers = None

        return vers

    @property
    def exp_info(self):
        """Dictionary of experiment info"""
        # initialize
        exp_info = {
            "investigator": "",
            "exp name": "",
            "exp description": "",
            "exp set name": "",
            "exp set description": "",
        }

        # assign values
        for key, val in self._hdf_obj[self.DEVICE_PATHS["digitizer"]].attrs.items():
            if isinstance(val, (np.bytes_, bytes)):
                val = _bytes_to_str(val)

            if key == "Investigator":
                exp_info["investigator"] = val
            elif key == "Experiment name":
                exp_info["exp name"] = val
            elif key == "Experiment description":
                exp_info["exp description"] = val
            elif key == "Experiment set name":
                exp_info["exp set name"] = val
            elif key == "Experiment set description":
                exp_info["exp set description"] = val

        # return
        return exp_info

    @property
    def run_info(self):
        """Dictionary of experimental run info."""
        # initialize
        run_info = {
            "run name": "",
            "run description": "",
            "run status": "",
            "run date": "",
        }

        # assign values
        for key, val in self._hdf_obj[self.DEVICE_PATHS["digitizer"]].attrs.items():
            if isinstance(val, (np.bytes_, bytes)):
                val = _bytes_to_str(val)

            if key == "Data run":
                run_info["run name"] = val
            elif key == "Description":
                run_info["run description"] = val
            elif key == "Status":
                run_info["run status"] = val
            elif key == "Status date":
                run_info["run date"] = val

        # return
        return run_info
