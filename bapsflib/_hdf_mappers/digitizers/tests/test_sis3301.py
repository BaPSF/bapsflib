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
# TODO: detailed tests on map.configs
# TODO: testing of shot and sample averaging identification
# - this feature has to be added to the FauxSIS3301 first
#
import unittest as ut

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

    def test_adc_identification(self):
        """Test the map's identification of a configurations adc."""
        config = self.map.active_configs[0]
        self.assertEqual(self.map.configs[config]['adc'], ['SIS 3301'])

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
        my_bcs = [(0, [0, 3, 5]),
                  (3, [0, 1, 2, 3]),
                  (5, [5, 6, 7])]
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


if __name__ == '__main__':
    ut.main()
