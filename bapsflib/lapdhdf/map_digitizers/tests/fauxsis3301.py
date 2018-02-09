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
from warnings import warn


class FauxSIS3301(h5py.Group):
    """
    Creates a Faux 'SIS 3301' Group in a HDF5 file.
    """

    def __init__(self, id, n_configs=1, sn_size=100, nt=10000, **kwargs):
        # ensure id is for a HDF5 group
        if not isinstance(id, h5py.h5g.GroupID):
            raise ValueError('{} is not a GroupID'.format(id))

        # create control group
        gid = h5py.h5g.create(id, b'SIS 3301')
        h5py.Group.__init__(self, gid)

        # define key values
        self._n_configs = n_configs
        self._sn_size = sn_size
        self._nt = nt
        self._active_brdch = np.zeros((13, 8), dtype=bool)
        self._active_brdch[0][0] = True
        self._config_names = []
        self._active_config = 'config01'

        # set root attributes
        self._set_sis3301_attrs()

        # build control device sub-groups, datasets, and attributes
        self._update()

    @property
    def active_brdch(self):
        """
        Boolean numpy array of active board, channel combinations.
        Shape = (13, 8) 13 boards and 8 channels
        """
        return self._active_brdch.copy()

    @active_brdch.setter
    def active_brdch(self, val):
        """
        Set the active board, channel combinations
        """
        if isinstance(val, np.ndarray):
            if val.shape == self._active_brdch.shape \
                    and val.dtype == self._active_brdch.dtype:
                self._active_brdch = val
                self._update()
            else:
                warn('`val` not valid, no update performed')
        else:
            warn('`val` not valid, no update performed')

    @property
    def active_config(self):
        """current active configuration"""
        return self._active_config

    @active_config.setter
    def active_config(self, val):
        if val in self._config_names:
            if val != self._active_config:
                self._active_config = val
                self._update()
        else:
            warn('`val` not valid, no update performed')

    @property
    def config_names(self):
        """list of 'SIS 3301' configuration names"""
        return self._config_names.copy()

    @property
    def n_configs(self):
        """Number of SIS 3301 configurations"""
        return self._n_configs

    @n_configs.setter
    def n_configs(self, val):
        """Set number of waveform configurations"""
        if val >= 1 and isinstance(val, int):
            if val != self._n_configs:
                self._n_configs = val
                self._update()
        else:
            warn('`val` not valid, no update performed')

    @property
    def nt(self):
        """Number of temporal samples"""
        return self._nt

    @nt.setter
    def nt(self, val):
        """Set the number of temporal samples"""
        if isinstance(val, int):
            if val != self._nt:
                self._nt = val
                self._update()
        else:
            warn('`val` not valid, no update performed')

    @property
    def sn_size(self):
        """Number of shot numbers in a dataset"""
        return self._sn_size

    @sn_size.setter
    def sn_size(self, val):
        """Set the number of shot numbers in a dataset"""
        if isinstance(val, int):
            if val != self._sn_size:
                self._sn_size = val
                self._update()
        else:
            warn('`val` not valid, no update performed')

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
            config_name = 'config{:02}'.format(i + 1)
            self._config_names.append(config_name)
            self._build_config_group(config_name)

        # reset active configuration if necessary
        if self._active_config not in self._config_names:
            self._active_config = self._config_names[0]

    def _build_config_group(self, config_name):
        # create configuration group
        gname = 'Configuration: ' + config_name
        self.create_group(gname)

        # set attributes for configuration group
        # TODO: allow setting of sample averaging
        # TODO: allow setting of shot averaging
        self[gname].attrs.update({
            'Clock rate': b'Internal 100 MHz',
            'Configuration': config_name.encode(),
            'Samples to average': 'No averaging',
            'Shots to average': 1,
            'Software start': b'TRUE',
            'Stop delay': 0,
            'Trigger mode': b'Start/stop'
        })

    def _set_sis3301_attrs(self):
        """Sets the 'SIS 3301' group attributes"""
        self.attrs.update({
            'Created date': b'5/21/2004 4:09:05 PM',
            'Description': b'Struck Innovative Systeme 3301 8 channel '
                           b'ADC boards, 100 MHz.  Also provides '
                           b'access to SIS 3820 VME clock distribute.',
            'Device name': b'SIS 3301',
            'Module IP address': b'192.168.7.3',
            'Module VI path': b'C:\\ACQ II home\\Modules\\SIS 3301\\'
                              b'SIS 3301.vi',
            'Type': b'Data acquisition'
        })
