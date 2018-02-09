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
from ..sixk import hdfMap_control_6k
from .common import ControlTestCase

from bapsflib.lapdhdf.tests import FauxHDFBuilder

import unittest as ut


class TestSixK(ControlTestCase):
    """Test class for hdfMap_control_sixk"""

    def setUp(self):
        self.f = FauxHDFBuilder(
            add_modules={'6K Compumotor': {'n_configs': 1}})
        self.controls = self.f.modules['6K Compumotor']

    def tearDown(self):
        self.f.cleanup()

    @property
    def map(self):
        return hdfMap_control_6k(self.cgroup)

    @property
    def cgroup(self):
        return self.f['Raw data + config/6K Compumotor']

    def test_map_basics(self):
        self.assertControlMapBasics(self.map, self.cgroup)

    def test_info(self):
        self.assertEqual(self.map.info['group name'], '6K Compumotor')
        self.assertEqual(self.map.info['group path'],
                         '/Raw data + config/6K Compumotor')
        self.assertEqual(self.map.info['contype'], 'motion')

    def test_one_config_one_ml(self):
        # reset to one config and one motion list
        if self.controls.n_configs != 1:
            self.controls.n_configs = 1
        if self.controls.n_motionlists != 1:
            self.n_motionlists = 1

        # assert details
        self.assertSixKDetails()

    def test_one_config_three_ml(self):
        # reset to one config and one motion list
        if self.controls.n_configs != 1:
            self.controls.n_configs = 1
        if self.controls.n_motionlists != 3:
            self.n_motionlists = 3

        # assert details
        self.assertSixKDetails()

    def test_three_config(self):
        # reset to one config and one motion list
        if self.controls.n_configs != 3:
            self.controls.n_configs = 3

        # assert details
        self.assertSixKDetails()

    def assertSixKDetails(self):
        # test dataset names
        # TODO: test dataset names

        # test construct_dataset_names
        # TODO: how to test 'construct_dataset_names'

        # re-test all sub-group names
        self.assertSubgroupNames(self.map, self.cgroup)

        # test attribute 'group'
        self.assertEqual(self.map.group, self.cgroup)

        # test for command list
        self.assertFalse(self.map.has_command_list)

        # test attribute 'one_config_per_dataset'
        self.assertTrue(self.map.one_config_per_dset)

        # test that 'configs' attribute is setup correctly
        self.assertConfigs()

    def assertConfigs(self):
        self.assertEqual(len(self.map.configs), self.controls.n_configs)

        for config in self.map.configs:
            # keys 'dataset fields' and 'dset to numpy field' tested in
            # assertControlMapBasic
            #
            self.assertIn(config, self.controls.config_names)
            self.assertIn('probe name', self.map.configs[config])
            self.assertIn('port', self.map.configs[config])
            self.assertIn('receptacle', self.map.configs[config])
            self.assertIn('motion lists', self.map.configs[config])

            self.assertEqual(config,
                             self.map.configs[config]['receptacle'])


if __name__ == '__main__':
    ut.main()
