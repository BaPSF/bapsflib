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


class hdfMap_msi_gaspressure(hdfMap_msi_template):
    """
    Mapping class for the 'Gas pressure' MSI diagnostic.

    Simple group structure looks like:

    .. code-block:: none

        +-- Gas pressure
        |   +-- Gas pressure summary
        |   +-- RGA partial pressures

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
        warn_why = ''
        for dset_name in ['Gas pressure summary',
                          'RGA partial pressures']:
            if dset_name not in self.group:
                warn_why = 'dataset (' + dset_name + ') not found'
                warn("Mapping for MSI Diagnostic 'Gas pressure' was"
                     " unsuccessful (" + warn_why + ")")
                self._build_successful = False
                return

        # initialize general info values
        self._configs['RGA AMUs'] = [self.group.attrs['RGA AMUs']]
        self._configs['shape'] = ()

        # initialize 'shotnum'
        self._configs['shotnum'] = {
            'dset paths': [],
            'dset field': 'Shot number',
            'shape': [],
            'dtype': np.int32
        }

        # initialize 'signals'
        # - there is only one signal fields
        #   1. 'partial pressures'
        #
        self._configs['signals'] = {
            'partial pressures': {
                'dset paths': [],
                'dset field': None,
                'shape': [],
                'dtype': np.float32
            },
        }

        # initialize 'meta'
        self._configs['meta'] = {
            'shape': (),
            'timestamp': {
                'dset paths': [],
                'dset field': 'Timestamp',
                'shape': [],
                'dtype': np.float64
            },
            'data valid - ion gauge': {
                'dset paths': [],
                'dset field': 'Ion gauge data valid',
                'shape': [],
                'dtype': np.int8
            },
            'data valid - RGA': {
                'dset paths': [],
                'dset field': 'RGA data valid',
                'shape': [],
                'dtype': np.int8
            },
            'fill pressure': {
                'dset paths': [],
                'dset field': 'Fill pressure',
                'shape': [],
                'dtype': np.float32
            },
            'peak AMU': {
                'dset paths': [],
                'dset field': 'Peak AMU',
                'shape': [],
                'dtype': np.float32
            },
        }

        # ---- update configs related to 'Gas pressure summary'     ----
        # - dependent configs are:
        #   1. 'shape'
        #   2. 'shotnum'
        #   3. all of 'meta'
        #
        dset_name = 'Gas pressure summary'
        dset = self.group[dset_name]

        # define 'shape'
        if dset.ndim == 1:
            self._configs['shape'] = dset.shape
        else:
            warn_why = "'/Gas pressure summary' does not match " \
                       "expected shape"
            warn("Mapping for MSI Diagnostic 'Gas pressure' was"
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

        # update 'meta/data valid - ion gauge'
        self._configs['meta']['data valid - ion gauge'][
            'dset paths'].append(dset.name)
        self._configs['meta']['data valid - ion gauge']['shape'].append(
            dset.dtype['Ion gauge data valid'].shape)

        # update 'meta/data valid - RGA'
        self._configs['meta']['data valid - RGA'][
            'dset paths'].append(dset.name)
        self._configs['meta']['data valid - RGA']['shape'].append(
            dset.dtype['RGA data valid'].shape)

        # update 'meta/fill pressure'
        self._configs['meta']['fill pressure']['dset paths'].append(
            dset.name)
        self._configs['meta']['fill pressure']['shape'].append(
            dset.dtype['Fill pressure'].shape)

        # update 'meta/peak AMU'
        self._configs['meta']['peak AMU']['dset paths'].append(
            dset.name)
        self._configs['meta']['peak AMU']['shape'].append(
            dset.dtype['Peak AMU'].shape)

        # ---- update configs related to 'RGA partial pressures'   ----
        # - dependent configs are:
        #   1. 'signals/partial pressures'
        #
        dset_name = 'RGA partial pressures'
        dset = self.group[dset_name]
        self._configs['signals']['partial pressures']['dset paths'].append(
            dset.name)

        # check 'shape'
        if dset.ndim == 2:
            if dset.shape[0] == self._configs['shape'][0]:
                self._configs['signals']['partial pressures'][
                    'shape'].append((dset.shape[1],))
            else:
                self._build_successful = False
        else:
            self._build_successful = False
        if not self._build_successful:
            warn_why = "'/RGA partial pressures' does not " \
                       "match expected shape"
            warn("Mapping for MSI Diagnostic 'Gas pressure' was"
                 " unsuccessful (" + warn_why + ")")
            return
