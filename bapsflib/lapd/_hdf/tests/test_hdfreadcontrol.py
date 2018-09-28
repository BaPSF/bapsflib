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

from bapsflib._hdf_mappers.controls.waveform import \
    HDFMapControlWaveform
from ..files import File
from ..hdfreadcontrol import (build_shotnum_dset_relation,
                              condition_controls,
                              condition_shotnum,
                              do_shotnum_intersection,
                              HDFReadControl)

from bapsflib.lapd._hdf.tests import FauxHDFBuilder


class TestBase(ut.TestCase):
    """Base test class for all test classes here."""

    f = NotImplemented

    @classmethod
    def setUpClass(cls):
        # create HDF5 file
        super().setUpClass()
        cls.f = FauxHDFBuilder()

    def tearDown(self):
        self.f.remove_all_modules()

    @classmethod
    def tearDownClass(cls):
        # cleanup and close HDF5 file
        super().tearDownClass()
        cls.f.cleanup()


class TestConditionControls(TestBase):
    """Test Case for condition_controls"""
    # What to test:
    # 1. passing of non lapd.File object
    #    - raises AttributeError
    # 2. passing of controls as None (or not a list)
    #    - raises TypeError
    # 3. HDF5 file with no controls
    #    - raises AttributeError
    # 4. HDF5 file with one control
    #    - pass controls with
    #      a. just control name, no config
    #      b. control name and valid config
    #      c. control name and invalid config
    #      d. two control names
    # 5. HDF5 file with multiple controls
    #

    def setUp(self):
        # setup HDF5 file
        super().setUp()

    def tearDown(self):
        super().tearDown()

    @property
    def lapdf(self):
        return File(self.f.filename)

    def test_input_failures(self):
        """Test input failures of `controls`"""
        # `controls` is Null
        self.assertRaises(ValueError,
                          condition_controls, self.lapdf, [])

        # `controls` is not a string or Iterable
        self.assertRaises(TypeError,
                          condition_controls, self.lapdf, True)

        # 'controls` element is not a str or tuple
        self.assertRaises(TypeError,
                          condition_controls,
                          self.lapdf, ['Waveform', 8])

        # `controls` tuple element has length > 2
        self.assertRaises(ValueError,
                          condition_controls,
                          self.lapdf, [('Waveform', 'c1', 'c2')])

    def test_file_w_one_control(self):
        """
        Test `controls` conditioning for file with one control device.
        """
        # set one control device
        self.f.add_module('Waveform',
                          mod_args={'n_configs': 1, 'sn_size': 100})
        _lapdf = self.lapdf

        # ---- Waveform w/ one Configuration                        ----
        # conditions that work
        con_list = [
            'Waveform',
            ('Waveform', ),
            ['Waveform'],
            [('Waveform', 'config01')],
        ]
        for og_con in con_list:
            self.assertEqual(
                condition_controls(_lapdf, og_con),
                [('Waveform', 'config01')])

        # conditions that raise ValueError
        con_list = [
            ['Waveform', 'config01'],
            ['Waveform', ('Waveform', 'config01')],
            ['Waveform', '6K Compumotor'],
        ]
        for og_con in con_list:
            self.assertRaises(ValueError,
                              condition_controls, _lapdf, og_con)

        # ---- Waveform w/ three Configurations                     ----
        self.f.modules['Waveform'].knobs.n_configs = 3
        _lapdf = self.lapdf

        # conditions that work
        con_list = [
            [('Waveform', 'config01')],
            [('Waveform', 'config02')]
        ]
        for og_con in con_list:
            self.assertEqual(
                condition_controls(_lapdf, og_con),
                og_con)

        # conditions that raise ValueError
        con_list = [
            ['Waveform'],
            ['6K Compumotor', ('Waveform', 'config01')],
        ]
        for og_con in con_list:
            self.assertRaises(ValueError,
                              condition_controls, _lapdf,
                              og_con)

    def test_file_w_multiple_controls(self):
        """
        Test `controls` conditioning for file with multiple (2) control
        devices.
        """
        # set modules
        self.f.add_module('Waveform',
                          {'n_configs': 1, 'sn_size': 100})
        self.f.add_module('6K Compumotor',
                          {'n_configs': 1, 'sn_size': 100})

        # ---- 1 Waveform Config & 1 6K Config                      ----
        _lapdf = self.lapdf
        sixk_cspec = self.f.modules['6K Compumotor'].config_names[0]

        # conditions that work
        con_list = [
            ('Waveform',
             [('Waveform', 'config01')]),
            (['Waveform'],
             [('Waveform', 'config01')]),
            ([('Waveform', 'config01')],
             [('Waveform', 'config01')]),
            (['6K Compumotor'],
             [('6K Compumotor', sixk_cspec)]),
            ([('6K Compumotor', sixk_cspec)],
             [('6K Compumotor', sixk_cspec)]),
            (['Waveform', '6K Compumotor'],
             [('Waveform', 'config01'), ('6K Compumotor', sixk_cspec)]),
            (['Waveform', ('6K Compumotor', sixk_cspec)],
             [('Waveform', 'config01'), ('6K Compumotor', sixk_cspec)]),
            ([('Waveform', 'config01'), '6K Compumotor'],
             [('Waveform', 'config01'), ('6K Compumotor', sixk_cspec)]),
            ([('Waveform', 'config01'), ('6K Compumotor', sixk_cspec)],
             [('Waveform', 'config01'), ('6K Compumotor', sixk_cspec)]),
        ]
        for og_con, correct_con in con_list:
            self.assertEqual(condition_controls(_lapdf, og_con),
                             correct_con)

        # conditions that raise TypeError
        con_list = [
            ['6K Compumotor', sixk_cspec],
        ]
        for og_con in con_list:
            self.assertRaises(TypeError,
                              condition_controls, _lapdf, og_con)

        # conditions that raise ValueError
        con_list = [
            ['Waveform', 'config01'],
            ['Waveform', ('Waveform', 'config01')],
            ['6K Compumotor', ('6K Compumotor', sixk_cspec)],
            [('Waveform', 'config02')],
        ]
        for og_con in con_list:
            self.assertRaises(ValueError,
                              condition_controls, _lapdf, og_con)

        # ---- 3 Waveform Config & 1 6K Config                      ----
        self.f.modules['Waveform'].knobs.n_configs = 3
        _lapdf = self.lapdf
        sixk_cspec = self.f.modules['6K Compumotor'].config_names[0]

        # conditions that work
        con_list = [
            ([('Waveform', 'config01')],
             [('Waveform', 'config01')]),
            ([('Waveform', 'config03')],
             [('Waveform', 'config03')]),
            ('6K Compumotor',
             [('6K Compumotor', sixk_cspec)]),
            (['6K Compumotor'],
             [('6K Compumotor', sixk_cspec)]),
            ([('6K Compumotor', sixk_cspec)],
             [('6K Compumotor', sixk_cspec)]),
            ([('Waveform', 'config01'), '6K Compumotor'],
             [('Waveform', 'config01'), ('6K Compumotor', sixk_cspec)]),
            ([('Waveform', 'config02'), ('6K Compumotor', sixk_cspec)],
             [('Waveform', 'config02'), ('6K Compumotor', sixk_cspec)]),
        ]
        for og_con, correct_con in con_list:
            self.assertEqual(
                condition_controls(_lapdf, og_con),
                correct_con)

        # conditions that raise TypeError
        con_list = [
            ['6K Compumotor', sixk_cspec],
        ]
        for og_con in con_list:
            self.assertRaises(TypeError,
                              condition_controls, _lapdf, og_con)

        # conditions that raise ValueError
        con_list = [
            ['Waveform'],
            ['Waveform', 'config01'],
            ['Waveform', '6K Compumotor'],
            ['Waveform', ('6K Compumotor', sixk_cspec)],
            ['Waveform', ('Waveform', 'config01')],
            ['6K Compumotor', ('6K Compumotor', sixk_cspec)],
            [('Waveform', 'config05')],
        ]
        for og_con in con_list:
            self.assertRaises(ValueError,
                              condition_controls, _lapdf, og_con)

        # ---- 1 Waveform Config & 3 6K Config                      ----
        self.f.modules['Waveform'].knobs.n_configs = 1
        self.f.modules['6K Compumotor'].knobs.n_configs = 3
        _lapdf = self.lapdf
        sixk_cspec = self.f.modules['6K Compumotor'].config_names

        # conditions that work
        con_list = [
            (['Waveform'],
             [('Waveform', 'config01')]),
            ([('Waveform', 'config01')],
             [('Waveform', 'config01')]),
            ([('6K Compumotor', sixk_cspec[0])],
             [('6K Compumotor', sixk_cspec[0])]),
            ([('6K Compumotor', sixk_cspec[2])],
             [('6K Compumotor', sixk_cspec[2])]),
            (['Waveform', ('6K Compumotor', sixk_cspec[1])],
             [('Waveform', 'config01'),
              ('6K Compumotor', sixk_cspec[1])])
        ]
        for og_con, correct_con in con_list:
            self.assertEqual(condition_controls(_lapdf, og_con),
                             correct_con)

        # conditions that raise TypeError
        con_list = [
            ['6K Compumotor', sixk_cspec[0]],
        ]
        for og_con in con_list:
            self.assertRaises(TypeError,
                              condition_controls, _lapdf, og_con)

        # conditions that raise ValueError
        con_list = [
            ['Waveform', 'config01'],
            ['6K Compumotor'],
            ['Waveform', '6K Compumotor'],
            [('Waveform', 'config01'), '6K Compumotor'],
            ['Waveform', ('Waveform', 'config01')],
            ['6K Compumotor', ('6K Compumotor', sixk_cspec[1])],
            [('Waveform', 'config02')],
        ]
        for og_con in con_list:
            self.assertRaises(ValueError,
                              condition_controls, _lapdf, og_con)

        # ---- 3 Waveform Config & 3 6K Config                      ----
        self.f.modules['Waveform'].knobs.n_configs = 3
        _lapdf = self.lapdf
        sixk_cspec = self.f.modules['6K Compumotor'].config_names

        # conditions that work
        con_list = [
            ([('Waveform', 'config01')],
             [('Waveform', 'config01')]),
            ([('Waveform', 'config02')],
             [('Waveform', 'config02')]),
            ([('6K Compumotor', sixk_cspec[0])],
             [('6K Compumotor', sixk_cspec[0])]),
            ([('6K Compumotor', sixk_cspec[2])],
             [('6K Compumotor', sixk_cspec[2])]),
            ([('Waveform', 'config03'),
              ('6K Compumotor', sixk_cspec[1])],
             [('Waveform', 'config03'),
              ('6K Compumotor', sixk_cspec[1])])
        ]
        for og_con, correct_con in con_list:
            self.assertEqual(condition_controls(_lapdf, og_con),
                             correct_con)

        # conditions that raise TypeError
        con_list = [
            ['6K Compumotor', sixk_cspec[0]],
        ]
        for og_con in con_list:
            self.assertRaises(TypeError,
                              condition_controls, _lapdf, og_con)

        # conditions that raise ValueError
        con_list = [
            ['Waveform'],
            ['Waveform', 'config01'],
            ['6K Compumotor'],
            ['Waveform', '6K Compumotor'],
            [('Waveform', 'config01'), '6K Compumotor'],
            ['Waveform', ('Waveform', 'config01')],
            ['6K Compumotor', ('6K Compumotor', sixk_cspec[1])],
        ]
        for og_con in con_list:
            self.assertRaises(ValueError,
                              condition_controls, _lapdf,
                              og_con)

    def test_controls_w_same_contype(self):
        """
        Test `controls` conditioning for multiple devices with the
        same contype.
        """
        # set modules (1 Waveform Config & 1 6K Config)
        self.f.add_module('Waveform',
                          {'n_configs': 1, 'sn_size': 100})
        self.f.add_module('6K Compumotor',
                          {'n_configs': 1, 'sn_size': 100})
        _lapdf = self.lapdf

        # fake 6K as contype.waveform
        _lapdf.file_map.controls['6K Compumotor'].info['contype'] = \
            _lapdf.file_map.controls['Waveform'].info['contype']

        # test
        self.assertRaises(TypeError,
                          condition_controls,
                          _lapdf, ['Waveform', '6K Compumotor'])


