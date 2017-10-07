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

from .sis3301 import hdfMap_digi_sis3301
from .siscrate import hdfMap_digi_siscrate


class hdfMap_digitizers(dict):
    """
    Creates a dictionary that contains mapping instances for all the
    discovered digitizers in the HDF5 data group.
    """
    _defined_digitizer_mappings = {
        'SIS 3301': hdfMap_digi_sis3301,
        'SIS crate': hdfMap_digi_siscrate}
    """
    A dictionary containing references to the defined digitizer mapping
    classes.
    """

    def __init__(self, data_group):
        """
        :param data_group: the HDF5 group that contains the digitizer
            groups
        :type data_group: :mod:`h5py.Group`
        """

        # condition data_group arg
        if not isinstance(data_group, h5py.Group):
            raise TypeError('data_group is not of type h5py.Group')

        self.__data_group = data_group
        # all data_group subgroups
        # - each of these subgroups can fall into one of four 'LaPD
        #   data types'
        #   1. data sequence
        #   2. digitizer groups (known)
        #   3. controls (known)
        #   4. unknown
        #: list of all group names in the HDF5 data group
        self.data_group_subgroups = []
        for key in data_group.keys():
            if isinstance(data_group[key], h5py.Group):
                self.data_group_subgroups.append(key)

        # Build the self dictionary
        dict.__init__(self, self.__build_dict)

    @property
    def data_group(self):
        """
        :return: instance of the HDF5 data group containing the
            digitizers
        :rtype: :mod:`h5py.Group`
        """
        return self.__data_group

    @property
    def predefined_digitizer_groups(self):
        """
        :return: list of the predefined digitizer group names
        :rtype: list(str)
        """
        return list(self._defined_digitizer_mappings.keys())

    @property
    def __build_dict(self):
        """
        Builds a dictionary containing mapping instances of all the
        discovered digitizers in the data group.

        :return: digitizer mapping dictionary
        """
        digi_dict = {}
        try:
            for item in self.data_group_subgroups:
                if item in self._defined_digitizer_mappings.keys():
                    digi_dict[item] = \
                        self._defined_digitizer_mappings[item](
                            self.data_group[item])
        except TypeError:
            pass

        return digi_dict
