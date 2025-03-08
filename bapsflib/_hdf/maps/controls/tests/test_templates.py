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
import re
import unittest as ut

from abc import ABC
from unittest import mock

from bapsflib._hdf.maps import FauxHDFBuilder
from bapsflib._hdf.maps.controls.parsers import CLParse
from bapsflib._hdf.maps.controls.templates import (
    HDFMapControlCLTemplate,
    HDFMapControlTemplate,
)
from bapsflib._hdf.maps.controls.types import ConType
from bapsflib._hdf.maps.templates import HDFMapTemplate, MapTypes
from bapsflib.utils.warnings import HDFMappingWarning


class ControlTemplateTestCase:
    _control_device_path = "/Raw data + config/Control device"
    MAP_CLASS = NotImplemented

    def __init__(self):
        # Create a fully defined DummyMap to test basic functionality
        # of HDFMapTemplate
        new__dict__ = self.MAP_CLASS.__dict__.copy()
        for _abc_method_name in self.MAP_CLASS.__abstractmethods__:
            new__dict__[_abc_method_name] = lambda *args, **kwargs: NotImplemented

        # Creates class DummyMap which is subclass of HDFMapTemplate with
        # all abstract methods returning NotImplemented
        self._DummyMap = type("DummyMap", (self.MAP_CLASS,), new__dict__)
        self._DummyMap._maptype = MapTypes.CONTROL
        self._DummyMap._contype = ConType.MOTION

    def setUp(self):
        # blank/temporary HDF5 file
        self.f = FauxHDFBuilder()

        # self.f["Raw data + config"].create_group("Control Device")
        # _control_group = self.f.get(self._control_device_path)
        self.f.create_group(self._control_device_path)
        control_group = self.f.get(self._control_device_path)

        # fill the MSI group for testing
        _path = self._control_device_path
        control_group.create_group("g1")
        control_group.create_group("g2")

        # correct 'command list' dataset
        dtype = np.dtype([("Shot number", np.int32), ("Command index", np.int8)])
        data = np.empty((5,), dtype=dtype)
        control_group.create_dataset("d1", data=data)

        # dataset missing 'Command index'
        dtype = np.dtype([("Shot number", np.int32), ("Not command index", np.int8)])
        data = np.empty((5,), dtype=dtype)
        control_group.create_dataset("d2", data=data)

        # dataset missing 'Command index' wrong shape and size
        dtype = np.dtype([("Shot number", np.int32), ("Command index", np.float16, (2,))])
        data = np.empty((5,), dtype=dtype)
        control_group.create_dataset("d3", data=data)

    def tearDown(self):
        """Cleanup temporary HDF5 file"""
        self.f.cleanup()

    @property
    def control_group(self):
        return self.f[self._control_device_path]

    def test_abstractness(self):
        self.assertTrue(issubclass(self.MAP_CLASS, ABC))

    def test_inheritance(self):
        self.assertTrue(issubclass(self.MAP_CLASS, HDFMapTemplate))

    def test_attribute_existence(self):
        expected_attributes = {
            "_contype",
            "contype",
            "device_name",
            "get_config_id",
            "has_command_list",
            "one_config_per_dset",
        }
        for attr_name in expected_attributes:
            with self.subTest(attr_name=attr_name):
                assert hasattr(self.MAP_CLASS, attr_name)

    def test_abstractmethod_existence(self):
        expected_attributes = {"construct_dataset_name"}
        for attr_name in expected_attributes:
            with self.subTest(attr_name=attr_name):
                assert hasattr(self.MAP_CLASS, attr_name)

    def test_attribute_values(self):
        _map = self._DummyMap(self.control_group)
        _expected = {
            "configs": dict(),
            "group_name": "Control device",
            "device_name": _map.group_name,
            "maptype": MapTypes.CONTROL,
            "contype": ConType.MOTION,
        }
        for attr_name, expected in _expected.items():
            with self.subTest(attr_name=attr_name, expected=expected):
                self.assertEqual(getattr(_map, attr_name), expected)

    def test_not_h5py_group(self):
        with self.assertRaises(TypeError):
            self._DummyMap(None)

    def test_get_config_id(self):
        _map = self._DummyMap(self.control_group)
        self.assertEqual(_map.get_config_id("config01"), "config01")

    def test_one_config_per_dset(self):
        # control_group is set up with 3 datasets
        _map = self._DummyMap(self.control_group)

        _cases = [  # (one_config_per_dset? , mock_configs)
            (False, {"config1": {}}),
            (True, {"config1": {}, "config2": {}, "config3": {}}),
        ]
        for case in _cases:
            with self.subTest(case=case):
                with mock.patch.dict(_map.configs, case[1]):
                    self.assertEqual(_map.one_config_per_dset, case[0])

    def test_info_dict(self):
        _map = self._DummyMap(self.control_group)

        _expected = {
            True: isinstance(_map.info, dict),
            "group name": "Control device",
            "group path": self._control_device_path,
            "maptype": _map.maptype,
            "contype": _map.contype,
        }
        for key, expected in _expected.items():
            with self.subTest(key=key, expected=expected):
                val = key if not isinstance(key, str) else _map.info[key]
                self.assertEqual(val, expected)

    def test_has_command_list(self):
        # control_group is set up with 3 datasets
        _map = self._DummyMap(self.control_group)

        _cases = [  # (one_config_per_dset? , mock_configs)
            (False, {"config1": {}}),
            (False, {"config1": {}, "config2": {}}),
            (True, {"config1": {"command list": ("start",)}}),
            (True, {"config1": {"command list": ("start",)}, "config2": {}}),
        ]
        for case in _cases:
            with self.subTest(case=case):
                with mock.patch.dict(_map.configs, case[1]):
                    self.assertEqual(_map.has_command_list, case[0])


