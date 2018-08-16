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

from abc import ABC, abstractmethod


class hdfMap_digi_template(ABC):
    """
    Template class for all digitizer mapping classes to inherit from.

    Any inheriting class should define :code:`__init__` as::

        def __init__(self, digi_group)
            # initialize
            hdfMap_digi_template.__init__(self, digi_group)

            # populate self.configs
            self._build_configs()

    .. note::

        Any method that raises a :exc:`NotImplementedError` is intended
        to be overwritten by the inheriting class.
    """
    # If I wanted the mapping object to also be an instance of the
    # digit group I would need to change:
    #    1. inheritance of the templabe from 'object' to 'h5py.Group'
    #    2. to initialize w/ h5py.Group.__init__(digi_group.id)
    #
    def __init__(self, digi_group):
        """
        :param digi_group: the digitizer HDF5 group
        :type digi_group: :class:`h5py.Group`
        """
        # condition digi_group arg
        if type(digi_group) is h5py.Group:
            self.__digi_group = digi_group
        else:
            raise TypeError('arg digi_group is not of type h5py.Group')

        self.info = {'group name': digi_group.name.split('/')[-1],
                     'group path': digi_group.name}
        """
        Information dict of digitizer HDF5 Group
        
        .. code-block:: python
        
            info = {
                'group name': str, # name of digitizer group
                'group path': str  # full path to digitizer group
            }
        """

        self.configs = {}
        """
        :data:`configs` will contain all the mapping metadata for each
        digitizer configuration.  If no configurations are found then
        :data:`configs` will be an empty :obj:`dict`.  Otherwise, each 
        found configuration will be given an entry in :data:`configs`
        where the dictionary key will be the configuration name and its
        value will be a :obj:`dict` that looks like::
        
            configs[config_name] = {
                'active': bool, # True/False if config is active or not
                'adc': ['adc_name', ], # list of active adc's
                'group name': '', # name of configuration group
                'group path': ''  # absolute path to configuration group
            }
        
        In Addition, for each 
        :code:`adc_name in configs[config_name]['adc']` there will be
        a dictionary item added to :data:`configs` that looks like::
        
            configs[config_name][adc_name] = [(
                int,     # board number of active boards
                [int, ], # channel numbers of active channels
                {'bit': int, # adc bit resolution
                 'clock rate': (float, 'unit'), # adc clock rate
                 'shot average (software)': int, # adc shot averaging
                 'sample average (hardware)': int # adc sample averaging
            }), ]
        """

    @property
    def active_configs(self):
        """
        :return: list of active configuration names
        :rtype: list(str)
        """
        afigs = []
        for key in self.configs:
            try:
                if self.configs[key]['active']:
                    afigs.append(key)
            except KeyError:
                pass
        return afigs

    @property
    def digi_name(self):
        """Name of digitizer"""
        return self.info['group name']

    @property
    @abstractmethod
    def shotnum_field(self):
        """Field name for shot number column in header dataset"""
        raise NotImplementedError

    @property
    @abstractmethod
    def _predefined_adc(self):
        """
        :return: list of all predefined (known)
            analog-digital-converters (adc's) for the digitizer
        :rtype: list(str)
        :raise: :exc:`NotImplementedError`
        """
        raise NotImplementedError

    @property
    def group(self):
        """
        :return: HDF5 digitizer group
        :rtype: :class:`h5py.Group`
        """
        return self.__digi_group

    @abstractmethod
    def _build_configs(self):
        """
        Gathers the necessary metadata and fills :data:`configs`

        Should call on the following methods to populate
        :data:`configs`:

        - :meth:`parse_config_name`
        - :meth:`is_config_active`
        - :meth:`_find_config_adc`
        - :meth:`_adc_info`

        :raise: :exc:`NotImplementedError`
        """
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def _parse_config_name(name):
        """
        Will parse the passed group name and determine if the name
        matches a digitizer configuration group name.

        :param str name: name of proposed HDF5 digitizer configuration
            group
        :return: (:code:`True`/:code:`False` if :data:`name` is a
            configuration group, the name of the configuration)
        :rtype: (bool, str)
        """
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def _is_config_active(config_name, dataset_names):
        """
        Determines if :code:`config_name` was used in collecting the
        digitizer data.

        :param str config_name: the digitizer configuration name
        :param dataset_names: list of HDF5 dataset names in the
            digitizer group
        :type dataset_names: list(str)
        :return: :code:`True`/:code:`False` if the digitizer
            configuration `config_name` was used for collecting the
            digitizer data
        :rtype: bool
        """
        raise NotImplementedError

    @abstractmethod
    def _adc_info(self, adc_name, config_group):
        """
        Builds information on how the adc was configured.

        Should call on :meth:`_find_adc_connections` to determine
        active connections to the adc.

        :param str adc_name: name of analog-digital-converter
        :param config_group: instance of the digitizers configuration
            group
        :type config_group: :class:`h5py.Group`
        :return: a list of of tuples containing configuration
            information of the requested adc

        The returned :data:`adc_info` looks like::

            adc_info = [(
                board,
                channels,
                {'bit': int,
                 'clock rate': (float, str),
                 'sample average (hardware)': int,
                 'shot average (software)': int}
            ), ]

        where

        * :code:`board` (`int`) = active board number
        * :code:`channels` (`list(int)`) = list of active channels on
          :code:`board`
        * :code:`'bit'` = bit resolution of adc
        * :code:`'clock rate'` = 2-element tuple defining the sample
          rate of the adc. First element is value and second is its
          unit (e.g. :code:`'MHz'`, :code:`'GHz'`, etc.).
        * :code:`'sample average (hardware)'` = `int` for the number of
          samples averaged together and :code:`None` for no averaging
        * :code:`'shot average (software)'` = `int` for the number of
          consecutive shots averaged together and :code:`None` for no
          averaging

        :raise: :exc:`NotImplementedError`
        """
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def _find_config_adc(config_group):
        """
        Determines which adc's are used in the digitizer configuration.

        :param config_group: the digitizer configuration group
        :type config_group: :class:`h5py.Group`
        :return: list of active adc's
        :rtype: list(str)
        :raise: :exc:`NotImplementedError`
        """
        raise NotImplementedError

    @abstractmethod
    def _find_adc_connections(self, adc_name, config_group):
        """
        Finds the active connections (boards, channels, and extras) on
        the adc.  This is called by :meth:`_adc_info` to help gather all
        the adc info.  It is specifically designed to find the active
        board and channel combinations, as well as, any "extra" info
        that can only be gathered at the same time as determining the
        active board and channel combinations.

        :param str adc_name: name of adc
        :param config_group: digitizer configuration group
        :type config_group: :class:`h5py.Group`
        :return: list of tuples containing the active adc connections
            and "extra" information

        .. code-block:: python

            adc_conns = [(board, channels, extras), ]

        where

        * :code:`board` (`int`) = active board number
        * :code:`channels` (`list(int)`) = list of active channels on
          :code:`board`
        * :code:`extras` (`dict`) = dictionary of "extra" information,
          can include the dictionary keys :code:`'bit'`,
          :code:`'clock rate'`, etc.

        :raise: :exc:`NotImplementedError`
        """
        raise NotImplementedError

    @abstractmethod
    def construct_dataset_name(self, board, channel,
                               config_name=None, adc=None,
                               return_info=False):
        """
        Constructs the dataset name corresponding to the input
        arguments.

        :param int board: board number
        :param int channel: channel number
        :param str config_name: name of configuration
        :param str adc: name of adc
        :param bool return_info: Set :code:`True` to also return an adc
            information dictionary
        :return: dataset name (and adc information dictionary if
            :code:`return_info=True`)

        The returned adc information dictionary should look like::

            adc_dict = {
                'bit': int,
                'clock rate': (float, str),
                'sample average (hardware)': int,
                'shot average (software)': int,
                'adc': str,
                'configuration name': str,
                'digitizer': str
            }

        :rtype: str (Default) or (str, adc_dict)

        :data:`config_name` behavior:
            * If only one configuration is active for the digitizer,
              then that configuration is assumed and
              :data:`config_name` does not need to be specified.
            * If multiple configurations are active for the digitizer,
              then one of them needs to be specified.

        :data:`adc` behavior:
            * If only one adc is active, then that adc is assumed and
              :data:`adc` does not need to be specified.
            * If multiple adc's are active, then the adc with the
              slowest clock rate is assumed.  To direct to any other
              adc, then :data:`adc` needs to be specified.

        :raise: :exc:`NotImplementedError`
        """
        raise NotImplementedError

    @abstractmethod
    def construct_header_dataset_name(self, board, channel, **kwargs):
        """"Name of header dataset"""
        raise NotImplementedError
