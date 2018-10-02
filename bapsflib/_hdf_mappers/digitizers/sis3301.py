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

from warnings import warn

from .templates import HDFMapDigiTemplate


class HDFMapDigiSIS3301(HDFMapDigiTemplate):
    """
    Mapping class for the 'SIS 3301' digitizer.
    """
    def __init__(self, group: h5py.Group):
        """
        :param group: the HDF5 digitizer group
        """
        # initialize
        HDFMapDigiTemplate.__init__(self, group)

        # populate self.configs
        self._build_configs()

    @property
    def shotnum_field(self):
        """Field name for shot number column in header dataset"""
        return 'Shot'

    @property
    def _predefined_adc(self):
        """
        Predefined (known) adc's for digitizer 'SIS 3301'

        (See
        :attr:`~.digi_template.HDFMapDigiTemplate._predefined_adc`
        of the base class for details)
        """
        return ['SIS 3301']

    def _build_configs(self):
        """
        Populates :attr:`configs` dictionary

        (See :meth:`~.digi_template.HDFMapDigiTemplate._build_configs`
        and :attr:`~.digi_template.HDFMapDigiTemplate.configs`
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

                # update adc info with 'nshotnum' and 'nt'
                if self.configs[config_name]['active']:
                    for conn in self.configs[config_name]['SIS 3301']:
                        nshotnum, nt = self._get_dset_shape(
                            config_name, 'SIS 3301', conn)
                        conn[2].update({
                            'nshotnum': nshotnum,
                            'nt': nt
                        })
                else:
                    for conn in self.configs[config_name]['SIS 3301']:
                        conn[2].update({
                            'nshotnum': None,
                            'nt': None
                        })

    @staticmethod
    def _parse_config_name(name):
        """
        Parses :code:`name` to determine the digitizer configuration
        name.  A configuration group name follows the format:

            | Configuration: `config_name`

        (See
        :meth:`~.digi_template.HDFMapDigiTemplate.parse_config_name`
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
        :meth:`~.digi_template.HDFMapDigiTemplate._is_config_active`
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

        (See :meth:`~.digi_template.HDFMapDigiTemplate._adc_info`
        of the base class for details)
        """
        # 'Raw data + config/SIS 3301' group has only one possible
        # adc ('SIS 3301')
        # adc_info = ( int, # board
        #              [int, ], # channels
        #              {'bit': 14, # bit resolution
        #               'clock rate': (100.0, 'MHz'),
        #               'shot average (software)': int,
        #               'sample average (hardware)': int})
        adc_info = []

        # conns is a list of tuples where each tuple has the same
        # structure as adc_info
        conns = self._find_adc_connections(adc_name, config_group)

        for conn in conns:
            # define 'bit' and 'clock rate'
            conn[2]['bit'] = 14
            conn[2]['clock rate'] = (100.0, 'MHz')

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

    def _get_dset_shape(self, config_name, adc, conn_tuple):
        conn = conn_tuple

        # gather all dataset shapes
        brd = conn[0]
        dset_shapes = []
        for ch in conn[1]:
            dset_name = self.construct_dataset_name(
                brd, ch,
                config_name=config_name,
                adc=adc,
                silent=True
            )
            dset_shapes.append(self.group[dset_name].shape)

        # check all datasets have the same shape
        if all(shape == dset_shapes[0] for shape in dset_shapes):
            # all shapes are consistent
            if len(dset_shapes[0]) == 1:
                nshotnum = 1
                nt = dset_shapes[0][0]
            else:
                nshotnum = dset_shapes[0][0]
                nt = dset_shapes[0][1]
        else:
            raise ValueError(
                'Dataset shapes on board {} are not'.format(
                    brd)
                + ' consistent adc ({})'.format(adc))

        # return
        return nshotnum, nt

    @staticmethod
    def _find_config_adc(config_group):
        """
        Determines active adc's used in the digitizer configuration.

        (See
        :meth:`~.digi_template.HDFMapDigiTemplate._find_config_adc`
        of the base class for details)
        """
        return ['SIS 3301']

    def _find_adc_connections(self, adc_name, config_group):
        """
        Determines active connections on the adc.

        (See
        :meth:`~.digi_template.HDFMapDigiTemplate._find_adc_connections`
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
                       {'bit': None, 'clock rate': (None, 'MHz')})
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
        :meth:`~.digi_template.HDFMapDigiTemplate.construct_dataset_name`
        of the base class for details)
        """

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
                warn_str += ('\nconfig_name not specified, '
                             'assuming ' + config_name + '.')
            elif found > 1:
                raise ValueError("There are multiple active digitizer"
                                 "configurations. User must specify"
                                 "config_name keyword.")
            else:
                raise ValueError("No active digitizer configuration "
                                 "detected.")
        elif config_name not in self.configs:
            # config_name must be a known configuration
            raise ValueError('Invalid configuration name given.')
        elif self.configs[config_name]['active'] is False:
            raise ValueError('Specified configuration name is not '
                             'active.')

        # Condition adc keyword
        if adc != 'SIS 3301':
            raise ValueError(
                'Specified adc ({}) is not in specified '.format(adc)
                + 'configuration ({}).'.format(config_name))

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
                    d_info['digitizer'] = self._info['group name']

        # (board, channel) combo must be active
        if bc_valid is False:
            raise ValueError('Specified (board, channel) is not valid')

        # checks passed, build dataset_name
        dataset_name = '{0} [{1}:{2}]'.format(config_name, board,
                                              channel)

        # print warnings
        if not silent and warn_str != '':
            warn(warn_str)

        # return
        if return_info is True:
            return dataset_name, d_info
        else:
            return dataset_name

    def construct_header_dataset_name(self, board, channel, **kwargs):
        """"Name of header dataset"""
        # ensure return_info kwarg is always False
        kwargs['return_info'] = False

        # get dataset name
        dset_name = self.construct_dataset_name(board, channel,
                                                **kwargs)
        # build and return header name
        dheader_name = dset_name + ' headers'
        return dheader_name
