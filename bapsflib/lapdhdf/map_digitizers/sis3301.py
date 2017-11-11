# This file is part of the bapsflib package, a Python toolkit for the
# BaPSF group at UCLA.
#
# http://plasma.physics.ucla.edu/
#
# Copyright 2017 Erik T. Everson and contributors
#
# License: Standard 3-clause BSD; see "LICENSES/LICENSE.txt" for full
#   license terms and contributor agreement.
#
import h5py

from .digi_template import hdfMap_digi_template


class hdfMap_digi_sis3301(hdfMap_digi_template):
    """
    Mapping class for the 'SIS 3301' digitizer.
    """
    def __init__(self, digi_group):
        """
        :param digi_group: the HDF5 digitizer group
        :type digi_group: :class:`h5py.Group`
        """
        # initialize
        hdfMap_digi_template.__init__(self, digi_group)

        # populate self.configs
        self._build_configs()

    @property
    def _predefined_adc(self):
        """
        Predefined (known) adc's for digitizer 'SIS 3301'

        (See
        :attr:`~.digi_template.hdfMap_digi_template._predefined_adc`
        of the base class for details)
        """
        return ['SIS 3301']

    def _build_configs(self):
        """
        Populates :attr:`configs` dictionary

        (See :meth:`~.digi_template.hdfMap_digi_template._build_configs`
        and :attr:`~.digi_template.hdfMap_digi_template.configs`
        of the base class for details)
        """
        # self.configs is initialized in the template

        # collect digi_group's dataset names and sub-group names
        subgroup_names = []
        dataset_names = []
        for key in self.group.keys():
            if isinstance(self.group[key], h5py.Dataset):
                dataset_names.append(key)
            if isinstance(self.group[key], h5py.Group):
                subgroup_names.append(key)

        # populate self.configs
        for name in subgroup_names:
            is_config, config_name = self._parse_config_name(name)
            if is_config:
                # initialize configuration name in the config dict
                self.configs[config_name] = {}

                # determine if config is active
                self.configs[config_name]['active'] = \
                    self._is_config_active(config_name, dataset_names)

                # assign active adc's to the configuration
                self.configs[config_name]['adc'] = \
                    self._find_config_adc(self.group[name])

                # add 'group name'
                self.configs[config_name]['group name'] = name

                # add 'group path'
                self.configs[config_name]['group path'] = \
                    self.group[name].name

                # add adc info
                self.configs[config_name]['SIS 3301'] = \
                    self._adc_info('SIS 3301', self.group[name])

    @staticmethod
    def _parse_config_name(name):
        """
        Parses :code:`name` to determine the digitizer configuration
        name.  A configuration group name follows the format:

            | Configuration: `config_name`

        (See
        :meth:`~.digi_template.hdfMap_digi_template.parse_config_name`
        of the base class for details)
        """
        split_name = name.split()
        is_config = True if split_name[0] == 'Configuration:' else False
        config_name = ' '.join(split_name[1::]) if is_config else None
        return is_config, config_name

    @staticmethod
    def _is_config_active(config_name, dataset_names):
        """
        Determines if :code:`config_name` is an active digitizer
        configuration.

        (See
        :meth:`~.digi_template.hdfMap_digi_template._is_config_active`
        of the base class for details)
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
        """
        Gathers information on the adc configuration.

        (See :meth:`~.digi_template.hdfMap_digi_template._adc_info`
        of the base class for details)
        """
        # 'Raw data + config/SIS 3301' group has only one possible
        # adc ('SIS 3301')
        # adc_info = ( int, # board
        #              [int, ], # channels
        #              {'bit': 14, # bit resolution
        #               'sample rate': (100.0, 'MHz'),
        #               'shot average (software)': int,
        #               'sample average (hardware)': int})
        adc_info = []

        # conns is a list of tuples where each tuple has the same
        # structure as adc_info
        conns = self._find_adc_connections(adc_name, config_group)

        for conn in conns:
            # define 'bit' and 'sample rate'
            conn[2]['bit'] = 14
            conn[2]['sample rate'] = (100.0, 'MHz')

            # add shot average to dict
            if 'Shots to average' in config_group.attrs:
                shtave = config_group.attrs['Shots to average']
                if shtave == 0 or shtave == 1:
                    shtave = None
            else:
                shtave = None
            conn[2]['shot average (software)'] = shtave

            # add sample average to dict
            if 'Samples to average' in config_group.attrs:
                avestr = config_group.attrs['Samples to average']
                if isinstance(avestr, bytes):
                    avestr = avestr.decode('utf-8')
                if avestr == 'No averaging':
                    splave = None
                else:
                    splave = int(avestr.split()[1])
                    if splave == 0 or splave == 1:
                        splave = None
            else:
                splave = None
            conn[2]['sample average (hardware)'] = splave

            # append info
            adc_info.append(conn)

        return adc_info

    @staticmethod
    def _find_config_adc(config_group):
        """
        Determines active adc's used in the digitizer configuration.

        (See
        :meth:`~.digi_template.hdfMap_digi_template._find_config_adc`
        of the base class for details)
        """
        return ['SIS 3301']

    def _find_adc_connections(self, adc_name, config_group):
        """
        Determines active connections on the adc.

        (See
        :meth:`~.digi_template.hdfMap_digi_template._find_adc_connections`
        of the base class for details)
        """
        # initialize conn, brd, and chs
        # conn = list of connections
        # brd  = board number
        # chs  = list of connect channels of board brd
        #
        conn = []
        brd = None
        chs = []

        # Determine connected (brd, ch) combinations
        for ibrd, board in enumerate(config_group.keys()):
            brd_group = config_group[board]
            for ich, ch_key in enumerate(brd_group.keys()):
                ch_group = brd_group[ch_key]

                if ich == 0:
                    brd = ch_group.attrs['Board']
                    chs = [ch_group.attrs['Channel']]
                else:
                    chs.append(ch_group.attrs['Channel'])

            # build subconn tuple with connected board, channels, and
            # acquisition parameters
            subconn = (brd, chs,
                       {'bit': None, 'sample rate': (None, 'MHz')})
            conn.append(subconn)

        return conn

    def construct_dataset_name(self, board, channel,
                               config_name=None, adc='SIS 3301',
                               return_info=False, silent=False):
        """
        Constructs the HDF5 dataset name based on inputs.  The dataset
        name follows the format:

            | `config_name` [`board`:`channel`]'

        (See
        :meth:`~.digi_template.hdfMap_digi_template.construct_dataset_name`
        of the base class for details)
        """
        # TODO: Replace Warnings with proper error handling

        # initiate warning string
        warn_str = ''

        # Condition adc keyword
        if adc != 'SIS 3301':
            warn_str = ('** Warning: passed adc ({}) is '.format(adc)
                        + 'not valid for this digitizer. Forcing '
                        "adc = 'SIS 3301'")
            adc = 'SIS 3301'

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
                warn_str += ('\n** Warning: config_name not specified, '
                             'assuming ' + config_name + '.')
            elif found >= 1:
                # raise Exception("Too many active digitizer "
                #                 "configurations detected. Currently "
                #                 "do not know how to handle,")
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

        # search if (board, channel) combo is connected
        bc_valid = False
        d_info = None
        for brd, chs, extras in \
                self.configs[config_name]['SIS 3301']:
            if board == brd:
                if channel in chs:
                    bc_valid = True

                    # save adc settings for return if requested
                    d_info = extras
                    d_info['adc'] = 'SIS 3301'
                    d_info['configuration name'] = config_name
                    d_info['digitizer'] = self.info['group name']

        # (board, channel) combo must be active
        if bc_valid is False:
            raise Exception('Specified (board, channel) is not valid')

        # checks passed, build dataset_name
        dataset_name = '{0} [{1}:{2}]'.format(config_name, board,
                                              channel)

        # print warnings
        if not silent:
            print(warn_str)

        if return_info is True:
            return dataset_name, d_info
        else:
            return dataset_name
