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
import unittest as ut

from . import FauxHDFBuilder

from ..hdfmappers import hdfMap


class TestHDFMap(ut.TestCase):
    """
    Test Case for :class:`~bapsflib.lapdhdf.hdfmappers.hdfMap`
    """
    def setUp(self):
        self.f = FauxHDFBuilder()
        self.map = hdfMap(self.f)

    def tearDown(self):
        self.f.cleanup()

    def test_attribute_existence(self):
        # informational attributes
        self.assertTrue(hasattr(self.map, 'msi'))
        self.assertTrue(hasattr(self.map, 'digitizers'))
        self.assertTrue(hasattr(self.map, 'main_digitizer'))
        self.assertTrue(hasattr(self.map, 'controls'))
        self.assertTrue(hasattr(self.map, 'unknowns'))
        self.assertTrue(hasattr(self.map, 'hdf_version'))

        # has indicators
        self.assertTrue(hasattr(self.map, 'has_msi_group'))
        self.assertTrue(hasattr(self.map, 'has_data_group'))
        self.assertTrue(hasattr(self.map, 'has_data_run_sequence'))
        self.assertTrue(hasattr(self.map, 'has_diagnostics'))
        self.assertTrue(hasattr(self.map, 'has_digitizers'))
        self.assertTrue(hasattr(self.map, 'has_controls'))
        self.assertTrue(hasattr(self.map, 'has_unknowns'))

    def test_hdf_version(self):
        self.assertEqual(self.map.hdf_version, '0.0.0')

    def test_base_hdf(self):
        """No diagnostics, digitizers, or control devices"""
        # existence of root groups
        self.assertTrue(self.map.has_msi_group)
        self.assertTrue(self.map.has_data_group)

        # ensure HDF is empty
        self.assertFalse(self.map.has_data_run_sequence)
        self.assertFalse(self.map.has_diagnostics)
        self.assertFalse(self.map.has_digitizers)
        self.assertFalse(self.map.has_controls)
        self.assertFalse(self.map.has_unknowns)

        # ensure format of informational attributes
        self.assertIsInstance(self.map.msi, dict)
        self.assertEqual(len(self.map.msi), 0)
        self.assertIsInstance(self.map.digitizers, dict)
        self.assertEqual(len(self.map.digitizers), 0)
        self.assertIsInstance(self.map.controls, dict)
        self.assertEqual(len(self.map.controls), 0)
        self.assertIsInstance(self.map.unknowns, list)
        self.assertEqual(len(self.map.unknowns), 0)
        self.assertIs(self.map.main_digitizer, None)

    def test_hdf_one_control(self):
        pass

    def test_hdf_one_digitizer(self):
        pass

    def test_hdf_one_diagnostic(self):
        pass

    def test_hdf_one_unknown(self):
        pass


if __name__ == '__main__':
    ut.main()
