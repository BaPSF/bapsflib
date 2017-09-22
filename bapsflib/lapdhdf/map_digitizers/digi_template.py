# This file is part of the bapsflib package, a Python toolkit for the
# BaPSF group at UCLA.
#
# http://plasma.physics.ucla.edu/
#
# Copyright 2017 Erik T. Everson and contributors
#
# License:
#
# TODO: determine a default structure for all digitizer classes
#
import h5py

from abc import abstractmethod


class hdfMap_digi_template(object):
    """
    A template class for all digitizer mapping classes to inherit from.

    .. note::

        Any method that raises a :exc:`NotImplementedError` is intended
        to be overwritten by the inheriting class.
    """
    def __init__(self, digi_group):
        """
        :param digi_group: the digitizer HDF5 group
        :type digi_group: :py:mod:`h5py.Group`
        """
        # condition digi_group arg
        if isinstance(digi_group, h5py.Group):
            self.__digi_group = digi_group
        else:
            raise TypeError('arg digi_group is not of type h5py.Group')

        self.info = {'group name': digi_group.name.split('/')[-1],
                     'group path': digi_group.name}
        """
        Information dict of digitizer HDF5 Group
        
        >>> list(info.keys())
        ['group name', 'group path']
        """

        self.data_configs = {}
        """
        :data:`data_configs` will contain all the mapping information
        for each configuration of the digitizer.  If no configurations
        are found the :data:`data_configs` will be an empty `dict`.
        Otherwise, the dict keys will be the configuration names and
        :data:`data_configs` will be structured as:
        
        .. code-block:: python
        
            data_configs[config_name] = {
                'active': True/False, # config is active or not
                'adc': ['adc_name', ], # list of active adc's
                'group name': '', # name of configuration group
                'group path': '', # absolute path to configuration group
                'adc_name': [(int, # board number
                              [int, ], # list of active channels
                              {'bit': int, # bit resolution
                               'sample rate': (float, 'unit'),
                               'shot average (software)': int,
                               'sample average (hardware)': int}), ]}
        
        where there will be a corresponding :code:`adc_name` key for each
        adc in :code:`data_configs[config_name]['adc']`.
        """

    @property
    @abstractmethod
    def _predefined_adc(self):
        """
        :return: a list of all known/defined analog-digital converters
            (adc)
        :rtype: list(str)
        :raise: :exc:`NotImplementedError`
        """
        raise NotImplementedError

    @property
    def digi_group(self):
        """
        :return: HDF5 digitizer group
        :rtype: :py:mod:`h5py.Group`
        """
        return self.__digi_group

    @abstractmethod
    def __build_data_configs(self):
        """
        Builds and binds the dictionary :py:data:`data_configs` that
        contains information about how the digitizer was configured.

        Should call on the following methods to build
        :data:`data_configs`:

        - :meth:`parse_config_name`
        - :meth:`is_config_active`
        - :meth:`__find_config_adc`
        - :meth:`__adc_info`

        :raise: :exc:`NotImplementedError`
        """
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def parse_config_name(name):
        """
        Will parse the passed group name and determine if the group is
        a digitizer configuration group.

        :param str name: name of proposed HDF5 digitizer configuration
            group
        :return: True/False if `name` is a configuration group,
            name of configuration
        :rtype: tuple(bool, str)
        """
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def is_config_active(config_name, dataset_names):
        """
        Determines if `config_name` was used in collecting the digitizer
        data.

        :param str config_name: the digitizer configuration name
        :param dataset_names: list of HDF5 dataset names in the
            digitizer group
        :type dataset_names: list(str)
        :return: True/False if the digitizer configuration
            `config_name` was used for collecting the digitizer data
        :rtype: bool
        """
        raise NotImplementedError

    @abstractmethod
    def __adc_info(self, adc_name, config_group):
        """
        Builds information on how the adc was configured.

        Should call on :meth:`__find_adc_connections` to determine
        active connections to the adc.

        :param str adc_name: name of analog-digital converter
        :param config_group: instance of the digitizers configuration
            group
        :type config_group: :mod:`h5py.Group`
        :return: a list of of tuples containing configuration
            information of the adc that looks like

        .. code-block:: python

            adc_info = [(board, [channel, ],
                         {'bit': int,
                         'sample rate': (float, 'MHz')}), ]

        where

        - **board** (`int`) = active board number
        - **channel** (`list(int)`) = list of active channels on
          **baord**
        - :code:`'bit'` = bit resolution of adc
        - :code:`'sample rate'` = 2-element tuple defining sample rate
          of the adc. First element is value and second is its units.

        :raise: :exc:`NotImplementedError`
        """
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def __find_config_adc(config_group):
        """
        Determines the adc's used in the digitizer configuration.

        :param config_group: the digitizer configuration group
        :type config_group: :mod:`h5py.Group`
        :return: list of used adc's
        :rtype: list(str)
        :raise: :exc:`NotImplementedError`
        """
        raise NotImplementedError

    @abstractmethod
    def __find_adc_connections(self, adc_name, config_group):
        """
        Finds the active connections on the adc.

        :param str adc_name: name of adc
        :param config_group: digitizer configuration group
        :type config_group: :mod:`h5py.Group`
        :return: list of active adc connections formatted in the same
            manner as the **return** of :meth:`__adc_info`
        :raise: :exc:`NotImplementedError`
        """
        raise NotImplementedError

    @abstractmethod
    def construct_dataset_name(self, board, channel,
                               config_name=None, adc=None,
                               return_info=False):
        """
        Constructs the name of the dataset corresponding to the input
        arguments.

        :param int board: board number
        :param int channel: channel number
        :param str config_name: name of configuration
        :param str adc: name of adc
        :param bool return_info: True/False to indicate if adc
            information should be returned
        :return: (dataset name, adc information)...adc info will
            contain adc bit resoltions, sample rate, and adc name
        :rtype: str, dict
        :raise: :exc:`NotImplementedError`
        """
        raise NotImplementedError
