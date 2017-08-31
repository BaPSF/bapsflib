# This file is part of the bapsflib package, a Python toolkit for the
# BaPSF group at UCLA.
#
# http://plasma.physics.ucla.edu/
#
# Copyright 2017 Erik T. Everson and contributors
#
# License:
#
# TODO: consider having hdfMap_digi_sis3301 become digi_group
#  i.e. def __init__(self, digi_group):
#           digi_group.__init__()
#
import h5py


class hdfMap_digi_sis3301(object):
    __predefined_adc = ['SIS 3301']

    def __init__(self, digi_group):
        # condition digi_group arg
        if not isinstance(digi_group, h5py.Group):
            raise TypeError('data_group is not of type h5py.Group')

        self.info = {'group name': digi_group.name.split('/')[-1],
                     'group path': digi_group.name}

    def build_data_configs(self, group):
        pass

    @staticmethod
    def parse_config_name(name):
        """
        Parses 'name' to see if it matches the naming scheme for a
        data configuration group.  A group representing a data
        configuration has the scheme:

            Configuration: config_name

        :param name:
        :return:
        """
        split_name = name.split()
        is_config = True if split_name[0] == 'Configuration:' else False
        config_name = ' '.join(split_name[1::]) if is_config else None
        return is_config, config_name

    @staticmethod
    def is_config_active(config_name, dataset_names):
        return False

    def __adc_info(self, adc_name, config_gorup):
        pass

    @staticmethod
    def __find_adc_connections(adc_name, config_group):
        pass

    def construct_dataset_name(self, board, channel, *args,
                               config_name=None, return_info=False,
                               **kwargs):
        pass