class TestConditionShotnum(TestBase):
    """Test Case for condition_shotnum"""

    def test_shotnum_int(self):
        # shotnum <= 0 (invalid)
        sn = [-20, 0]
        for shotnum in sn:
            with self.assertRaises(ValueError):
                _sn = condition_shotnum(shotnum, {}, {})

        # shotnum > 0 (valid)
        sn = [1, 100]
        for shotnum in sn:
            _sn = condition_shotnum(shotnum, {}, {})

            self.assertIsInstance(_sn, np.ndarray)
            self.assertEqual(_sn.shape, (1,))
            self.assertTrue(np.issubdtype(_sn.dtype, np.uint32))
            self.assertEqual(_sn[0], shotnum)

    def test_shotnum_list(self):
        # not all list elements are integers
        sn = [
            [0, 1, None],
            [1.5, 2.6],
        ]
        for shotnum in sn:
            with self.assertRaises(ValueError):
                _sn = condition_shotnum(shotnum, {}, {})

        # all shotnum values are <= 0
        sn = [
            [0],
            [-20, -5, -1],
        ]
        for shotnum in sn:
            with self.assertRaises(ValueError):
                _sn = condition_shotnum(shotnum, {}, {})

        # valid shotnum lists
        sn = [
            ([0, 1, 5, 8], np.array([1, 5, 8], dtype=np.uint32)),
            ([-20, -5, 10], np.array([10], dtype=np.uint32)),
            ([1, 2, 4], np.array([1, 2, 4], dtype=np.uint32)),
        ]
        for shotnum, ex_sn in sn:
            _sn = condition_shotnum(shotnum, {}, {})

            self.assertIsInstance(_sn, np.ndarray)
            self.assertTrue(np.array_equal(_sn, ex_sn))

    def test_shotnum_slice(self):
        # create 2 fake datasets (d1 and d1)
        data = np.array(np.arange(1, 6, dtype=np.uint32),
                        dtype=[('Shot number', np.uint32)])
        self.f.create_dataset('d1', data=data)
        data['Shot number'] = np.arange(3, 8, dtype=np.uint32)
        self.f.create_dataset('d2', data=data)

        # make fake dicts
        dset_dict ={
            'c1': self.f['d1'],
            'c2': self.f['d2'],
        }
        shotnumkey_dict = {
            'c1': 'Shot number',
            'c2': 'Shot number',
        }

        # invalid shotnum slices (creats NULL arrays)
        with self.assertRaises(ValueError):
            _sn = condition_shotnum(slice(-1, -4, 1),
                                    dset_dict, shotnumkey_dict)

        # valid shotnum slices
        sn = [
            (slice(None),
             np.array([1, 2, 3, 4, 5, 6, 7], dtype=np.uint32)),
            (slice(3),
             np.array([1, 2], dtype=np.uint32)),
            (slice(1, 8, 3),
             np.array([1, 4, 7], dtype=np.uint32)),
            (slice(5, 10, 1),
             np.array([5, 6, 7, 8, 9], dtype=np.uint32)),
            (slice(-2, -1),
             np.array([6], dtype=np.uint32)),
        ]
        for shotnum, ex_sn in sn:
            _sn = condition_shotnum(shotnum, dset_dict, shotnumkey_dict)

            self.assertIsInstance(_sn, np.ndarray)
            self.assertTrue(np.array_equal(_sn, ex_sn))

        # remove datasets
        del self.f['d1']
        del self.f['d2']

    def test_shotnum_ndarray(self):
        # shotnum invalid
        # 1. is not 1 dimentional
        # 2. has fields
        # 3. is not np.integer
        # 4. would result in NULL
        sn = [
            np.array([[1, 2], [3, 5]], dtype=np.uint32),
            np.zeros((5,), dtype=[('f1', np.uint8)]),
            np.array([True, False], dtype=bool),
            np.array([5.5, 7], dtype=np.float32),
            np.array([-20, -1], dtype=np.int32),
            np.array([0], dtype=np.int32),
        ]
        for shotnum in sn:
            with self.assertRaises(ValueError):
                _sn = condition_shotnum(shotnum, {}, {})

        # shotnum valid
        sn = [
            (np.array([-5, 0, 10], np.int32),
             np.array([10], np.uint32)),
            (np.array([20, 30], np.int32),
             np.array([20, 30], np.uint32)),
        ]
        for shotnum, ex_sn in sn:
            _sn = condition_shotnum(shotnum, {}, {})

            self.assertIsInstance(_sn, np.ndarray)
            self.assertTrue(np.array_equal(_sn, ex_sn))

    def test_shotnum_invalid(self):
        # shotnum not int, List[int], slice, or ndarray
        sn = [1.5, None, True, {}]
        for shotnum in sn:
            with self.assertRaises(ValueError):
                _sn = condition_shotnum(shotnum, {}, {})


