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
    __defined_digitizer_mappings = {
        'SIS 3301': hdfMap_digi_sis3301,
        'SIS crate': hdfMap_digi_siscrate}

    def __init__(self, data_group):

        # condition data_group arg
        if not isinstance(data_group, h5py.Group):
            raise TypeError('data_group is not of type h5py.Group')

        self.__data_group = data_group
        # all data_group subgroups
        # - each of these subgroups can fall into one of four 'LaPD
        #   data types'
        #   1. data sequence
        #   2. digitizer groups (known)
        #   3. motion lists
        #   4. unknown
        self.data_group_subgroups = []
        for key in data_group.keys():
            if isinstance(data_group[key], h5py.Group):
                self.data_group_subgroups.append(key)

        # Build the self dictionary
        dict.__init__(self, self.__build_dict)

    @property
    def data_group(self):
        return self.__data_group

    @property
    def predefined_digitizer_groups(self):
        return list(self.__defined_digitizer_mappings.keys())

    @property
    def __build_dict(self):
        digi_dict = {}
        try:
            for item in self.data_group_subgroups:
                if item in self.__defined_digitizer_mappings.keys():
                    digi_dict[item] = \
                        self.__defined_digitizer_mappings[item](
                            self.data_group[item])
        except TypeError:
            pass

        return digi_dict
