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


class FauxSixK(h5py.Group):
    """
    Creates a Faux '6K Compumotor' Group in a HDF5 file.
    """
    def __init__(self, id, n_configs=1, sn_size=100, **kwargs):
        # ensure id is for a HDF5 group
        if not isinstance(id, h5py.h5g.GroupID):
            raise ValueError('{} is not a GroupID'.format(id))

        # create control group
        gid = h5py.h5g.create(id, b'6K Compumotor')
        h5py.Group.__init__(self, gid)

        # store number on configurations
        self._n_configs = n_configs

        # define number of shot numbers
        self._sn_size = sn_size

        # build control device sub-groups, datasets, and attributes
        self._update()

    @property
    def n_configs(self):
        """Number of waveform configurations"""
        return self._n_configs

    @n_configs.setter
    def n_configs(self, val):
        """Set number of waveform configurations"""
        if val != self._n_configs:
            self._n_configs = val
            self._update()

    @property
    def config_names(self):
        """list of waveform configuration names"""
        return self._config_names

    @property
    def sn_size(self):
        """Number of shot numbers in dataset"""
        return self._sn_size

    @sn_size.setter
    def sn_size(self, val):
        """Set the number of shot numbers in the dataset"""
        if val != self._sn_size:
            self._sn_size = val
            self._update()

    def _update(self):
        """
        Updates control group structure (Groups, Datasets, and
        Attributes)
        """
        self._config_names = []

    def _set_attrs(self):
        """Sets attributes for the control group and its sub-members"""
        pass
