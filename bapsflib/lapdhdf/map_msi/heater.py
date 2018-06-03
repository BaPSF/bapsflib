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

from .msi_template import hdfMap_msi_template


class hdfMap_msi_heater(hdfMap_msi_template):
    """
    Mapping class for the 'Heater' MSI diagnostic.

    Simple group structure looks like:

    .. code-block:: none

        +-- Heater
        |   +-- Heater summary

    """
    def __init__(self, diag_group):
        """
        :param diag_group: the HDF5 MSI diagnostic group
        :type diag_group: :class:`h5py.Group`
        """
        # initialize
        hdfMap_msi_template.__init__(self, diag_group)

        # populate self.configs
        self._build_configs()

    def _build_configs(self):
        """Builds the :attr:`configs` dictionary."""
        # assume build is successful
        # - alter if build fails
        #
        self._build_successful = True
        for dset_name in ['Heater summary']:
            if dset_name not in self.group:
                warn_why = 'dataset (' + dset_name + ') not found'
                warn("Mapping for MSI Diagnostic 'Heater' was"
                     " unsuccessful (" + warn_why + ")")
                self._build_successful = False
                return

        # initialize general info values
        self._configs['shape'] = ()

        # initialize 'shotnum'
        self._configs['shotnum'] = {
            'dset paths': [],
            'dset field': 'Shot number',
            'shape': [],
            'dtype': np.int32
        }

        # initialize 'signals'
        # - there are NO signal fields
        #
        self._configs['signals'] = {}

        # initialize 'meta'
        self._configs['meta'] = {
            'shape': (),
            'timestamp': {
                'dset paths': [],
                'dset field': 'Timestamp',
                'shape': [],
                'dtype': np.float64
            },
            'data valid': {
                'dset paths': [],
                'dset field': 'Data valid',
                'shape': [],
                'dtype': np.int8
            },
            'current': {
                'dset paths': [],
                'dset field': 'Heater current',
                'shape': [],
                'dtype': np.float32
            },
            'voltage': {
                'dset paths': [],
                'dset field': 'Heater voltage',
                'shape': [],
                'dtype': np.float32
            },
            'temperature': {
                'dset paths': [],
                'dset field': 'Heater temperature',
                'shape': [],
                'dtype': np.float32
            },
        }

        # ---- update configs related to 'Heater summary'           ----
        # - dependent configs are:
        #   1. 'shape'
        #   2. 'shotnum'
        #   3. all of 'meta'
        #
        dset_name = 'Heater summary'
        dset = self.group[dset_name]

        # define 'shape'
        if dset.ndim == 1:
            self._configs['shape'] = dset.shape
        else:
            warn_why = "'/Heater summary' does not match " \
                       "expected shape"
            warn("Mapping for MSI Diagnostic 'Heater' was"
                 " unsuccessful (" + warn_why + ")")
            self._build_successful = False
            return

        # update 'shotnum'
        self._configs['shotnum']['dset paths'].append(dset.name)
        self._configs['shotnum']['shape'].append(
            dset.dtype['Shot number'].shape)

        # update 'meta/timestamp'
        self._configs['meta']['timestamp']['dset paths'].append(
            dset.name)
        self._configs['meta']['timestamp']['shape'].append(
            dset.dtype['Timestamp'].shape)

        # update 'meta/data valid'
        self._configs['meta']['data valid']['dset paths'].append(
            dset.name)
        self._configs['meta']['data valid']['shape'].append(
            dset.dtype['Data valid'].shape)

        # update 'meta/current'
        self._configs['meta']['current']['dset paths'].append(
            dset.name)
        self._configs['meta']['current']['shape'].append(
            dset.dtype['Heater current'].shape)

        # update 'meta/voltage'
        self._configs['meta']['voltage']['dset paths'].append(
            dset.name)
        self._configs['meta']['voltage']['shape'].append(
            dset.dtype['Heater voltage'].shape)

        # update 'meta/current'
        self._configs['meta']['temperature']['dset paths'].append(
            dset.name)
        self._configs['meta']['temperature']['shape'].append(
            dset.dtype['Heater temperature'].shape)