class TestBuildShotnumDsetRelation(TestBase):
    """Test Case for build_shotnum_dset_relation"""

    def setUp(self):
        # setup HDF5 file
        super().setUpClass()
        self.f.add_module('Waveform',
                          mod_args={'n_configs': 1, 'sn_size': 100})
        self.mod = self.f.modules['Waveform']

    def tearDown(self):
        super().tearDown()

    @property
    def cgroup(self):
        return self.f['Raw data + config/Waveform']

    @property
    def map(self):
        return HDFMapControlWaveform(self.cgroup)

    def test_simple_dataset(self):
        """
        Tests for a dataset containing recorded data for a single
        configuration.
        """
        # -- dset with 1 shotnum                                    ----
        self.mod.knobs.sn_size = 1
        self.assertInRangeSN()
        self.assertOutRangeSN()

        # -- typical dset with sequential shot numbers              ----
        self.mod.knobs.sn_size = 100
        self.assertInRangeSN()
        self.assertOutRangeSN()

        # -- dset with non-sequential shot numbers                  ----
        self.mod.knobs.sn_size = 100
        dset = self.cgroup['Run time list']
        data = dset[...]
        data['Shot number'] = np.append(
            np.arange(5, 25, dtype=np.uint32),
            np.append(np.arange(51, 111, dtype=np.uint32),
                      np.arange(150, 170, dtype=np.uint32)))
        del self.cgroup['Run time list']
        self.cgroup.create_dataset('Run time list', data=data)
        self.assertInRangeSN()
        self.assertOutRangeSN()

    def test_complex_dataset(self):
        """
        Tests for a dataset containing recorded data for a multiple
        configurations.
        """
        # define multiple configurations for one dataset
        self.mod.knobs.n_configs = 3

        # test in range shot number cases
        self.assertInRangeSN()

        # test out of range shot number cases
        self.assertOutRangeSN()

    def assertInRangeSN(self):
        """
        Assert shot numbers cases with in-range of dataset shot numbers.
        """
        shotnum_list = [
            [10],
            [50, 51],
            [50, 60],
            [1, self.mod.knobs.sn_size],
            [50, 51, 52, 53, 54, 55, 56, 57, 58, 59],
            [1, 11, 21, 31, 41, 51, 61, 71, 81, 91]
        ]
        cdset = self.cgroup['Run time list']
        shotnumkey = 'Shot number'
        configkey = 'Configuration name'
        for og_shotnum in shotnum_list:
            if og_shotnum == [1, 1]:
                continue

            sn_arr = np.array(og_shotnum, dtype=np.uint32)
            for cconfn in self.map.configs:
                index, shotnum, sni = \
                    build_shotnum_dset_relation(sn_arr, cdset,
                                                shotnumkey, self.map,
                                                cconfn)

                self.assertSNSuite(sn_arr, index, shotnum, sni,
                                   cdset, shotnumkey,
                                   configkey, cconfn)

    def assertOutRangeSN(self):
        """
        Assert shot number cases where some shot numbers are out of
        range of the dataset shotnumbers.
        """
        # Note: condition_shotnum() will ensure shotnum >= 0 so
        #       build_shotnum_dset_relation() does not handle this
        #
        # - one above largest shot number
        # - out of range above (sn_size+1, sn_size+10, sn_size+100)
        #   and valid
        #
        shotnum_list = [
            [self.mod.knobs.sn_size + 1],
            [self.mod.knobs.sn_size + 1, self.mod.knobs.sn_size + 10],
            [10, 15, self.mod.knobs.sn_size + 1],
            [10, 15, self.mod.knobs.sn_size + 1,
             self.mod.knobs.sn_size + 10,
             self.mod.knobs.sn_size + 100],
        ]
        cdset = self.cgroup['Run time list']
        shotnumkey = 'Shot number'
        configkey = 'Configuration name'
        for og_shotnum in shotnum_list:
            sn_arr = np.array(og_shotnum, dtype=np.uint32)
            for cconfn in self.map.configs:
                index, shotnum, sni = \
                    build_shotnum_dset_relation(sn_arr, cdset,
                                                shotnumkey, self.map,
                                                cconfn)

                self.assertSNSuite(sn_arr, index, shotnum, sni,
                                   cdset, shotnumkey,
                                   configkey, cconfn)

    def assertSNSuite(self, og_shotnum, index, shotnum, sni,
                      cdset, shotnumkey, configkey, cconfn):
        """Suite of assertions for shot number conditioning"""
        # og_shotnum - original requested shot number
        # index      - index of dataset
        # shotnum    - calculate shot number array
        # sni        - boolean mask for shotnum
        #               shotnum[sni] = cdset[index, shotnumkey]
        # cdset      - control devices dataset
        # shotnumkey - field in cdset that corresponds to shot numbers
        # configkey  - field in cdset that corresponds to configuration
        #              names
        # cconfn     - configuration name for control device
        #
        # all return variables should be np.ndarray
        self.assertTrue(isinstance(index, np.ndarray))
        self.assertTrue(isinstance(shotnum, np.ndarray))
        self.assertTrue(isinstance(sni, np.ndarray))

        # all should be 1D arrays
        self.assertEqual(index.ndim, 1)
        self.assertEqual(shotnum.ndim, 1)
        self.assertEqual(sni.ndim, 1)

        # equate array sizes
        self.assertEqual(shotnum.size, sni.size)
        self.assertEqual(np.count_nonzero(sni), index.size)

        # shotnum is og_shotnum
        self.assertTrue(np.array_equal(shotnum, og_shotnum))

        # shotnum[sni] = cdset[index, shotnumkey]
        if index.size != 0:
            self.assertTrue(np.array_equal(
                shotnum[sni], cdset[index.tolist(), shotnumkey]))
        else:
            self.assertEqual(shotnum[sni].size, 0)

        # ensure correct config is grabbed
        if index.size != 0:
            cname_arr = cdset[index.tolist(), configkey]
            for name in cname_arr:
                self.assertEqual(name.decode('utf-8'), cconfn)


