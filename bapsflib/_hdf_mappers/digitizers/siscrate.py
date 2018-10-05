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


class HDFMapDigiSISCrate(HDFMapDigiTemplate):
    """
    Mapping class for the 'SIS crate' digitizer.
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
    def _device_adcs(self):
        """
        Predefined (known) adc's for digitizer 'SIS crate'

        (See
        :attr:`~.templates.HDFMapDigiTemplate._device_adcs`
        of the base class for details)
        """
        return ['SIS 3302', 'SIS 3305']

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
                self._configs[config_name] = {}

                # determine if config is active
                self._configs[config_name]['active'] = \
                    self._is_config_active(config_name, dataset_names)

                # assign active adc's to the configuration
                self._configs[config_name]['adc'] = \
                    self._find_config_adc(self.group[name])

                # add 'group name'
                self._configs[config_name]['group name'] = name

                # add 'group path'
                self._configs[config_name]['group path'] = \
                    self.group[name].name

                # add adc info
                for adc in self._configs[config_name]['adc']:
                    self._configs[config_name][adc] = \
                        self._adc_info(adc, self.group[name])

                # update adc info with 'nshotnum' and 'nt'
                for adc in self._configs[config_name]['adc']:
                    for conn in self._configs[config_name][adc]:
                        if self._configs[config_name]['active']:
                            nshotnum, nt = self._get_dset_shape(
                                config_name, adc, conn)
                            conn[2].update({
                                'nshotnum': nshotnum,
                                'nt': nt
                            })
                        else:
                            conn[2].update({
                                'nshotnum': None,
                                'nt': None
                            })

    @staticmethod
    def _parse_config_name(name):
        """
        Parses :code:`name` to determine the digitizer configuration
        name.  A configuration group name follows the format:

            | `config_name`

        (See
        :meth:`~.digi_template.HDFMapDigiTemplate.parse_config_name`
        of the base class for details)
        """
        return True, name

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
        # digitizer 'Raw data + config/SIS crate' has two adc's,
        # SIS 3302 and SIS 3305
        # adc_info = ( int, # board
        #              [int, ], # channels
        #              {'bit': int, # bit resolution
        #               'clock rate': (float, 'unit'),
        #               'shot average (software)': int,
        #               'sample average (hardware)': int})
        adc_info = []

        # build adc_info
        if adc_name == 'SIS 3302':
            # for SIS 3302
            conns = self._find_adc_connections('SIS 3302',
                                               config_group)
            for conn in conns:
                # define 'bit' and 'clock rate'
                conn[2]['bit'] = 16
                conn[2]['clock rate'] = (100.0, 'MHz')

                # keys 'shot average (software)' and
                # 'sample average (hardware)' are added in
                # self.__find_crate_connections

                # append info
                adc_info.append(conn)
        elif adc_name == 'SIS 3305':
            # note: clock rate for 'SIS 3305' depends on how
            # diagnostics are connected to the DAQ. Thus, assignment is
            # left to method self.__find_crate_connections.
            conns = self._find_adc_connections('SIS 3305',
                                               config_group)
            for conn in conns:
                # define 'bit' and 'clock rate'
                # - clock rate is defined in __find_adc_connections
                conn[2]['bit'] = 10

                # keys 'shot average (software)' and
                # 'sample average (hardware)' are added in
                # self.__find_crate_connections

                # append info
                adc_info.append(conn)
        else:
            adc_info.append((None, [None],
                             {'bit': None,
                              'clock rate': (None, 'MHz'),
                              'shot average (software)': None,
                              'sample average (hardware)': None}))

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
        active_adc = []
        adc_types = list(config_group.attrs['SIS crate board types'])
        if 2 in adc_types:
            active_adc.append('SIS 3302')
        if 3 in adc_types:
            active_adc.append('SIS 3305')

        return active_adc

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
        # TODO: make this section more efficient
        if adc_name == 'SIS 3302':
            for name in sis3302_gnames:

                # Find board number
                config_index = int(name[-2])
                brd = None
                for slot, index, board, adc in info_list:
                    if '3302' in adc and config_index == index:
                        brd = board
                        break

                # Find active channels
                chs = []
                for key in config_group[name].attrs:
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
                            'clock rate': (None, 'MHz'),
                            'shot average (software)': shtave,
                            'sample average (hardware)': splave})
                if brd is not None:
                    # This counters a bazaar occurrence in the
                    # 'SIS crate' configuration where there's more
                    # configuration subgroups in config_group than there
                    # are listed in
                    # config_group.attrs['SIS crate config indices']
                    conn.append(subconn)

                # reset values
                # brd = None
                # chs = []

        elif adc_name == 'SIS 3305':
            for name in sis3305_gnames:

                # Find board number
                config_index = int(name[-2])
                brd = None
                for slot, index, board, adc in info_list:
                    if '3305' in adc and config_index == index:
                        brd = board
                        break

                # Find active channels and clock mode
                chs = []
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
                            'clock rate': cmode,
                            'shot average (software)': shtave,
                            'sample average (hardware)': splave})
                if brd is not None:
                    conn.append(subconn)

                # reset values
                cmode = (None, 'GHz')

        return conn

    def construct_dataset_name(self, board, channel,
                               config_name=None, adc=None,
                               return_info=False, silent=False):
        """
        Constructs the HDF5 dataset name based on inputs.  The dataset
        name follows the format:

            | `config_name` [Slot `#`: SIS `####` FPGA `#` ch `#`]

        (See
        :meth:`~.digi_template.HDFMapDigiTemplate.construct_dataset_name`
        of the base class for details)
        """
        # TODO: Replace Warnings with proper error handling

        # initiate warning string
        warn_str = ''

        # Condition config_name
        # - if config_name is not specified then the 'active' config
        #   is sought out
        if config_name is None:
            found = 0
            for name in self._configs:
                if self._configs[name]['active'] is True:
                    config_name = name
                    found += 1

            if found == 1:
                warn_str = ('\nconfig_name not specified, '
                            'assuming ' + config_name + '.')
            elif found >= 1:
                raise ValueError("There are multiple active digitizer"
                                 "configurations. User must specify"
                                 "config_name keyword.")
            else:
                raise ValueError("No active digitizer configuration "
                                 "detected.")
        elif config_name not in self._configs:
            # config_name must be a known configuration
            raise ValueError('Invalid configuration name given.')
        elif self._configs[config_name]['active'] is False:
            raise ValueError('Specified configuration name is not '
                             'active.')

        # Condition adc
        # - if adc is not specified then the slow adc '3302' is assumed
        #   or, if 3305 is the only active adc, then it is assumed
        # - self.__config_crates() always adds 'SIS 3302' first. If
        #   '3302' is not active then the list will only contain '3305'.
        if adc is None:
            adc = self._configs[config_name]['adc'][0]
            warn_str += '\nNo adc specified, so assuming ' + adc + '.'
        elif adc not in self._configs[config_name]['adc']:
            raise ValueError(
                'Specified adc ({}) is not in specified '.format(adc)
                + 'configuration ({}).'.format(config_name))

        # search if (board, channel) combo is connected
        bc_valid = False
        d_info = None
        for brd, chs, extras in self._configs[config_name][adc]:
            if board == brd:
                if channel in chs:
                    bc_valid = True

                    # save adc settings for return if requested
                    d_info = extras
                    d_info['adc'] = adc
                    d_info['configuration name'] = config_name
                    d_info['digitizer'] = self._info['group name']

        # (board, channel) combo must be active
        if bc_valid is False:
            raise ValueError('Specified (board, channel) is not valid')

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
            raise ValueError('We have a problem! Somehow adc '
                             + '({}) is not known.'.format(adc))

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

        # get dataset naem
        dset_name = self.construct_dataset_name(board, channel,
                                                **kwargs)
        # build and return header name
        dheader_name = dset_name + ' headers'
        return dheader_name

    @staticmethod
    def slot_to_brd(slot):
        """
        Translates the 'SIS crate` slot number to the board number and
        adc.

        :param int slot: digitizer slot number
        :return: (board number, adc name)
        :rtype: (int, str)
        """
        sb_map = {5: (1, 'SIS 3302'),
                  7: (2, 'SIS 3302'),
                  9: (3, 'SIS 3302'),
                  11: (4, 'SIS 3302'),
                  13: (1, 'SIS 3305'),
                  15: (2, 'SIS 3305')}
        return sb_map[slot]

    @staticmethod
    def brd_to_slot(brd, adc):
        """
        Translates board number and adc name to the digitizer slot
        number.

        :param int brd: board number
        :param str adc: adc name
        :return: digitizer slot number
        :rtype: int
        """
        bs_map = {(1, 'SIS 3302'): 5,
                  (2, 'SIS 3302'): 7,
                  (3, 'SIS 3302'): 9,
                  (4, 'SIS 3302'): 11,
                  (1, 'SIS 3305'): 13,
                  (2, 'SIS 3305'): 15}
        return bs_map[(brd, adc)]
