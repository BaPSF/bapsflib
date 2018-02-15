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


class FauxWaveform(h5py.Group):
    """
    Creates a Faux 'Waveform' Group in a HDF5 file
    """
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
            """Number of waveform configurations"""
            return self._faux._n_configs

        @n_configs.setter
        def n_configs(self, val: int):
            """Set number of waveform configurations"""
            if val >= 1 and isinstance(val, int):
                if val != self._faux._n_configs:
                    self._faux._n_configs = val
                    self._faux._update()
            else:
                warn('`val` not valid, no update performed')

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
                warn('`val` not valid, no update performed')

    def __init__(self, id, n_configs=1, sn_size=100, **kwargs):
        # ensure id is for a HDF5 group
        if not isinstance(id, h5py.h5g.GroupID):
            raise ValueError('{} is not a GroupID'.format(id))

        # create control group
        gid = h5py.h5g.create(id, b'Waveform')
        h5py.Group.__init__(self, gid)

        # store number on configurations
        self._n_configs = n_configs

        # define number of shot numbers
        self._sn_size = sn_size

        # build control device sub-groups, datasets, and attributes
        self._update()

    @property
    def knobs(self):
        """Knobs for controlling structure of digitizer group"""
        return self._knobs(self)

    # @property
    # def n_configs(self):
    #     """Number of waveform configurations"""
    #     return self._n_configs

    # @n_configs.setter
    # def n_configs(self, val: int):
    #     """Set number of waveform configurations"""
    #     if val != self._n_configs and val >= 1:
    #         self._n_configs = val
    #         self._update()

    @property
    def config_names(self):
        """list of waveform configuration names"""
        return self._config_names

    # @property
    # def sn_size(self):
    #     """Number of shot numbers in dataset"""
    #     return self._sn_size

    # @sn_size.setter
    # def sn_size(self, val):
    #     """Set the number of shot numbers in the dataset"""
    #     if val != self._sn_size:
    #         self._sn_size = val
    #         self._update()

    def _update(self):
        """
        Updates control group structure (Groups, Datasets, and
        Attributes)
        """
        # clear group before rebuild
        self.clear()

        # add configuration sub-groups
        self._config_names = []
        for i in range(self._n_configs):
            config_name = 'config{:02}'.format(i + 1)
            self._config_names.append(config_name)
            self.create_group(config_name)
            self._set_attrs(config_name, i + 1)

        # add and populate dataset
        self.create_dataset(
            'Run time list', shape=(self._sn_size * self._n_configs,),
            dtype=[('Shot number', '<i4'),
                   ('Configuration name', 'S120'),
                   ('Command index', '<i4')])
        dset = self['Run time list']
        ci_list = ([0] * 5) + ([1] * 5) + ([2] * 5)
        ci_list = ci_list * int(math.ceil(self._sn_size / 15))
        ci_list = ci_list[:self._sn_size:]
        for i, config in enumerate(self._config_names):
            dset[i::self._n_configs, 'Shot number'] = \
                np.arange(self._sn_size, dtype='<i4') + 1
            dset[i::self._n_configs, 'Configuration name'] = \
                config.encode()
            dset[i::self._n_configs, 'Command index'] = np.array(ci_list)
            ci_list.reverse()

    def _set_attrs(self, config_name, config_number):
        """
        Sets attributes for the control group and its sub-members
        """
        self[config_name].attrs.update({
            'IP address': '192.168.1.{}'.format(config_number).encode(),
            'Generator type': b'Agilent 33220A - LAN',
            'Waveform command list': b'FREQ 40000.000000 \n'
                                     b'FREQ 80000.000000 \n'
                                     b'FREQ 120000.000000 \n'
        })
