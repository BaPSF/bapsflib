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
import numpy as np
import unittest as ut

from ..files import File
from ..hdfreaddata import (hdfReadData, condition_shotnum)

from bapsflib.lapdhdf.tests import FauxHDFBuilder


class TestConditionShotnum(ut.TestCase):
    """Test Case for condition_shotnum"""

    def setUp(self):
        self.f = FauxHDFBuilder(
            add_modules={'SIS 3301': {'n_configs': 1, 'sn_size': 50}})
        self.mod = self.f.modules['SIS 3301']

    def tearDown(self):
        self.f.cleanup()

    @property
    def group(self):
        return self.f['Raw data + config/SIS 3301']

    @property
    def dheader(self):
        return self.group['config01 [0:0] headers']

    def test_sequential_sn(self):
        """
        Test shotnum conditioning on a dheader with sequential shot
        numbers
        """
        # setup HDF5 file
        self.mod._update()

        # test zero shot number
        self.assertZeroSN()

        # test negative shot number cases
        self.assertZeroSN()

        # ====== test cases have NO valid shot numbers ======
        # ------ intersection_set = True               ------
        sn_requested = [
            [self.mod.knobs.sn_size + 1],
            [-1, self.mod.knobs.sn_size + 1],
            [-1, 0, 60]
        ]
        for sn in sn_requested:
            self.assertRaises(ValueError,
                              condition_shotnum,
                              sn, self.dheader, 'Shot', True)

        # ------ intersection_set = False              ------
        shotnum = {}
        sn_requested = [
            [self.mod.knobs.sn_size + 1],
            [-1, self.mod.knobs.sn_size + 1],
            [-1, 0, 60]
        ]
        sn_correct = [
            [self.mod.knobs.sn_size + 1],
            [self.mod.knobs.sn_size + 1],
            [60]
        ]
        for sn_r, sn_c in zip(sn_requested, sn_correct):
            shotnum['requested'] = sn_r
            shotnum['correct'] = sn_c
            index, sn, sni = \
                condition_shotnum(sn_r, self.dheader, 'Shot',
                                  False)
            shotnum['shotnum'] = sn

            # assert
            self.assertSNSuite(shotnum, index, sni,
                               self.dheader, 'Shot')

        # ====== test in range shot number cases ======
        # ------ intersection_set = True         ------
        shotnum = {}
        sn_requested = [
            [1],
            [10],
            [5, 40],
            [30, 41],
            [1, self.mod.knobs.sn_size],
            [30, 31, 32, 33, 34, 35, 36, 37, 38, 39],
            [1, 11, 21, 31, 41]
        ]
        sn_correct = sn_requested
        for sn_r, sn_c in zip(sn_requested, sn_correct):
            shotnum['requested'] = sn_r
            shotnum['correct'] = sn_c
            index, sn, sni = \
                condition_shotnum(sn_r, self.dheader, 'Shot', True)
            shotnum['shotnum'] = sn

            # assert
            self.assertSNSuite(shotnum, index, sni,
                               self.dheader, 'Shot')

        # ------ intersection_set = False         ------
        for sn_r, sn_c in zip(sn_requested, sn_correct):
            shotnum['requested'] = sn_r
            shotnum['correct'] = sn_c
            index, sn, sni = \
                condition_shotnum(sn_r, self.dheader, 'Shot',
                                  False)
            shotnum['shotnum'] = sn

            # assert
            self.assertSNSuite(shotnum, index, sni,
                               self.dheader, 'Shot')

        # ====== test out of range shot number cases ======
        # ------ intersection_set = True             ------
        shotnum = {}
        sn_requested = [
            [1, self.mod.knobs.sn_size + 1],
            [-1, 10, self.mod.knobs.sn_size + 1],
            [48, 49, 50, 51, 52]
        ]
        sn_correct = [
            [1],
            [10],
            [48, 49, 50]
        ]
        for sn_r, sn_c in zip(sn_requested, sn_correct):
            shotnum['requested'] = sn_r
            shotnum['correct'] = sn_c
            index, sn, sni = \
                condition_shotnum(sn_r, self.dheader, 'Shot', True)
            shotnum['shotnum'] = sn

            # assert
            self.assertSNSuite(shotnum, index, sni,
                               self.dheader, 'Shot')

        # ------ intersection_set = False             ------
        shotnum = {}
        sn_requested = [
            [1, self.mod.knobs.sn_size + 1],
            [-1, 10, self.mod.knobs.sn_size + 1],
            [48, 49, 50, 51, 52]
        ]
        sn_correct = [
            [1, self.mod.knobs.sn_size + 1],
            [10, self.mod.knobs.sn_size + 1],
            [48, 49, 50, 51, 52]
        ]
        for sn_r, sn_c in zip(sn_requested, sn_correct):
            shotnum['requested'] = sn_r
            shotnum['correct'] = sn_c
            index, sn, sni = \
                condition_shotnum(sn_r, self.dheader, 'Shot',
                                  False)
            shotnum['shotnum'] = sn

            # assert
            self.assertSNSuite(shotnum, index, sni,
                               self.dheader, 'Shot')

    def test_non_sequential_sn(self):
        """
        Test shotnum conditioning on a dheader with sequential shot
        numbers
        """
        # setup HDF5 file
        # - shot numbers will have a 10 shot number jump after shot
        #   number 30
        #   [..., 29, 30, 41, 42, ...]
        #
        self.mod._update()
        sn_arr = np.arange(1, self.mod.knobs.sn_size + 1, 1)
        sn_arr[30::] = np.arange(41, 61, 1)
        self.dheader['Shot'] = sn_arr

        # test zero shot number
        self.assertZeroSN()

        # test negative shot number cases
        self.assertZeroSN()

        # ====== test cases have NO valid shot numbers ======
        # ------ intersection_set = True               ------
        sn_requested = [
            [sn_arr[-1] + 1],
            [-1, sn_arr[-1] + 1],
            [35],
            [-1, 0, 70]
        ]
        for sn in sn_requested:
            self.assertRaises(ValueError,
                              condition_shotnum,
                              sn, self.dheader, 'Shot', True)

        # ------ intersection_set = False              ------
        shotnum = {}
        sn_requested = [
            [sn_arr[-1] + 1],
            [-1, sn_arr[-1] + 1],
            [35],
            [-1, 0, 70]
        ]
        sn_correct = [
            [sn_arr[-1] + 1],
            [sn_arr[-1] + 1],
            [35],
            [70]
        ]
        for sn_r, sn_c in zip(sn_requested, sn_correct):
            shotnum['requested'] = sn_r
            shotnum['correct'] = sn_c
            index, sn, sni = \
                condition_shotnum(sn_r, self.dheader, 'Shot',
                                  False)
            shotnum['shotnum'] = sn

            # assert
            self.assertSNSuite(shotnum, index, sni,
                               self.dheader, 'Shot')

        # ====== test in range shot number cases ======
        # ------ intersection_set = True         ------
        shotnum = {}
        sn_requested = [
            [1],
            [10],
            [5, 60],
            [29, 30, 41, 42],
            [1, 11, 21, 41, 51]
        ]
        sn_correct = sn_requested
        for sn_r, sn_c in zip(sn_requested, sn_correct):
            shotnum['requested'] = sn_r
            shotnum['correct'] = sn_c
            index, sn, sni = \
                condition_shotnum(sn_r, self.dheader, 'Shot',
                                  True)
            shotnum['shotnum'] = sn

            # assert
            self.assertSNSuite(shotnum, index, sni,
                               self.dheader, 'Shot')

        # ------ intersection_set = False         ------
        for sn_r, sn_c in zip(sn_requested, sn_correct):
            shotnum['requested'] = sn_r
            shotnum['correct'] = sn_c
            index, sn, sni = \
                condition_shotnum(sn_r, self.dheader, 'Shot',
                                  False)
            shotnum['shotnum'] = sn

            # assert
            self.assertSNSuite(shotnum, index, sni,
                               self.dheader, 'Shot')

        # ====== test out of range shot number cases ======
        # ------ intersection_set = True             ------
        shotnum = {}
        sn_requested = [
            [1, sn_arr[-1] + 1],
            [-1, 10, sn_arr[-1] + 1],
            [28, 29, 30, 31, 32],
            [58, 59, 60, 61, 62]
        ]
        sn_correct = [
            [1],
            [10],
            [28, 29, 30],
            [58, 59, 60]
        ]
        for sn_r, sn_c in zip(sn_requested, sn_correct):
            shotnum['requested'] = sn_r
            shotnum['correct'] = sn_c
            index, sn, sni = \
                condition_shotnum(sn_r, self.dheader, 'Shot',
                                  True)
            shotnum['shotnum'] = sn

            # assert
            self.assertSNSuite(shotnum, index, sni,
                               self.dheader, 'Shot')

        # ------ intersection_set = False             ------
        shotnum = {}
        sn_requested = [
            [1, sn_arr[-1] + 1],
            [-1, 10, sn_arr[-1] + 1],
            [28, 29, 30, 31, 32],
            [58, 59, 60, 61, 62]
        ]
        sn_correct = [
            [1, sn_arr[-1] + 1],
            [10, sn_arr[-1] + 1],
            [28, 29, 30, 31, 32],
            [58, 59, 60, 61, 62]
        ]
        for sn_r, sn_c in zip(sn_requested, sn_correct):
            shotnum['requested'] = sn_r
            shotnum['correct'] = sn_c
            index, sn, sni = \
                condition_shotnum(sn_r, self.dheader, 'Shot',
                                  False)
            shotnum['shotnum'] = sn

            # assert
            self.assertSNSuite(shotnum, index, sni,
                               self.dheader, 'Shot')

    def test_dataset_w_one_sn(self):
        """
        Test shotnum conditioning on a dheader with a single shot
        number
        """
        # setup HDF5 file
        self.mod.knobs.sn_size = 1

        # test zero shot number
        self.assertZeroSN()

        # test negative shot number cases
        self.assertZeroSN()

        # ====== test cases have NO valid shot numbers ======
        # ------ intersection_set = True               ------
        sn_requested = [
            [-1, 0, 2],
            [5],
        ]
        for sn in sn_requested:
            self.assertRaises(ValueError,
                              condition_shotnum,
                              sn, self.dheader, 'Shot', True)

        # ------ intersection_set = False              ------
        shotnum = {}
        sn_requested = [
            [-1, 0, 2],
            [5]
        ]
        sn_correct = [
            [2],
            [5]
        ]
        for sn_r, sn_c in zip(sn_requested, sn_correct):
            shotnum['requested'] = sn_r
            shotnum['correct'] = sn_c
            index, sn, sni = \
                condition_shotnum(sn_r, self.dheader, 'Shot',
                                  False)
            shotnum['shotnum'] = sn

            # assert
            self.assertSNSuite(shotnum, index, sni,
                               self.dheader, 'Shot')

        # ====== test out of  range shot number cases ======
        # ------ intersection_set = True               ------
        shotnum = {}
        sn_requested = [
            [1],
            [-1, 0, 1, 2],
            [1, 5]
        ]
        sn_correct = [
            [1],
            [1],
            [1]
        ]
        for sn_r, sn_c in zip(sn_requested, sn_correct):
            shotnum['requested'] = sn_r
            shotnum['correct'] = sn_c
            index, sn, sni = \
                condition_shotnum(sn_r, self.dheader, 'Shot',
                                  True)
            shotnum['shotnum'] = sn

            # assert
            self.assertSNSuite(shotnum, index, sni,
                               self.dheader, 'Shot')

        # ------ intersection_set = True               ------
        shotnum = {}
        sn_requested = [
            [1],
            [-1, 0, 1, 2],
            [1, 5]
        ]
        sn_correct = [
            [1],
            [1, 2],
            [1, 5]
        ]
        for sn_r, sn_c in zip(sn_requested, sn_correct):
            shotnum['requested'] = sn_r
            shotnum['correct'] = sn_c
            index, sn, sni = \
                condition_shotnum(sn_r, self.dheader, 'Shot',
                                  False)
            shotnum['shotnum'] = sn

            # assert
            self.assertSNSuite(shotnum, index, sni,
                               self.dheader, 'Shot')

    def assertZeroSN(self):
        """Assert the zero shot number case."""
        # for intersection_set = True
        self.assertRaises(ValueError,
                          condition_shotnum,
                          [0], self.dheader, 'Shot', True)

        # for intersection_set = False
        self.assertRaises(ValueError,
                          condition_shotnum,
                          [0], self.dheader, 'Shot', False)

    def assertNegativeSN(self):
        """Assert negative shot number cases."""
        shotnum_list = [
            [-1],
            [-10, -5, 0]
        ]
        for og_sn in shotnum_list:
            # for intersection_set = True
            self.assertRaises(ValueError,
                              condition_shotnum,
                              og_sn, self.dheader, 'Shot', True)

            # for intersection_set = False
            self.assertRaises(ValueError,
                              condition_shotnum,
                              [0], self.dheader, 'Shot', False)

    def assertSNSuite(self, shotnum_dict, index, sni, dheader,
                      shotnumkey):
        """Suite of assertions for shot number conditioning"""
        # og_shotnum - original requested shot number
        # index      - index of dataset
        # shotnum    - calculate shot number array
        # sni        - boolean mask for shotnum
        #               shotnum[sni] = dheader[index, shotnumkey]
        # dheader    - digi header dataset
        # shotnumkey - field in dheader that corresponds to shot numbers
        #
        sn_r = shotnum_dict['requested']
        shotnum = shotnum_dict['shotnum']
        sn_c = shotnum_dict['correct']

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

        # all shotnum > 0
        self.assertTrue(np.all(np.where(shotnum > 0, True, False)))

        # ensure correct shot numbers were determined
        self.assertTrue(np.array_equal(shotnum, sn_c))

        # shotnum[sni] = dheader[index, shotnumkey]
        if len(index.tolist()) == 0:
            self.assertTrue(np.all(np.logical_not(sni)))
        else:
            self.assertTrue(np.array_equal(
                shotnum[sni], dheader[index.tolist(), shotnumkey]))


