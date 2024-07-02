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
from bapsflib._hdf.maps.controls.map_controls import HDFMapControls
from bapsflib._hdf.maps.controls.templates import (
    HDFMapControlCLTemplate,
    HDFMapControlTemplate,
)


class TestHDFMapControls(ut.TestCase):
    """Test class for HDFMapControls"""

    # What to test?
    # X  1. returned object is a dictionary
    # X  2. if input is not h5py.Group instance, then TypeError is
    #       raised
    # X  3. existence of:
    #       a. mappable_devices
    #          - check it's a tuple
    # X  4. data group has no sub-groups
    #       - dict is empty
    # X  5. data group has unknown & known control device sub-groups
    #       - only known group is added to dictionary
    #    6. data group has a known control sub-group, but mapping fails
    #       - failed map should not be added to to dict
    # X  7. all control devices are mappable, but not all mappable
    #       controls are included
    # X  8. data group has a dataset
    #

    def setUp(self):
        self.f = FauxHDFBuilder()

    def tearDown(self):
        self.f.cleanup()

    @property
    def map(self):
        """Map of Control Group"""
        return self.map_control(self.data_group)

    @property
    def data_group(self):
        """MSI group"""
        return self.f["Raw data + config"]

    @staticmethod
    def map_control(group):
        """Mapping function"""
        return HDFMapControls(group)

    def test_not_h5py_group(self):
        """Test error if object to map is not h5py.Group"""
        with self.assertRaises(TypeError):
            self.map_control(None)

    def test_msi_scenarios(self):
        """
        Test various scenarios of mappable and non-mappable control
        device groups.
        """
        # the data group has NO control device groups               ----
        self.f.remove_all_modules()
        _map = self.map
        self.assertBasics(_map)
        self.assertEqual(_map, {})

        # the control group has all mappable devices                ----
        self.f.remove_all_modules()
        self.f.add_module("6K Compumotor", {})
        self.f.add_module("Waveform", {})
        _map = self.map
        self.assertBasics(_map)

        # check all controls were mapped
        self.assertEqual(len(_map), 2)
        self.assertIn("6K Compumotor", _map)
        self.assertIn("Waveform", _map)

        # the data group has mappable and unknown controls          ----
        self.f.remove_all_modules()
        self.f.add_module("6K Compumotor", {})
        self.f.add_module("Waveform", {})
        self.f["Raw data + config"].create_group("Not known")
        _map = self.map
        self.assertBasics(_map)

        # check correct diagnostics were mapped
        self.assertEqual(len(_map), 2)
        self.assertIn("6K Compumotor", _map)
        self.assertIn("Waveform", _map)
        self.assertNotIn("Not known", _map)

        # delete unknown group
        del self.f["Raw data + config/Not known"]

        # the data group has a dataset                              ----
        self.f.remove_all_modules()
        self.f.add_module("Waveform", {})
        data = np.empty((2, 100), dtype=np.float32)
        self.f["Raw data + config"].create_dataset("A dataset", data=data)
        _map = self.map
        self.assertBasics(_map)

        # check correct diagnostics were mapped
        self.assertEqual(len(_map), 1)
        self.assertIn("Waveform", _map)
        self.assertNotIn("A dataset", _map)

        # delete dataset
        del self.f["Raw data + config/A dataset"]

        # the data group has a mappable control devices             ----
        # but mapping fails                                         ----
        self.f.remove_all_modules()
        self.f.add_module("6K Compumotor", {})
        self.f.add_module("Waveform", {})

        # remove a dataset from 'Waveform'
        # - this will cause mapping of 'Waveform' to fail
        #
        del self.f["Raw data + config/Waveform/config01"]

        # check map
        _map = self.map
        self.assertBasics(_map)

        # check correct controls were mapped
        self.assertEqual(len(_map), 1)
        self.assertIn("6K Compumotor", _map)
        self.assertNotIn("Waveform", _map)

    def assertBasics(self, _map: HDFMapControls):
        # mapped object is a dictionary
        self.assertIsInstance(_map, dict)

        # all dict items are a mapping class
        for val in _map.values():
            self.assertIsInstance(val, (HDFMapControlTemplate, HDFMapControlCLTemplate))

        # look for map attributes
        self.assertTrue(hasattr(_map, "mappable_devices"))

        # check attribute types
        self.assertIsInstance(_map.mappable_devices, tuple)


if __name__ == "__main__":
    ut.main()
