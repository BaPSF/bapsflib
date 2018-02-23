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
from ..hdfreaddata import hdfReadData

from bapsflib.lapdhdf.tests import FauxHDFBuilder


class TestHDFReadData(ut.TestCase):
    """Test Case for hdfReadData"""
    #
    # Notes:
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
        # clean and update HDF5 file
        if len(self.f.modules) >= 1:
            self.f.remove_all_modules()
        self.f.add_module('SIS 3301', {'n_configs': 1, 'sn_size': 50})

        # not a lapdfhdf.File object but a h5py.File object
        self.assertRaises(AttributeError, hdfReadData, self.f, 0, 0)

    def test_read_w_index(self):
        """Test reading out data using `index` keyword"""
        # Test Outline:
        # 1. Dataset with sequential shot numbers
        #    a. invalid indices
        #    b. intersection_set = True
        #       - index = int, list, slice
        #    c. intersection_set = False
        #       - index = int, list, slice
        #    d. index (& shotnum) omitted
        #       - intersection_set = True/False
        #         (should be no difference)
        #       - in this condition hdfReadData assumes index
        # 2. Dataset with sequential shot numbers
        #    a. intersection_set = True
        #       - index = int, list, slice
        #    b. intersection_set = False
        #       - index = int, list, slice
        #    c. index (& shotnum) omitted
        #       - intersection_set = True/False
        #         (should be no difference)
        #       - in this condition hdfReadData assumes index
        # 3. neither index or shotnum are specified
        #    - in this condition hdfReadData assumes index
        #

        # setup HDF5 file
        if len(self.f.modules) >= 1:
            self.f.remove_all_modules()
        self.f.add_module('SIS 3301', {'n_configs': 1, 'sn_size': 50})

        # ======              Invalid `index` values              ======
        index_list = [
            [-51],
            [40, 55]
        ]
        for index in index_list:
            self.assertRaises(ValueError,
                              hdfReadData,
                              self.lapdf, 0, 0, index=index)

        # ======        Dataset w/ Sequential Shot Numbers        ======
        # ------ intersection_set = True                          ------
        index_list = [
            0,
            [2],
            [10, 20, 40],
            slice(40, 80, 3)
        ]
        index_list_correct = [
            [0],
            [2],
            [10, 20, 40],
            [40, 43, 46, 49]
        ]
        dset = self.lapdf.get(
            'Raw data + config/SIS 3301/config01 [0:0]')
        dheader = self.lapdf.get(
            'Raw data + config/SIS 3301/config01 [0:0] headers')
        for ii, ii_c in zip(index_list, index_list_correct):
            data = hdfReadData(self.lapdf, 0, 0, index=ii)
            shotnum = {'correct': dheader[ii_c, 'Shot'].view(),
                       'valid': dheader[ii_c, 'Shot'].view()}

            # perform assertion
            self.assertDataFormat(data, shotnum, dset)

    def test_read_w_shotnum(self):
        pass

    def test_digitizer_kwarg_functionality(self):
        pass

    def test_adc_kwarg_functionality(self):
        pass

    def test_add_controls(self):
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

        # check proper fill of "Nan" values
        # TODO: this section needs to be written
        if intersection_set:
            pass
        else:
            pass


if __name__ == '__main__':
    ut.main()