class TestHDFReadData(ut.TestCase):
    """Test Case for hdfReadData"""
    #
    # Notes:
    # - tests are currently performed on digitizer 'SIS 3301'
    # - board and channel args are not directly tested here since...
    #   1. they are directly passed to the construct_dataset_name()
    #      method bound to the digitizer map
    #   2. the digitizer mapping tests should be testing the
    #      construct_dataset_name() behavior
    #
    # What to test:
    # X 1. basic input handling of hdf_file
    #   2. basic format of returned object
    #   3. detailed format of returned object (probably based on inputs)
    #   4. handling of `index`
    #      - intersection_set = True/False
    #   5. handling of `shotnum`
    #      - intersection_set = True/False
    #   6. handling of kwargs
    #      - digitizer (one and two digis)
    #        > specified and not specified
    #      - adc (one and two adc's)
    #        > specified and not specified
    #      - config_name
    #        > specified and not specified
    #        > behavior depends on how map.construct_dataset_name()
    #          behaves, construct_dataset_name() should return a dataset
    #          name as long as config_name is labelled as 'active'
    #     - keep_bits
    #       > by default 'signal' field should be voltage, but
    #         keep_bits=True retains the bit values
    #   7. handling of `add_controls`
    #      - ??? this might be complex
    #   8. test attributes
    #      - info and it's keys
    #      - plasma
    #        > it's keys
    #        > .set_plasma
    #        > .set_plasma_value
    #      - dv
    #      - dt
    #      - convert_signal
    #

    def setUp(self):
        self.f = FauxHDFBuilder()

    def tearDown(self):
        self.f.cleanup()

    @property
    def lapdf(self):
        return File(self.f.filename)

    def test_hdf_file_handling(self):
        """Test handling of input argument `hdf_file`."""
        # setup HDF5 file
        if len(self.f.modules) >= 1:
            self.f.remove_all_modules()
        self.f.add_module('SIS 3301', {'n_configs': 1, 'sn_size': 50})

        # not a lapdfhdf.File object but a h5py.File object
        self.assertRaises(AttributeError, hdfReadData, self.f, 0, 0)

    def test_misc_behavior(self):
        """Test miscellaneous behavior"""
        # setup HDF5 file
        self.f.remove_all_modules()
        self.f.add_module('SIS 3301', {'n_configs': 1, 'sn_size': 50})

        # shotnum is a list, but not all elements are ints
        self.assertRaises(ValueError,
                          hdfReadData,
                          self.lapdf, 0, 0, shotnum=[1, 'blah'])
        self.assertRaises(ValueError,
                          hdfReadData,
                          self.lapdf, 0, 0, shotnum=None)
        self.assertRaises(ValueError,
                          hdfReadData,
                          self.lapdf, 0, 0, shotnum='blahe')

        # index is a list, but not all elements are ints
        self.assertRaises(TypeError,
                          hdfReadData,
                          self.lapdf, 0, 0, index=[1, 'blah'])
        self.assertRaises(TypeError,
                          hdfReadData,
                          self.lapdf, 0, 0, index=None)
        self.assertRaises(ValueError,
                          hdfReadData,
                          self.lapdf, 0, 0, index='blah')

        # test when `index` and `shotnum` are both used
        # - hdfReadData should ignore `shotnum` and default to `index`
        #
        dset = self.lapdf.get(
            'Raw data + config/SIS 3301/config01 [0:0]')
        index = [2, 3]
        shotnum = [45, 50]
        data = hdfReadData(self.lapdf, 0, 0,
                           index=index, shotnum=shotnum)
        self.assertDataFormat(data,
                              {'correct': [3, 4], 'valid': [3, 4]},
                              dset)

    def test_read_w_index(self):
        """Test reading out data using `index` keyword"""
        # Test Outline: (#see Note below)
        # 1. Dataset with sequential shot numbers
        #    a. invalid indices
        #    b. intersection_set = True
        #       - index = int, list, slice
        #    c. index (& shotnum) omitted
        #       - intersection_set = True
        #       - in this condition hdfReadData assumes index
        #
        # Note:
        # - When using `index`, intersection_set = False only comes in
        #   play when control device data is added
        # - When using `index` hdfReadData does note care if the shot
        #   numbers are sequential or not
        #

        # setup HDF5 file
        if len(self.f.modules) >= 1:
            self.f.remove_all_modules()
        self.f.add_module('SIS 3301', {'n_configs': 1, 'sn_size': 50})
        dset = self.lapdf.get(
            'Raw data + config/SIS 3301/config01 [0:0]')
        dheader = self.lapdf.get(
            'Raw data + config/SIS 3301/config01 [0:0] headers')

        # ======        Dataset w/ Sequential Shot Numbers        ======
        # ------ Invalid `index` values                           ------
        index_list = [
            [-51],
            [40, 55]
        ]
        for index in index_list:
            self.assertRaises(ValueError,
                              hdfReadData,
                              self.lapdf, 0, 0, index=index)

        # ------ intersection_set = True                          ------
        index_list = [
            0,
            [2],
            [10, 20, 40],
            slice(40, 80, 3),
            [-1]
        ]
        index_list_correct = [
            [0],
            [2],
            [10, 20, 40],
            [40, 43, 46, 49],
            [49]
        ]
        for ii, ii_c in zip(index_list, index_list_correct):
            # defined data for testing
            data = hdfReadData(self.lapdf, 0, 0, index=ii)
            shotnum = {'correct': dheader[ii_c, 'Shot'].view(),
                       'valid': dheader[ii_c, 'Shot'].view()}

            # perform assertion
            self.assertDataFormat(data, shotnum, dset)

        # ------ `index` (and `shotnum`) omitted                  ------
        # defined data for testing
        data = hdfReadData(self.lapdf, 0, 0)
        shotnum = {'correct': dheader['Shot'].view(),
                   'valid': dheader['Shot'].view()}

        # perform assertion
        self.assertDataFormat(data, shotnum, dset)

    def test_read_w_shotnum(self):
        """Test reading out data using `index` keyword"""
        # Test Outline: (#see Note below)
        # 1. Dataset with sequential shot numbers
        #    a. intersection_set = True
        #       - shotnum = int, list, slice
        #    b. intersection_set = False
        #       - shotnum = int, list, slice
        # 2. Dataset with sequential shot numbers
        #    a. intersection_set = True
        #       - shotnum = int, list, slice
        #    b. intersection_set = False
        #       - shotnum = int, list, slice
        #
        # Note:
        # - TestConditionShotnum tests hdfReadData's ability to properly
        #   identify the dataset indices corresponding to the desired
        #   shot numbers (it checks against the original dataset)
        # - TestConditionShotnum also tests hdfReadData's ability to
        #   intersect shot numbers between shotnum and the digi data,
        #   but not the control device data...intersection with control
        #   device data will be done with test_add_controls
        # - Thus, testing here should focus on the construction and
        #   basic population of data and not so much ensuring the exact
        #   dset values are populated
        # - The condition of omitting `shotnum` and `index` is not
        #   tested here since omitting both defaults to `index`. `index`
        #   is tested with test_read_w_index
        #
        # setup HDF5 file
        self.f.remove_all_modules()
        self.f.add_module('SIS 3301', {'n_configs': 1, 'sn_size': 50})
        dset = self.lapdf.get(
            'Raw data + config/SIS 3301/config01 [0:0]')
        dheader = self.lapdf.get(
            'Raw data + config/SIS 3301/config01 [0:0] headers')

        # ======        Dataset w/ Sequential Shot Numbers        ======
        # ------ intersection_set = True                          ------
        sn_list_requested = [
            1,
            [2],
            [10, 20, 30],
            [45, 110],
            slice(40, 61, 3)
        ]
        sn_list_correct = [
            [1],
            [2],
            [10, 20, 30],
            [45],
            [40, 43, 46, 49]
        ]
        sn_list_valid = sn_list_correct
        for sn_r, sn_c, sn_v in zip(sn_list_requested,
                                    sn_list_correct,
                                    sn_list_valid):
            # define data for testing
            shotnum = {'requested': sn_r,
                       'correct': sn_c,
                       'valid': sn_v}
            data = hdfReadData(self.lapdf, 0, 0, shotnum=sn_r)

            # perform assertion
            self.assertDataFormat(data, shotnum, dset)

        # ------ intersection_set = False                         ------
        sn_list_requested = [
            1,
            [2],
            [10, 20, 30],
            [45, 110],
            slice(40, 61, 3)
        ]
        sn_list_correct = [
            [1],
            [2],
            [10, 20, 30],
            [45, 110],
            [40, 43, 46, 49, 52, 55, 58]
        ]
        sn_list_valid = [
            [1],
            [2],
            [10, 20, 30],
            [45],
            [40, 43, 46, 49]
        ]
        for sn_r, sn_c, sn_v in zip(sn_list_requested,
                                    sn_list_correct,
                                    sn_list_valid):
            # define data for testing
            shotnum = {'requested': sn_r,
                       'correct': sn_c,
                       'valid': sn_v}
            data = hdfReadData(self.lapdf, 0, 0, shotnum=sn_r,
                               intersection_set=False)

            # perform assertion
            self.assertDataFormat(data, shotnum, dset,
                                  intersection_set=False)

        # ======         Dataset w/ Jump in Shot Numbers         ======
        # create shot number jump
        dheader[30::, 'Shot'] = np.arange(41, 61, 1)

        # ------ intersection_set = True                         ------
        sn_list_requested = [
            1,
            [2],
            [10, 20, 35],
            [45, 110],
            slice(34, 65, 4)
        ]
        sn_list_correct = [
            [1],
            [2],
            [10, 20],
            [45],
            [42, 46, 50, 54, 58]
        ]
        sn_list_valid = sn_list_correct
        for sn_r, sn_c, sn_v in zip(sn_list_requested,
                                    sn_list_correct,
                                    sn_list_valid):
            # define data for testing
            shotnum = {'requested': sn_r,
                       'correct': sn_c,
                       'valid': sn_v}
            data = hdfReadData(self.lapdf, 0, 0, shotnum=sn_r)

            # perform assertion
            self.assertDataFormat(data, shotnum, dset)

        # ------ intersection_set = False                        ------
        sn_list_requested = [
            1,
            [2],
            [10, 20, 35],
            [45, 110],
            slice(34, 65, 4)
        ]
        sn_list_correct = [
            [1],
            [2],
            [10, 20, 35],
            [45, 110],
            [34, 38, 42, 46, 50, 54, 58, 62]
        ]
        sn_list_valid = [
            [1],
            [2],
            [10, 20],
            [45],
            [42, 46, 50, 54, 58]
        ]
        for sn_r, sn_c, sn_v in zip(sn_list_requested,
                                    sn_list_correct,
                                    sn_list_valid):
            # define data for testing
            shotnum = {'requested': sn_r,
                       'correct': sn_c,
                       'valid': sn_v}
            data = hdfReadData(self.lapdf, 0, 0, shotnum=sn_r,
                               intersection_set=False)

            # perform assertion
            self.assertDataFormat(data, shotnum, dset,
                                  intersection_set=False)

    def test_digitizer_kwarg_functionality(self):
        """Test kwarg `digitizer` functionality"""
        #
        # Behavior:
        # 1. not specified
        #    - will default to the file_map.main_digitizer
        # 2. specified
        #    a. specified digi exists (valid)
        #       i. only one digis is in HDF5
        #          - routine runs w/ specified `digitizer`
        #       ii. multiple digis are in HDF5
        #          - routine runs w/ specified `digitizer`
        #    b. specified digi DOES NOT exist (not valid)
        #       - ValueError is raised
        #
        # Test Outline:
        # 1. `digitizer` not specified
        # 2. `digitizer` specified w/ one existing digis
        #    a. `digitizer` is valid
        #    b. `digitizer` is NOT valid
        # 3. `digitizer` specified w/ two existing digis
        #    a. `digitizer` is valid
        #    a. `digitizer` is valid (and NOT main_digitizer)
        #    b. `digitizer` is NOT valid
        #
        # setup HDF5
        if len(self.f.modules) >= 1:
            self.f.remove_all_modules()
        self.f.add_module('SIS 3301', {'n_configs': 1, 'sn_size': 50})
        main_digi = self.lapdf.file_map.main_digitizer.digi_name

        # ----- `digitizer` not specified ------
        data = hdfReadData(self.lapdf, 0, 0)
        self.assertEqual(data.info['digitizer'], main_digi)

        # ----- `digitizer` specified w/ ONE Digitizer ------
        # valid `digitizer`
        data = hdfReadData(self.lapdf, 0, 0, digitizer='SIS 3301')
        self.assertEqual(data.info['digitizer'], 'SIS 3301')

        # invalid `digitizer`
        self.assertRaises(ValueError,
                          hdfReadData,
                          self.lapdf, 0, 0, digitizer='blah')

        # ----- `digitizer` specified w/ TWO Digitizer ------
        # TODO: #3 NEEDS TO BE ADDED WHEN FausSISCrate IS CREATED
        #
        # added another digit to the HDF5 file
        # self.f.add_module('SIS Crate',
        #                   {'n_configs': 1, 'sn_size': 50})
        # main_digi = self.lapdf.file_map.main_digitizer.digi_name

        # valid `digitizer`
        data = hdfReadData(self.lapdf, 0, 0, digitizer='SIS 3301')
        self.assertEqual(data.info['digitizer'], main_digi)

        # valid `digitizer` (not main_digitizer)
        # data = hdfReadData(self.lapdf, 0, 0, digitizer='SIS Crate')
        # self.assertEqual(data.info['digitizer'], 'SIS Crate')

        # invalid `digitizer`
        self.assertRaises(ValueError,
                          hdfReadData,
                          self.lapdf, 0, 0, digitizer='blah')

    @ut.skip
    def test_adc_kwarg_functionality(self):
        pass

    @ut.skip
    def test_config_name_kwarg_functionality(self):
        pass

    def test_add_controls(self):
        # TODO: add tests for adding control device data
        # - will have to test a shotnum that is in digi data but not in
        #   control data w/ intersection_set = True
        #
        pass

    @ut.skip
    def test_obj_attributes(self):
        # 1. assertWarn(UserWarning) when keep_bits=False and no
        #    voltage offset is found
        #
        pass

    def assertDataFormat(self, data, shotnum, dset, keep_bits=False,
                         intersection_set=True):
        # subclass of data is a np.recarray
        self.assertIsInstance(data, np.recarray)

        # check all required fields are in data
        self.assertIn('shotnum', data.dtype.fields)
        self.assertIn('signal', data.dtype.fields)
        self.assertIn('xyz', data.dtype.fields)
        self.assertEqual(data.dtype['xyz'].shape, (3,))
        self.assertTrue(np.all(np.isnan(data['xyz'])))

        # check shot numbers are correct
        self.assertTrue(np.array_equal(data['shotnum'],
                                       shotnum['correct']))

        # check 'signal' dtype
        self.assertEqual(data.dtype['signal'].shape[0], dset.shape[1])
        if keep_bits:
            # signal should be bits (integer)
            self.assertTrue(np.issubdtype(data.dtype['signal'].base,
                                          np.integer))
        else:
            # signal should be volts (floating point)
            self.assertTrue(np.issubdtype(data.dtype['signal'].base,
                                          np.floating))

        # ------ Check proper fill of "NaN" values in 'signal' ------
        #
        # grab dtype
        dtype = data.dtype['signal'].base

        # find "NaN" elements
        if np.issubdtype(dtype, np.integer):
            # 'signal' is an integer
            d_nan = np.where(data['signal'] == -99999, True, False)
        elif np.issubdtype(dtype, np.floating):
            # 'signal' is an integer
            d_nan = np.isnan(data['signal'])
        else:
            # something went wrong
            raise ValueError(
                "dtype of data['signal'] is not an integer or "
                "float")

        # perform tests
        if intersection_set:
            # there should be NO "NaN" fills
            # 1. d_nan should be False for all entries
            #
            self.assertTrue(np.all(np.logical_not(d_nan)))
        else:
            # there could be "NaN" fills
            #
            # build `sni` and `sni_not`
            sni = np.isin(data['shotnum'], shotnum['valid'])
            sni_not = np.logical_not(sni)

            # test
            # 1. d_nan should be False for all sni entries
            # 2. d_nan should be True for all sni_not entries
            self.assertTrue(np.all(np.logical_not(d_nan[sni])))
            self.assertTrue(np.all(d_nan[sni_not]))

        # ------ Check proper fill of "NaN" values in 'xyz' ------
        # 'xyz' behavior:
        # 1. NO motion control device added
        #    - all 'xyz' entries should be np.nan
        # 2. motion control device added
        #    a. intersection_set = True
        #       - NO 'xyz' element should be np.nan
        #    b. intersection_set = False
        #       - some entries will be np.nan and some won't
        #
        # Note:
        # - hdfReadControl handles the construction of 'xyz' when a
        #   control device is added (#2 above).  Thus, I assume the
        #   behavior is correct by the time it gets to hdfReadData
        # - Thus, here only #1 from above is tested
        #
        # Determine if a motion control was added
        controls = data.info['added controls']
        motion_added = False
        if len(controls) != 0:
            # Possible motion control added
            for con, config in controls:
                if self.lapdf.file_map.controls[con].contype \
                        == 'motion':
                    # a motion control was added
                    motion_added = True
                    break

        # test
        if not motion_added:
            self.assertTrue(np.all(np.isnan(data['xyz'])))


if __name__ == '__main__':
    ut.main()
