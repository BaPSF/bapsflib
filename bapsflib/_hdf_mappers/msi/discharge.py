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

from .templates import hdfMap_msi_template


class hdfMap_msi_discharge(hdfMap_msi_template):
    """
    Mapping class for the 'Discharge' MSI diagnostic.

    Simple group structure looks like:

    .. code-block:: none

        +-- Discharge
        |   +-- Cathode-anode voltage
        |   +-- Discharge current
        |   +-- Discharge summary

    """
    def __init__(self, group):
        """
        :param group: the HDF5 MSI diagnostic group
        :type group: :class:`h5py.Group`
        """
        # initialize
        hdfMap_msi_template.__init__(self, group)

        # populate self.configs
        self._build_configs()

    def _build_configs(self):
        """Builds the :attr:`configs` dictionary."""
        # assume build is successful
        # - alter if build fails
        #
        self._build_successful = True
        for dset_name in ['Cathode-anode voltage',
                          'Discharge current',
                          'Discharge summary']:
            if dset_name not in self.group:
                warn_why = "dataset '" + dset_name + "' not found"
                warn("Mapping for MSI Diagnostic 'Discharge' was"
                     " unsuccessful (" + warn_why + ")")
                self._build_successful = False
                return

        # initialize general info values
        pairs = [('current conversion factor',
                  'Current conversion factor'),
                 ('voltage conversion factor',
                  'Voltage conversion factor'),
                 ('t0', 'Start time'),
                 ('dt', 'Timestep')]
        for pair in pairs:
            try:
                self._configs[pair[0]] = [self.group.attrs[pair[1]]]
            except KeyError:
                self._configs[pair[0]] = []
                warn("Attribute '" + pair[1]
                     + "' not found for MSI diagnostic '"
                     + self.device_name
                     + "', continuing with mapping")

        # initialize 'shape'
        # - this is used by HDFReadMSI
        self._configs['shape'] = ()

        # initialize 'shotnum'
        self._configs['shotnum'] = {
            'dset paths': [],
            'dset field': 'Shot number',
            'shape': [],
            'dtype': np.int32
        }

        # initialize 'signals'
        # - there are two signal fields
        #   1. 'voltage'
        #   2. 'current'
        #
        self._configs['signals'] = {
            'voltage': {
                'dset paths': [],
                'dset field': None,
                'shape': [],
                'dtype': np.float32
            },
            'current': {
                'dset paths': [],
                'dset field': None,
                'shape': [],
                'dtype': np.float32
            }
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
            'data valid': {
                'dset paths': [],
                'dset field': 'Data valid',
                'shape': [],
                'dtype': np.int8
            },
            'pulse length': {
                'dset paths': [],
                'dset field': 'Pulse length',
                'shape': [],
                'dtype': np.float32
            },
            'peak current': {
                'dset paths': [],
                'dset field': 'Peak current',
                'shape': [],
                'dtype': np.float32
            },
            'bank voltage': {
                'dset paths': [],
                'dset field': 'Bank voltage',
                'shape': [],
                'dtype': np.float32
            },
        }

        # ---- update configs related to 'Discharge summary'        ----
        # - dependent configs are:
        #   1. 'shape'
        #   2. 'shotnum'
        #   3. all of 'meta'
        #
        dset_name = 'Discharge summary'
        dset = self.group[dset_name]

        # define 'shape'
        expected_fields = ['Shot number', 'Timestamp', 'Data valid',
                           'Pulse length', 'Peak current',
                           'Bank voltage']
        if dset.ndim == 1 and \
                all(field in dset.dtype.names
                    for field in expected_fields):
            self._configs['shape'] = dset.shape
        else:
            warn_why = "'/Discharge summary' does not match " \
                       "expected shape"
            warn("Mapping for MSI Diagnostic 'Discharge' was"
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

        # update 'meta/pulse length'
        self._configs['meta']['pulse length']['dset paths'].append(
            dset.name)
        self._configs['meta']['pulse length']['shape'].append(
            dset.dtype['Pulse length'].shape)

        # update 'meta/peak current'
        self._configs['meta']['peak current']['dset paths'].append(
            dset.name)
        self._configs['meta']['peak current']['shape'].append(
            dset.dtype['Peak current'].shape)

        # update 'meta/bank voltage'
        self._configs['meta']['bank voltage']['dset paths'].append(
            dset.name)
        self._configs['meta']['bank voltage']['shape'].append(
            dset.dtype['Bank voltage'].shape)

        # ---- update configs related to 'Cathode-anode voltage'   ----
        # - dependent configs are:
        #   1. 'signals/voltage'
        #
        dset_name = 'Cathode-anode voltage'
        dset = self.group[dset_name]
        self._configs['signals']['voltage']['dset paths'].append(
            dset.name)

        # check 'shape'
        if dset.dtype.names is not None:
            # dataset has fields (it should not have fields)
            self._build_successful = False
        elif dset.ndim == 2:
            if dset.shape[0] == self._configs['shape'][0]:
                self._configs['signals']['voltage']['shape'].append(
                    (dset.shape[1],))
            else:
                self._build_successful = False
        else:
            self._build_successful = False
        if not self._build_successful:
            warn_why = "'/Cathode-anode voltage' does not " \
                       "match expected shape"
            warn("Mapping for MSI Diagnostic 'Discharge' was"
                 " unsuccessful (" + warn_why + ")")
            return

        # update configs related to 'Discharge current'             ----
        # - dependent configs are:
        #   1. 'signals/current'
        #
        dset_name = 'Discharge current'
        dset = self.group[dset_name]
        self._configs['signals']['current']['dset paths'].append(
            dset.name)

        # check 'shape'
        if dset.dtype.names is not None:
            # dataset has fields (it should not have fields)
            self._build_successful = False
        elif dset.ndim == 2:
            if dset.shape[0] == self._configs['shape'][0]:
                self._configs['signals']['current']['shape'].append(
                    (dset.shape[1],))
            else:
                self._build_successful = False
        else:
            self._build_successful = False
        if not self._build_successful:
            warn_why = "'/Discharge current' does not " \
                       "match expected shape"
            warn("Mapping for MSI Diagnostic 'Discharge' was"
                 " unsuccessful (" + warn_why + ")")
            return
