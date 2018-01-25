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
import tempfile
import h5py
import numpy as np

import unittest as ut

from ..map_controls import TemporaryWaveform
from ..map_controls.waveform import hdfMap_control_waveform
from ..hdfreadcontrol import condition_shotnum_list


class TestConditionShotnumList(ut.TestCase):
    N_WAVEFORM_CONFIGS = 1

    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory(prefix='hdf-test_')
        self.f = TemporaryWaveform(self.N_WAVEFORM_CONFIGS,
                                   dir=self.tempdir)
        self.cgroup = self.f['Raw data + config/Waveform']
        self.cmap = hdfMap_control_waveform(self.cgroup)

    def tearDown(self):
        self.f.close()
        self.tempdir.cleanup()

    def test_single_shotnum(self):
        shotnum = [50]
        cdset = self.cgroup['Run time list']
        shotnumkey = 'Shot number'
        configkey = 'Configuration name'
        for cspec in self.cmap.configs:
            index, shotnum, sni = condition_shotnum_list(shotnum,
                                                         cdset,
                                                         shotnumkey,
                                                         self.cmap,
                                                         cspec)
            self.suite_of_array_assertions(index, shotnum, sni,
                                           cdset, shotnumkey, configkey,
                                           cspec)

    def test_two_shotnum(self):
        shotnum_list = [[50, 51], [50, 60], [1, self.f.sn_size - 1]]
        cdset = self.cgroup['Run time list']
        shotnumkey = 'Shot number'
        configkey = 'Configuration name'
        for shotnum in shotnum_list:
            for cspec in self.cmap.configs:
                index, shotnum, sni = \
                    condition_shotnum_list(shotnum, cdset, shotnumkey,
                                           self.cmap, cspec)
                self.suite_of_array_assertions(index, shotnum, sni,
                                               cdset, shotnumkey,
                                               configkey, cspec)

    def test_ten_shotnum(self):
        shotnum_list = [[50, 51, 52, 53, 54, 55, 56, 57, 58, 59],
                        [1, 11, 21, 31, 41, 51, 61, 71, 81, 91]]
        cdset = self.cgroup['Run time list']
        shotnumkey = 'Shot number'
        configkey = 'Configuration name'
        for shotnum in shotnum_list:
            for cspec in self.cmap.configs:
                index, shotnum, sni = \
                    condition_shotnum_list(shotnum, cdset, shotnumkey,
                                           self.cmap, cspec)
                self.suite_of_array_assertions(index, shotnum, sni,
                                               cdset, shotnumkey,
                                               configkey, cspec)

    def test_zero_shotnum(self):
        shotnum = [0]
        cdset = self.cgroup['Run time list']
        shotnumkey = 'Shot number'
        for cspec in self.cmap.configs:
            self.assertRaises(ValueError, condition_shotnum_list,
                              shotnum, cdset, shotnumkey, self.cmap,
                              cspec)

    def test_out_of_range_shotnum(self):
        # low and high
        # just high
        # low and valid
        # high and valid
        # low, high, and valid
        pass

    def suite_of_array_assertions(self, index, shotnum, sni,
                                  cdset, shotnumkey, configkey, cspec):
        # all return variables should be np.ndarray
        self.assertTrue(isinstance(index, np.ndarray))
        self.assertTrue(isinstance(shotnum, np.ndarray))
        self.assertTrue(isinstance(sni, np.ndarray))

        # all should be 1D arrays
        self.assertEqual(index.shape[0], index.size)
        self.assertEqual(shotnum.shape[0], shotnum.size)
        self.assertEqual(sni.shape[0], sni.size)

        # equate array sizes
        self.assertEqual(shotnum.size, sni.size)
        self.assertEqual(np.count_nonzero(sni), index.size)

        # shotnum[sni] = cdset[index, shotnumkey]
        self.assertTrue(np.array_equal(
            shotnum[sni], cdset[index.tolist(), shotnumkey]))

        #
        cname_arr = cdset[index.tolist(), configkey]
        for name in cname_arr:
            self.assertEqual(name.decode('utf-8'), cspec)


if __name__ == '__main__':
    ut.main(verbosity=2)
