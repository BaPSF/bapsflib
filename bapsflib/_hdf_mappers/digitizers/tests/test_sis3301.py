#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
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
# TODO: testing of shot and sample averaging identification
# - this feature has to be added to the FauxSIS3301 first
#
import unittest as ut

from bapsflib.utils.errors import HDFMappingError

from .common import DigitizerTestCase
from ..sis3301 import HDFMapDigiSIS3301


class TestSIS3301(DigitizerTestCase):
    """Test class for HDFMapDigiSIS3301"""
    #
    # * There is currently no test for a situation where there
    #   are multiple active 'SIS 3301' configurations.
    #

    DEVICE_NAME = 'SIS 3301'
    DEVICE_PATH = '/Raw data + config/' + DEVICE_NAME
    MAP_CLASS = HDFMapDigiSIS3301

    def setUp(self):
        super().setUp()

    def tearDown(self):
        super().tearDown()

    def test_map_failures(self):
        """Test scenarios that should raise HDFMappingError"""
        # 1. board config group missing attribute 'Board'
        # 2. more than one board config group (for the same config_name)
        #    defines the same board number
        # 3. channel config group missing attribute 'Channel'
        # 4. there are no identifiable configuration groups
        # 5. none of the configurations are active
        # 6. adc connections for active config are NULL
        #
        # setup group
        config_name = 'config01'
        # adc = 'SIS 3301'
        config_path = 'Configuration: {}'.format(config_name)
        my_bcs = [(0, (0, 3, 5)),
                  (3, (0, 1, 2, 3)),
                  (5, (5, 6, 7))]
        bc_arr = self.mod.knobs.active_brdch
        bc_arr[...] = False
        for brd, chns in my_bcs:
            bc_arr[brd, chns] = True
        self.mod.knobs.active_brdch = bc_arr

        # -- failures that occur in `_find_adc_connections`         ----
        # attribute 'Board' missing in board config group
        path = config_path + '/Boards[0]'
        brd_group = self.dgroup[path]
        brd = brd_group.attrs['Board']
        del brd_group.attrs['Board']
        with self.assertRaises(HDFMappingError):
            _map = self.map
        brd_group.attrs['Board'] = brd

        # the same board number is defined multiple times for an active
        # configuration
        path = config_path + '/Boards[0]'
        path2 = config_path + '/Boards[{}]'.format(len(my_bcs))
        brd = self.dgroup[path].attrs['Board']
        self.dgroup.create_group(path2)
        self.dgroup[path2].attrs['Board'] = brd
        with self.assertRaises(HDFMappingError):
            _map = self.map
        del self.dgroup[path2]

        # attribute 'Channel' missing in channel config group
        brd_path = config_path + '/Boards[0]'
        ch_path = brd_path + '/Channels[0]'
        ch_group = self.dgroup[ch_path]
        ch = ch_group.attrs['Channel']
        del ch_group.attrs['Channel']
        with self.assertRaises(HDFMappingError):
            _map = self.map
        ch_group.attrs['Channel'] = ch

        # -- failures that occur in `_build_configs`                ----
        # group had no identifiable configuration group
        self.dgroup.move(config_path, 'wrong config name')
        with self.assertRaises(HDFMappingError):
            _map = self.map
        self.dgroup.move('wrong config name', config_path)

        # none of the configurations are active
        self.dgroup.move(config_path, 'Configuration: Not used')
        with self.assertRaises(HDFMappingError):
            _map = self.map
        self.dgroup.move('Configuration: Not used', config_path)

        # adc connections for active config are NULL
        brd_config_names = list(self.dgroup[config_path])
        for name in brd_config_names:
            path = config_path + '/' + name
            del self.dgroup[path]
        with self.assertRaises(HDFMappingError):
            _map = self.map

    def test_map_warnings(self):
        """Test scenarios that should cause a UserWarning."""
        # 1.  a configuration group sub-group does not match naming
        #     scheme for a board config group
        # 2.  'Board' attribute for a board config group is not an int
        #     or np.integer
        # 3.  'Board' attribute for a board config group is a negative
        #     integer
        # 4.  for a none active config, two board groups define the same
        #     board number
        # 5.  a board config sub-group does not match the naming scheme
        #     for a channel group
        # 6.  'Channel' attribute for a channel config group is not an
        #     int or np.integer
        # 7.  'Channel' attribute for a channel config group is a
        #     negative integer
        # 8.  two channel config groups define the same channel number
        # 9.  the list of discovered channel numbers is NULL
        # 10. config group attribute 'Samples to average' is not
        #     convertible to int
        # 11. an expected dataset is missing
        # 12. all expected datasets for a board are missing
        #
        # setup group
        config_name = 'config01'
        adc = 'SIS 3301'
        config_path = 'Configuration: {}'.format(config_name)
        my_bcs = [(0, (0, 3, 5)),
                  (3, (0, 1, 2, 3)),
                  (5, (5, 6, 7))]
        bc_arr = self.mod.knobs.active_brdch
        bc_arr[...] = False
        for brd, chns in my_bcs:
            bc_arr[brd, chns] = True
        self.mod.knobs.n_configs = 2
        self.mod.knobs.active_brdch = bc_arr

        # -- warnings that occur in `_find_adc_connections`         ----
        # configuration group sub-group does not match board group   (1)
        # name
        brd_path = config_path + '/Boards[0]'
        new_path = config_path + '/Not a board'
        self.dgroup.move(brd_path, new_path)
        with self.assertWarns(UserWarning):
            _map = self.map
        self.dgroup.move(new_path, brd_path)

        # 'Board' attribute for a board config group is not an int   (2)
        # or np.integer
        brd_path = config_path + '/Boards[0]'
        brd_group = self.dgroup[brd_path]
        brd = brd_group.attrs['Board']
        brd_group.attrs['Board'] = 'five'
        with self.assertWarns(UserWarning):
            _map = self.map

            self.assertNotIn(
                'five',
                [conn[0] for conn in _map.configs[config_name][adc]])

        # 'Board' attribute for a board config group is a negative   (3)
        # int
        brd_group.attrs['Board'] = -1
        with self.assertWarns(UserWarning):
            _map = self.map

            self.assertNotIn(
                -1,
                [conn[0] for conn in _map.configs[config_name][adc]])
        brd_group.attrs['Board'] = brd

        # for none active config, two board config groups define     (4)
        # the same board number
        path = 'Configuration: config02/Boards[0]'
        path2 = 'Configuration: config02/Boards[1]'
        brd = self.dgroup[path2].attrs['Board']
        self.dgroup[path2].attrs['Board'] = \
            self.dgroup[path].attrs['Board']
        with self.assertWarns(UserWarning):
            _map = self.map

            self.assertNotIn(
                brd,
                [conn[0] for conn in _map.configs['config02'][adc]])
        self.dgroup[path2].attrs['Board'] = brd

        # a board config group sub-group does not match naming       (5)
        # scheme for a channel group
        brd_path = config_path + '/Boards[0]'
        ch_path = brd_path + '/Channels[0]'
        new_path = brd_path + '/Not a channel'
        self.dgroup.move(ch_path, new_path)
        with self.assertWarns(UserWarning):
            _map = self.map
        self.dgroup.move(new_path, ch_path)

        # 'Channel' attribute for a channel config group is not an   (6)
        # int or np.integer
        brd_path = config_path + '/Boards[0]'
        ch_path = brd_path + '/Channels[0]'
        ch_group = self.dgroup[ch_path]
        brd = self.dgroup[brd_path].attrs['Board']
        ch = ch_group.attrs['Channel']
        ch_group.attrs['Channel'] = 'five'
        with self.assertWarns(UserWarning):
            _map = self.map

            chs = None
            for conn in _map.configs[config_name][adc]:
                if conn[0] == brd:
                    chs = conn[1]

            if chs is None:
                self.fail('board missing from connections')
            else:
                self.assertNotIn('five', chs)

        # 'Channel' attribute for a channel config group is a        (7)
        # negative int
        ch_group.attrs['Channel'] = -1
        with self.assertWarns(UserWarning):
            _map = self.map

            chs = None
            for conn in _map.configs[config_name][adc]:
                if conn[0] == brd:
                    chs = conn[1]

            if chs is None:
                self.fail('board missing from connections')
            else:
                self.assertNotIn(-1, chs)
        ch_group.attrs['Channel'] = ch

        # two channel config groups define the same channel number   (8)
        path = brd_path + '/Channels[0]'
        path2 = brd_path + '/Channels[1]'
        brd = self.dgroup[brd_path].attrs['Board']
        ch = self.dgroup[path2].attrs['Channel']
        self.dgroup[path2].attrs['Channel'] = \
            self.dgroup[path].attrs['Channel']
        with self.assertWarns(UserWarning):
            _map = self.map

            self.assertNotIn(
                brd,
                [conn[0] for conn in _map.configs[config_name][adc]])
        self.dgroup[path2].attrs['Channel'] = ch

        # the list of discovered channel numbers is NULL             (9)
        # - this could happen if there are no channel config groups
        brd_path = config_path + '/Boards[0]'
        brd = self.dgroup[brd_path].attrs['Board']
        ch_group_names = list(self.dgroup[brd_path])
        for name in ch_group_names:
            old_path = brd_path + '/' + name
            new_path = old_path + 'Q'
            self.dgroup.move(old_path, new_path)
        with self.assertWarns(UserWarning):
            _map = self.map

            self.assertNotIn(
                brd,
                [conn[0] for conn in _map.configs[config_name][adc]])
        for name in ch_group_names:
            old_path = brd_path + '/' + name
            new_path = old_path + 'Q'
            self.dgroup.move(new_path, old_path)

        # -- warnings that occur in `_adc_info_first_pass`          ----
        # config group attribute 'Samples to average' is not        (10)
        # convertible to int
        config_group = self.dgroup[config_path]
        s2a = config_group.attrs['Samples to average']
        config_group.attrs['Samples to average'] = \
            b'Average 9.0 Samples'
        with self.assertWarns(UserWarning):
            _map = self.map

            for conn in _map.configs[config_name][adc]:
                self.assertIsNone(conn[2]['sample average (hardware)'])
        config_group.attrs['Samples to average'] = s2a

        # -- warnings that occur in `_adc_info_second_pass`         ----
        # an expected dataset is missing                            (11)
        # i.e. the config groups define a board-channel combo that
        #      does not have an existing dataset

        # all expected datasets for a given board are missing       (12)

        self.fail()

    def test_mappings(self):
        # -- One Config & One Active Config                         ----
        # setup faux group
        config_name = 'config01'
        adc = 'SIS 3301'
        my_bcs = [(0, (0, 3, 5)),
                  (3, (0, 1, 2, 3)),
                  (5, (5, 6, 7))]
        bc_arr = self.mod.knobs.active_brdch
        bc_arr[...] = False
        for brd, chns in my_bcs:
            bc_arr[brd, chns] = True
        self.mod.knobs.active_brdch = bc_arr

        # test
        _map = self.map
        self.assertDigitizerMapBasics(_map, self.dgroup)
        self.assertEqual(_map.active_configs, [config_name])
        self.assertEqual(list(_map.configs), [config_name])
        self.assertConnectionsEqual(_map, tuple(my_bcs),
                                    adc, config_name)

        # -- Multiple Configs & One Active Config                   ----
        # setup faux group
        config_name = 'config02'
        adc = 'SIS 3301'
        self.mod.knobs.n_configs = 3
        self.mod.knobs.active_config = config_name
        my_bcs = [(0, (1, 2, 3)),
                  (3, (0, 1, 2, 3))]
        bc_arr = self.mod.knobs.active_brdch
        bc_arr[...] = False
        for brd, chns in my_bcs:
            bc_arr[brd, chns] = True
        self.mod.knobs.active_brdch = bc_arr

        # test
        _map = self.map
        self.assertDigitizerMapBasics(_map, self.dgroup)
        self.assertEqual(_map.active_configs, [config_name])
        self.assertEqual(list(_map.configs), self.mod.config_names)
        self.assertConnectionsEqual(_map, tuple(my_bcs),
                                    adc, config_name)

        # -- Multiple Configs & Two Active Config                   ----
        # setup faux group
        config_names = ('config02', 'config03')
        adc = 'SIS 3301'
        self.mod.knobs.n_configs = 3
        self.mod.knobs.active_config = config_names
        my_bcs = [(0, (0, 3, 5)),
                  (3, (0, 1, 2, 3)),
                  (5, (5, 6, 7)),
                  (8, (1,))]
        bc_arr = self.mod.knobs.active_brdch
        bc_arr[...] = False
        for brd, chns in my_bcs:
            bc_arr[brd, chns] = True
        self.mod.knobs.active_brdch = bc_arr

        # test
        _map = self.map
        self.assertDigitizerMapBasics(_map, self.dgroup)
        self.assertEqual(_map.active_configs, list(config_names))
        self.assertEqual(list(_map.configs), self.mod.config_names)
        for config_name in config_names:
            self.assertConnectionsEqual(_map, tuple(my_bcs),
                                        adc, config_name)

    def test_misc(self):
        # config group missing 'Shot to average' attribute

        # config group missing 'Samples to average' attribute

        # skip a sub-group name that is not a configuration group
        self.fail()

    def test_parse_config_name(self):
        """Test HDFMapDigiSIS3301 method `_parse_config_name`."""
        _map = self.map  # type: HDFMapDigiSIS3301
        self.assertTrue(hasattr(_map, '_parse_config_name'))
        self.assertEqual(
            _map._parse_config_name("Configuration: all-probes"),
            'all-probes')
        self.assertIsNone(_map._parse_config_name('Not a config'))

    '''
    def test_active_configs(self):
        """
        Test the map's identification of the active configuration
        returned by the :attr:`active_configs` attribute.
        """
        # one config and one active config
        if self.mod.knobs.n_configs != 1:
            self.mod.knobs.n_configs = 1
        self.assertTrue(len(self.map.active_configs) == 1)
        self.assertTrue(self.map.active_configs[0] == 'config01')

        # three configs and one active config
        self.mod.knobs.n_configs = 3
        self.mod.knobs.active_config = 'config02'
        self.assertTrue(len(self.map.active_configs) == 1)
        self.assertTrue(self.map.active_configs[0] == 'config02')
    '''

    '''
    def test_adc_identification(self):
        """Test the map's identification of a configurations adc."""
        config = self.map.active_configs[0]
        self.assertEqual(self.map.configs[config]['adc'], ['SIS 3301'])
    '''

    '''
    def test_brdch_identification(self):
        """
        Test the map's identification of a configurations connected
        board and channel combinations.
        """
        # one config and one active config
        if self.mod.knobs.n_configs != 1:
            self.mod.knobs.n_configs = 1

        # get active configuration
        config = self.map.active_configs[0]

        # set active board and channel combinations
        my_bcs = [(0, (0, 3, 5)),
                  (3, (0, 1, 2, 3)),
                  (5, (5, 6, 7))]
        bc_arr = self.mod.knobs.active_brdch
        bc_arr[...] = False
        for brd, chns in my_bcs:
            bc_arr[brd, chns] = True
        self.mod.knobs.active_brdch = bc_arr

        # test board identification
        self.assertBoards(config, my_bcs)

        # test channel identification
        self.assertChannels(config, my_bcs)

    def assertBoards(self, config_name, my_bcs):
        """
        Asserts the map identified boards matches the pre-defined
        connected boards.
        """
        # get defined boards
        brds = []
        for brd, chs in my_bcs:
            brds.append(brd)

        # get map identified boards
        map_brds = []
        for conn in self.map.configs[config_name]['SIS 3301']:
            map_brds.append(conn[0])

        # assert discovered boards are equal to defined boards
        self.assertEqual(brds, map_brds)

    def assertChannels(self, config_name, my_bcs):
        """
        Asserts the map identified channels for each board matches the
        pre-defined connected channels for each board.
        """
        # get defined boards
        brds = []
        for brd, chs in my_bcs:
            brds.append(brd)

        # assert discovered channels are equal to defined channels for
        # each defined board
        for conn in self.map.configs[config_name]['SIS 3301']:
            brd = conn[0]
            ibrd = brds.index(brd)
            self.assertEqual(conn[1], my_bcs[ibrd][1])
    '''

    '''
    def test_construct_dataset_name(self):
        """
        Test behavior of the map's :meth:`construct_dataset_name`
        method.
        """
        # default inputs: board, channel
        # keywords to test:
        # - config_name
        # - adc
        # - return_info
        #
        # one config and one active config
        if self.mod.knobs.n_configs != 2:
            self.mod.knobs.n_configs = 2

        # set active config
        self.mod.knobs.active_config = 'config01'

        # set active board and channel combinations
        my_bcs = [(0, [0, 3, 5]),
                  (3, [0, 1, 2, 3]),
                  (5, [5, 6, 7])]
        bc_arr = self.mod.knobs.active_brdch
        bc_arr[...] = False
        for brd, chns in my_bcs:
            bc_arr[brd, chns] = True
        self.mod.knobs.active_brdch = bc_arr

        # get active configuration
        config = self.map.active_configs[0]

        # testing board, channel inputs
        # 1. valid brd, ch combo
        #    - exception raised
        # 2. in-valid brd, chn combo
        #    - everything should behave
        self.assertEqual(self.map.construct_dataset_name(0, 0),
                         'config01 [0:0]')
        self.assertRaises(ValueError,
                          self.map.construct_dataset_name, 0, 1)

        # testing 'adc'
        # - keyword should be unresponsive for 'SIS 3301'
        # self.assertEqual(
        #     self.map.construct_dataset_name(0, 0, adc='blah'),
        #     'config01 [0:0]')

        # testing 'config_name'
        # 1. no config_name
        #    - will auto choose active config assuming there is only
        #      one active config
        #    - tested w/ above cases
        # 2. config_name is active config
        #    - everything should works
        # 3. config_name is not active config
        #    - exception raised
        # 4. config_name is not one of the configs
        #    - exception raised
        self.assertEqual(
            self.map.construct_dataset_name(0, 0, config_name=config),
            'config01 [0:0]')
        self.assertRaises(ValueError,
                          self.map.construct_dataset_name,
                          0, 0, config_name='config02')
        self.assertRaises(ValueError,
                          self.map.construct_dataset_name,
                          0, 0, config_name='config22')

        # testing 'return_info'
        # 1. False:
        #    - only the dataset name is returned
        #    - everything above
        # 2. True
        #    - 2-element tuple is returned
        #      > 1st element is the dataset name
        #      > 2nd element is a a dict of meta-info about the
        #        connection
        #
        dset_tup = self.map.construct_dataset_name(0, 0,
                                                   return_info=True)
        self.assertIsInstance(dset_tup, tuple)
        self.assertEqual(len(dset_tup), 2)
        self.assertEqual(dset_tup[0], 'config01 [0:0]')
        self.assertIsInstance(dset_tup[1], dict)
        self.assertIn('bit', dset_tup[1])
        self.assertIn('clock rate', dset_tup[1])
        self.assertIn('shot average (software)', dset_tup[1])
        self.assertIn('sample average (hardware)', dset_tup[1])
        self.assertIn('adc', dset_tup[1])
        self.assertIn('configuration name', dset_tup[1])
        self.assertIn('digitizer', dset_tup[1])
        self.assertEqual(dset_tup[1]['bit'], 14)
        self.assertEqual(dset_tup[1]['clock rate'], (100.0, 'MHz'))
        self.assertIs(dset_tup[1]['shot average (software)'], None)
        self.assertIs(dset_tup[1]['sample average (hardware)'], None)
        self.assertEqual(dset_tup[1]['adc'], 'SIS 3301')
        self.assertEqual(dset_tup[1]['configuration name'], 'config01')
        self.assertEqual(dset_tup[1]['digitizer'], 'SIS 3301')
    '''


if __name__ == '__main__':
    ut.main()
