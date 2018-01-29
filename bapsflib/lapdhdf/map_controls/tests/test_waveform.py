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
#from .fauxwaveform import FauxWaveform
from ..waveform import hdfMap_control_waveform

from bapsflib.lapdhdf.tests.fauxhdfbuilder import FauxHDFBuilder

import tempfile
import h5py
import unittest as ut


class TestWaveform(ut.TestCase):
    """Test clase for hdfMap_control_waveform"""
    N_CONFIGS = 1

    def setUp(self):
        # self.tempdir = tempfile.TemporaryDirectory(prefix='hdf-test_')
        # self.f = FauxWaveform(self.N_CONFIGS, dir=self.tempdir)
        self.f = FauxHDFBuilder()
        self.controls = self.f.modules['waveform']
        self.controls.n_configs = self.N_CONFIGS
        self.cgroup = self.f['Raw data + config/Waveform']
        self.cmap = hdfMap_control_waveform(self.cgroup)

    def tearDown(self):
        self.f.cleanup()
        #self.f.close()
        #self.tempdir.cleanup()

    def test_info(self):
        self.assertTrue(hasattr(self.cmap, 'info'))
        self.assertDictEqual(self.cmap.info, {
            'group name': 'Waveform',
            'group path': '/Raw data + config/Waveform',
            'contype': 'waveform'})

    def test_contype(self):
        self.assertTrue(hasattr(self.cmap, 'contype'))
        self.assertEqual(self.cmap.contype, 'waveform')

    def test_dataset_names(self):
        self.assertEqual(self.cmap.dataset_names, ['Run time list'])

    def test_group(self):
        self.assertIs(self.cmap.group, self.cgroup)

    def test_has_command_list(self):
        self.assertTrue(self.cmap.has_command_list)

    def test_one_config_per_dataset(self):
        if self.controls.n_configs == 1:
            self.assertTrue(self.cmap.one_config_per_dset)
        else:
            self.assertFalse(self.cmap.one_config_per_dset)

    def test_spgroup_names(self):
        sgroup_names = [name
                        for name in self.cgroup
                        if isinstance(self.cgroup[name], h5py.Group)]
        self.assertEqual(self.cmap.sgroup_names, sgroup_names)

    def test_configs(self):
        self.assertTrue(hasattr(self.cmap, 'configs'))
        self.assertEqual(len(self.cmap.configs), self.N_CONFIGS)

        for config in self.cmap.configs:
            self.assertIn(config, self.controls.config_names)
            self.assertIn('IP address', self.cmap.configs[config])
            self.assertIn('device name', self.cmap.configs[config])
            self.assertIn('command list', self.cmap.configs[config])
            self.assertIn('cl pattern', self.cmap.configs[config])
            self.assertIn('dataset fields', self.cmap.configs[config])
            self.assertIn('dset field to numpy field',
                          self.cmap.configs[config])


class TestWaveform2(TestWaveform):
    """Repeat TestWaveform with 3 configurations."""
    N_CONFIGS = 3


if __name__ == '__main__':
    ut.main()
