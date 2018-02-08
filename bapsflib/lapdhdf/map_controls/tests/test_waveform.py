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

import h5py
import unittest as ut


class TestWaveform(ControlTestCase):
    """Test clase for hdfMap_control_waveform"""
    # N_CONFIGS = 1

    def setUp(self):
        self.f = FauxHDFBuilder(
            add_modules={'Waveform': {'n_configs': 1}})
        self.controls = self.f.modules['Waveform']
        # self.cgroup = self.f['Raw data + config/Waveform']

    def tearDown(self):
        self.f.cleanup()

    @property
    def map(self):
        return hdfMap_control_waveform(self.cgroup)

    @property
    def cgroup(self):
        return self.f['Raw data + config/Waveform']

    def test_map_basics(self):
        self.assertControlMapBasics(self.map)

    def test_info(self):
        self.assertEqual(self.map.info['group name'], 'Waveform')
        self.assertEqual(self.map.info['group path'],
                         '/Raw data + config/Waveform')
        self.assertEqual(self.map.info['contype'], 'waveform')

    def test_one_config(self):
        # reset to one config
        if self.controls.n_configs != 1:
            self.controls.n_configs = 1

        # assert details
        self.assertWaveformDetails()

    def test_three_configs(self):
        # reset to 3 configs
        if self.controls.n_configs != 3:
            self.controls.n_configs = 3

        # assert details
        self.assertWaveformDetails()

    def assertWaveformDetails(self):
        # test dataset names
        self.assertEqual(self.map.dataset_names, ['Run time list'])

        # test attribute 'group'
        self.assertEqual(self.map.group, self.cgroup)

        # test for command list
        self.assertTrue(self.map.has_command_list)

        # test attribute 'one_config_per_dataset'
        if self.controls.n_configs == 1:
            self.assertTrue(self.map.one_config_per_dset)
        else:
            self.assertFalse(self.map.one_config_per_dset)

        # test all sub-group names
        self.assertSubgroupNames()

        # test that 'configs' attribute is setup correctly
        self.assertConfigs()

    def assertSubgroupNames(self):
        sgroup_names = [name
                        for name in self.cgroup
                        if isinstance(self.cgroup[name], h5py.Group)]
        self.assertEqual(self.map.sgroup_names, sgroup_names)

    def assertConfigs(self):
        self.assertEqual(len(self.map.configs), self.controls.n_configs)

        for config in self.map.configs:
            self.assertIn(config, self.controls.config_names)
            self.assertIn('IP address', self.map.configs[config])
            self.assertIn('device name', self.map.configs[config])
            self.assertIn('command list', self.map.configs[config])
            self.assertIn('cl pattern', self.map.configs[config])
            self.assertIn('dataset fields', self.map.configs[config])
            self.assertIn('dset field to numpy field',
                          self.map.configs[config])


if __name__ == '__main__':
    ut.main()
