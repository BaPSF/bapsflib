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

from bapsflib._hdf.maps import FauxHDFBuilder
from bapsflib._hdf.maps.msi.map_msi import HDFMapMSI
from bapsflib._hdf.maps.msi.templates import HDFMapMSITemplate


class TestHDFMapMSI(ut.TestCase):
    """Test class for HDFMapMSI"""

    # What to test?
    # X  1. returned object is a dictionary
    # X  2. if input is not h5py.Group instance, then TypeError is
    #       raised
    # X  3. existence of:
    #       a. mappable_devices
    #          - check it's a tuple
    # X  4. MSI group has no sub-groups
    #       - dict is empty
    # X  5. MSI has unknown & known sub-groups
    #       - only known group is added to dictionary
    # X  6. MSI has a known sub-group, but mapping fails
    #       - failed map should not be added to to dict
    # X  7. all diagnostics are mappable, but not all mappable
    #       diagnostics are included
    # X  8. MSI group has a diagnostic dataset
    #

    def setUp(self):
        self.f = FauxHDFBuilder()

    def tearDown(self):
        self.f.cleanup()

    @property
    def map(self):
        """Map of MSI Group"""
        return self.map_msi(self.msi_group)

    @property
    def msi_group(self):
        """MSI group"""
        return self.f["MSI"]

    @staticmethod
    def map_msi(group):
        """Mapping function"""
        return HDFMapMSI(group)

    def test_not_h5py_group(self):
        """Test error if object to map is not h5py.Group"""
        with self.assertRaises(TypeError):
            self.map_msi(None)

    def test_msi_scenarios(self):
        """
        Test various scenarios of mappable and non-mappable diagnostics
        in the MSI group
        """
        # the MSI group is empty                                    ----
        self.f.remove_all_modules()
        _map = self.map
        self.assertBasics(_map)
        self.assertEqual(_map, {})

        # the MSI group has all mappable diagnostics                ----
        self.f.remove_all_modules()
        self.f.add_module("Discharge", {})
        self.f.add_module("Heater", {})
        self.f.add_module("Magnetic field", {})
        _map = self.map
        self.assertBasics(_map)

        # check all diagnostics were mapped
        self.assertEqual(len(_map), 3)
        self.assertIn("Discharge", _map)
        self.assertIn("Heater", _map)
        self.assertIn("Magnetic field", _map)

        # the MSI group has mappable and unknown diagnostics        ----
        self.f.remove_all_modules()
        self.f.add_module("Discharge", {})
        self.f.add_module("Heater", {})
        self.f.add_module("Magnetic field", {})
        self.f["MSI"].create_group("Not known")
        _map = self.map
        self.assertBasics(_map)

        # check correct diagnostics were mapped
        self.assertEqual(len(_map), 3)
        self.assertIn("Discharge", _map)
        self.assertIn("Heater", _map)
        self.assertIn("Magnetic field", _map)
        self.assertNotIn("Not known", _map)

        # delete unknown group
        del self.f["MSI/Not known"]

        # the MSI group has a dataset                               ----
        self.f.remove_all_modules()
        self.f.add_module("Discharge", {})
        self.f.add_module("Heater", {})
        self.f.add_module("Magnetic field", {})
        data = np.empty((2, 100), dtype=np.float32)
        self.f["MSI"].create_dataset("A dataset", data=data)
        _map = self.map
        self.assertBasics(_map)

        # check correct diagnostics were mapped
        self.assertEqual(len(_map), 3)
        self.assertIn("Discharge", _map)
        self.assertIn("Heater", _map)
        self.assertIn("Magnetic field", _map)
        self.assertNotIn("A dataset", _map)

        # delete dataset
        del self.f["MSI/A dataset"]

        # the MSI group has a mappable diagnostic                   ----
        # but mapping fails                                         ----
        self.f.remove_all_modules()
        self.f.add_module("Discharge", {})
        self.f.add_module("Heater", {})

        # remove a dataset from 'Discharge'
        # - this will cause mapping of 'Discharge' to fail
        #
        del self.f["MSI/Discharge/Discharge current"]

        # check map
        _map = self.map
        self.assertBasics(_map)

        # check correct diagnostics were mapped
        self.assertEqual(len(_map), 1)
        self.assertIn("Heater", _map)
        self.assertNotIn("Discharge", _map)

    def assertBasics(self, msi_map: HDFMapMSI):
        # mapped object is a dictionary
        self.assertIsInstance(msi_map, dict)

        # all dict items are a mapping class
        for val in msi_map.values():
            self.assertIsInstance(val, HDFMapMSITemplate)

        # look for map attributes
        self.assertTrue(hasattr(msi_map, "mappable_devices"))

        # check attribute types
        self.assertIsInstance(msi_map.mappable_devices, tuple)


if __name__ == "__main__":
    ut.main()
