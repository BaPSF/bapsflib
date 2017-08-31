# This file is part of the bapsflib package, a Python toolkit for the
# BaPSF group at UCLA.
#
# http://plasma.physics.ucla.edu/
#
# Copyright 2017 Erik T. Everson and contributors
#
# License:
#
# TODO: consider having hdfMap_digi_siscrate become digi_group
#  i.e. def __init__(self, digi_group):
#           digi_group.__init__()
#
import h5py

class hdfMap_digi_siscrate(object):
    __predefined_adc = ['SIS 3302', 'SIS 3305']

    def __init__(self, digi_group):
        # condition digi_group arg
        if isinstance(digi_group, h5py.Group):
            self.__digi_group = digi_group
        else:
            raise TypeError('digi_group is not of type h5py.Group')

        self.info = {'group name': digi_group.name.split('/')[-1],
                     'group path': digi_group.name}

        self.data_configs = {}
        self.__build_data_configs()

    @property
    def digi_group(self):
        return self.__digi_group

    def __build_data_configs(self):
        """
            Builds self.data_configs dictionary. A dict. entry follows:

            data_configs[config_name] = {
                'active': True/False,
                'adc': [list of active analog-digital converters],
                'group name': 'name of config group',
                'group path': 'absolute path to config group',
                'SIS 3301': [(brd,
                              [ch,],
                              {'bit': 14,
                               'sample rate': (100.0, 'MHz')}
                              ), ]
                }

            :return:
        """
        # collect digi_group's dataset names and sub-group names
        subgroup_names = []
        dataset_names = []
        for key in self.digi_group.keys():
            if isinstance(self.digi_group[key], h5py.Dataset):
                dataset_names.append(key)
            if isinstance(self.digi_group[key], h5py.Group):
                subgroup_names.append(key)

        # populate self.data_configs
        for name in subgroup_names:
            is_config, config_name = self.parse_config_name(name)
            if is_config:
                # initialize configuration name in the config dict
                self.data_configs[config_name] = {}

                # determine if config is active
                self.data_configs[config_name]['active'] = \
                    self.is_config_active(config_name, dataset_names)

        #        # assign active adc's to the configuration
        #        self.data_configs[config_name]['adc'] = \
        #            self.__config_adc(self.digi_group[name])
        #
        #        # add 'group name'
        #        self.data_configs[config_name]['group name'] = name
        #
        #        # add 'group path'
        #        self.data_configs[config_name]['group path'] = \
        #            self.digi_group[name].name
        #
        #        # add adc info
        #        self.data_configs[config_name]['SIS 3301'] = \
        #            self.__adc_info('SIS 3301', self.digi_group[name])

    @staticmethod
    def parse_config_name(name):
        """
        Parses 'name' to see if it matches the naming scheme for a
        data configuration group.  A group representing a data
        configuration has the scheme:

            config_name

        :param name:
        :return:
        """
        return True, name

    @staticmethod
    def is_config_active(config_name, dataset_names):
        """
        The naming of a dataset starts with the name of its
        corresponding configuration.  This scans 'dataset_names'
        fo see if 'config_name' is used in the list of datasets.

        :param config_name:
        :param dataset_names:
        :return:
        """
        active = False

        # if config_name is in any dataset name then config_name is
        # active
        for name in dataset_names:
            if config_name in name:
                active = True
                break

        return active

    def __adc_info(self, adc_name, config_group):
        pass

    @staticmethod
    def __find_config_adc(config_group):
        active_adc = []
        adc_types = list(config_group.attrs['SIS crate board types'])
        if 2 in adc_types:
            active_adc.append('SIS 3302')
        if 3 in adc_types:
            active_adc.append('SIS 3305')

        return active_adc

    @staticmethod
    def ___find_adc_connections(adc_name, config_group):
        pass

    def construct_dataset_name(self, board, channel,
                               config_name=None, adc=None,
                               return_info=False):
        pass