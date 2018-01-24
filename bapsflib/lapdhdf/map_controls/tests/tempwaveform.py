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


class TemporaryWaveform(h5py.File):
    """
    A Temporary HDF5 file with Waveform control group.
    """
    def __init__(self, n_configs, suffix='.hdf5', prefix='', dir=None):
        # Create Temporary HDF5 File
        self.tempdir = tempfile.TemporaryDirectory(prefix='hdf-test_')\
            if dir is None else None
        self.tempfile = \
            tempfile.NamedTemporaryFile(suffix=suffix,
                                        prefix=prefix,
                                        dir=self.tempdir.name,
                                        delete=False)
        h5py.File.__init__(self, self.tempfile.name, 'w')

        # store number on configurations
        self._n_configs = n_configs

        # add data and waveform groups
        self.create_group('/Raw data + config/Waveform')
        self._wgroup = self['Raw data + config/Waveform']

        # add config subgroups
        self._config_names = []
        for i in range(n_configs):
            config_name = 'config{:02}'.format(n_configs)
            self._config_names.append(config_name)
            self._wgroup.create_group(config_name)

        # add dataset

    @property
    def n_configs(self):
        """Number of waveform configurations"""
        return self._n_configs

    @n_configs.setter
    def n_configs(self, val):
        """Set number of wavefrom configurations"""
        if val != self._n_configs:
            self._n_configs = val
            self._update_waverform()

    def _update_waverform(self):
        """Updates Groups, Datasets, and Attributes"""
        #

    def _set_attrs(self):
        self._wgroup.attrs.update({
            'IP address': b'192.168.1.1',
            'Generator type': b''
        })


