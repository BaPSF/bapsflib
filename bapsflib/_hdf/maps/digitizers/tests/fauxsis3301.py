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
import numpy as np

from typing import Iterable
from warnings import warn


class FauxSIS3301(h5py.Group):
    """
    Creates a Faux 'SIS 3301' Group in a HDF5 file.
    """

    # noinspection SpellCheckingInspection,PyProtectedMember
    class _knobs(object):
        """
        A class that contains all the controls for specifying the
        digitizer group structure.
        """

        def __init__(self, val):
            super().__init__()
            self._faux = val

        @property
        def active_brdch(self):
            """
            Boolean numpy array of active board, channel combinations.
            Shape = (13, 8) 13 boards and 8 channels
            """
            return self._faux._active_brdch.copy()

        @active_brdch.setter
        def active_brdch(self, val):
            """
            Set the active board, channel combinations
            """
            if isinstance(val, np.ndarray):
                if (
                    val.shape == (13, 8)
                    and np.issubdtype(val.dtype, bool)
                    and np.any(val)
                ):
                    self._faux._active_brdch = val
                    self._faux._update()
                else:
                    warn("`val` not valid, no update performed")
            else:
                warn("`val` not valid, no update performed")

        @property
        def active_config(self):
            """current active configuration"""
            return self._faux._active_config

        @active_config.setter
        def active_config(self, val):
            if not isinstance(val, Iterable) or isinstance(val, str):
                val = (val,)
            elif isinstance(val, tuple):
                pass
            else:
                val = tuple(val)

            # if val in self._faux._config_names:
            if all(cname in self._faux._config_names for cname in val):
                if val != self._faux._active_config:
                    self._faux._active_config = val
                    self._faux._update()
            else:
                warn("`val` not valid, no update performed")

        @property
        def n_configs(self):
            """Number of SIS 3301 configurations"""
            return self._faux._n_configs

        @n_configs.setter
        def n_configs(self, val):
            """Set number of waveform configurations"""
            if val >= 1 and isinstance(val, int):
                if val != self._faux._n_configs:
                    self._faux._n_configs = val
                    self._faux._update()
            else:
                warn("`val` not valid, no update performed")

        @property
        def nt(self):
            """Number of temporal samples"""
            return self._faux._nt

        @nt.setter
        def nt(self, val):
            """Set the number of temporal samples"""
            if isinstance(val, int):
                if val != self._faux._nt:
                    self._faux._nt = val
                    self._faux._update()
            else:
                warn("`val` not valid, no update performed")

        @property
        def sn_size(self):
            """Number of shot numbers in a dataset"""
            return self._faux._sn_size

        @sn_size.setter
        def sn_size(self, val):
            """Set the number of shot numbers in a dataset"""
            if isinstance(val, int) and val >= 1:
                if val != self._faux._sn_size:
                    self._faux._sn_size = val
                    self._faux._update()
            else:
                warn("`val` not valid, no update performed")

        def reset(self):
            """Reset 'SIS 3301' group to defaults."""
            self._faux._default_setup()
            self._faux._update()

    def __init__(self, id, n_configs=1, sn_size=100, nt=10000, **kwargs):
        # ensure id is for a HDF5 group
        if not isinstance(id, h5py.h5g.GroupID):
            raise ValueError(f"{id} is not a GroupID")

        # create control group
        # noinspection PyUnresolvedReferences
        gid = h5py.h5g.create(id, b"SIS 3301")
        h5py.Group.__init__(self, gid)

        # define key values
        self._default_setup()
        if n_configs != self._n_configs:
            self._n_configs = n_configs
        if sn_size != self._sn_size:
            self._sn_size = sn_size
        if nt != self._nt:
            self._nt = nt

        # set root attributes
        self._set_sis3301_attrs()

        # build control device sub-groups, datasets, and attributes
        self._update()

    @property
    def knobs(self):
        """Knobs for controlling structure of digitizer group"""
        return self._knobs(self)

    @property
    def config_names(self):
        """list of 'SIS 3301' configuration names"""
        return self._config_names.copy()

    def _default_setup(self):
        """Set group setup parameters to defaults"""
        self._n_configs = 1
        self._sn_size = 100
        self._nt = 10000
        self._active_brdch = np.zeros((13, 8), dtype=bool)
        self._active_brdch[0][0] = True
        self._config_names = []
        self._active_config = ("config01",)

    def _set_sis3301_attrs(self):
        """Sets the 'SIS 3301' group attributes"""
        self.attrs.update(
            {
                "Created date": np.bytes_("5/21/2004 4:09:05 PM"),
                "Description": np.bytes_(
                    "Struck Innovative Systeme 3301 8 channel ADC boards, "
                    "100 MHz.  Also provides access to SIS 3820 VME clock "
                    "distribute."
                ),
                "Device name": np.bytes_("SIS 3301"),
                "Module IP address": np.bytes_("192.168.7.3"),
                "Module VI path": np.bytes_(
                    "C:\ACQ II home\Modules\SIS 3301\SIS 3301.vi"
                ),
                "Type": np.bytes_("Data acquisition"),
            }
        )

    def _update(self):
        """
        Updates digitizer group structure (Groups, Datasets, and
        Attributes)
        """
        # clear group before rebuild
        self.clear()

        # build configuration groups
        self._config_names = []
        for i in range(self._n_configs):
            config_name = f"config{i+1:02}"
            self._config_names.append(config_name)
            self._build_config_group(config_name)

        # reset active configuration if necessary
        if not all(cname in self._config_names for cname in self._active_config):
            self._active_config = (self._config_names[0],)

        # build datasets
        self._build_datasets()

    def _build_config_group(self, config_name: str):
        """
        Creates and populates the digitizer configuration group.

        :param config_name: name of digitizer configuration
        """
        # create configuration group
        gname = f"Configuration: {config_name}"
        self.create_group(gname)

        # set attributes for configuration group
        # TODO: allow setting of sample averaging
        # TODO: allow setting of shot averaging
        self[gname].attrs.update(
            {
                "Clock rate": np.bytes_("Internal 100 MHz"),
                "Configuration": np.bytes_(config_name),
                "Samples to average": np.bytes_("No averaging"),
                "Shots to average": np.int16(1),
                "Software start": np.bytes_("TRUE"),
                "Stop delay": np.uint16(0),
                "Trigger mode": np.bytes_("Start/stop"),
            }
        )

        # create and build Board[] and Channels[] sub-groups
        brd_count = 0
        brd_bool_arr = np.any(self._active_brdch, axis=1)
        brd_index = np.where(brd_bool_arr)[0]
        for brd in brd_index:
            # create Board[] group
            brd_name = f"Boards[{brd_count}]"
            brd_path = f"{gname}/{brd_name}"
            self[gname].create_group(brd_name)
            brd_count += 1

            # define Board[] attrs
            self[brd_path].attrs.update(
                {
                    "Board": np.uint32(brd),
                    "Board samples": np.uint32(self._nt),
                }
            )

            # build Channels[] groups
            ch_index = np.where(self._active_brdch[brd])[0]
            ch_count = 0
            for ch in ch_index:
                # create Channels[] group
                ch_name = f"Channels[{ch_count}]"
                ch_path = f"{brd_path}/{ch_name}"
                self[brd_path].create_group(ch_name)
                ch_count += 1

                # define Channels[] attrs
                self[ch_path].attrs.update(
                    {
                        "Board": np.uint32(brd),
                        "Channel": np.uint32(ch),
                        "DC offset (mV)": np.float64(0.0),
                        "Data type": np.bytes_("signal type info"),
                    }
                )

    def _build_datasets(self):
        brds, chs = np.where(self._active_brdch)
        for i in range(brds.size):
            brd = brds[i]
            ch = chs[i]

            # create and populate datasets
            for cname in self._active_config:
                # create "main" data set
                # dset_name = (self._active_config
                #              + ' [{}:{}]'.format(brd, ch))
                dset_name = f"{cname} [{brd}:{ch}]"
                shape = (self._sn_size, self._nt)
                data = np.empty(shape=shape, dtype=np.int16)
                self.create_dataset(dset_name, data=data)

                # create & populate header dataset
                dheader_name = f"{dset_name} headers"
                shape = (self._sn_size,)
                dtype = np.dtype(
                    [
                        ("Shot", np.uint32),
                        ("Scale", np.float64),
                        ("Offset", np.float64),
                        ("Min", np.int16),
                        ("Max", np.int16),
                        ("Clipped", np.uint8),
                    ]
                )
                dheader = np.empty(shape=shape, dtype=dtype)
                dheader["Shot"] = np.arange(
                    1, shape[0] + 1, 1, dtype=dheader["Shot"].dtype
                )
                dheader["Scale"] = 3.051944077014923e-4
                dheader["Offset"] = -2.5
                dheader["Min"] = data.min(axis=1)
                dheader["Max"] = data.max(axis=1)
                dheader["Clipped"] = 0
                self.create_dataset(dheader_name, data=dheader)