class TestHDFMapControlTemplate(ControlTemplateTestCase, ut.TestCase):
    MAP_CLASS = HDFMapControlTemplate

    def __init__(self, methodName):
        ut.TestCase.__init__(self, methodName=methodName)
        ControlTemplateTestCase.__init__(self)


class TestHDFMapControlCLTemplate(ControlTemplateTestCase, ut.TestCase):
    MAP_CLASS = HDFMapControlCLTemplate

    def __init__(self, methodName):
        ut.TestCase.__init__(self, methodName=methodName)
        ControlTemplateTestCase.__init__(self)

    def test_additional_attribute_existence(self):
        expected_attributes = {
            "_construct_state_values_dict",
            "_default_re_patterns",
            "clparse",
            "reset_state_values_config",
            "set_state_values_config",
        }
        for attr_name in expected_attributes:
            with self.subTest(attr_name=attr_name):
                assert hasattr(self.MAP_CLASS, attr_name)

    def test_additional_abstractmethod_existence(self):
        expected_attributes = {"_default_state_values_dict"}
        for attr_name in expected_attributes:
            with self.subTest(attr_name=attr_name):
                assert hasattr(self.MAP_CLASS, attr_name)

    def test_default_re_patterns(self):
        _map = self._DummyMap(self.control_group)

        _cases = [
            isinstance(_map._default_re_patterns, tuple),
            _map._default_re_patterns == (),
        ]
        for case in _cases:
            with self.subTest(case=case):
                self.assertTrue(case)

    def test_clparse(self):
        _map = self._DummyMap(self.control_group)

        with mock.patch.dict(
            _map._configs,
            {"config1": {"command list": ("VOLT 25.0",)}},
        ):
            self.assertIsInstance(_map.clparse("config1"), CLParse)

    def test_construct_state_values_dict(self):
        _map = self._DummyMap(self.control_group)

        cl = ("VOLT 20.0", "VOLT 25.0", "VOLT 30.0")
        config_name = "config1"
        configs_dict = {
            config_name: {
                "command list": cl,
                "dset paths": (f"{_map.group_path}/d1",),
            },
        }
        clparse_dict = {
            "VOLT": {
                "command list": (20.0, 25.0, 30.0),
                "cl str": cl,
                "dtype": np.float64,
            }
        }
        pattern = r"(?P<VOLT>(\bVOLT\s)(?P<VAL>(\d+\.\d*|\.\d+|\d+\b)))"

        # run tests on a mock _map._configs
        with mock.patch.dict(_map._configs, configs_dict):
            # mock CLParse attribute 'apply_patterns'
            with mock.patch.object(
                CLParse,
                "apply_patterns",
            ) as mock_apply_pat:
                # 'apply_patterns' is unsuccessful
                mock_apply_pat.return_value = (False, {})
                sv_dict = _map._construct_state_values_dict(config_name, [pattern])
                self.assertFalse(bool(sv_dict))

                # 'apply_patterns' is successful
                mock_apply_pat.return_value = (True, clparse_dict)
                sv_dict = _map._construct_state_values_dict(config_name, [pattern])
                self.assertTrue(bool(sv_dict))
                self.assertIsInstance(sv_dict, dict)
                self.assertEqual(len(sv_dict), 1)
                self.assertEqual(
                    sv_dict["VOLT"]["dset paths"], configs_dict[config_name]["dset paths"]
                )
                self.assertEqual(sv_dict["VOLT"]["dset field"], ("Command index",))
                self.assertEqual(sv_dict["VOLT"]["shape"], ())
                self.assertEqual(sv_dict["VOLT"]["dtype"], clparse_dict["VOLT"]["dtype"])
                self.assertEqual(
                    sv_dict["VOLT"]["command list"], clparse_dict["VOLT"]["command list"]
                )
                self.assertEqual(
                    sv_dict["VOLT"]["cl str"], clparse_dict["VOLT"]["cl str"]
                )

                # the 'dset_paths' dataset does NOT have 'Command index'
                configs_dict[config_name]["dset paths"] = (f"{_map.group_path}/d2",)
                with self.assertWarns(HDFMappingWarning):
                    sv_dict = _map._construct_state_values_dict(config_name, [pattern])
                    self.assertFalse(bool(sv_dict))

                # the 'dset_paths' dataset 'Command index' field does
                # NOT have correct shape or dtype
                configs_dict[config_name]["dset paths"] = (f"{_map.group_path}/d3",)
                with self.assertWarns(HDFMappingWarning):
                    sv_dict = _map._construct_state_values_dict(config_name, [pattern])
                    self.assertFalse(bool(sv_dict))

    def test_reset_state_values_config(self):
        _map = self._DummyMap(self.control_group)

        cl = ("VOLT 20.0", "VOLT 25.0", "VOLT 30.0")
        pattern = r"(?P<VOLT>(\bVOLT\s)(?P<VAL>(\d+\.\d*|\.\d+|\d+\b)))"
        config_name = "config1"
        configs_dict = {
            config_name: {
                "command list": cl,
                "dset paths": (f"{_map.group_path}/d1",),
                "shotnum": {},
                "state values": {},
            }
        }
        dsv_dict = {
            "command": {
                "command list": cl,
                "cl str": cl,
                "re pattern": None,
                "dset paths": configs_dict[config_name]["dset paths"],
                "dset field": ("Command index",),
                "shape": (),
                "dtype": np.dtype((np.str_, 10)),
            }
        }
        sv_dict = {
            "VOLT": {
                "command list": (20.0, 25.0, 30.0),
                "cl str": cl,
                "re pattern": re.compile(pattern),
                "dset paths": configs_dict[config_name]["dset paths"],
                "dset field": ("Command index",),
                "shape": (),
                "dtype": np.float64,
            }
        }

        # mock _map._configs
        # mock the '_default_state_values_dict' method
        with mock.patch.dict(_map._configs, configs_dict), mock.patch.object(
            _map, "_default_state_values_dict"
        ) as mock_dsvdict:
            mock_dsvdict.return_value = dsv_dict

            # kwarg apply_patterns=False (default behavior)
            _map.reset_state_values_config(config_name, apply_patterns=False)
            self.assertEqual(_map._configs[config_name]["state values"], dsv_dict)

            # kwarg apply_patterns=True
            # mock '_construct_state_values_dict'
            with mock.patch.object(_map, "_construct_state_values_dict") as mock_csvd:
                # '_construct_state_values_dict' returns {}
                mock_csvd.return_value = {}
                _map._configs[config_name]["state values"] = {}
                _map.reset_state_values_config(config_name, apply_patterns=True)
                self.assertEqual(_map._configs[config_name]["state values"], dsv_dict)

                # '_construct_state_values_dict' returns sv_dict
                mock_csvd.return_value = sv_dict
                _map._configs[config_name]["state values"] = {}
                _map.reset_state_values_config(config_name, apply_patterns=True)
                self.assertEqual(_map._configs[config_name]["state values"], sv_dict)

    def test_set_state_values_config(self):
        _map = self._DummyMap(self.control_group)

        # -- check 'set_state_values_config'                        ----
        cl = ("VOLT 20.0", "VOLT 25.0", "VOLT 30.0")
        pattern = r"(?P<VOLT>(\bVOLT\s)(?P<VAL>(\d+\.\d*|\.\d+|\d+\b)))"
        config_name = "config1"
        configs_dict = {
            config_name: {
                "command list": cl,
                "dset paths": (f"{_map.group_path}/d1",),
                "shotnum": {},
                "state values": {},
            }
        }
        sv_dict = {
            "VOLT": {
                "command list": (20.0, 25.0, 30.0),
                "cl str": cl,
                "re pattern": re.compile(pattern),
                "dset paths": configs_dict[config_name]["dset paths"],
                "dset field": ("Command index",),
                "shape": (),
                "dtype": np.float64,
            }
        }

        # mock _map._configs
        # mock the '_construct_state_values_dict' method
        with mock.patch.dict(_map._configs, configs_dict), mock.patch.object(
            _map, "_construct_state_values_dict"
        ) as mock_csvd:
            # '_construct_state_values_dict' fails and returns {}
            mock_csvd.return_value = {}
            with self.assertWarns(HDFMappingWarning):
                _map.set_state_values_config(config_name, [pattern])
                self.assertEqual(_map._configs[config_name]["state values"], {})

            # '_construct_state_values_dict' fails and returns sv_dict
            mock_csvd.return_value = sv_dict
            _map._configs[config_name]["state values"] = {}
            _map.set_state_values_config(config_name, [pattern])
            self.assertEqual(_map._configs[config_name]["state values"], sv_dict)

        # -- check abstract methods                                 ----
        # Note: `self.dummy_map` overrides all abstract methods to
        #       return NotImplemented values
        #
        self.assertEqual(_map._default_state_values_dict(""), NotImplemented)
