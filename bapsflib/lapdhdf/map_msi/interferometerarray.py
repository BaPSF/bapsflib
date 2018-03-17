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
        # assume build is successful
        # - alter if build fails
        #
        self._build_successful = True

        # initialize general info values
        self._configs['n interferometer'] = \
            self.group.attrs['Interferometer count']
        self._configs['interferometer name'] = []
        self._configs['t0'] = []
        self._configs['dt'] = []
        self._configs['n_bar_L'] = []
        self._configs['z'] = []
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
        warn_why = ''
        for name in self.group:
            if isinstance(self.group[name], h5py.Group) \
                    and 'Interferometer' in name:
                # count the number of interferometers
                n_inter += 1

                # ensure dataset sizes are consistent
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
                if n_inter == 1:
                    # define sn_size
                    dset_name = name + '/Interferometer summary list'
                    if self.group[dset_name].ndim == 1:
                        sn_size = self.group[dset_name].shape[0]
                    else:
                        warn_why = "'/Interferometer summary list' " \
                                   "does not match expected shape"
                        self._build_successful = False
                        break

                    # define sig_size
                    dset_name = name + '/Interferometer trace'
                    shape = self.group[dset_name].shape
                    if len(shape) == 2:
                        if shape[0] == sn_size:
                            sig_size = shape[1]
                        else:
                            warn_why = "'/Interferometer trace' shot" \
                                       " number axis size is not" \
                                       " consistent with " \
                                       "'/Interferometer summary list"
                            self._build_successful = False
                            break
                    else:
                        warn_why = "'/Interferometer race' does not" \
                                   " match expected shape"
                        self._build_successful = False
                        break

                    # define 'shape'
                    self._configs['shape'] = (sn_size,)
                else:
                    # check 'summary list' size
                    dset_name = name + '/Interferometer summary list'
                    if self.group[dset_name].shape != (sn_size,):
                        # shape is not consistent among all datasets
                        # TODO: ADD WARNING
                        self._build_successful = False
                        break

                    # check 'trace' size
                    dset_name = name + '/Interferometer trace'
                    if self.group[dset_name].shape \
                            != (sn_size, sig_size):
                        # shape is not consistent among all datasets
                        warn_why = "'/Interferometer trace' shape is" \
                                   "not consistent across all " \
                                   "interferometers"
                        self._build_successful = False
                        break

                # populate general info values
                self._configs['interferometer name'].append(name)
                self._configs['t0'].append(
                    self.group[name].attrs['Start time'])
                self._configs['dt'].append(
                    self.group[name].attrs['Timestep'])
                self._configs['n_bar_L'].append(
                    self.group[name].attrs['n_bar_L'])
                self._configs['z'].append(
                    self.group[name].attrs['z location'])

                # populate 'shotnum' values
                dset_name = name + '/Interferometer summary list'
                path = self.group[dset_name].name
                self._configs['shotnum']['dset paths'].append(path)
                self._configs['shotnum']['shape'].append(())

                # populate 'meta'
                # - uses same dset as 'shotnum'
                #
                # 'timestamp'
                self._configs['meta']['timestamp']['dset paths'].append(
                    path
                )
                self._configs['meta']['timestamp']['shape'].append(
                    self.group[path].dtype['Timestamp'].shape
                )
                #
                # 'data valid'
                self._configs['meta']['data valid']['dset paths'].append(
                    path
                )
                self._configs['meta']['data valid']['shape'].append(
                    self.group[path].dtype['Data valid'].shape
                )
                #
                # 'peak density'
                self._configs['meta']['peak density']['dset paths'].append(
                    path
                )
                self._configs['meta']['peak density']['shape'].append(
                    self.group[path].dtype['Peak density'].shape
                )

                # populate 'signals' values
                # - only 'signal' field is in 'signals'
                #   ~ 'dset paths' = []
                #   ~ 'dset field' = None
                #   ~ 'shape' = []
                #   ~ 'dtype' = np.float32
                dset_name = name + '/Interferometer trace'
                path = self.group[dset_name].name
                shape = (self._configs['n interferometer'],
                         self.group[dset_name].shape[1])
                self._configs['signals']['signal']['dset paths'].append(
                    path
                )
                self._configs['signals']['signal']['shape'].append(shape)

        # ensure the number of found interferometers is equal to the
        # diagnostics 'Interferometer count'
        #
        if n_inter != self._configs['n interferometer']:
            self._build_successful = False

        # warn that build was unsuccessful
        if not self._build_successful:
            warn(
                "Mapping for MSI Diagnostic 'Interferometer array' was"
                " unsuccessful (" + warn_why + ")")
