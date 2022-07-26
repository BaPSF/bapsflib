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

from bapsflib._hdf.maps.controls import HDFMapControls
from bapsflib._hdf.maps.controls.templates import HDFMapControlTemplate
from bapsflib._hdf.maps.core import HDFMap
from bapsflib._hdf.maps.digitizers import HDFMapDigitizers
from bapsflib._hdf.maps.digitizers.templates import HDFMapDigiTemplate
from bapsflib._hdf.maps.msi import HDFMapMSI
from bapsflib._hdf.maps.msi.templates import HDFMapMSITemplate
from bapsflib._hdf.maps.tests.fauxhdfbuilder import FauxHDFBuilder


class TestHDFMap(ut.TestCase):
    """
    Test Case for :class:`~bapsflib._hdf.maps.core.HDFMap`
    """

    f = NotImplemented  # type: FauxHDFBuilder
    MAP_CLASS = HDFMap

    @classmethod
    def setUpClass(cls):
        # create hDF5 file
        super().setUpClass()
        cls.f = FauxHDFBuilder()

    def setUp(self):
        super().setUp()

    def tearDown(self):
        super().tearDown()
        self.f.remove_all_modules()

    @classmethod
    def tearDownClass(cls):
        # cleanup and close HDF5 file
        super().tearDownClass()
        cls.f.cleanup()

    @property
    def map(self):
        return self.map_file(
            self.f,
            msi_path="MSI",
            digitizer_path="Raw data + config",
            control_path="Raw data + config",
        )

    def map_file(self, file, msi_path, digitizer_path, control_path):
        return self.MAP_CLASS(
            file,
            msi_path=msi_path,
            digitizer_path=digitizer_path,
            control_path=control_path,
        )

    def test_all_devices_in_one_group(self):
        """
        Test the case where all devices (Controls, Digitizers, and
        MSI diagnostics) share the same group.
        """
        # add one of each device
        self.f.add_module("Waveform")
        self.f.add_module("SIS 3301")
        self.f.add_module("Discharge")
        self.f.move("/MSI/Discharge", "/Raw data + config/Discharge")
        _map = self.map_file(
            self.f,
            msi_path="Raw data + config",
            digitizer_path="Raw data + config",
            control_path="Raw data + config",
        )
        self.assertHDFMapBasics(_map, self.f)

        self.assertIsInstance(_map.controls, HDFMapControls)
        self.assertEqual(len(_map.controls), 1)
        self.assertIn("Waveform", _map.controls)

        self.assertIsInstance(_map.digitizers, HDFMapDigitizers)
        self.assertEqual(len(_map.digitizers), 1)
        self.assertIn("SIS 3301", _map.digitizers)

        self.assertIsInstance(_map.msi, HDFMapMSI)
        self.assertEqual(len(_map.msi), 1)
        self.assertIn("Discharge", _map.msi)

        self.assertEqual(_map.unknowns, ["/MSI"])

        # add an unknown device
        self.f.create_group("Raw data + config/Unknown")
        _map = self.map_file(
            self.f,
            msi_path="Raw data + config",
            digitizer_path="Raw data + config",
            control_path="Raw data + config",
        )
        self.assertHDFMapBasics(_map, self.f)

        self.assertIsInstance(_map.controls, HDFMapControls)
        self.assertEqual(len(_map.controls), 1)
        self.assertIn("Waveform", _map.controls)

        self.assertIsInstance(_map.digitizers, HDFMapDigitizers)
        self.assertEqual(len(_map.digitizers), 1)
        self.assertIn("SIS 3301", _map.digitizers)

        self.assertIsInstance(_map.msi, HDFMapMSI)
        self.assertEqual(len(_map.msi), 1)
        self.assertIn("Discharge", _map.msi)

        self.assertEqual(
            sorted(_map.unknowns), sorted(["/MSI", "/Raw data + config/Unknown"])
        )

        del self.f["Raw data + config/Unknown"]

    def test_control_mapping_attachment(self):
        """Test attachment of mapped control devices."""
        #   1. specified control path does NOT exist
        #   2. control path VALID, but NO controls
        #   3. control path VALID, mixture of mappable and non-mappable
        #      controls
        #
        # specified control path does NOT exist                      (1)
        with self.assertWarns(UserWarning):
            _map = self.map_file(
                self.f,
                msi_path="MSI",
                digitizer_path="Raw data + config",
                control_path="Not a control path",
            )
            self.assertHDFMapBasics(_map, self.f)
            self.assertEqual(_map.controls, {})

        # control path VALID, but NO controls                        (2)
        _map = self.map_file(
            self.f,
            msi_path="MSI",
            digitizer_path="Raw data + config",
            control_path="Raw data + config",
        )
        self.assertHDFMapBasics(_map, self.f)
        self.assertEqual(_map.controls, {})
        self.assertIsInstance(_map.controls, HDFMapControls)

        # control path VALID, mixture of mappable and                (3)
        # non-mappable controls
        self.f.add_module("Waveform")
        self.f.create_group("Raw data + config/Not control or digi")
        _map = self.map_file(
            self.f,
            msi_path="MSI",
            digitizer_path="Raw data + config",
            control_path="Raw data + config",
        )
        self.assertHDFMapBasics(_map, self.f)
        self.assertIsInstance(_map.controls, HDFMapControls)
        self.assertEqual(len(_map.controls), 1)
        self.assertIn("Waveform", _map.controls)
        self.assertEqual(_map.unknowns, ["/Raw data + config/Not control or digi"])
        del self.f["Raw data + config/Not control or digi"]

    def test_digitizer_mapping_attachment(self):
        """Test attachment of mapped digitizers."""
        #   1. specified digitizer path does NOT exist
        #   2. digitizer path VALID, but NO digitizers
        #   3. digitizer path VALID, mixture of mappable and
        #      non-mappable digitizers
        #
        # specified digitizer path does NOT exist                    (1)
        with self.assertWarns(UserWarning):
            _map = self.map_file(
                self.f,
                msi_path="MSI",
                digitizer_path="Not a digi path",
                control_path="Raw data + config",
            )
            self.assertHDFMapBasics(_map, self.f)
            self.assertEqual(_map.digitizers, {})

        # digitizer path VALID, but NO digitizers                    (2)
        _map = self.map_file(
            self.f,
            msi_path="MSI",
            digitizer_path="Raw data + config",
            control_path="Raw data + config",
        )
        self.assertHDFMapBasics(_map, self.f)
        self.assertEqual(_map.digitizers, {})
        self.assertIsInstance(_map.digitizers, HDFMapDigitizers)

        # digitizer path VALID, mixture of mappable and              (3)
        # non-mappable digitizers
        self.f.add_module("SIS 3301")
        self.f.create_group("Raw data + config/Not control or digi")
        _map = self.map_file(
            self.f,
            msi_path="MSI",
            digitizer_path="Raw data + config",
            control_path="Raw data + config",
        )
        self.assertHDFMapBasics(_map, self.f)
        self.assertIsInstance(_map.digitizers, HDFMapDigitizers)
        self.assertEqual(len(_map.digitizers), 1)
        self.assertIn("SIS 3301", _map.digitizers)
        self.assertEqual(_map.unknowns, ["/Raw data + config/Not control or digi"])
        del self.f["Raw data + config/Not control or digi"]

    def test_empty_file(self):
        """Test a file that is empty of any devices."""
        # all devices are in root
        _map = self.map_file(self.f, msi_path="", digitizer_path="", control_path="")
        self.assertHDFMapBasics(_map, self.f)
        self.assertEqual(_map.controls, {})
        self.assertEqual(_map.digitizers, {})
        self.assertEqual(_map.msi, {})
        self.assertEqual(sorted(_map.unknowns), sorted(["/MSI", "/Raw data + config"]))
        self.assertIs(_map.main_digitizer, None)

        # only controls are in root
        _map = self.map_file(
            self.f, msi_path="MSI", digitizer_path="Raw data + config", control_path="/"
        )
        self.assertHDFMapBasics(_map, self.f)
        self.assertEqual(_map.controls, {})
        self.assertEqual(_map.digitizers, {})
        self.assertEqual(_map.msi, {})
        self.assertEqual(_map.unknowns, [])
        self.assertIs(_map.main_digitizer, None)

    def test_get(self):
        """Test method `get`"""
        # populate with one of each device
        self.f.add_module("Waveform")
        self.f.add_module("SIS 3301")
        self.f.add_module("Discharge")
        _map = self.map_file(
            self.f,
            msi_path="MSI",
            digitizer_path="Raw data + config",
            control_path="Raw data + config",
        )

        # get control device
        device_map = _map.get("Waveform")
        self.assertEqual(device_map, _map.controls["Waveform"])

        # get digitizer
        device_map = _map.get("SIS 3301")
        self.assertEqual(device_map, _map.digitizers["SIS 3301"])

        # get MSI diagnostic
        device_map = _map.get("Discharge")
        self.assertEqual(device_map, _map.msi["Discharge"])

        # get an un-mapped device
        device_map = _map.get("Not a device")
        self.assertIs(device_map, None)

    def test_main_digitizer(self):
        """Test identification of the "main" digitizer"""
        # 1. there are no mapped digitizers
        # 2. there is one mapped digitizer
        # 3. the are MULTIPLE mapped digitizers
        #
        # there are no mapped digitizers                             (1)
        _map = self.map_file(
            self.f,
            msi_path="MSI",
            digitizer_path="Raw data + config",
            control_path="Raw data + config",
        )
        self.assertHDFMapBasics(_map, self.f)
        self.assertEqual(_map.digitizers, {})
        self.assertIs(_map.main_digitizer, None)

        # there is ONE mapped digitizer                              (2)
        self.f.add_module("SIS 3301")
        _map = self.map_file(
            self.f,
            msi_path="MSI",
            digitizer_path="Raw data + config",
            control_path="Raw data + config",
        )
        self.assertHDFMapBasics(_map, self.f)
        self.assertEqual(_map.main_digitizer, _map.digitizers["SIS 3301"])

        # there are MULTIPLE mapped digitizerS                       (3)
        self.f.add_module("SIS crate")
        _map = self.map_file(
            self.f,
            msi_path="MSI",
            digitizer_path="Raw data + config",
            control_path="Raw data + config",
        )
        self.assertHDFMapBasics(_map, self.f)
        self.assertEqual(len(_map.digitizers), 2)
        self.assertIn("SIS 3301", _map.digitizers)
        self.assertIn("SIS crate", _map.digitizers)
        self.assertEqual(_map.main_digitizer, _map.digitizers["SIS 3301"])

    def test_msi_mapping_attachment(self):
        """Test attachment of mapped MSI diagnostics."""
        #   1. specified MSI path does NOT exist
        #   2. MSI path VALID, but NO MSI diagnostics
        #   3. MSI path VALID, mixture of mappable and
        #      non-mappable MSI diagnostics
        #
        # specified MSI path does NOT exist                          (1)
        with self.assertWarns(UserWarning):
            _map = self.map_file(
                self.f,
                msi_path="Not a MSI path",
                digitizer_path="Raw data + config",
                control_path="Raw data + config",
            )
            self.assertHDFMapBasics(_map, self.f)
            self.assertEqual(_map.msi, {})

        # MSI path VALID, but NO MSI diagnostics                     (2)
        _map = self.map_file(
            self.f,
            msi_path="MSI",
            digitizer_path="Raw data + config",
            control_path="Raw data + config",
        )
        self.assertHDFMapBasics(_map, self.f)
        self.assertEqual(_map.msi, {})
        self.assertIsInstance(_map.msi, HDFMapMSI)

        # MSI path VALID, mixture of mappable and                    (3)
        # non-mappable MSI diagnostics
        self.f.add_module("Discharge")
        self.f.add_module("Gas pressure")
        self.f.create_group("MSI/Not a MSI")
        _map = self.map_file(
            self.f,
            msi_path="MSI",
            digitizer_path="Raw data + config",
            control_path="Raw data + config",
        )
        self.assertHDFMapBasics(_map, self.f)
        self.assertIsInstance(_map.msi, HDFMapMSI)
        self.assertEqual(len(_map.msi), 2)
        self.assertIn("Discharge", _map.msi)
        self.assertIn("Gas pressure", _map.msi)
        self.assertEqual(_map.unknowns, ["/MSI/Not a MSI"])
        del self.f["MSI/Not a MSI"]

    def test_not_h5py_group(self):
        """Test error if object to map is not h5py.Group"""
        with self.assertRaises(TypeError):
            self.map_file(None, "", "", "")

    def assertHDFMapBasics(self, _map, _file):
        # check instance
        self.assertIsInstance(_map, HDFMap)

        # check attribute existence
        attrs = (
            "DEVICE_PATHS",
            "controls",
            "digitizers",
            "main_digitizer",
            "msi",
            "unknowns",
        )
        for attr in attrs:
            self.assertTrue(hasattr(_map, attr))

        # -- check 'DEVICE_PATHS'                                   ----
        self.assertIsInstance(_map.DEVICE_PATHS, dict)
        for device in ("control", "digitizer", "msi"):
            self.assertIn(device, _map.DEVICE_PATHS)
            self.assertIsInstance(_map.DEVICE_PATHS[device], str)

        # -- check 'controls'                                       ----
        self.assertIsInstance(type(_map).controls, property)
        self.assertIsInstance(_map.controls, (dict, HDFMapControls))
        for key, val in _map.controls.items():
            self.assertIsInstance(key, str)
            self.assertIsInstance(val, HDFMapControlTemplate)

        # -- check 'digitizers'                                     ----
        self.assertIsInstance(type(_map).digitizers, property)
        self.assertIsInstance(_map.digitizers, (dict, HDFMapDigitizers))
        for key, val in _map.digitizers.items():
            self.assertIsInstance(key, str)
            self.assertIsInstance(val, HDFMapDigiTemplate)

        # -- check 'main_digitizers'                                ----
        self.assertIsInstance(type(_map).main_digitizer, property)
        self.assertIsInstance(_map.main_digitizer, (type(None), HDFMapDigiTemplate))

        # -- check 'msi'                                            ----
        self.assertIsInstance(type(_map).msi, property)
        self.assertIsInstance(_map.msi, (dict, HDFMapMSI))
        for key, val in _map.msi.items():
            self.assertIsInstance(key, str)
            self.assertIsInstance(val, HDFMapMSITemplate)

        # -- check 'unknowns'                                       ----
        self.assertIsInstance(type(_map).unknowns, property)
        self.assertIsInstance(_map.unknowns, list)
        self.assertTrue(all(isinstance(val, str) for val in _map.unknowns))


if __name__ == "__main__":
    ut.main()
