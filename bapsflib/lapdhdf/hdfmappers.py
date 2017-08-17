# This file is part of the bapsflib package, a Python toolkit for the
# BaPSF group at UCLA.
#
# http://plasma.physics.ucla.edu/
#
# Copyright 2017 Erik T. Everson and contributors
#
# License:
#
# TODO: make a pickle save for the hdfMap...
#       Then, if a user adds additional mappings for a specific HDF5
#       file, those can be maintained
#
import h5py


def get_hdfMap(hdf_version, hdf_file):
    """
        Function to simulate a Class with dynamic inheritance.  An
        instance of the hdfMap class is returned.  The superclass
        inheritance of hdfMap is determined by the param hdf_version.

        :param hdf_file:
        :param hdf_version:
        :return:
    """
    known_hdf_version = {'1.1': hdfMap_LaPD_1dot1,
                         '1.2': hdfMap_LaPD_1dot2}

    if hdf_version in known_hdf_version.keys():
        class hdfMap(known_hdf_version[hdf_version]):
            """
                Contains the mapping relations for a given LaPD
                generated HDF5 file.
            """

            def __init__(self, hdf_obj):
                super(hdfMap, self).__init__(hdf_obj)

        hdf_mapping = hdfMap(hdf_file)
        return hdf_mapping
    else:
        print('Mapping of HDF5 file is not known.\n')


class hdfMapTemplate(object):
    """
        Template for all HDF Mapping Classes

        Class Attributes
        ----------------
            msi_group  -- str -- name of MSI group
            data_group -- str -- name of data group

        Object Attributes
        -----------------
            hdf_version  -- str
                - string representation of the version number
                  corresponding the the LaPD HDF Software version used
                  to generate the HDF5 file
            msi_diagnostic_groups -- [str]
                - list of the group names for each diagnostic recorded
                  in the MSI group
            sis_group -- str
                - SIS group name which contains all the DAQ recorded
                  data and associated DAQ configuration
            sis_crates -- [str]
                - list of SIS crates (digitizers) available to record
                  data
            data_configs -- {}
                - dict containing key parameters associated with the
                  crate configurations
                - dict is constructed using method build_data_configs

        Methods
        -------
            sis_path
                - returns the HDF internal absolution path to the
                  sis_group
            build_data_configs
                - used to construct the data_configs attribute
            parse_config_name
            is_config_active
            __config_crates
            __crate_info
            __find_crate_connections

    """
    msi_group = 'MSI'
    data_group = 'Raw data + config'

    def __init__(self):
        self.hdf_version = ''
        self.msi_diagnostic_groups = []
        self.sis_group = ''
        self.sis_crates = []
        self.data_configs = {}

    def sis_path(self):
        return self.data_group + '/' + self.sis_group

    def build_data_configs(self):
        pass


