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

from unittest import mock

from bapsflib._hdf.maps.controls.map_controls import HDFMapControls
from bapsflib._hdf.maps.controls.sixk import HDFMapControl6K
from bapsflib._hdf.maps.controls.templates import (
    HDFMapControlCLTemplate,
    HDFMapControlTemplate,
)
from bapsflib._hdf.maps.tests import FauxHDFBuilder, MapTestBase


class TestHDFMapControls(MapTestBase):
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

    def test__str__(self):
        # add controls to the Faux HDF5 file
        self.f.add_module("6K Compumotor", {"n_configs": 2})
        self.f.add_module("Waveform", {})

        # remap the file
        _map = self.map

        expected = (
            "| Control         | Configuration | Shot Num. Range | Readout Data Fields                       |\n"
            "+-----------------+---------------+-----------------+-------------------------------------------+\n"
            "| '6K Compumotor' | '1'           | ??              | ('xyz', 'ptip_rot_theta', 'ptip_rot_phi') |\n"
            "|                 | '2'           | ??              | ('xyz', 'ptip_rot_theta', 'ptip_rot_phi') |\n"
            "| --------------- | ------------- | --------------- | ----------------------------------------- |\n"
            "| 'Waveform'      | 'config01'    | ??              | ('FREQ',)                                 |\n"
        )
        self.assertEqual(_map.__str__(), expected)

    def test__str__no_controls(self):
        # the faux modules start without any controls
        _map = self.map
        self.assertEqual(_map.__str__(), "")

    def test__repr__(self):
        # add controls to the Faux HDF5 file
        self.f.add_module("6K Compumotor", {})
        self.f.add_module("Waveform", {})

        # remap the file
        _map = self.map

        expected = f"{dict.__repr__(_map)}\n\n{_map.__str__()}"
        self.assertEqual(_map.__repr__(), expected)

    def test_map_control_with_alternate_group_name(self):
        # test mapping a control device whose group name does NOT match
        # the mapper primary key (i.e. the key in _defined_mapping_classes)
        # but corresponds to the devices _EXPECTED_GROUP_NAME
        #
        # The 180E_positions mapper follows this scheme.  The primary
        # key is '180E_positions' but the group name is 'Positions'.
        #
        self.f.add_module("180E_positions")

        self.assertIn("Positions", self.data_group)

        _map = self.map
        self.assertIn("180E_positions", _map)

    def test_map_two_controls_with_same_alternate_group_name(self):
        # test mapping a control device whose group name does NOT match
        # the mapper primary key (i.e. the key in _defined_mapping_classes)
        # but corresponds to the devices _EXPECTED_GROUP_NAME
        #
        # The 180E_positions mapper follows this scheme.  The primary
        # key is '180E_positions' but the group name is 'Positions'.
        #
        self.f.add_module("180E_positions")
        self.f.add_module("6K Compumotor")

        with mock.patch(
            f"{HDFMapControl6K.__module__}."
            f"{HDFMapControl6K.__name__}._EXPECTED_GROUP_NAME",
            "Positions",
        ):
            # artificially define the expected group name for the 6K mapper
            # as "Positions"

            self.assertEqual(HDFMapControl6K._EXPECTED_GROUP_NAME, "Positions")
            self.assertIn("Positions", self.data_group)

            _map = self.map
            self.assertIn("180E_positions", _map)

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