class TestDoShotnumIntersection(ut.TestCase):
    """Test Case for do_shotnum_intersection"""
    def test_one_control(self):
        """Test intersection behavior with one control device"""
        # test a case that results in a null result
        shotnum = np.arange(1, 21, 1)
        shotnum_dict = {'Waveform': shotnum}
        sni_dict = {'Waveform': np.zeros(shotnum.shape, dtype=bool)}
        index_dict = {'Waveform': np.array([])}
        self.assertRaises(ValueError,
                          do_shotnum_intersection,
                          shotnum, shotnum_dict, sni_dict, index_dict)

        # test a working case
        shotnum = np.arange(1, 21, 1)
        shotnum_dict = {'Waveform': shotnum}
        sni_dict = {'Waveform': np.zeros(shotnum.shape, dtype=bool)}
        index_dict = {'Waveform': np.array([5, 6, 7])}
        sni_dict['Waveform'][[5, 6, 7]] = True
        shotnum, shotnum_dict, sni_dict, index_dict = \
            do_shotnum_intersection(shotnum,
                                    shotnum_dict,
                                    sni_dict,
                                    index_dict)
        self.assertTrue(np.array_equal(shotnum, [6, 7, 8]))
        self.assertTrue(np.array_equal(shotnum,
                                       shotnum_dict['Waveform']))
        self.assertTrue(np.array_equal(sni_dict['Waveform'],
                                       [True] * 3))
        self.assertTrue(np.array_equal(index_dict['Waveform'],
                                       [5, 6, 7]))

    def test_two_controls(self):
        """Test intersection behavior with two control devices"""
        # test a case that results in a null result
        shotnum = np.arange(1, 21, 1)
        shotnum_dict = {
            'Waveform': shotnum,
            '6K Compumotor': shotnum
        }
        sni_dict = {
            'Waveform': np.zeros(shotnum.shape, dtype=bool),
            '6K Compumotor': np.zeros(shotnum.shape, dtype=bool)
        }
        index_dict = {
            'Waveform': np.array([]),
            '6K Compumotor': np.array([5, 6, 7])
        }
        sni_dict['6K Compumotor'][[6, 7, 8]] = True
        self.assertRaises(ValueError,
                          do_shotnum_intersection,
                          shotnum, shotnum_dict, sni_dict, index_dict)

        # test a working case
        shotnum = np.arange(1, 21, 1)
        shotnum_dict = {
            'Waveform': shotnum,
            '6K Compumotor': shotnum
        }
        sni_dict = {
            'Waveform': np.zeros(shotnum.shape, dtype=bool),
            '6K Compumotor': np.zeros(shotnum.shape, dtype=bool)
        }
        index_dict = {
            'Waveform': np.array([5, 6]),
            '6K Compumotor': np.array([5, 6, 7])
        }
        sni_dict['Waveform'][[5, 6]] = True
        sni_dict['6K Compumotor'][[5, 6, 7]] = True
        shotnum, shotnum_dict, sni_dict, index_dict = \
            do_shotnum_intersection(shotnum,
                                    shotnum_dict,
                                    sni_dict,
                                    index_dict)
        self.assertTrue(np.array_equal(shotnum, [6, 7]))
        for key in shotnum_dict:
            self.assertTrue(np.array_equal(shotnum, shotnum_dict[key]))
            self.assertTrue(np.array_equal(sni_dict[key], [True] * 2))
            self.assertTrue(np.array_equal(index_dict[key], [5, 6]))


