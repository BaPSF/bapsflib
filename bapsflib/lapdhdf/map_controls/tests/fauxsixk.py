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
    def n_probes(self):
        return self._n_probes

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

        # re-initialize key lists
        self._config_names = []
        self._probe_names = []
        self._motionlist_names = []

        # set root attributes
        self._set_6K_attrs()

        # add sub-groups
        self._add_probe_groups()
        self._add_motionlist_groups()

        # TODO: CREATE DATASET

    def _set_6K_attrs(self):
        """Sets the '6K Compumotor' group attributes"""
        self.attrs.update({})
        pass

    def _add_probe_groups(self):
        """Adds all probe groups"""
        # - define probe names
        # - define receptacle number
        # - define configuration name
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

    def _add_motionlist_groups(self):
        """Add motion list groups"""
        # determine possible data point arrangements for motion lists
        # 1. find divisible numbers of sn_size
        # 2. find (Nx, Ny) combos for each dataset
        sn_size_for_ml = []
        NN = []
        if self.n_motionlists == 1:
            # set shot number size per for each motion list
            sn_size_for_ml.append(self.sn_size)

            # find divisible numbers
            sn_div = []
            for j in range(sn_size_for_ml[0]):
                if sn_size_for_ml[0] % (j + 1) == 0:
                    sn_div.append(j + 1)

            # build [(Nx, Ny), ]
            sn_div_index = random.randint(0, len(sn_div) - 1)
            Nx = sn_div[sn_div_index]
            Ny = int(self.sn_size / Nx)
            NN.append((Nx, Ny))
        else:
            # set shot number size per for each motion list
            sn_per_ml = int(math.floor(
                self.sn_size / self.n_motionlists))
            sn_remainder = (self.sn_size
                            - ((self.n_motionlists - 1) * sn_per_ml))
            sn_size_for_ml.extend([sn_per_ml]
                                  * (self.n_motionlists - 1))
            sn_size_for_ml.append(sn_remainder)

            # build NN of each motion list
            for i in range(self.n_motionlists):
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
        for i in range(self.n_motionlists):
            # define motionlist name
            ml_name = 'ml-{:04}'.format(i + 1)
            self._motionlist_names.append(ml_name)

            # create motionlist group
            ml_gname = 'Motion list: ' + ml_name
            self.create_group(ml_gname)

            # set motionlist attributes
            timestamp = dt.now().strftime('%-m/%-d/%Y %-I:%M:%S %p')
            self[ml_gname].attrs.update({
                'Created date': timestamp.encode(),
                'Grid center x': 0.0,
                'Grid cneter y': 0.0,
                'Delta x': 1.0,
                'Delta y': 1.0,
                'Nx': NN[i][0],
                'Ny': NN[i][1],
                'Motion list': ml_name.encode(),
                'Data motion count': sn_size_for_ml[i],
                'Motion count': -99999
            })

    def _add_dataset(self, dname):
        pass
