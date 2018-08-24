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
import os
import h5py

from abc import ABC, abstractmethod


class hdfMap_msi_template(ABC):
    # noinspection PySingleQuotedDocstring
    '''
    Template class for all MSI diagnostic mapping classes to inherit
    from.

    Any inheriting class should define :code:`__init__` as::

        def __init__(self, diag_group):
            """
            :param diag_group: the HDF5 MSI diagnostic group
            :type diag_group: :class:`h5py.Group`
            """
            # initialize
            hdfMap_msi_template.__init__(self, diag_group)

            # populate self.configs
            self._build_configs()

    .. note::

        Any method that raises a :exc:`NotImplementedError` is intended
        to be overwritten by the inheriting class.
    '''
    def __init__(self, diag_group):
        """
        :param diag_group: the MSI diagnostic HDF5 group
        :type diag_group: :class:`h5py.Group`
        """
        # condition diag_group arg
        if isinstance(diag_group, h5py.Group):
            self.__diag_group = diag_group
        else:
            raise TypeError('arg diag_group is not of type h5py.Group')

        # define info attribute
        self._info = {
            'group name': os.path.basename(diag_group.name),
            'group path': diag_group.name
        }

        # initialize self.configs
        self._configs = {}

        # initialize build success
        self._build_successful = False

    @property
    def configs(self):
        """
        Dictionary containing all the relevant mapping information to
        translate the HDF5 data locations for the
        :mod:`bapsflib.lapd` module.

        The required structure follows (with example values)::

            import numpy as np

            # outline of `configs` dict
            # - any additional key added beyond these four will be
            #   added to the `info` attribute of the data array
            #   constructed by hdfReadMSI
            configs = {
                'shape': (), # numpy shape to be used by hdfReadMSI
                             # - typically (2,)
                'shotnum': {}, # mapping for the 'shotnum'`field used by
                               # hdfReadMSI
                'signals': {}, # mapping for the signal fields used by
                               # hdfReadMSI
                               # - this is semi-polymorphic
                'meta': {} # mapping for the 'meta' field used by
                           # hdfReadMSI
                           # - this is semi-polymorphic
            }

            # 'shotnum' key and its value
            configs['shotnum'] = {
                'dset path': [str], # list of HDF% dataset paths where
                                    # shot number values are store
                                    # - typically one element, but the
                                    #   'Interferometer array' will have
                                    #   and entry for each
                                    #   interferometer
                'dset field': 'Shot number', # field name in the dataset
                                             # that corresponds to shot
                                             # number values
                'shape': [(), ], # list of numpy shapes for each dataset
                                 # - length is equal to length of the
                                 #   'dset path' list
                                 # - typically [(),]
                'dtype': np.int32 # numpy dtype value to be used by
                                  # hdfReadMSI
            }

            # 'signals' key and its values
            # - 'signals' keys become the fields become the fields in
            #   the numpy array constructed by hdfReadMSI
            # - data associated with 'signals' are consider to be
            #   recorded or plot-able data arrays and typically have
            #   their own dataset in the HDF5 file
            # - the example below would tell hdfReadMSI to make a
            #   'magnetic field' field in the numpy array
            #
            configs['signals'] = {
                'magnetic field': {
                    'dset paths': [str], # path to dataset
                    'dset field': None,  # dataset has no field
                                         # the dataset is a 2D array
                                         # all the data corresponds to
                                         # magnetic field values
                    'shape': [(100,)],   # each magnetic field array for
                                         # each shot number is 100
                                         # samples long
                    'dtype': np.float32  # values have type np.float32
                },
            }

            # 'meta' keys the their values
            # - 'meta' keys become the sub-field names under the 'meta'
            #   field of the numpy array constructed by hdfReadMSI
            # - values in 'meta' should be quantities that relate to
            #   both shot numbers and diagnostics
            #    ~ these types of quantites are general stored in the
            #      'summary' datasets
            # - the  example below would tell hdfReadMSI to make a
            #   'peak magnetic field' field in the 'meta' field of the
            #   numpy array
            #
            configs['meta'] = {
                'peak magnetic field': {
                    'dset paths': [str], # path to dataset
                    'dset field': 'Peak magnetic field',
                        # field name in the dataset
                    'shape': [()],  # list of numpy shapes for each
                                    # dataset
                                    # - typically [(),]
                    'dtype': np.float32 # values have type np.float32
                },
            }

        .. note::

            For further details, look to :ref:`add_msi_mod`.
        """
        return self._configs

    @property
    def info(self):
        """
        Information dict for the MSI diagnostic::

            info = {
                'group name': str, # name of diagnostic group
                'group path': str  # full path to diagnostic group
            }
        """
        return self._info

    @property
    def device_name(self):
        """Name of MSI diagnostic (device)"""
        return self._info['group name']

    @property
    def group(self):
        """Instance of MSI diagnostic group (:class:`h5py.Group`)"""
        return self.__diag_group

    @property
    def build_successful(self):
        """Indicates if the map construction was successful or not."""
        return self._build_successful

    @abstractmethod
    def _build_configs(self):
        """
        Gathers the necessary mapping data and fills :attr:`configs`

        :raises: :exc:`NotImplementedError`

        .. note::

            Examine :meth:`_build_configs` in existing modules for ideas
            on how to construct method.  Also read :ref:`add_msi_mod`.
        """
        raise NotImplementedError
