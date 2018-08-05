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
import os

import numpy as np
import unittest as ut

from ..sixk import hdfMap_control_6k
from .common import ControlTestCase

from unittest import mock
from bapsflib.lapdhdf.tests import FauxHDFBuilder


class TestSixK(ControlTestCase):
    """Test class for hdfMap_control_sixk"""

    def setUp(self):
        self.f = FauxHDFBuilder(
            add_modules={'6K Compumotor': {'n_configs': 1}})
        self.mod = self.f.modules['6K Compumotor']

    def tearDown(self):
        self.f.cleanup()

    @property
    def map(self):
        """Map object of control device"""
        return self.map_control(self.cgroup)

    @property
    def cgroup(self):
        """Control device group"""
        return self.f['Raw data + config/6K Compumotor']

    @staticmethod
    def map_control(group):
        """Mapping function"""
        return hdfMap_control_6k(group)

    def test_map_basics(self):
        self.assertControlMapBasics(self.map, self.cgroup)

    def test_contype(self):
        self.assertEqual(self.map.info['contype'], 'motion')

    def test_one_config_one_ml(self):
        # reset to one config and one motion list
        if self.mod.knobs.n_configs != 1:
            self.mod.knobs.n_configs = 1
        if self.mod.knobs.n_motionlists != 1:
            self.mod.knobs.n_motionlists = 1

        # assert details
        self.assertSixKDetails()

    def test_one_config_three_ml(self):
        # reset to one config and one motion list
        if self.mod.knobs.n_configs != 1:
            self.mod.knobs.n_configs = 1
        if self.mod.knobs.n_motionlists != 3:
            self.mod.knobs.n_motionlists = 3

        # assert details
        self.assertSixKDetails()

    def test_three_config(self):
        # reset to one config and one motion list
        if self.mod.knobs.n_configs != 3:
            self.mod.knobs.n_configs = 3

        # assert details
        self.assertSixKDetails()

    def assertSixKDetails(self):
        """
        Test details of a '6K Compumotor' mapping, i.e. the basic tests
        for a control device plus the unique features for the
        '6K Compumotor' group.
        """
        # define map instance
        _map = self.map

        # re-assert Mapping Basics
        self.assertControlMapBasics(_map, self.cgroup)

        # test dataset names
        # TODO: test dataset names

        # test construct_dataset_names
        # TODO: how to test 'construct_dataset_names'

        # test for command list
        self.assertFalse(_map.has_command_list)

        # test attribute 'one_config_per_dataset'
        self.assertTrue(_map.one_config_per_dset)

        # test that 'configs' attribute is setup correctly
        self.assertConfigsGeneralItems(_map)

    def assertConfigsGeneralItems(self, cmap):
        """
        Test structure of the general, polymorphic elements of the
        `configs` mapping dictionary.
        """
        self.assertEqual(len(cmap.configs),
                         self.mod.knobs.n_configs)

        for cname, config in cmap.configs.items():
            # look for '6K Compumotor' specific keys
            #
            self.assertIn(cname, self.mod.config_names)
            self.assertIn('receptacle', config)
            self.assertIn('probe', config)
            self.assertIn('motion lists', config)

            # inspect 'receptacle' item
            self.assertTrue(
                np.issubdtype(type(config['receptacle']), np.integer))
            self.assertTrue(config['receptacle'] > 0)
            self.assertEqual(cname, config['receptacle'])

            # inspect 'probe' item
            self.assertIsInstance(config['probe'], dict)
            self.assertProbeConfigDict(config['probe'])

            # inspect 'motion lists' item
            self.assertIsInstance(config['motion lists'], dict)
            for val in config['motion lists'].values():
                self.assertMLConfigDict(val)

    def assertProbeConfigDict(self, config: dict):
        """Test existence of keys for a 'probe' item config"""
        pkeys = ['probe name', 'group name', 'group path',
                 'receptacle', 'calib', 'level sy (cm)',
                 'port', 'probe channels', 'probe type', 'unnamed',
                 'sx at end (cm)', 'z']
        for key in pkeys:
            self.assertIn(key, config)

    def assertMLConfigDict(self, config: dict):
        """Test existence of keys for a 'motion list' item config"""
        self.assertIsInstance(config, dict)
        mkeys = ['group name', 'group path', 'created date',
                 'data motion count', 'motion count',
                 'delta', 'center', 'npoints']
        for key in mkeys:
            self.assertIn(key, config)


if __name__ == '__main__':
    ut.main()
