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
Module for the 6K Compumotor motion control mapper
`~bapsflib._hdf.maps.controls.sixk.HDFMapControl6K`.
"""
__all__ = ["HDFMapControl6K"]

import h5py
import numpy as np
import re

from warnings import warn

from bapsflib._hdf.maps.controls.templates import HDFMapControlTemplate
from bapsflib._hdf.maps.controls.types import ConType
from bapsflib.utils import _bytes_to_str
from bapsflib.utils.exceptions import HDFMappingError


class HDFMapControl6K(HDFMapControlTemplate):
    """
    Mapping module for control device '6K Compumotor'.

    Simple group structure looks like:

    .. code-block:: none

        +-- 6K Compumotor
        |   +-- Motion list: <name>
        |   |   +--
        |   +-- Probe: XY[<receptacle #>]: <probe name>
        |   |   +-- Axes[0]
        |   |   |   +--
        |   |   +-- Axes[1]
        |   |   |   +--
        |   +-- XY[<receptacle #>]: <probe name>

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
        """Builds the :attr:`configs` dictionary."""
        # build order:
        #  1. build a local motion list dictionary
        #  2. build a local probe list dictionary
        #  3. build configs dict
        #
        # TODO: HOW TO ADD MOTION LIST TO DICT
        # - right now, the dataset has to be read which has the
        #   potential for creating long mapping times
        # - this is probably best left to HDFReadControls
        #

        # build 'motion list' and 'probe list'
        _motion_lists = {}
        _probe_lists = {}
        for name in self.subgroup_names:
            ml_stuff = self._analyze_motionlist(name)
            if bool(ml_stuff):
                # build 'motion list'
                _motion_lists[ml_stuff["name"]] = ml_stuff["config"]
            else:
                pl_stuff = self._analyze_probelist(name)
                if bool(pl_stuff):
                    # build 'probe list'
                    _probe_lists[pl_stuff["probe-id"]] = pl_stuff["config"]

        # ensure a PL item (config group) is found
        if len(_probe_lists) == 0:
            why = "has no mappable configurations (Probe List groups)"
            raise HDFMappingError(self._info["group path"], why=why)

        # build configuration dictionaries
        # - the receptacle number is the config_name
        # - each probe is one-to-one with receptacle number
        #
        for pname in _probe_lists:
            # define configuration name
            config_name = _probe_lists[pname]["receptacle"]

            # initialize _configs
            self._configs[config_name] = {}

            # ---- define general info values                       ----
            # - this has to be done before getting the dataset since
            #   the _configs dist is used by construct_dataset_name()
            #
            # add motion list info
            self._configs[config_name]["motion lists"] = _motion_lists

            # add probe info
            self._configs[config_name]["probe"] = _probe_lists[pname]

            # add 'receptacle'
            self._configs[config_name]["receptacle"] = self._configs[config_name][
                "probe"
            ]["receptacle"]

            # ---- get configuration dataset                        ----
            try:
                dset_name = self.construct_dataset_name(config_name)
                dset = self.group[dset_name]
            except (KeyError, ValueError):
                # KeyError: the dataset was not found
                # ValueError: the dataset name was not properly
                #             constructed
                #
                why = (
                    f"Dataset for configuration '{pname}' could not be "
                    f"determined or found."
                )
                raise HDFMappingError(self._info["group path"], why=why)

            # ---- define 'dset paths'                              ----
            self._configs[config_name]["dset paths"] = (dset.name,)

            # ---- define 'shotnum'                                 ----
            # initialize
            self._configs[config_name]["shotnum"] = {
                "dset paths": self._configs[config_name]["dset paths"],
                "dset field": ("Shot number",),
                "shape": dset.dtype["Shot number"].shape,
                "dtype": np.int32,
            }

            # ---- define 'state values'                            ----
            self._configs[config_name]["state values"] = {
                "xyz": {
                    "dset paths": self._configs[config_name]["dset paths"],
                    "dset field": ("x", "y", "z"),
                    "shape": (3,),
                    "dtype": np.float64,
                },
                "ptip_rot_theta": {
                    "dset paths": self._configs[config_name]["dset paths"],
                    "dset field": ("theta",),
                    "shape": (),
                    "dtype": np.float64,
                },
                "ptip_rot_phi": {
                    "dset paths": self._configs[config_name]["dset paths"],
                    "dset field": ("phi",),
                    "shape": (),
                    "dtype": np.float64,
                },
            }

    def construct_dataset_name(self, *args) -> str:
        # The first arg passed is assumed to be the receptacle number.
        # If none are passed and there is only one receptacle deployed,
        # then the deployed receptacle is assumed.

        # get list of configurations
        # - configuration names are receptacle numbers
        #
        _receptacles = list(self.configs)

        # get receptacle number
        err = True
        rnum = -1
        if len(args) == 0:
            if len(_receptacles) == 1:
                # assume the sole receptacle number
                rnum = _receptacles[0]
                err = False
        else:  # len(args) >= 1:
            receptacle = args[0]
            if receptacle in _receptacles:
                rnum = receptacle
                err = False
        if err:
            raise ValueError(
                f"A valid receptacle number needs to be passed: {_receptacles}"
            )

        # Find matching probe to receptacle
        # - note that probe naming in the HDF5 are not consistent, this
        #   is why dataset name is constructed based on receptacle and
        #   not probe name
        #
        pname = self._configs[rnum]["probe"]["probe name"]

        # Construct dataset name
        dname = f"XY[{rnum}]: {pname}"

        # return
        return dname

    def _analyze_motionlist(self, gname: str) -> dict:
        """
        Determines if `gname` matches the RE for a motion list group
        name.  It yes, then it gathers the motion list info.

        :param str gname: name of potential motion list group
        :return: dictionary with `'name'` and `'config'` keys
        """
        # Define RE pattern
        # - A motion list group follows the naming scheme of:
        #
        #     'Motion list: <NAME>'
        #
        #   where <NAME> is the motion list name
        #
        _pattern = r"(\bMotion list:\s)(?P<NAME>.+\b)"

        # match _pattern against gname
        _match = re.fullmatch(_pattern, gname)

        # gather ml info
        # - Note: a missing HDF5 attribute will not cause the mapping to
        #         fail, the associated mapping item will be given an
        #         appropriate None vale
        #
        if _match is not None:
            # define motion list dict
            ml = {"name": _match.group("NAME"), "config": {}}

            # get ml group
            mlg = self.group[gname]

            # gather motion list info
            # -- define 'group name' and 'group path' --
            ml["config"]["group name"] = gname
            ml["config"]["group path"] = mlg.name

            # -- check ML name --
            try:
                ml_name = mlg.attrs["Motion list"]
                if np.issubdtype(type(ml_name), np.bytes_):
                    # decode to 'utf-8'
                    ml_name = _bytes_to_str(ml_name)

                if ml["name"] != ml_name:
                    warn_str = (
                        f"Discovered motion list name '{ml['name']}' does not "
                        f"match the name defined in attributes '{ml_name}', "
                        f"using discovered name"
                    )
                    warn(warn_str)
            except KeyError:
                warn_str = (
                    f"Motion list attribute 'Motion list' not found for ML "
                    f"'{ml['config']['group name']}'"
                )
                warn(warn_str)

            # -- check simple pairs --
            pairs = [
                ("created date", "Created date"),
                ("data motion count", "Data motion count"),
                ("motion count", "Motion count"),
            ]
            for pair in pairs:
                try:
                    # get attribute value
                    val = mlg.attrs[pair[1]]

                    # condition value
                    if np.issubdtype(type(val), np.bytes_):
                        # - val is a np.bytes_ string
                        val = _bytes_to_str(val)

                    # assign val
                    ml["config"][pair[0]] = val
                except KeyError:
                    ml["config"][pair[0]] = None
                    warn_str = (
                        f"Motion list attribute '{pair[1]}' not found for ML "
                        f"'{ml['name']}'"
                    )
                    warn(warn_str)

            # -- check 'delta' --
            try:
                val = np.array([mlg.attrs["Delta x"], mlg.attrs["Delta y"], 0.0])
                ml["config"]["delta"] = val
            except KeyError:
                ml["config"]["delta"] = np.array([None, None, None])
                warn_str = (
                    f"Motion list attributes 'Delta x' and/or 'Delta y' not "
                    f"found for ML '{ml['name']}'"
                )
                warn(warn_str)

            # -- check 'center' --
            try:
                val = np.array(
                    [mlg.attrs["Grid center x"], mlg.attrs["Grid center y"], 0.0]
                )
                ml["config"]["center"] = val
            except KeyError:
                ml["config"]["center"] = np.array([None, None, None])
                warn_str = (
                    f"Motion list attributes 'Grid center x' and/or 'Grid "
                    f"center y' not found for ML '{ml['name']}'"
                )
                warn(warn_str)

            # -- check 'npoints' --
            try:
                val = np.array([mlg.attrs["Nx"], mlg.attrs["Ny"], 1])
                ml["config"]["npoints"] = val
            except KeyError:
                ml["config"]["npoints"] = np.array([None, None, None])
                warn_str = (
                    f"Motion list attributes 'Nx' and/or 'Ny' not found "
                    f"for ML '{ml['name']}'"
                )
                warn(warn_str)

            # return
            return ml
        else:
            # not a motion list
            return {}

    def _analyze_probelist(self, gname: str) -> dict:
        """
        Determines if `gname` matches the RE for a probe list group
        name.  If yes, then it gathers the probe info.

        :param str gname: name of potential probe list group
        :return: dictionary with `'probe-id'` and `'config'` keys
        """
        # Define RE pattern
        # - A probe list group follows the naming scheme of:
        #
        #     'Probe: XY[<RNUM>]: <NAME>'
        #
        #   where <RNUM> is the receptacle number and <NAME> is the
        #   probe name
        #
        _pattern = r"(\bProbe:\sXY\[)(?P<RNUM>\b\d+\b)(\]:\s)(?P<NAME>.+\b)"

        # match _pattern against gname
        _match = re.fullmatch(_pattern, gname)

        # gather pl info
        # - Note: a missing HDF5 attribute will not cause the mapping to
        #         fail, the associated mapping item will be given an
        #         appropriate None vale
        #
        if _match is not None:
            # define probe list dict
            probe_name = _match.group("NAME")
            receptacle_str = _match.group("RNUM")
            pl = {"probe-id": f"{probe_name} - {receptacle_str}", "config": {}}

            # get pl group
            plg = self.group[gname]

            # gather pl info
            # -- define 'group name', 'group path', and 'probe name' --
            pl["config"]["group name"] = gname
            pl["config"]["group path"] = plg.name
            pl["config"]["probe name"] = probe_name

            # -- check PL name --
            try:
                # get value
                pl_name = plg.attrs["Probe"]
                if np.issubdtype(type(pl_name), np.bytes_):
                    # decode to 'utf-8'
                    pl_name = _bytes_to_str(pl_name)

                # check against discovered probe name
                if probe_name != pl_name:
                    warn(
                        f"{pl['config']['group name']} Discovered probe list name "
                        f"'{probe_name}' does not match the name defined in "
                        f"attributes '{pl_name}', using discovered name."
                    )
            except KeyError:
                warn_str = (
                    f"{pl['config']['group name']}: Probe list attribute 'Probe' "
                    f"not found"
                )
                warn(warn_str)

            # -- check receptacle number --
            try:
                # define receptacle number
                pl["config"]["receptacle"] = int(_match.group("RNUM"))

                # get value
                rnum = plg.attrs["Receptacle"]

                # check against discovered receptacle number
                if pl["config"]["receptacle"] != rnum:
                    warn_str = (
                        f"{pl['config']['group name']}: Discovered receptacle "
                        f"number '{pl['config']['receptacle']}' does not match "
                        f"the number defined in attributes '{rnum}', using "
                        f"discovered name."
                    )
                    warn(warn_str)
            except KeyError:
                warn_str = (
                    f"{pl['config']['group name']}: Probe list attribute 'Receptacle' "
                    f"not found"
                )
                warn(warn_str)

            # -- check pairs --
            pairs = [
                ("calib", "Calibration"),
                ("level sy (cm)", "Level sy (cm)"),
                ("port", "Port"),
                ("probe channels", "Probe channels"),
                ("probe type", "Probe type"),
                ("unnamed", "Unnamed"),
                ("sx at end (cm)", "sx at end (cm)"),
                ("z", "z"),
            ]
            for pair in pairs:
                try:
                    # get value
                    val = plg.attrs[pair[1]]

                    # condition value
                    if np.issubdtype(type(val), np.bytes_):
                        # - val is a np.bytes_ string
                        val = _bytes_to_str(val)

                    # assign val
                    pl["config"][pair[0]] = val
                except KeyError:
                    pl["config"][pair[0]] = None
                    warn_str = (
                        f"{pl['config']['group name']}: attribute '{pair[1]}' "
                        f"not found"
                    )
                    warn(warn_str)

            # return
            return pl
        else:
            # not a probe list
            return {}