class hdfMap_LaPD_1dot1(hdfMapTemplate):
    def __init__(self, hdf_obj):
        hdfMapTemplate.__init__(self)

        self.hdf_version = '1.1'
        self.msi_diagnostic_groups.extend(['Discharge', 'Gas pressure',
                                           'Heater',
                                           'Interferometer array',
                                           'Magnetic field'])
        self.sis_group = 'SIS 3301'
        self.sis_crates.extend(['SIS 3301'])

        # Gather and build data configurations if sis_group exists
        dgroup = hdf_obj.get(self.sis_path())
        if dgroup is not None:
            self.build_data_configs(dgroup)

    def build_data_configs(self, group):
        """
            Builds self.data_configs dictionary. A dict. entry follows:

            data_configs[config_name] = {
                'active': True/False,
                'crates: [list of active SIS crates],
                'group name': 'name of config group',
                'group path': 'absolute path to config group',
                'SIS 3301': {'bit': 14,
                             'sample rate': (100.0, 'MHz'),
                             'connections': [(br, [ch,]), ]}}

            :param group:
            :return:
        """
        # collect sis_group's dataset names and sub-group names
        subgroup_names = []
        dataset_names = []
        for key in group.keys():
            if isinstance(group[key], h5py.Dataset):
                dataset_names.append(key)
            if isinstance(group[key], h5py.Group):
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

                # assign active crates to the configuration
                self.data_configs[config_name]['crates'] = \
                    self.sis_crates

                # add 'group name'
                self.data_configs[config_name]['group name'] = name

                # add 'group path'
                self.data_configs[config_name]['group path'] = \
                    group.name

                # add SIS info
                self.data_configs[config_name]['SIS 3301'] = \
                    self.__crate_info('SIS 3301', group[name])

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
        """
            The naming of a dataset starts with the name of its
            corresponding configuration.  This scans 'dataset_names'
            fo see if 'config_name' is used in the list of datasets.

            :param config_name:
            :param dataset_names:
            :return:
        """
        active = False

        for name in dataset_names:
            if config_name in name:
                active = True
                break

        return active

    def __crate_info(self, crate_name, config_group):
        """
            Builds a list of tuples that contains info for each
            connected board of the SIS crate.  The format looks like:

            crate_info = [(brd, [ch,..],
                          {'bit': 14, 'sample rate': (100.0, 'MHz')}),]

            Calling crate_info looks like:
            crate_info[0] = (brd, [ch,..],
                             {'bit': 14, 'sample rate': (100.0, 'MHz'})
            crate_info[0][0] = brd
            crate_info[0][1] = [ch, ...] -> list of connected channels
            crate_info[0][2]['bit'] = 14
            crate_info[0][2]['sample rate'] = (100.0, 'MHz')

            :param crate_name:
            :param config_group:
            :return:
        """
        # LaPD v1.1 only has crate 'SIS 3301'
        # crate_info = {'bit': 14,
        #              'sample rate': (100, 'MHz'),
        #              'connections': self.__find_crate_connections(
        #                  crate_name, config_group)}
        crate_info = []
        conns = self.__find_crate_connections(crate_name, config_group)

        for conn in conns:
            conn[2]['bit'] = 14
            conn[2]['sample rate'] = (100.0, 'MHZ')
            crate_info.append(conn)

        return crate_info

    @staticmethod
    def __find_crate_connections(crate_name, config_group):
        conn = []
        brd = None
        chs = []
        for ibrd, board in enumerate(config_group.keys()):
            brd_group = config_group[board]
            for ich, ch_key in enumerate(brd_group.keys()):
                ch_group = brd_group[ch_key]

                if ich == 0:
                    brd = ch_group.attrs['Board']
                    chs = [ch_group.attrs['Channel']]
                else:
                    chs.append(ch_group.attrs['Channel'])

            subconn = (brd, chs,
                       {'bit': None, 'sample rate': (None, 'MHz')})
            conn.append(subconn)

        return conn

    def parse_dataset_name(self, name):
        pass


