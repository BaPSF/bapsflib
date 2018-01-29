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
import tempfile
import h5py
import math
import numpy as np


class FauxWaveform(h5py.Group):
    """
    A Temporary HDF5 file with Waveform control group.
    """
    def __init__(self, id, n_configs=1, sn_size=100):
        # Create Temporary HDF5 File
        #tempdir = dir.name \
        #    if isinstance(dir, tempfile.TemporaryDirectory) else dir
        #self.tempfile = \
        #    tempfile.NamedTemporaryFile(suffix=suffix,
        #                                prefix=prefix,
        #                                dir=tempdir,
        #                                delete=False)
        #h5py.File.__init__(self, self.tempfile.name, 'w')

        # create waveform group
        if not isinstance(id, h5py.h5g.GroupID):
            raise ValueError('{} is not a GroupID'.format(id))

        gid = h5py.h5g.create(id, b'Waveform')
        # super().__init__()
        h5py.Group.__init__(self, gid)

        # store number on configurations
        self._n_configs = n_configs

        # define number of shotnumbers
        self._sn_size = sn_size

        # add data and waveform groups
        # self.create_group('/Raw data + config/Waveform')
        # self._wgroup = self['Raw data + config/Waveform']
        self._wgroup = self

        # build waveform groups, datasets, and attributes
        self._update_waverform()

    @property
    def n_configs(self):
        """Number of waveform configurations"""
        return self._n_configs

    @n_configs.setter
    def n_configs(self, val):
        """Set number of waveform configurations"""
        if val != self._n_configs:
            self._n_configs = val
            self._update_waverform()

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
            self._update_waverform()

    def _update_waverform(self):
        """Updates Groups, Datasets, and Attributes"""
        # waveform needs to be re-built...must clear group first
        self._wgroup.clear()

        # add configuration sub-groups
        self._config_names = []
        for i in range(self.n_configs):
            config_name = 'config{:02}'.format(i + 1)
            self._config_names.append(config_name)
            self._wgroup.create_group(config_name)
            self._set_attrs(config_name, i + 1)

        # add and populate dataset
        self._wgroup.create_dataset(
            'Run time list', shape=(self._sn_size * self.n_configs,),
            dtype=[('Shot number', '<i4'),
                   ('Configuration name', 'S120'),
                   ('Command index', '<i4')])
        dset = self._wgroup['Run time list']
        ci_list = ([0] * 5) + ([1] * 5) + ([2] * 5)
        ci_list = ci_list * int(math.ceil(self._sn_size / 15))
        ci_list = ci_list[:self._sn_size:]
        for i, config in enumerate(self._config_names):
            dset[i::self.n_configs, 'Shot number'] = \
                np.arange(self._sn_size, dtype='<i4') + 1
            dset[i::self.n_configs, 'Configuration name'] = \
                config.encode()
            dset[i::self.n_configs, 'Command index'] = np.array(ci_list)
            ci_list.reverse()

    def _set_attrs(self, config_name, config_number):
        self._wgroup[config_name].attrs.update({
            'IP address': '192.168.1.{}'.format(config_number).encode(),
            'Generator type': b'Agilent 33220A - LAN',
            'Waveform command list': b'FREQ 40000.000000 \n'
                                     b'FREQ 80000.000000 \n'
                                     b'FREQ 120000.000000 \n'
        })


