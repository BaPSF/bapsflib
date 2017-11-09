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

from .digi_template import hdfMap_digi_template


class hdfMap_digi_siscrate(hdfMap_digi_template):
    def __init__(self, digi_group):
        hdfMap_digi_template.__init__(self, digi_group)

        # build self.data_configs
        self._build_configs()

    @property
    def _predefined_adc(self):
        """
        :return: ['SIS 3302', 'SIS 3305']
        """
        return ['SIS 3302', 'SIS 3305']

    def _build_configs(self):
        """
        Builds self.data_configs dictionary. A dict. entry follows:

        .. code-block:: python

            data_configs[config_name] = {
                'active': True/False,
                'adc': [list of active analog-digital converters],
                'group name': 'name of config group',
                'group path': 'absolute path to config group',
                'SIS 3301': [(brd,
                              [ch,],
                              {'bit': 14,
                               'sample rate': (100.0, 'MHz'),
                               'shot average (software)': int,
                               'sample average (hardware)': int}), ]}
        """
        # initialize data_configs
        # self.data_configs = {}

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
                self.configs[config_name] = {}

                # determine if config is active
                self.configs[config_name]['active'] = \
                    self.is_config_active(config_name, dataset_names)

                # assign active adc's to the configuration
                self.configs[config_name]['adc'] = \
                    self._find_config_adc(self.digi_group[name])

                # add 'group name'
                self.configs[config_name]['group name'] = name

                # add 'group path'
                self.configs[config_name]['group path'] = \
                    self.digi_group[name].name

                # add adc info
                for adc in self.configs[config_name]['adc']:
                    self.configs[config_name][adc] = \
                        self._adc_info(adc, self.digi_group[name])

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

    def _adc_info(self, adc_name, config_group):
        # digitizer 'Raw data + config/SIS crate' two adc's, SIS 3302
        # and SIS 3305
        # adc_info = ( int, # board
        #              [int, ], # channels
        #              {'bit': int, # bit resolution
        #               'sample rate': (float, 'unit'),
        #               'shot average (software)': int,
        #               'sample average (hardware)': int})
        adc_info = []

        # build adc_info
        if adc_name == 'SIS 3302':
            # for SIS 3302
            conns = self._find_adc_connections('SIS 3302',
                                               config_group)
            for conn in conns:
                # define 'bit' and 'sample rate'
                conn[2]['bit'] = 16
                conn[2]['sample rate'] = (100.0, 'MHz')

                # keys 'shot average (software)' and
                # 'sample average (hardware)' are added in
                # self.__find_crate_connections

                # append info
                adc_info.append(conn)
        elif adc_name == 'SIS 3305':
            # note: sample rate for 'SIS 3305' depends on how
            # diagnostics are connected to the DAQ. Thus, assignment is
            # left to method self.__find_crate_connections.
            conns = self._find_adc_connections('SIS 3305',
                                               config_group)
            for conn in conns:
                # define 'bit' and 'sample rate'
                # - sample rate is defined in __find_adc_connections
                conn[2]['bit'] = 10

                # keys 'shot average (software)' and
                # 'sample average (hardware)' are added in
                # self.__find_crate_connections

                # append info
                adc_info.append(conn)
        else:
            adc_info.append((None, [None],
                             {'bit': None,
                              'sample rate': (None, 'MHz'),
                              'shot average (software)': None,
                              'sample average (hardware)': None}))

        return adc_info

    @staticmethod
    def _find_config_adc(config_group):
        active_adc = []
        adc_types = list(config_group.attrs['SIS crate board types'])
        if 2 in adc_types:
            active_adc.append('SIS 3302')
        if 3 in adc_types:
            active_adc.append('SIS 3305')

        return active_adc

    def _find_adc_connections(self, adc_name, config_group):
        # initialize conn, brd, and chs
        # conn = list of connections
        # brd  = board number
        # chs  = list of connect channels of board brd
        #
        conn = []
        brd = None
        chs = []
        cmode = (None, 'GHz')

        # Build a tuple relating the adc name (adc), adc slot number
        # (slot), associated data configuration unique identifier index
        # (index), and board number (brd)
        active_slots = config_group.attrs['SIS crate slot numbers']
        config_indices = config_group.attrs['SIS crate config indices']
        info_list = []
        for slot, index in zip(active_slots, config_indices):
            if slot != 3:
                brd, adc = self.slot_to_brd(slot)
                info_list.append((slot, index, brd, adc))

        # filter out calibration groups and only gather configuration
        # groups
        sis3302_gnames = []
        sis3305_gnames = []
        for key in config_group.keys():
            if 'configurations' in key:
                if '3302' in key:
                    sis3302_gnames.append(key)
                elif '3305' in key:
                    sis3305_gnames.append(key)

        # Determine connected (brd, ch) combinations
        if adc_name == 'SIS 3302':
            for name in sis3302_gnames:

                # Find board number
                config_index = int(name[-2])
                for slot, index, board, adc in info_list:
                    if '3302' in adc and config_index == index:
                        brd = board
                        break

                # Find active channels
                for key in config_group[name].attrs.keys():
                    if 'Enable' in key:
                        tf_str = config_group[name].attrs[key]
                        if 'TRUE' in tf_str.decode('utf-8'):
                            chs.append(int(key[-1]))

                # determine 'shot average (software)'
                if 'Shot averaging (software)' \
                        in config_group[name].attrs:
                    shtave = config_group[name].attrs[
                        'Shot averaging (software)']
                    if shtave == 0 or shtave == 1:
                        shtave = None
                else:
                    shtave = None

                # determine 'sample average (hardware)'
                # - the HDF5 attribute is the power to 2
                # - So, a hardware sample of 5 actually means the number
                #   of points sampled is 2^5
                if 'Sample averaging (hardware)'\
                        in config_group[name].attrs:
                    splave = config_group[name].attrs[
                        'Sample averaging (hardware)']
                    if splave == 0:
                        splave = None
                    else:
                        splave = 2 ** splave
                else:
                    splave = None

                # build subconn tuple with connected board, channels
                # and acquisition parameters
                subconn = (brd, chs,
                           {'bit': None,
                            'sample rate': (None, 'MHz'),
                            'shot average (software)': shtave,
                            'sample average (hardware)': splave})
                conn.append(subconn)
                brd = None
                chs = []

        elif adc_name == 'SIS 3305':
            for name in sis3305_gnames:

                # Find board number
                config_index = int(name[-2])
                for slot, index, board, adc in info_list:
                    if '3305' in adc and config_index == index:
                        brd = board
                        break

                # Find active channels and clock mode
                for key in config_group[name].attrs.keys():
                    # channels
                    if 'Enable' in key:
                        if 'FPGA 1' in key:
                            tf_str = config_group[name].attrs[key]
                            if 'TRUE' in tf_str.decode('utf-8'):
                                chs.append(int(key[-1]))
                        elif 'FPGA 2' in key:
                            tf_str = config_group[name].attrs[key]
                            if 'TRUE' in tf_str.decode('utf-8'):
                                chs.append(int(key[-1]) + 4)

                    # clock mode
                    # the clock state of 3305 is stored in the 'channel
                    # mode' attribute.  The values follow
                    #   0 = 1.25 GHz
                    #   1 = 2.5  GHz
                    #   2 = 5.0  GHz
                    cmodes = [(1.25, 'GHz'),
                              (2.5, 'GHz'),
                              (5.0, 'GHz')]
                    if 'Channel mode' in key:
                        cmode = cmodes[config_group[name].attrs[key]]

                # determine 'shot average (software)'
                if 'Shot averaging (software)' \
                        in config_group[name].attrs:
                    shtave = config_group[name].attrs[
                        'Shot averaging (software)']
                    if shtave == 0 or shtave == 1:
                        shtave = None
                else:
                    shtave = None

                # determine 'sample average (hardware)'
                # - SIS 3305 has no hardware sampling feature
                splave = None

                # build subconn tuple with connected board, channels
                # and acquisition parameters
                subconn = (brd, chs,
                           {'bit': None,
                            'sample rate': cmode,
                            'shot average (software)': shtave,
                            'sample average (hardware)': splave})
                conn.append(subconn)
                brd = None
                chs = []
                cmode = (None, 'GHz')

        return conn

    def construct_dataset_name(self, board, channel,
                               config_name=None, adc=None,
                               return_info=False, silent=False):
        """
        Returns the name of a HDF5 dataset based on its configuration
        name, board, channel, and adc. Format follows:

            'config_name [Slot #: SIS #### FPGA # ch #]'

        :param board:
        :param channel:
        :param config_name:
        :param adc:
        :param return_info:
        :param silent:
        :return:
        """
        # TODO: Replace Warnings with proper error handling
        # TODO: Add a Silent kwd

        # initiate warning string
        warn_str = ''

        # Condition config_name
        # - if config_name is not specified then the 'active' config
        #   is sought out
        if config_name is None:
            found = 0
            for name in self.configs:
                if self.configs[name]['active'] is True:
                    config_name = name
                    found += 1

            if found == 1:
                warn_str = ('** Warning: config_name not specified, '
                            'assuming ' + config_name + '.')
            elif found >= 1:
                # raise Exception("Too many active digitizer "
                #                 "configurations detected. Currently "
                #                 "do not know how to handle.")
                raise Exception("There are multiple active digitizer"
                                "configurations. User must specify"
                                "config_name keyword.")
            else:
                raise Exception("No active digitizer configuration "
                                "detected.")
        elif config_name not in self.configs:
            # config_name must be a known configuration
            raise Exception('Invalid configuration name given.')
        elif self.configs[config_name]['active'] is False:
            raise Exception('Specified configuration name is not '
                            'active.')

        # Condition adc
        # - if adc is not specified then the slow adc '3302' is assumed
        #   or, if 3305 is the only active adc, then it is assumed
        # - self.__config_crates() always adds 'SIS 3302' first. If
        #   '3302' is not active then the list will only contain '3305'.
        if adc is None:
            adc = self.configs[config_name]['adc'][0]
            warn_str += ('\n** Warning: No adc specified, so assuming '
                         + adc + '.')
        elif adc not in self.configs[config_name]['adc']:
            raise Exception(
                'Specified adc ({}) is not in specified '.format(adc)
                + 'configuration ({}).'.format(config_name))

        # search if (board, channel) combo is connected
        bc_valid = False
        d_info = None
        for brd, chs, extras in self.configs[config_name][adc]:
            if board == brd:
                if channel in chs:
                    bc_valid = True

                    # save adc settings for return if requested
                    d_info = extras
                    d_info['adc'] = adc
                    d_info['configuration name'] = config_name
                    d_info['digitizer'] = self.info['group name']

        # (board, channel) combo must be active
        if bc_valid is False:
            raise Exception('Specified (board, channel) is not valid')

        # checks passed, build dataset_name
        if '3302' in adc:
            slot = self.brd_to_slot(board, 'SIS 3302')
            dataset_name = '{0} [Slot {1}: SIS 3302 ch {2}]'.format(
                config_name, slot, channel)
        elif '3305' in adc:
            slot = self.brd_to_slot(board, 'SIS 3305')
            if channel in range(1, 5):
                fpga = 1
                ch = channel
            else:
                fpga = 2
                ch = channel - 4

            dataset_name = '{0} [Slot {1}: '.format(config_name, slot) \
                           + 'SIS 3305 FPGA {0} ch {1}]'.format(fpga,
                                                                ch)
        else:
            raise Exception('We have a problem! Somehow adc '
                            + '({}) is not known.'.format(adc))

        # print warnings
        if not silent:
            print(warn_str)

        if return_info is True:
            return dataset_name, d_info
        else:
            return dataset_name

    @staticmethod
    def slot_to_brd(slot):
        """
        Mapping between the SIS crate slot number to the DAQ
        displayed board number.

        :param slot:
        :return:
        """
        # TODO: add arg conditioning
        sb_map = {'5': (1, 'SIS 3302'),
                  '7': (2, 'SIS 3302'),
                  '9': (3, 'SIS 3302'),
                  '11': (4, 'SIS 3302'),
                  '13': (1, 'SIS 3305'),
                  '15': (2, 'SIS 3305')}
        return sb_map['{}'.format(slot)]

    @staticmethod
    def brd_to_slot(brd, adc):
        # TODO: add arg conditioning
        bs_map = {(1, 'SIS 3302'): 5,
                  (2, 'SIS 3302'): 7,
                  (3, 'SIS 3302'): 9,
                  (4, 'SIS 3302'): 11,
                  (1, 'SIS 3305'): 13,
                  (2, 'SIS 3305'): 15}
        return bs_map[(brd, adc)]
