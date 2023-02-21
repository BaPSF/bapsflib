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
import math
import numpy as np
import platform
import random

from datetime import datetime as dt
from warnings import warn


# noinspection PyPep8Naming
class FauxSixK(h5py.Group):
    """
    Creates a Faux '6K Compumotor' Group in a HDF5 file.
    """

    _MAX_CONFIGS = 4

    # noinspection PyProtectedMember
    class _knobs(object):
        """
        A class that contains all the controls for specifying the
        digitizer group structure.
        """

        def __init__(self, val):
            super().__init__()
            self._faux = val

        @property
        def n_configs(self):
            """Number of 6K configurations"""
            return self._faux._n_configs

        @n_configs.setter
        def n_configs(self, val: int):
            """Set number of 6K configurations"""
            if 1 <= val <= self._faux._MAX_CONFIGS and isinstance(val, int):
                if val != self._faux._n_configs:
                    self._faux._n_configs = val
                    self._faux._n_probes = self._faux._n_configs
                    if val > 1:
                        self._faux._n_motionlists = 1
                    self._faux._update()
            else:
                warn("`val` not valid, no update performed")

        @property
        def n_motionlists(self):
            """
            Number of motion lists used. Will always be one unless
            :code:`n_configs == 1` and then :code:`n_motionlists >= 1`
            """
            return self._faux._n_motionlists

        @n_motionlists.setter
        def n_motionlists(self, val):
            """Setter for n_motionlists"""
            if val >= 1 and isinstance(val, int):
                if val != self._faux._n_motionlists and self._faux._n_configs == 1:
                    self._faux._n_motionlists = val
                    self._faux._update()
            else:
                warn("`val` not valid, no update performed")

        @property
        def sn_size(self):
            """Number of shot numbers in dataset"""
            return self._faux._sn_size

        @sn_size.setter
        def sn_size(self, val):
            """Set the number of shot numbers in the dataset"""
            if val >= 1 and isinstance(val, int):
                if val != self._faux._sn_size:
                    self._faux._sn_size = val
                    self._faux._update()
            else:
                warn("`val` not valid, no update performed")

        def reset(self):
            """Reset '6K Compumotor' group to defaults."""
            self._faux._n_configs = 1
            self._faux._n_probes = 1
            self._faux._n_motionlists = 1
            self._faux._sn_size = 100
            self._faux._update()

    def __init__(self, id, n_configs=1, n_motionlists=1, sn_size=100, **kwargs):
        # ensure id is for a HDF5 group
        if not isinstance(id, h5py.h5g.GroupID):
            raise ValueError(f"{id} is not a GroupID")

        # create control group
        gid = h5py.h5g.create(id, b"6K Compumotor")
        h5py.Group.__init__(self, gid)

        # store number on configurations
        self._n_configs = n_configs
        self._n_probes = n_configs
        self._n_motionlists = n_motionlists if n_configs == 1 else 1

        # define number of shot numbers
        self._sn_size = sn_size

        # set root attributes
        self._set_6K_attrs()

        # build control device sub-groups, datasets, and attributes
        self._update()

    @property
    def knobs(self):
        """Knobs for controlling structure of control device group"""
        return self._knobs(self)

    @property
    def n_probes(self):
        """Number of probes drives used"""
        return self._n_probes

    @property
    def config_names(self):
        """list of configuration names"""
        return tuple(self._configs)

    def _update(self):
        """
        Updates control group structure (Groups, Datasets, and
        Attributes)
        """
        # clear group before rebuild
        self.clear()

        # re-initialize key lists
        # self._config_names = []
        self._probe_names = []
        self._motionlist_names = []

        # re-initialize key dicts
        self._configs = {}

        # add sub-groups
        self._add_probe_groups()
        self._add_motionlist_groups()

        # add datasets
        self._add_datasets()

    def _set_6K_attrs(self):
        """Sets the '6K Compumotor' group attributes"""
        self.attrs.update(
            {
                "Created date": np.bytes_("5/21/2004 4:09:05 PM"),
                "Description": np.bytes_(
                    "Controls XY probe drives using the 6K "
                    "Compumotor motor controller."
                ),
                "Device name": np.bytes_("6K Compumotor"),
                "Module IP address": np.bytes_("192.168.7.6"),
                "Module VI path": np.bytes_(
                    "C:\\ACQ II home\\Modules\\XY probe drive\\XY probe drive.vi"
                ),
                "Type": np.bytes_("Motion"),
            }
        )

    def _add_probe_groups(self):
        """Adds all probe groups"""
        # - define probe names
        # - define receptacle number
        # - define configuration name
        # - create probe groups and sub-groups
        # - define probe group attributes
        for i in range(self._n_configs):
            # define probe name
            pname = f"probe{i+1:02}"
            self._probe_names.append(pname)

            # define receptacle number
            if self._n_configs == 1:
                receptacle = random.randint(1, self._MAX_CONFIGS)
            else:
                receptacle = i + 1

            # create probe group
            probe_gname = f"Probe: XY[{receptacle}]: {pname}"
            self.create_group(probe_gname)
            self.create_group(f"{probe_gname}/Axes[0]")
            self.create_group(f"{probe_gname}/Axes[1]")

            # set probe group attributes
            self[probe_gname].attrs.update(
                {
                    "Calibration": np.bytes_("2004-06-04 0.375 inch calibration"),
                    "Level sy (cm)": np.float64(70.46),
                    "Port": np.uint8(27),
                    "Probe": np.bytes_(pname),
                    "Probe channels": np.bytes_(""),
                    "Probe type": np.bytes_("LaPD probe"),
                    "Receptacle": np.int8(receptacle),
                    "Unnamed": np.bytes_("lower East"),
                    "sx at end (cm)": np.float64(112.01),
                    "z": np.float64(830.699999),
                }
            )

            # add attributes to Axes[0] group
            self[f"{probe_gname}/Axes[0]"].attrs.update(
                {
                    "6K #": np.uint8(1),
                    "Axis": np.uint8((2 * (receptacle - 1)) + 1),
                    "Id": np.uint8(receptacle),
                }
            )

            # add attributes to Axes[1] group
            self[f"{probe_gname}/Axes[1]"].attrs.update(
                {
                    "6K #": np.uint8(1),
                    "Axis": np.uint8((2 * (receptacle - 1)) + 2),
                    "Id": np.uint8(receptacle),
                }
            )

            # fill configs dict
            self._configs[receptacle] = {
                "probe name": pname,
                "receptacle": receptacle,
                "motion lists": [],
            }

    # noinspection PyPep8Naming
    def _add_motionlist_groups(self):
        """Add motion list groups"""
        # determine possible data point arrangements for motion lists
        # 1. find divisible numbers of sn_size
        # 2. find (Nx, Ny) combos for each dataset
        sn_size_for_ml = []
        NN = []
        if self._n_motionlists == 1:
            # set shot number size per for each motion list
            sn_size_for_ml.append(self._sn_size)

            # find divisible numbers
            sn_div = []
            for j in range(sn_size_for_ml[0]):
                if sn_size_for_ml[0] % (j + 1) == 0:
                    sn_div.append(j + 1)

            # build [(Nx, Ny), ]
            sn_div_index = random.randint(0, len(sn_div) - 1)
            Nx = sn_div[sn_div_index]
            Ny = int(self._sn_size / Nx)
            NN.append((Nx, Ny))
        else:
            # set shot number size per for each motion list
            sn_per_ml = int(math.floor(self._sn_size / self._n_motionlists))
            sn_remainder = self._sn_size - ((self._n_motionlists - 1) * sn_per_ml)
            sn_size_for_ml.extend([sn_per_ml] * (self._n_motionlists - 1))
            sn_size_for_ml.append(sn_remainder)

            # build NN of each motion list
            for i in range(self._n_motionlists):
                # find divisible numbers
                sn_div = []
                for j in range(sn_size_for_ml[i]):
                    if sn_size_for_ml[i] % (j + 1) == 0:
                        sn_div.append(j + 1)

                # build (Nx, Ny)
                sn_div_index = random.randint(0, len(sn_div) - 1)
                Nx = sn_div[sn_div_index]
                Ny = int(sn_size_for_ml[i] / Nx)
                NN.append((Nx, Ny))

        # add motionlist sub-groups
        # - define motionlist names
        # - create motionlist group
        # - define motionlist group attributes
        for i in range(self._n_motionlists):
            # define motionlist name
            ml_name = f"ml-{i+1:04}"
            self._motionlist_names.append(ml_name)

            # create motionlist group
            ml_gname = f"Motion list: {ml_name}"
            self.create_group(ml_gname)

            # set motionlist attributes
            time_format = "%-m/%-d/%Y %-I:%M:%S %p"
            if platform.system() == "Windows":
                time_format = time_format.replace("-", "#")
            timestamp = dt.now().strftime(time_format)
            self[ml_gname].attrs.update(
                {
                    "Created date": np.bytes_(timestamp),
                    "Data motion count": np.uint32(sn_size_for_ml[i]),
                    "Delta x": np.float64(1.0),
                    "Delta y": np.float64(1.0),
                    "Grid center x": np.float64(0.0),
                    "Grid center y": np.float64(0.0),
                    "Motion count": np.uint32(sn_size_for_ml[i] + NN[i][1]),
                    "Motion list": np.bytes_(ml_name),
                    "Nx": np.uint32(NN[i][0]),
                    "Ny": np.uint32(NN[i][1]),
                }
            )

        # fill configs dict
        if self._n_motionlists == 1:
            # same ml for all configs
            for config_name in self._configs:
                self._configs[config_name]["motion lists"].append(
                    self._motionlist_names[0]
                )
        else:
            # there's one config and all ml's are in it
            for config_name in self._configs:
                self._configs[config_name]["motion lists"] = self._motionlist_names

    def _add_datasets(self):
        """Create datasets for each configurations"""
        # TODO: fill data fields 'x', 'y', 'z', 'theta', 'phi'
        shape = (self._sn_size,)
        dtype = np.dtype(
            [
                ("Shot number", np.int32),
                ("x", np.float64),
                ("y", np.float64),
                ("z", np.float64),
                ("theta", np.float64),
                ("phi", np.float64),
                ("Motion list", np.bytes_, 120),
                ("Probe name", np.bytes_, 120),
            ]
        )

        # create numpy array
        data = np.ndarray(shape=shape, dtype=dtype)

        # assign universal data
        data["Shot number"] = np.arange(
            1, shape[0] + 1, 1, dtype=data["Shot number"].dtype
        )

        # create dataset
        for cname in self._configs:
            # construct dataset name
            dset_name = (
                f"XY[{self._configs[cname]['receptacle']}]: "
                f"{self._configs[cname]['probe name']}"
            )
            self._configs[cname]["dset name"] = dset_name

            # fill motion list name
            if self._n_motionlists == 1:
                data["Motion list"] = self._motionlist_names[0]
            else:
                start = 0
                for ml in self._motionlist_names:
                    ml_gname = f"Motion list: {ml}"
                    ml_sn_size = self[ml_gname].attrs["Data motion count"]
                    stop = start + ml_sn_size
                    data["Motion list"][start:stop:] = ml

                    # move start
                    start = stop

            # fill 'Probe name' field
            data["Probe name"] = dset_name.encode()

            # fill remaining fields
            # TODO: need to connect this to motion lists
            #
            data["x"].fill(0.0)
            data["y"].fill(0.0)
            data["z"].fill(0.0)
            data["theta"].fill(0.0)
            data["phi"].fill(0.0)

            # create dataset
            self.create_dataset(dset_name, data=data)
