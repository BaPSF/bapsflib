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
from .tempwaveform import TemporaryWaveform
from ..waveform import hdfMap_control_waveform

import h5py
import unittest as ut


class TestWaveform(ut.TestCase):
    def setUp(self):
        self.f = TemporaryWaveform(1)
        self.cgroup = self.f['Raw data + config/Waveform']
        self.cmap = hdfMap_control_waveform(self.cgroup)

    def tearDown(self):
        self.f.close()

    def test_info(self):
        self.assertTrue(hasattr(self.cmap, 'info'))
        self.assertDictEqual(self.cmap.info, {
            'group name': 'Waveform',
            'group path': '/Raw data + config/Waveform',
            'contype': 'waveform'})