class hdfMap_LaPD_1dot2(hdfMapTemplate):
    def __init__(self, hdf_obj):
        hdfMapTemplate.__init__(self)

        self.hdf_version = '1.2'
        self.msi_diagnostic_groups.extend(['Discharge', 'Gas pressure',
                                           'Heater',
                                           'Interferometer array',
                                           'Magnetic field'])
        self.sis_group = 'SIS crate'
        self.sis_crates.extend(['SIS 3302', 'SIS 3305'])

        # Gather and build data configurations if sis_group exists
        dgroup = hdf_obj.get(self.sis_path())
        if dgroup is not None:
            self.build_data_configs(dgroup)

    def build_data_configs(self, group):
        """
            Builds self.data_configs dictionary. A dict. entry follows:

            data_configs[config_name] = {
                'active': True/False,
                'crates: [list of active SIS crates],
                'group name': 'name of config group',
                'group path': 'absolute path to config group',
                'SIS 3301': {'bit': 14,
                             'sample rate': (100.0, 'MHz'),
                             'connections': [(br, [ch,]), ]}}

            :param group:
            :return:
        """
        # collect sis_group's dataset names and sub-group names
        subgroup_names = []
        dataset_names = []
        for key in group.keys():
            if isinstance(group[key], h5py.Dataset):
                dataset_names.append(key)
            if isinstance(group[key], h5py.Group):
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

                # assign active crates to the configuration
                self.data_configs[config_name]['crates'] = \
                    self.__config_crates(group[name])

                # add 'group name'
                self.data_configs[config_name]['group name'] = name

                # add 'group path'
                self.data_configs[config_name]['group path'] = \
                    group.name

                # add SIS info
                for crate in self.data_configs[config_name]['crates']:
                    self.data_configs[config_name][crate] = \
                        self.__crate_info(crate, group[name])

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

        for name in dataset_names:
            if config_name in name:
                active = True
            break

        return active

    @staticmethod
    def __config_crates(group):
        active_crates = []
        crate_types = list(group.attrs['SIS crate board types'])
        if 2 in crate_types:
            active_crates.append('SIS 3302')
        if 3 in crate_types:
            active_crates.append('SIS 3305')

        return active_crates

    def __crate_info(self, crate_name, config_group):
        # LaPD v1.2 has two DAQ crates, SIS 3302 and SIS 3305
        crate_info = []

        # build crate_info
        if crate_name == 'SIS 3302':
            # for SIS 3302
            conns = self.__find_crate_connections('SIS 3302',
                                                  config_group)
            for conn in conns:
                conn[2]['bit'] = 16
                conn[2]['sample rate'] = (100.0, 'MHz')
                crate_info.append(conn)
        elif crate_name == 'SIS 3305':
            # note: sample rate for 'SIS 3305' depends on how
            # diagnostics are connected to the DAQ. Thus, assignment is
            # left to method self.__find_crate_connections.
            conns = self.__find_crate_connections('SIS 3305',
                                                  config_group)
            for conn in conns:
                conn[2]['bit'] = 10
                crate_info.append(conn)
        else:
            crate_info.append((None, [None],
                               {'bit': None,
                                'sample rate': (None, 'MHz')}))

        return crate_info

    def __find_crate_connections(self, crate_name, config_group):
        conn = []
        brd = None
        chs = []

        active_slots = config_group.attrs['SIS crate slot numbers']
        config_indices = config_group.attrs['SIS crate config indices']
        info_list = []
        for slot, index in zip(active_slots, config_indices):
            if slot != 3:
                brd, sis = self.slot_to_brd(slot)
                info_list.append((slot, index, brd, sis))

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

        if crate_name == 'SIS 3302':
            for name in sis3302_gnames:

                # Find board number
                config_index = int(name[-2])
                for slot, index, board, sis in info_list:
                    if '3302' in sis and config_index == index:
                        brd = board
                        break

                # Find active channels
                for key in config_group[name].attrs.keys():
                    if 'Enable' in key:
                        tf_str = config_group[name].attrs[key]
                        if 'TRUE' in tf_str.decode('utf-8'):
                            chs.append(int(key[-1]))

                subconn = (brd, chs,
                           {'bit': None, 'sample rate': (None, 'MHZ')})
                conn.append(subconn)
                brd = None
                chs = []

        elif crate_name == 'SIS 3305':
            for name in sis3305_gnames:

                # Find board number
                config_index = int(name[-2])
                for slot, index, board, sis in info_list:
                    if '3305' in sis and config_index == index:
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

                subconn = (brd, chs,
                           {'bit': None, 'sample rate': cmode})
                conn.append(subconn)
                brd = None
                chs = []

        return conn

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
    def brd_to_slot(brd, sis):
        # TODO: add arg conditioning
        bs_map = {(1, 'SIS 3302'): 5,
                  (2, 'SIS 3302'): 7,
                  (3, 'SIS 3302'): 9,
                  (4, 'SIS 3302'): 11,
                  (1, 'SIS 3305'): 13,
                  (2, 'SIS 3305'): 15}
        return bs_map[(brd, sis)]
