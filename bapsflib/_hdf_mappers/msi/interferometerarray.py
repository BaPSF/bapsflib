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

from bapsflib.utils.errors import HDFMappingError
from warnings import warn

from .templates import hdfMap_msi_template


# noinspection PyPep8Naming
class hdfMap_msi_interarr(hdfMap_msi_template):
    """
    Mapping class for the 'Interferometer array' MSI diagnostic.

    Simple group structure looks like:

    .. code-block:: none

        +-- Interferometer array
        |   +-- Interferometer [0]
        |   |   +-- Interferometer summary list
        |   |   +-- Interferometer trace
        |   +-- Interferometer [1]
        |   |   +-- Interferometer summary list
        |   |   +-- Interferometer trace
        .
        .
        .
        |   +-- Interferometer [6]
        |   |   +-- Interferometer summary list
        |   |   +-- Interferometer trace
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
        # What should be in configs
        # 1. num. of interferometers
        # 2. start times for each interferometers
        # 3. dt for each interferometer
        # 4. n_bar_L for each interferometer
        # 5. z location for each interferometer
        # 6. 'shotnum' field
        #    - contains mapping of HDF5 file quantity to np
        #    a. shape
        #    b. dtype
        # 7. 'signals' field
        #    - another dict where keys are the fields to be added to
        #      the np.array
        # 8. 'meta' field
        #

        # initialize general info values
        # - pairs[0:2] are found in the main group's attributes
        # - pairs[2] corresponds to the sub-group names
        # - pairs[3:] are found in the main group's attributes (as an
        #     array) and in the sub-group attributes (elements of the
        #     main group's array)...I'm choosing to populate via the
        #     sub-group attributes to ensure one-to-one correspondence
        #     when extracting data with the HDFReadMSI class
        #
        pairs = [('n interferometer', 'Interferometer count'),
                 ('calib tag', 'Calibration tag'),
                 ('interferometer name', None),
                 ('t0', 'Start time'),
                 ('dt', 'Timestep'),
                 ('n_bar_L', 'n_bar_L'),
                 ('z', 'z location')]
        self._configs['interferometer name'] = []
        self._configs['t0'] = []
        self._configs['dt'] = []
        self._configs['n_bar_L'] = []
        self._configs['z'] = []
        for pair in pairs[0:2]:
            try:
                val = self.group.attrs[pair[1]]
                if isinstance(val, (list, tuple, np.ndarray)):
                    self._configs[pair[0]] = val
                else:
                    self._configs[pair[0]] = [val]
            except KeyError:
                self._configs[pair[0]] = []
                warn("Attribute '" + pair[1]
                     + "' not found for MSI diagnostic '"
                     + self.device_name
                     + "', continuing with mapping")

        # more handling of general info value 'n interferometer'
        pair = pairs[0]
        check_n_inter = True
        if len(self._configs[pair[0]]) != 1:
            check_n_inter = False
            warn("Attribute '" + pair[1] + "' for MSI diagnostic '"
                 + self.device_name
                 + "' not an integer, continuing with mapping")
        elif not isinstance(self._configs['n interferometer'][0],
                            (int, np.integer)):
            check_n_inter = False
            warn("Attribute '" + pair[1] + "' for MSI diagnostic '"
                 + self.device_name +
                 "' not an integer, continuing with mapping")

        # initialize 'shape'
        # - this is used by hdfReadMSI
        self._configs['shape'] = ()

        # initialize 'shotnum'
        self._configs['shotnum'] = {
            'dset paths': [],
            'dset field': 'Shot number',
            'shape': [],
            'dtype': np.int32
        }

        # initialize 'signals'
        # - there is only one signal field named 'signal'
        self._configs['signals'] = {'signal': {
            'dset paths': [],
            'dset field': None,
            'shape': [],
            'dtype': np.float32
        }}

        # initialize 'meta'
        self._configs['meta'] = {
            'shape': (self._configs['n interferometer'],),
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
            'peak density': {
                'dset paths': [],
                'dset field': 'Peak density',
                'shape': [],
                'dtype': np.float32
            },
        }

        # populate self.configs from each interferometer group
        # - all the population is done in this for-loop to ensure all
        #   lists are one-to-one
        #
        n_inter = 0
        sn_size = 0
        sig_size = 0
        for name in self.group:
            if isinstance(self.group[name], h5py.Group) \
                    and 'Interferometer' in name:
                # count the number of interferometers
                n_inter += 1

                # ensure required datasets are present
                for dset_name in ['Interferometer summary list',
                                  'Interferometer trace']:
                    if dset_name not in self.group[name]:
                        why = ("dataset '" + dset_name + "' not found "
                               + "for 'Interferometer/" + name + "'")
                        raise HDFMappingError(self.info['group path'],
                                              why=why)

                # populate general info values
                self._configs['interferometer name'].append(name)
                for pair in pairs[3::]:
                    try:
                        self._configs[pair[0]].append(
                            self.group[name].attrs[pair[1]])
                    except KeyError:
                        self._configs[pair[0]].append(None)
                        warn("Attribute '" + pair[1]
                             + "' not found for MSI diagnostic '"
                             + self.device_name + '/' + name
                             + "', continuing with mapping")

                # define values to ensure dataset sizes are consistent
                # sn_size  = number of shot numbers
                # sig_size = number of samples in interferometer trace
                #            - the way the np.array will be constructed
                #              requires all interferometer signals to
                #              have the same sample size
                # - define sn_size and ensure it's consistent among all
                #   datasets
                # - define sig_size and ensure it's consistent among all
                #   datasets
                #
                # - Enforcement of the these dimensions is done when
                #   mapping each dataset below
                #
                if n_inter == 1:
                    # define sn_size
                    dset_name = name + '/Interferometer summary list'
                    dset = self.group[dset_name]
                    if dset.ndim == 1:
                        sn_size = self.group[dset_name].shape[0]
                    else:
                        why = "'/Interferometer summary list' " \
                              "does not match expected shape"
                        raise HDFMappingError(self.info['group path'],
                                              why=why)

                    # define sig_size
                    dset_name = name + '/Interferometer trace'
                    dset = self.group[dset_name]
                    shape = self.group[dset_name].shape
                    if dset.dtype.names is not None:
                        # dataset has fields (it should not have fields)
                        why = "can not handle a 'signal' dataset" \
                              + "(" + dset_name + ") with fields"
                        raise HDFMappingError(self.info['group path'],
                                              why=why)
                    elif dset.ndim == 2:
                        if dset.shape[0] == sn_size:
                            sig_size = shape[1]
                        else:
                            why = "'Interferometer trace' and " \
                                  "'Interferometer summary list' do " \
                                  "not have same number of rows " \
                                  "(shot numbers)"
                            raise HDFMappingError(
                                self.info['group path'],
                                why=why)
                    else:
                        why = "'/Interferometer race' does not" \
                              " match expected shape"
                        raise HDFMappingError(self.info['group path'],
                                              why=why)

                    # define 'shape'
                    self._configs['shape'] = (sn_size,)

                # -- update configs related to                      ----
                # -- 'Interferometer summary list'                  ----
                # - dependent configs are:
                #   1. 'shotnum'
                #   2. all of 'meta'
                #
                dset_name = name + '/Interferometer summary list'
                dset = self.group[dset_name]
                path = dset.name

                # check 'shape'
                expected_fields = ['Shot number', 'Timestamp',
                                   'Data valid', 'Peak density']
                if dset.shape != (sn_size,):
                    # shape is not consistent among all datasets
                    why = "'/Interferometer summary list' shape " \
                          "is not consistent across all " \
                          "interferometers"
                    raise HDFMappingError(self.info['group path'],
                                          why=why)
                elif not all(field in dset.dtype.names
                             for field in expected_fields):
                    # required fields are not present
                    why = "'/Interferometer summary list' does " \
                          "NOT have required fields"
                    raise HDFMappingError(self.info['group path'],
                                          why=why)

                # update 'shotnum'
                self._configs['shotnum']['dset paths'].append(path)
                self._configs['shotnum']['shape'].append(
                    dset.dtype['Shot number'].shape)

                # update 'meta/timestamp'
                self._configs['meta']['timestamp'][
                    'dset paths'].append(dset.name)
                self._configs['meta']['timestamp'][
                    'shape'].append(dset.dtype['Timestamp'].shape)

                # update 'meta/data valid'
                self._configs['meta']['data valid'][
                    'dset paths'].append(dset.name)
                self._configs['meta']['data valid'][
                    'shape'].append(dset.dtype['Data valid'].shape)

                # update 'meta/peak density'
                self._configs['meta']['peak density'][
                    'dset paths'].append(dset.name)
                self._configs['meta']['peak density'][
                    'shape'].append(dset.dtype['Peak density'].shape)

                # -- update configs related to                      ----
                # -- 'Interferometer trace'                         ----
                # - dependent configs are:
                #   1. 'signals/signal'
                #
                dset_name = name + '/Interferometer trace'
                dset = self.group[dset_name]

                # check 'shape'
                if dset.shape != (sn_size, sig_size):
                    # shape is not consistent among all datasets
                    why = "'/Interferometer trace' shape is" \
                          "not consistent across all " \
                          "interferometers"
                    raise HDFMappingError(self.info['group path'],
                                          why=why)
                elif dset.dtype.names is not None:
                    # dataset has fields (it should not have fields)
                    why = "'/Interferometer trace' shape does" \
                          "not match expected shape "
                    raise HDFMappingError(self.info['group path'],
                                          why=why)

                # update 'signals/signal' values
                shape = (self._configs['n interferometer'], sig_size)
                self._configs['signals']['signal'][
                    'dset paths'].append(dset.name)
                self._configs['signals']['signal'][
                    'shape'].append(shape)

        # ensure the number of found interferometers is equal to the
        # diagnostics 'Interferometer count'
        #
        if check_n_inter:
            if n_inter != self._configs['n interferometer'][0]:
                why = 'num. of found interferometers did not ' \
                      'match the expected num. of interferometers'
                raise HDFMappingError(self.info['group path'],
                                      why=why)
