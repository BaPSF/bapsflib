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

from warnings import warn

from bapsflib.utils import _bytes_to_str


class FauxN5700PS(h5py.Group):
    """
    Creates a Faux 'N57700_PS' Group in a HDF5 file
    """

    class _knobs(object):
        """
        A class that contains all the controls for specifying the
        group structure.
        """

        def __init__(self, val):
            super().__init__()
            self._faux = val

        @property
        def n_configs(self):
            """Number of configurations"""
            return self._faux._n_configs

        @n_configs.setter
        def n_configs(self, val: int):
            """Set number of configurations"""
            if val >= 1 and isinstance(val, int):
                if val != self._faux._n_configs:
                    self._faux._n_configs = val
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
            if isinstance(val, int) and val >= 1:
                if val != self._faux._sn_size:
                    self._faux._sn_size = val
                    self._faux._update()
            else:
                warn("`val` not valid, no update performed")

        def reset(self):
            """Reset 'N5700_PS' group to defaults."""
            self._faux._n_configs = 1
            self._faux._sn_size = 100
            self._faux._update()

    def __init__(self, id, n_configs=1, sn_size=100, **kwargs):
        # ensure id is for a HDF5 group
        if not isinstance(id, h5py.h5g.GroupID):
            raise ValueError(f"{id} is not a GroupID")

        # create control group
        gid = h5py.h5g.create(id, b"N5700_PS")
        h5py.Group.__init__(self, gid)

        # store number on configurations
        self._n_configs = n_configs

        # define number of shot numbers
        self._sn_size = sn_size

        # build control device sub-groups, datasets, and attributes
        self._update()

    @property
    def knobs(self):
        """Knobs for controlling structure of control device group"""
        return self._knobs(self)

    @property
    def config_names(self):
        """list of configuration names"""
        return list(self._configs)

    def _update(self):
        """
        Updates control group structure (Groups, Datasets, and
        Attributes)
        """
        # clear group before rebuild
        self.clear()

        # set group attributes
        self._set_attrs()

        # re-initialize key dicts
        self._configs = {}

        # add configuration sub-groups
        for i in range(self._n_configs):
            config_name = f"config{i+1:02}"
            self._configs[config_name] = {}
            self.create_group(config_name)
            self._set_subgroup_attrs(config_name, i + 1)

        # add and populate dataset
        self.create_dataset(
            "Run time list",
            shape=(self._sn_size * self._n_configs,),
            dtype=np.dtype(
                [
                    ("Shot number", np.int32),
                    ("Configuration name", np.bytes_, 120),
                    ("Command index", np.int32),
                    ("Current", np.float64),
                    ("Voltage", np.float64),
                ]
            ),
        )
        dset = self["Run time list"]
        ci_list = ([0] * 5) + ([1] * 5) + ([2] * 5)
        ci_list = ci_list * int(math.ceil(self._sn_size / 15))
        ci_list = ci_list[: self._sn_size :]
        ci_list[-1] = 3
        # for i, config in enumerate(self._config_names):
        for i, config in enumerate(self._configs):
            # add dataset name to configs
            self._configs[config]["dset name"] = "Run time list"

            # fill dataset
            dset[i :: self._n_configs, "Shot number"] = (
                np.arange(self._sn_size, dtype=np.int32) + 1
            )
            dset[i :: self._n_configs, "Configuration name"] = config.encode()
            dset[i :: self._n_configs, "Command index"] = np.array(ci_list)
            ci_list.reverse()

    def _set_attrs(self):
        """
        Set attributes for control group
        """
        self.attrs.update(
            {
                "Created date": np.bytes_("12/3/2008 10:47:20 AM"),
                "Description": np.bytes_(
                    "Agilent Technologies\n"
                    "System DC power supply\n"
                    "Series N5700\n\n"
                    "Programmable Power Supply over Ethernet\n\n"
                    "Most-recent hardware manual is available online at\n"
                    "http://www.agilent.com/find/N5700\n\n"
                    "Original module development for DAQ system by Steve "
                    "Vincena, November 2008\n"
                    "using model N5751A, 300V, 2.5A supply."
                ),
                "Device name": np.bytes_("N5700_PS"),
                "Module IP address": np.bytes_("192.168.7.3"),
                "Module VI path": np.bytes_("Modules/N5700_PS/N5700_PS.vi"),
                "Type": np.bytes_("Experiment control"),
            }
        )

    def _set_subgroup_attrs(self, config_name, config_number):
        """
        Sets attributes for the control sub-groups
        """
        self[config_name].attrs.update(
            {
                "IP address": np.bytes_(f"192.168.7.{config_number}"),
                "Initialization commands": np.bytes_(
                    "*RST;*WAI;OUTPUT ON;VOLTAGE 0.0;CURRENT 1.0"
                ),
                "Model Number": np.bytes_("N5751A"),
                "N5700 power supply command list": np.bytes_(
                    "SOURCE:VOLTAGE:LEVEL 20.0000000 \n"
                    "SOURCE:VOLTAGE:LEVEL 30.0000000 \n"
                    "SOURCE:VOLTAGE:LEVEL 40.0000000 \n"
                    "SOURCE:VOLTAGE:LEVEL 5.0000000 \n"
                ),
            }
        )

        # add command list to _configs
        cl = self[config_name].attrs["N5700 power supply command list"]
        cl = _bytes_to_str(cl).splitlines()
        cl = [command.strip() for command in cl]
        self._configs[config_name]["command list"] = cl