class TestHDFReadControl(TestBase):
    """Test Case for HDFReadControl class."""
    # Note:
    # - TestBuildShotnumDsetRelation tests HDFReadControl's ability to
    #   properly identify the dataset indices corresponding to the
    #   desired shot numbers (it checks against the original dataset)
    # - TestDoIntersection tests HDFReadControl's ability to intersect
    #   all shot numbers between the datasets and shotnum
    # - Thus, testing here should focus on the construction and
    #   basic population of cdata and not so much ensuring the exact
    #   dset values are populated
    #
    # What to test:
    # 1. handling of hdf_file input
    # 2. output object format
    # 3. reading from one control dataset
    #    - for all cases ensure fields are properly transferred over
    #    - datasets w/ sequential and non-sequential shot numbers
    #    - intersection_set = True/False
    #      > shotnum is omitted, int, list, or slice
    #      > proper fill of "NaN" values
    # 4. reading from two control datasets
    #    - for all cases ensure fields are properly transferred over
    #    - datasets w/ sequential and non-sequential shot numbers
    #    - intersection_set = True/False
    #      > shotnum is omitted, int, list, or slice
    #      > proper fill of "NaN" values
    # 5. command list functionality
    #    - for command list datasets, commands are properly assigned
    #

    def setUp(self):
        super(TestHDFReadControl, self).setUp()

    def tearDown(self):
        super(TestHDFReadControl, self).tearDown()

    @property
    def lapdf(self):
        return File(self.f.filename)

    def test_hdf_file_handling(self):
        """Test handling of input argument `hdf_file`."""
        # Note:
        # - all possibilities of the 'controls' argument are not tested
        #   here since they are essentially tested with the
        #   TestConditionControls class
        #
        # not a lapdfhdf.File object but a h5py.File object
        self.assertRaises(TypeError, HDFReadControl, self.f, [])

        # a lapd.File object with no control devices
        self.assertRaises(ValueError, HDFReadControl, self.lapdf, [])

        # improper (empty) controls argument
        self.f.add_module('Waveform')
        self.assertRaises(ValueError, HDFReadControl, self.lapdf, [])
        self.assertRaises(ValueError,
                          HDFReadControl, self.lapdf, [],
                          assume_controls_conditioned=True)

    def test_output_obj_format(self):
        """Test format of returned object."""
        # 1. output data is a np.recarray
        # 2. has attributes 'info' and 'configs' (both are dicts)
        #
        # remove all modules
        self.f.remove_all_modules()
        self.f.add_module('Waveform')
        cdata = HDFReadControl(self.lapdf, ['Waveform'], shotnum=1)

        # subclass of cdata is a np.recarray
        self.assertIsInstance(cdata, np.recarray)

        # required fields in all cdata
        self.assertIn('shotnum', cdata.dtype.fields)

        # look for required attributes
        # TODO: attribute 'configs' needs to be added
        #
        self.assertTrue(hasattr(cdata, 'info'))
        # self.assertTrue(hasattr(cdata, 'configs'))

    def test_misc_behavior(self):
        """Test miscellaneous behavior"""
        # setup HDF5 file
        self.f.remove_all_modules()
        self.f.add_module('Waveform')

        # shotnum is a list, but not all elements are ints
        self.assertRaises(ValueError,
                          HDFReadControl,
                          self.lapdf, ['Waveform'], shotnum=[1, 'blah'])

        # shotnum is not int, list, or slice
        self.assertRaises(ValueError,
                          HDFReadControl,
                          self.lapdf, ['Waveform'], shotnum=None)
        self.assertRaises(ValueError,
                          HDFReadControl,
                          self.lapdf, ['Waveform'], shotnum='blah')

    def test_single_control(self):
        """
        Testing HDF5 with one control device that saves data from
        ONE configuration into ONE dataset. (Simple Control)
        """
        # Test Outline:
        # 1. Dataset with sequential shot numbers
        #    a. intersection_set = True
        #       - shotnum = int, list, slice
        #    b. intersection_set = False
        #       - shotnum = int, list, slice
        #    c. shotnum omitted
        #       - intersection_set = True/False
        #         (should be no difference)
        # 2. Dataset with a jump in shot numbers
        #    a. intersection_set = True
        #       - shotnum = int, list, slice
        #    b. intersection_set = False
        #       - shotnum = int, list, slice
        #    c. shotnum omitted
        #       - intersection_set = True/False
        #
        # clean HDF5 file
        self.f.remove_all_modules()
        self.f.add_module('6K Compumotor',
                          {'n_configs': 1, 'sn_size': 50,
                           'n_motionlists': 1})
        sixk_cspec = self.f.modules['6K Compumotor'].config_names[0]
        control = [('6K Compumotor', sixk_cspec)]
        control_plus = [('6K Compumotor', sixk_cspec,
                         {'sn_requested': [],
                          'sn_correct': [],
                          'sn_valid': []})]

        # ====== Dataset w/ Sequential Shot Numbers ======
        # ------ intersection_set = True            ------
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
            # update control plus
            control_plus[0][2]['sn_requested'] = sn_r
            control_plus[0][2]['sn_correct'] = sn_c
            control_plus[0][2]['sn_valid'] = sn_v

            # grab requested control data
            cdata = HDFReadControl(self.lapdf, control, shotnum=sn_r)

            # assert cdata format
            self.assertCDataFormat(cdata, control_plus, sn_c)

        # ====== Dataset w/ Sequential Shot Numbers ======
        # ------ intersection_set = False           ------
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
            # update control plus
            control_plus[0][2]['sn_requested'] = sn_r
            control_plus[0][2]['sn_correct'] = sn_c
            control_plus[0][2]['sn_valid'] = sn_v

            # grab requested control data
            cdata = HDFReadControl(self.lapdf, control,
                                   shotnum=sn_r,
                                   intersection_set=False)
            # assert cdata format
            self.assertCDataFormat(cdata, control_plus, sn_c,
                                   intersection_set=False)

        # ====== Dataset w/ Sequential Shot Numbers ======
        # ------ shotnum omitted                    ------
        # ------ intersection_set = True/False      ------
        sn_c = np.arange(1, 51, 1).tolist()
        control_plus[0][2]['sn_requested'] = slice(None)
        control_plus[0][2]['sn_correct'] = sn_c
        control_plus[0][2]['sn_valid'] = sn_c

        # grab & test data for intersection_set=True
        cdata = HDFReadControl(self.lapdf, control)
        self.assertCDataFormat(cdata, control_plus, sn_c)

        # grab & test data for intersection_set=False
        cdata = HDFReadControl(self.lapdf, control,
                               intersection_set=False)
        self.assertCDataFormat(cdata, control_plus, sn_c,
                               intersection_set=False)

        # ====== Dataset w/ a Jump in Shot Numbers ======
        # create a jump in the dataset
        dset_name = self.f.modules['6K Compumotor']._configs[
            sixk_cspec]['dset name']
        dset = self.f.modules['6K Compumotor'][dset_name]
        sn_arr = dset['Shot number']
        sn_arr[30::] = np.arange(41, 61, 1, dtype=sn_arr.dtype)
        dset['Shot number'] = sn_arr

        # ====== Dataset w/ a Jump in Shot Numbers ======
        # ------ intersection_set = True           ------
        sn_list_requested = [
            1,
            [2],
            [10, 20, 30],
            [22, 36, 110],
            slice(38, 75, 3)
        ]
        sn_list_correct = [
            [1],
            [2],
            [10, 20, 30],
            [22],
            [41, 44, 47, 50, 53, 56, 59]
        ]
        sn_list_valid = sn_list_correct
        for sn_r, sn_c, sn_v in zip(sn_list_requested,
                                    sn_list_correct,
                                    sn_list_valid):
            # update control plus
            control_plus[0][2]['sn_requested'] = sn_r
            control_plus[0][2]['sn_correct'] = sn_c
            control_plus[0][2]['sn_valid'] = sn_v

            # grab requested control data
            cdata = HDFReadControl(self.lapdf, control, shotnum=sn_r)

            # assert cdata format
            self.assertCDataFormat(cdata, control_plus, sn_c)

        # ====== Dataset w/ a Jump in Shot Numbers ======
        # ------ intersection_set = False          ------
        sn_list_requested = [
            1,
            [2],
            [10, 20, 30],
            [22, 36, 110],
            slice(38, 75, 3)
        ]
        sn_list_correct = [
            [1],
            [2],
            [10, 20, 30],
            [22, 36, 110],
            [38, 41, 44, 47, 50, 53, 56, 59, 62, 65, 68, 71, 74]
        ]
        sn_list_valid = [
            [1],
            [2],
            [10, 20, 30],
            [22],
            [41, 44, 47, 50, 53, 56, 59]
        ]
        for sn_r, sn_c, sn_v in zip(sn_list_requested,
                                    sn_list_correct,
                                    sn_list_valid):
            # update control plus
            control_plus[0][2]['sn_requested'] = sn_r
            control_plus[0][2]['sn_correct'] = sn_c
            control_plus[0][2]['sn_valid'] = sn_v

            # grab requested control data
            cdata = HDFReadControl(self.lapdf, control,
                                   shotnum=sn_r,
                                   intersection_set=False)

            # assert cdata format
            self.assertCDataFormat(cdata, control_plus, sn_c,
                                   intersection_set=False)

        # ====== Dataset w/ a Jump in Shot Numbers ======
        # ------ shotnum omitted                   ------
        # ------ intersection_set = True/False     ------
        sn_c = sn_arr.tolist()
        control_plus[0][2]['sn_requested'] = slice(None)
        control_plus[0][2]['sn_correct'] = sn_c
        control_plus[0][2]['sn_valid'] = sn_c

        # grab & test data for intersection_set=True
        cdata = HDFReadControl(self.lapdf, control)
        self.assertCDataFormat(cdata, control_plus, sn_c)

        # grab & test data for intersection_set=False
        sn_c = np.arange(1, 61, 1).tolist()
        control_plus[0][2]['sn_correct'] = sn_c
        cdata = HDFReadControl(self.lapdf, control,
                               intersection_set=False)
        self.assertCDataFormat(cdata, control_plus, sn_c,
                               intersection_set=False)

    def test_two_controls(self):
        """
        Testing HDF5 with two control devices.  Each control is setup
        with one configuration each.
        """
        # Test Outline:
        # 1. Both Datasets have matching sequential shot numbers
        #    a. intersection_set = True
        #       - shotnum = int, list, slice
        #    b. intersection_set = False
        #       - shotnum = int, list, slice
        #    c. shotnum omitted
        #       - intersection_set = True/False
        #         (should be no difference)
        # 2. Both Datasets have jumps in shot numbers
        #    a. intersection_set = True
        #       - shotnum = int, list, slice
        #    b. intersection_set = False
        #       - shotnum = int, list, slice
        #    c. shotnum omitted
        #       - intersection_set = True/False
        #
        # clean HDF5 file
        self.f.remove_all_modules()
        self.f.add_module('6K Compumotor',
                          {'n_configs': 1, 'sn_size': 50,
                           'n_motionlists': 1})
        self.f.add_module('Waveform', {'n_configs': 1, 'sn_size': 50})
        sixk_cspec = self.f.modules['6K Compumotor'].config_names[0]
        control = [('Waveform', 'config01'),
                   ('6K Compumotor', sixk_cspec)]
        control_plus = [('Waveform', 'config01',
                         {'sn_requested': [],
                          'sn_correct': [],
                          'sn_valid': []}),
                        ('6K Compumotor', sixk_cspec,
                         {'sn_requested': [],
                          'sn_correct': [],
                          'sn_valid': []})]

        # ==== Both Datasets Have Matching Sequential Shot Numbers ====
        # ---- intersection_set = True                             ----
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
        sn_list_waveform = sn_list_correct
        sn_list_sixk = sn_list_correct
        for sn_r, sn_c, sn_w, sn_sk in zip(sn_list_requested,
                                           sn_list_correct,
                                           sn_list_waveform,
                                           sn_list_sixk):
            # update control plus
            # 0 = Waveform
            # 1 = 6K Compumotor
            #
            control_plus[0][2]['sn_requested'] = sn_r
            control_plus[0][2]['sn_correct'] = sn_c
            control_plus[0][2]['sn_valid'] = sn_w
            control_plus[1][2]['sn_requested'] = sn_r
            control_plus[1][2]['sn_correct'] = sn_c
            control_plus[1][2]['sn_valid'] = sn_sk

            # grab requested control data
            cdata = HDFReadControl(self.lapdf, control, shotnum=sn_r)

            # assert cdata format
            self.assertCDataFormat(cdata, control_plus, sn_c)

        # ==== Both Datasets Have Matching Sequential Shot Numbers ====
        # ---- intersection_set = False                            ----
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
        sn_list_waveform = [
            [1],
            [2],
            [10, 20, 30],
            [45],
            [40, 43, 46, 49]
        ]
        sn_list_sixk = sn_list_waveform
        for sn_r, sn_c, sn_w, sn_sk in zip(sn_list_requested,
                                           sn_list_correct,
                                           sn_list_waveform,
                                           sn_list_sixk):
            # update control plus
            # 0 = Waveform
            # 1 = 6K Compumotor
            #
            control_plus[0][2]['sn_requested'] = sn_r
            control_plus[0][2]['sn_correct'] = sn_c
            control_plus[0][2]['sn_valid'] = sn_w
            control_plus[1][2]['sn_requested'] = sn_r
            control_plus[1][2]['sn_correct'] = sn_c
            control_plus[1][2]['sn_valid'] = sn_sk

            # grab requested control data
            cdata = HDFReadControl(self.lapdf, control, shotnum=sn_r,
                                   intersection_set=False)

            # assert cdata format
            self.assertCDataFormat(cdata, control_plus, sn_c,
                                   intersection_set=False)

        # ==== Both Datasets Have Matching Sequential Shot Numbers ====
        # ---- shotnum omitted                                     ----
        # ---- intersection_set = True/False                       ----
        # update control plus
        # 0 = Waveform
        # 1 = 6K Compumotor
        #
        sn_c = np.arange(1, 51, 1).tolist()
        control_plus[0][2]['sn_requested'] = slice(None)
        control_plus[0][2]['sn_correct'] = sn_c
        control_plus[0][2]['sn_valid'] = sn_c
        control_plus[1][2]['sn_requested'] = slice(None)
        control_plus[1][2]['sn_correct'] = sn_c
        control_plus[1][2]['sn_valid'] = sn_c

        # grab & test data for intersection_set=True
        cdata = HDFReadControl(self.lapdf, control)
        self.assertCDataFormat(cdata, control_plus, sn_c)

        # grab & test data for intersection_set=False
        cdata = HDFReadControl(self.lapdf, control,
                               intersection_set=False)
        self.assertCDataFormat(cdata, control_plus, sn_c,
                               intersection_set=False)

        # ====      Both Datasets Have Jumps in Shot Numbers      ====
        # ---- Waveform has a jump of 10 at sn = 20               ----
        # ---- 6K Compumotor has a jump of 8 at sn = 30           ----
        #
        # Place sn jump in 'Waveform'
        dset_name = self.f.modules['Waveform']._configs[
            'config01']['dset name']
        dset = self.f.modules['Waveform'][dset_name]
        sn_arr = dset['Shot number']
        sn_arr[20::] = np.arange(31, 61, 1, dtype=sn_arr.dtype)
        dset['Shot number'] = sn_arr
        sn_wave = sn_arr

        # Place sn jump in '6K Compumotor'
        dset_name = self.f.modules['6K Compumotor']._configs[
            sixk_cspec]['dset name']
        dset = self.f.modules['6K Compumotor'][dset_name]
        sn_arr = dset['Shot number']
        sn_arr[30::] = np.arange(38, 58, 1, dtype=sn_arr.dtype)
        dset['Shot number'] = sn_arr
        sn_sixk = sn_arr

        # ====      Both Datasets Have Jumps in Shot Numbers      ====
        # ---- intersection_set = True                            ----
        sn_list_requested = [
            1,
            [2],
            [10, 20, 30],
            [22, 45, 110],
            slice(35, 50, 3)
        ]
        sn_list_correct = [
            [1],
            [2],
            [10, 20],
            [45],
            [38, 41, 44, 47]
        ]
        sn_list_waveform = sn_list_correct
        sn_list_sixk = sn_list_correct
        for sn_r, sn_c, sn_w, sn_sk in zip(sn_list_requested,
                                           sn_list_correct,
                                           sn_list_waveform,
                                           sn_list_sixk):
            # update control plus
            # 0 = Waveform
            # 1 = 6K Compumotor
            #
            control_plus[0][2]['sn_requested'] = sn_r
            control_plus[0][2]['sn_correct'] = sn_c
            control_plus[0][2]['sn_valid'] = sn_w
            control_plus[1][2]['sn_requested'] = sn_r
            control_plus[1][2]['sn_correct'] = sn_c
            control_plus[1][2]['sn_valid'] = sn_sk

            # grab requested control data
            cdata = HDFReadControl(self.lapdf, control, shotnum=sn_r)

            # assert cdata format
            self.assertCDataFormat(cdata, control_plus, sn_c)

        # ====      Both Datasets Have Jumps in Shot Numbers      ====
        # ---- intersection_set = False                           ----
        sn_list_requested = [
            1,
            [2],
            [10, 20, 30],
            [22, 45, 110],
            slice(35, 50, 3)
        ]
        sn_list_correct = [
            [1],
            [2],
            [10, 20, 30],
            [22, 45, 110],
            [35, 38, 41, 44, 47]
        ]
        sn_list_waveform = [
            [1],
            [2],
            [10, 20],
            [45],
            [35, 38, 41, 44, 47]
        ]
        sn_list_sixk = [
            [1],
            [2],
            [10, 20, 30],
            [22, 45],
            [38, 41, 44, 47]
        ]
        for sn_r, sn_c, sn_w, sn_sk in zip(sn_list_requested,
                                           sn_list_correct,
                                           sn_list_waveform,
                                           sn_list_sixk):
            # update control plus
            # 0 = Waveform
            # 1 = 6K Compumotor
            #
            control_plus[0][2]['sn_requested'] = sn_r
            control_plus[0][2]['sn_correct'] = sn_c
            control_plus[0][2]['sn_valid'] = sn_w
            control_plus[1][2]['sn_requested'] = sn_r
            control_plus[1][2]['sn_correct'] = sn_c
            control_plus[1][2]['sn_valid'] = sn_sk

            # grab requested control data
            cdata = HDFReadControl(self.lapdf, control, shotnum=sn_r,
                                   intersection_set=False)

            # assert cdata format
            self.assertCDataFormat(cdata, control_plus, sn_c,
                                   intersection_set=False)

        # ====      Both Datasets Have Jumps in Shot Numbers      ====
        # ---- shotnum omitted                                     ----
        # ---- intersection_set = True/False                       ----
        # update control plus
        # 0 = Waveform
        # 1 = 6K Compumotor
        #
        sn_c = np.intersect1d(sn_wave, sn_sixk).tolist()
        control_plus[0][2]['sn_requested'] = slice(None)
        control_plus[0][2]['sn_correct'] = sn_c
        control_plus[0][2]['sn_valid'] = sn_c
        control_plus[1][2]['sn_requested'] = slice(None)
        control_plus[1][2]['sn_correct'] = sn_c
        control_plus[1][2]['sn_valid'] = sn_c

        # grab & test data for intersection_set=True
        cdata = HDFReadControl(self.lapdf, control)
        self.assertCDataFormat(cdata, control_plus, sn_c)

        # grab & test data for intersection_set=False
        sn_c = np.arange(1, 61, 1).tolist()
        control_plus[0][2]['sn_correct'] = sn_c
        control_plus[0][2]['sn_valid'] = \
            np.intersect1d(sn_c, sn_wave).tolist()
        control_plus[1][2]['sn_correct'] = sn_c
        control_plus[1][2]['sn_valid'] = \
            np.intersect1d(sn_c, sn_sixk).tolist()
        cdata = HDFReadControl(self.lapdf, control,
                               intersection_set=False)
        self.assertCDataFormat(cdata, control_plus, sn_c,
                               intersection_set=False)

    @ut.skip
    def test_command_list_functionality(self):
        """
        Testing HDF5 with a control device that utilizes a command list.
        """
        # TODO: command list functionality
        # clean HDF5 file
        # self.f.remove_all_modules()
        pass

    def assertCDataFormat(self, cdata, control_plus, sn_correct,
                          intersection_set=True):
        """Assertion for detailed format of returned data object."""
        # cdata            - returned data object of HDFReadControl()
        # control_plus     - control name, control configureation, and
        #                    expected shot numbers ('sn_valid')
        # sn_correct       - the correct shot numbers
        #                    (i.e. cdata['shotnumm'] == sn_correct)
        # intersection_set - whether cdata is generated w/
        #                    intersection_set=True (or False)
        #

        # check shot numbers are correct
        self.assertTrue(np.array_equal(cdata['shotnum'],
                                       sn_correct))

        # perform assertions based on control
        for control in control_plus:
            # extract necessary content
            device = control[0]
            config = control[1]
            # sn_r = control[2]['sn_requested']
            # sn_c = control[2]['sn_correct']
            sn_v = control[2]['sn_valid']

            # retrieve control mapping
            cmap = self.lapdf.file_map.controls[device]

            # gather fields that should be in cdata for this control
            # device
            fields = list(cmap.configs[config]['state values'])

            # check that all fields are in cdata
            for field in fields:
                self.assertIn(field, cdata.dtype.fields)

            # Check proper fill of "NaN" values
            #
            sni = np.isin(cdata['shotnum'], sn_v)
            sni_not = np.logical_not(sni)
            for field in fields:
                if field == 'shotnum':
                    continue

                # dtype for field
                dtype = cdata.dtype[field].base

                # assert "NaN" fills
                if intersection_set:
                    # there should be NO NaN fills
                    if np.issubdtype(dtype, np.integer):
                        cd_nan = np.where(cdata[field] == -99999,
                                          True, False)
                    elif np.issubdtype(dtype, np.floating):
                        cd_nan = np.isnan(cdata[field])
                    elif np.issubdtype(dtype, np.flexible):
                        cd_nan = np.where(cdata[field] == '',
                                          True, False)

                    # test
                    # 1. cd_nan should be False for all entries
                    # 2. sni should be True for all entries
                    self.assertTrue(np.all(np.logical_not(cd_nan)))
                    self.assertTrue(np.all(sni))
                else:
                    # there is a possibility for NaN fill
                    if np.issubdtype(dtype, np.integer):
                        cd_nan = np.where(cdata[field] == -99999,
                                          True, False)
                    elif np.issubdtype(dtype, np.floating):
                        cd_nan = np.isnan(cdata[field])
                    elif np.issubdtype(dtype, np.flexible):
                        cd_nan = np.where(cdata[field] == '',
                                          True, False)

                    # test
                    # 1. cd_nan should be False for all sni entries
                    # 2. cd_nan should be True for all sni_not entries
                    self.assertTrue(np.all(np.logical_not(cd_nan[sni])))
                    self.assertTrue(np.all(cd_nan[sni_not]))


if __name__ == '__main__':
    ut.main()
