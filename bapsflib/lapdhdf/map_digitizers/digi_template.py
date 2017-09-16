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
    # When inheriting from template, the new class must define the class
    # attribute `__predefined_adc` that is specific to that digitizer.
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
        """i'm here"""

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
        raise NotImplementedError

    @abstractmethod
    def __adc_info(self, adc_name, config_group):
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def __find_config_adc(config_group):
        raise NotImplementedError

    @abstractmethod
    def __find_adc_connections(self, adc_name, config_group):
        raise NotImplementedError

    @abstractmethod
    def construct_dataset_name(self, board, channel):
        raise NotImplementedError
