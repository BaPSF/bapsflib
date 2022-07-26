# This file is part of the bapsflib package, a Python toolkit for the
# BaPSF group at UCLA.
#
# http://plasma.physics.ucla.edu/
#
# Copyright 2017-2019 Erik T. Everson and contributors
#
# License: Standard 3-clause BSD; see "LICENSES/LICENSE.txt" for full
#   license terms and contributor agreement.
#
"""
Module for the NIXYZ motion control mapper
`~bapsflib._hdf.maps.controls.nixyz.HDFMapControlNIXYZ`.
"""
__all__ = ["HDFMapControlNIXYZ"]

import astropy.units as u
import h5py
import numpy as np

from warnings import warn

from bapsflib._hdf.maps.controls.templates import HDFMapControlTemplate
from bapsflib._hdf.maps.controls.types import ConType
from bapsflib.utils import _bytes_to_str
from bapsflib.utils.exceptions import HDFMappingError


class HDFMapControlNIXYZ(HDFMapControlTemplate):
    """
    Mapping module for control device 'NI_XYZ'.

    Simple group structure looks like:

    .. code-block:: none

        +-- NI_XYZ
        |   +-- <motion list name 1>
        |   |   +--
        .
        .
        .
        |   +-- <motion list name N>
        |   |   +--
        |   +-- Run time list
    """

    def __init__(self, group: h5py.Group):
        """
        :param group: the HDF5 control device group
        """
        HDFMapControlTemplate.__init__(self, group)

        # define control type
        self._info["contype"] = ConType.motion

        # populate self.configs
        self._build_configs()

    def _build_configs(self):
        """Build the :attr:`configs` dictionary"""
        # Assumptions:
        # 1. only one NI_XYZ drive was ever built, so there will always
        #    be only one configuration
        #    - naming configuration 'config01'
        # 2. there's only one dataset ever created 'Run time list'
        # 3. there can be multiple motion lists defined
        #    - each sub-group is a configuration for a different
        #      motion list
        #    - the name of the sub-group is the name of the motion list
        #
        # initialize configuration
        cname = "config01"
        self.configs[cname] = {}

        # check there are existing motion lists
        if len(self.subgroup_names) == 0:
            warn(f"{self.info['group path']}: no defining motion list groups exist")

        # get dataset
        try:
            dset = self.group[self.construct_dataset_name()]
        except KeyError:
            why = f"Dataset '{self.construct_dataset_name()}' not found"
            raise HDFMappingError(self.info["group path"], why=why)

        # ---- define general config values                         ----
        self.configs[cname].update(
            {
                "Note": "The 'r', 'theta', and 'phi' fields in the "
                "NI_XYZ data set are suppose to represent "
                "spherical coordinates of the probe tip with "
                "respect to the pivot point of the probe drive, "
                "but the current calculation and population of the"
                "fields is inaccurate.  For user reference, the "
                "distance between the probe drive pivot point and"
                "LaPD axis is (Lpp =) 58.771 cm.",
                "Lpp": 58.771 * u.cm,
            }
        )

        # ---- define motion list values                            ----
        self.configs[cname]["motion lists"] = {}

        # get sub-group names (i.e. ml names)
        _ml_names = []
        for name in self.group:
            if isinstance(self.group[name], h5py.Group):
                _ml_names.append(name)

        # a motion list group must have the attributes
        # Nx, Ny, Nz, dx, dy, dz, x0, y0, z0
        names_to_remove = []
        for name in _ml_names:
            if all(
                attr not in self.group[name].attrs
                for attr in ("Nx", "Ny", "Nz", "dx", "dy", "dz", "x0", "y0", "z0")
            ):
                names_to_remove.append(name)
        if bool(names_to_remove):
            for name in names_to_remove:
                _ml_names.remove(name)

        # warn if no motion lists exist
        if not bool(_ml_names):
            why = "NI_XYZ has no identifiable motion lists"
            warn(why)

        # gather ML config values
        pairs = [
            ("Nx", "Nx"),
            ("Ny", "Ny"),
            ("Nz", "Nz"),
            ("dx", "dx"),
            ("dy", "dy"),
            ("dz", "dz"),
            ("fan_XYZ", "fan_XYZ"),
            ("max_ydrive_steps", "max_ydrive_steps"),
            ("min_ydrive_steps", "min_ydrive_steps"),
            ("max_zdrive_steps", "max_zdrive_steps"),
            ("min_zdrive_steps", "min_zdrive_steps"),
            ("x0", "x0"),
            ("y0", "y0"),
            ("z0", "z0"),
            ("port", "z_port"),
        ]
        for name in _ml_names:
            # initialize ML dictionary
            self.configs[cname]["motion lists"][name] = {}

            # add ML values
            for pair in pairs:
                try:
                    # get attribute value
                    val = self.group[name].attrs[pair[1]]

                    # condition value
                    if np.issubdtype(type(val), np.bytes_):
                        # - val is a np.bytes_ string
                        val = _bytes_to_str(val)
                    if pair[1] == "fan_XYZ":
                        # convert to boolean
                        if val == "TRUE":
                            val = True
                        else:
                            val = False

                    # assign val to configs
                    self.configs[cname]["motion lists"][name][pair[0]] = val
                except KeyError:
                    self.configs[cname]["motion lists"][name][pair[0]] = None

                    why = (
                        f"Motion List attribute '{pair[1]}' not found for "
                        f"ML group '{name}'"
                    )
                    warn(why)

        # ---- define 'dset paths'                                  ----
        self.configs[cname]["dset paths"] = (dset.name,)

        # ---- define 'shotnum'                                     ----
        # check dset for 'Shot number' field
        if "Shot number" not in dset.dtype.names:
            why = f"Dataset '{dset.name}' is missing 'Shot number' field"
            raise HDFMappingError(self.info["group path"], why=why)

        # initialize
        self.configs[cname]["shotnum"] = {
            "dset paths": self.configs[cname]["dset paths"],
            "dset field": ("Shot number",),
            "shape": dset.dtype["Shot number"].shape,
            "dtype": np.int32,
        }

        # ---- define 'state values'                                ----
        self._configs[cname]["state values"] = {
            "xyz": {
                "dset paths": self._configs[cname]["dset paths"],
                "dset field": ("x", "y", "z"),
                "shape": (3,),
                "dtype": np.float64,
            },
        }

        # check dset for 'x', 'y' and 'z' fields
        fx = "x" not in dset.dtype.names
        fy = "y" not in dset.dtype.names
        fz = "z" not in dset.dtype.names
        if fx and fy and fz:
            why = f"Dataset '{dset.name}' missing fields 'x', 'y' and 'z'"
            raise HDFMappingError(self.info["group path"], why=why)
        elif fx or fy or fz:
            mlist = [("x", fx), ("y", fy), ("z", fz)]
            missf = ", ".join([val for val, bol in mlist if bol])
            why = f" Dataset '{dset.name}' missing field '{missf}'"
            warn(why)

    def construct_dataset_name(self, *args) -> str:
        """
        Constructs name of dataset containing control state value data.
        """
        return "Run time list"
