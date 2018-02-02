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
import random
import math
import numpy as np

from datetime import datetime as dt


class FauxSixK(h5py.Group):
    """
    Creates a Faux '6K Compumotor' Group in a HDF5 file.
    """
    _MAX_CONFIGS = 4

    def __init__(self, id, n_configs=1, n_motionlists=1,
                 sn_size=100, **kwargs):
        # ensure id is for a HDF5 group
        if not isinstance(id, h5py.h5g.GroupID):
            raise ValueError('{} is not a GroupID'.format(id))

        # create control group
        gid = h5py.h5g.create(id, b'6K Compumotor')
        h5py.Group.__init__(self, gid)

        # store number on configurations
        self._n_configs = n_configs
        self._n_probes = n_configs
        self._n_motionlists = n_motionlists if n_configs == 1 else 1

        # define number of shot numbers
        self._sn_size = sn_size

        # build control device sub-groups, datasets, and attributes
        self._update()

    @property
    def n_configs(self):
        """Number of waveform configurations"""
        return self._n_configs

    @n_configs.setter
    def n_configs(self, val: int):
        """Set number of waveform configurations"""
        if val != self._n_configs and 1 <= val <= self._MAX_CONFIGS:
            self._n_configs = val
            self._n_probes = self._n_configs
            if val > 1:
                self._n_motionlists = 1
            self._update()

    @property
    def n_motionlists(self):
        return self._n_motionlists

    @n_motionlists.setter
    def n_motionlists(self, val: int):
        if val != self._n_motionlists and self.n_configs == 1:
            self._n_motionlists = val
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
        # clear group before rebuild
        self.clear()

        self._config_names = []
        self._probe_names = []
        self._motionlist_names = []

        # add probe sub-groups
        # - define probe names
        # - receptacle number
        # - configuration name
        # - create probe groups and sub-groups
        # - define probe group attributes
        for i in range(self.n_configs):
            # define probe name
            pname = 'probe{:02}'.format(i + 1)
            self._probe_names.append(pname)

            # define receptacle number
            if self.n_configs == 1:
                receptacle = random.randint(1, self._MAX_CONFIGS)
            else:
                receptacle = i + 1

            # gather configuration names
            self._config_names.append(receptacle)

            # create probe group
            probe_gname = 'Probe: XY[{}]: '.format(receptacle) + pname
            self.create_group(probe_gname)
            self.create_group(probe_gname + '/Axes[0]')
            self.create_group(probe_gname + '/Axes[1]')

            # set probe group attributes
            self[probe_gname].attrs.update({
                'Port': -99999,
                'Probe': pname.encode(),
                'Probe type': b'LaPD probe',
                'Receptacle': receptacle
            })

        # add motionlist sub-groups
        # - define motionlist names
        # - create motionlist group
        # - define motionlist group attributes
        for i in range(self.n_motionlists):
            # define motionlist name
            ml_name = 'ml-{:04}'.format(i+1)
            self._motionlist_names.append(ml_name)

            # create motionlist group
            ml_gname = 'Motion list: ' + ml_name
            self.create_group(ml_gname)

            # find divisible numbers of sn_size
            sn_div = []
            for j in range(self.sn_size):
                if self.sn_size % (j + 1) == 0:
                    sn_div.append(j + 1)

            # set motionlist attributes
            sn_div_index = random.randint(0, len(sn_div) - 1)
            Nx = sn_div[sn_div_index]
            Ny = int( self.sn_size / Nx)
            timestamp = dt.now().strftime('%-m/%-d/%Y %-I:%M:%S %p')
            self[ml_gname].attrs.update({
                'Created date': timestamp.encode(),
                'Grid center x': 0.0,
                'Grid cneter y': 0.0,
                'Delta x': 1.0,
                'Delta y': 1.0,
                'Nx': Nx,
                'Ny': Ny,
                'Motion list': ml_name.encode(),
                'Data motion count': Nx * Ny,
                'Motion count': -99999
            })

            # TODO: CREATE DATASET
