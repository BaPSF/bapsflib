# This file is part of the bapsflib package, a Python toolkit for the
# BaPSF group at UCLA.
#
# http://plasma.physics.ucla.edu/
#
# Copyright 2017-2018 Erik T. Everson and contributors
#
# License: Standard 3-clause BSD; see "LICENSES/LICENSE.txt" for full
#   license terms and contributor agreement.
"""
Module for the N5700PS power supply mapper
`~bapsflib._hdf.maps.controls.n5700ps.HDFMapControlN5700PS`.
"""
__all__ = ["HDFMapControlN5700PS"]

import h5py
import numpy as np
import warnings

from warnings import warn

from bapsflib._hdf.maps.controls.templates import HDFMapControlCLTemplate
from bapsflib._hdf.maps.controls.types import ConType
from bapsflib.utils import _bytes_to_str
from bapsflib.utils.exceptions import HDFMappingError


class HDFMapControlN5700PS(HDFMapControlCLTemplate):
    """
    Mapping module for control device 'N5700_PS'.

    Simple group structure looks like:

    .. code-block:: none

        +-- N5700_PS
        |   +-- Run time list
        |   +-- nsconf_<descr>
        |   |   +--

    """

    def __init__(self, group: h5py.Group):
        """
        :param group: the HDF5 control device group
        """
        # initialize
        HDFMapControlCLTemplate.__init__(self, group)

        # define control type
        self._info["contype"] = ConType.power

        # define known command list RE patterns
        self._default_re_patterns = (
            r"(?P<VOLT>(\bSOURCE:VOLTAGE:LEVEL\s)(?P<VAL>(\d+\.\d*|\.\d+|\d+\b)))",
        )

        # populate self.configs
        self._build_configs()

    def _build_configs(self):
        """Builds the :attr:`configs` dictionary."""
        # check there are configurations to map
        if len(self.subgroup_names) == 0:
            why = "has no mappable configurations"
            raise HDFMappingError(self._info["group path"], why=why)

        # build configuration dictionaries
        # - assume every sub-group represents a unique configuration
        #   to the control device
        # - the name of each sub-group is used as the configuration
        #   name
        # - assume all configurations are active (i.e. used)
        #
        for name in self.subgroup_names:
            # get configuration group
            cong = self.group[name]

            # get dataset
            try:
                dset = self.group[self.construct_dataset_name()]
            except KeyError:
                why = (
                    f"Dataset '{self.construct_dataset_name()}' not found "
                    f"configuration group '{name}'"
                )
                raise HDFMappingError(self._info["group path"], why=why)

            # initialize _configs
            self._configs[name] = {}

            # ---- define general info values                       ----
            pairs = [
                ("IP address", "IP address"),
                ("power supply device", "Model Number"),
                ("initial state", "Initialization commands"),
                ("command list", "N5700 power supply command list"),
            ]
            for pair in pairs:
                try:
                    # get attribute value
                    val = cong.attrs[pair[1]]

                    # condition value
                    if pair[0] == "command list":
                        # - val gets returned as a np.bytes_ string
                        # - split line returns
                        # - remove trailing/leading whitespace
                        #
                        val = _bytes_to_str(val).splitlines()
                        val = tuple([cls.strip() for cls in val])
                    else:
                        # pair[0] in ('IP address',
                        #             'power supply device',
                        #             'initial state'):
                        # - val is a np.bytes_ string
                        #
                        val = _bytes_to_str(val)

                    # assign val to _configs
                    self._configs[name][pair[0]] = val
                except KeyError:
                    self._configs[name][pair[0]] = None
                    warn_str = (
                        f"Attribute '{pair[1]}' not found in control device "
                        f"'{self.device_name}' configuration group '{name}'"
                    )
                    if pair[0] != "command list":
                        warn_str += ", continuing with mapping"
                        warn(warn_str)
                    else:
                        why = (
                            f"Attribute '{pair[1]}' not found for configuration "
                            f"group '{name}'"
                        )
                        raise HDFMappingError(self._info["group path"], why=why)

            # ---- define 'dset paths'                              ----
            self._configs[name]["dset paths"] = (dset.name,)

            # ---- define 'shotnum'                                 ----
            # initialize
            self._configs[name]["shotnum"] = {
                "dset paths": self._configs[name]["dset paths"],
                "dset field": ("Shot number",),
                "shape": dset.dtype["Shot number"].shape,
                "dtype": np.int32,
            }

            # ---- define 'state values'                            ----
            # catch and suppress warnings only for initialization
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                try:
                    sv_dict = self._construct_state_values_dict(
                        name, self._default_re_patterns
                    )
                except KeyError:
                    sv_dict = {}

            # initialize
            self._configs[name]["state values"] = (
                sv_dict if bool(sv_dict) else self._default_state_values_dict(name)
            )

    def _default_state_values_dict(self, config_name: str) -> dict:
        # define default dict
        default_dict = {
            "command": {
                "dset paths": self._configs[config_name]["dset paths"],
                "dset field": ("Command index",),
                "re pattern": None,
                "command list": self._configs[config_name]["command list"],
                "cl str": self._configs[config_name]["command list"],
                "shape": (),
            }
        }
        default_dict["command"]["dtype"] = np.array(
            default_dict["command"]["command list"]
        ).dtype

        # return
        return default_dict

    def construct_dataset_name(self, *args) -> str:
        """
        Constructs name of dataset containing control state value data.
        """
        return "Run time list"
