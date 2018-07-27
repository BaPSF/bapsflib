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
from ..waveform import hdfMap_control_waveform
from .common import ControlTestCase

from bapsflib.lapdhdf.tests import FauxHDFBuilder

import numpy as np
import unittest as ut


class TestWaveform(ControlTestCase):
    """Test class for hdfMap_control_waveform"""

    def setUp(self):
        self.f = FauxHDFBuilder(
            add_modules={'Waveform': {'n_configs': 1}})
        self.mod = self.f.modules['Waveform']

    def tearDown(self):
        self.f.cleanup()

    @property
    def map(self):
        """Map object of control device"""
        return self.map_control(self.cgroup)

    @property
    def cgroup(self):
        """Control device group"""
        return self.f['Raw data + config/Waveform']

    @staticmethod
    def map_control(group):
        """Mapping function"""
        return hdfMap_control_waveform(group)

    def test_map_basics(self):
        self.assertControlMapBasics(self.map, self.cgroup)

    def test_info(self):
        self.assertEqual(self.map.info['group name'], 'Waveform')
        self.assertEqual(self.map.info['group path'],
                         '/Raw data + config/Waveform')
        self.assertEqual(self.map.info['contype'], 'waveform')

    def test_one_config(self):
        """
        Test mapping of the 'Waveform' group with only one
        configuration.
        """
        # reset to one config
        if self.mod.knobs.n_configs != 1:
            self.mod.knobs.n_configs = 1

        # assert details
        self.assertWaveformDetails()

    def test_three_configs(self):
        """
        Test mapping of the 'Waveform' group with THREE configurations.
        """
        # reset to 3 configs
        if self.mod.knobs.n_configs != 3:
            self.mod.knobs.n_configs = 3

        # assert details
        self.assertWaveformDetails()

    def assertWaveformDetails(self):
        """
        Test details of a 'Waveform' mapping, i.e. the basic tests for
        a control device plus the unique features for the 'Waveform'
        group.
        """
        # define map instance
        _map = self.map

        # re-assert Mapping Basics
        self.assertControlMapBasics(_map, self.cgroup)

        # test dataset names
        self.assertEqual(_map.dataset_names, ['Run time list'])

        # test construct_dataset_names
        self.assertEqual(_map.construct_dataset_name(), 'Run time list')

        # test for command list
        self.assertTrue(_map.has_command_list)

        # test attribute 'one_config_per_dataset'
        if self.mod.knobs.n_configs == 1:
            self.assertTrue(_map.one_config_per_dset)
        else:
            self.assertFalse(_map.one_config_per_dset)

        # test that 'configs' attribute is setup correctly
        self.assertConfigsGeneralItems(_map)

    def assertConfigsGeneralItems(self, cmap):
        """
        Test structure of the general, polymorphic elements of the
        `configs` mapping dictionary.
        """
        # only asserts 'Waveform' specific attributes
        self.assertEqual(len(cmap.configs),
                         self.mod.knobs.n_configs)

        for cname, config in cmap.configs.items():
            # keys 'dataset fields' and 'dset to numpy field' tested in
            # assertControlMapBasic
            #
            # - Note: 'command list' is not included since it is
            #         covered by assertControlMapBasics()
            #
            self.assertIn(cname, self.mod.config_names)
            self.assertIn('IP address', config)
            self.assertIn('generator device', config)
            self.assertIn('GPIB address', config)
            self.assertIn('initial state', config)


if __name__ == '__main__':
    ut.main()
