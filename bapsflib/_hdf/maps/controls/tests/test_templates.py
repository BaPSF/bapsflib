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
import h5py
import numpy as np
import os
import re
import unittest as ut

from enum import Enum
from unittest import mock

from bapsflib._hdf.maps import FauxHDFBuilder
from bapsflib._hdf.maps.controls.parsers import CLParse
from bapsflib._hdf.maps.controls.templates import (
    HDFMapControlCLTemplate,
    HDFMapControlTemplate,
)


class DummyTemplates(Enum):
    default = HDFMapControlTemplate
    cl = HDFMapControlCLTemplate


class TestControlTemplates(ut.TestCase):
    """
    Test class for HDFMapControlTemplate and
    HDFMapControlCLTemplate.
    """

    def setUp(self):
        # blank/temporary HDF5 file
        self.f = FauxHDFBuilder()

        # fill the MSI group for testing
        self.f["MSI"].create_group("g1")
        self.f["MSI"].create_group("g2")

        # correct 'command list' dataset
        dtype = np.dtype([("Shot number", np.int32), ("Command index", np.int8)])
        data = np.empty((5,), dtype=dtype)
        self.f["MSI"].create_dataset("d1", data=data)

        # dataset missing 'Command index'
        dtype = np.dtype([("Shot number", np.int32), ("Not command index", np.int8)])
        data = np.empty((5,), dtype=dtype)
        self.f["MSI"].create_dataset("d2", data=data)

        # dataset missing 'Command index' wrong shape and size
        dtype = np.dtype([("Shot number", np.int32), ("Command index", np.float16, (2,))])
        data = np.empty((5,), dtype=dtype)
        self.f["MSI"].create_dataset("d3", data=data)

    def tearDown(self):
        """Cleanup temporary HDF5 file"""
        self.f.cleanup()

    def group(self):
        """HDF5 group for testing"""
        return self.f["MSI"]

    @staticmethod
    def dummy_map(template, group):
        """A template mapping of a HDF5 group"""
        # Note: Since the template classes contain abstract methods that
        #       are intended to be overwritten, those methods must be
        #       overwritten before instantiating an object.
        #
        # retrieve desired template class
        template_cls = DummyTemplates[template].value

        # override abstract methods
        # - all abstract methods will now return NotImplemented instead
        #   of raising NotImplementedError
        #
        new_dict = template_cls.__dict__.copy()
        for abstractmethod in template_cls.__abstractmethods__:
            new_dict[abstractmethod] = lambda *args: NotImplemented

        # define new template class
        new_template_class = type(
            "dummy_%s" % template_cls.__name__, (template_cls,), new_dict
        )

        # return map
        return new_template_class(group)

    def test_not_h5py_group(self):
        """Test error if object to map is not h5py.Group"""
        with self.assertRaises(TypeError):
            self.dummy_map("default", None)
            self.dummy_map("cl", None)

    def test_structure(self):
        # test HDFMapControlTemplate
        self.assertControlTemplate(self.dummy_map("default", self.group()), self.group())

        # test HDFMapControlCLTemplate
        self.assertControlCLTemplate(self.dummy_map("cl", self.group()), self.group())

    def assertControlTemplate(self, _map, _group: h5py.Group):
        # check instance
        self.assertIsInstance(_map, HDFMapControlTemplate)

        # check attribute existence
        attrs = (
            "info",
            "configs",
            "contype",
            "dataset_names",
            "group",
            "has_command_list",
            "one_config_per_dset",
            "subgroup_names",
            "device_name",
            "construct_dataset_name",
            "_build_configs",
        )
        for attr in attrs:
            self.assertTrue(hasattr(_map, attr))

        # -- check 'info'                                           ----
        # assert is a dict
        self.assertIsInstance(_map.info, dict)

        # assert required keys
        self.assertIn("group name", _map.info)
        self.assertIn("group path", _map.info)
        self.assertIn("contype", _map.info)

        # assert values
        self.assertEqual(_map.info["group name"], os.path.basename(_group.name))
        self.assertEqual(_map.info["group path"], _group.name)
        self.assertEqual(_map.info["contype"], NotImplemented)

        # -- check 'configs'                                        ----
        self.assertIsInstance(_map.configs, dict)
        self.assertEqual(len(_map.configs), 0)

        # -- check 'one_config_per_dset'                            ----
        # empty configs dict
        self.assertFalse(_map.one_config_per_dset)

        # one config for three datasets
        with mock.patch.dict(_map._configs, {"config1": {}}):
            self.assertFalse(_map.one_config_per_dset)

        # 3 configs for 3 datasets
        with mock.patch.dict(
            _map._configs, {"config1": {}, "config2": {}, "config3": {}}
        ):
            self.assertTrue(_map.one_config_per_dset)

        # -- check 'has_command_list'                               ----
        # empty configs dict
        self.assertFalse(_map.has_command_list)

        # add artificial 'command list'
        with mock.patch.dict(
            _map.configs, {"config1": {}, "config2": {"command list": ("start",)}}
        ):
            self.assertTrue(_map.has_command_list)

        # -- check other attributes                                 ----
        self.assertEqual(_map.contype, _map.info["contype"])
        self.assertEqual(_map.group, _group)
        self.assertEqual(_map.device_name, _map.info["group name"])
        self.assertEqual(sorted(_map.dataset_names), sorted(["d1", "d2", "d3"]))
        self.assertEqual(sorted(_map.subgroup_names), sorted(["g1", "g2"]))

        # -- check abstract methods                                 ----
        # Note: `self.dummy_map` overrides all abstract methods to
        #       return NotImplemented values
        #
        self.assertEqual(_map.construct_dataset_name(), NotImplemented)
        self.assertEqual(_map._build_configs(), NotImplemented)

    def assertControlCLTemplate(self, _map, _group: h5py.Group):
        # check instance
        self.assertIsInstance(_map, HDFMapControlCLTemplate)

        # re-assert HDFMapControlTemplate structure
        self.assertControlTemplate(_map, _group)

        # check attribute existence
        attrs = (
            "_default_re_patterns",
            "clparse",
            "_construct_state_values_dict",
            "reset_state_values_config",
            "set_state_values_config",
            "_default_state_values_dict",
        )
        for attr in attrs:
            self.assertTrue(hasattr(_map, attr))

        # -- check '_default_re_patterns'                           ----
        self.assertIsInstance(_map._default_re_patterns, tuple)
        self.assertEqual(len(_map._default_re_patterns), 0)

        # -- check 'clparse'                                        ----
        with mock.patch.dict(
            _map._configs, {"config1": {"command list": ("VOLT 25.0",)}}
        ):
            self.assertIsInstance(_map.clparse("config1"), CLParse)

        # -- check '_construct_state_values_dict'                   ----
        cl = (
            "VOLT 20.0",
            "VOLT 25.0",
            "VOLT 30.0",
        )
        config_name = "config1"
        configs_dict = {config_name: {"command list": cl, "dset paths": ("/MSI/d1",)}}
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
                configs_dict[config_name]["dset paths"] = ("/MSI/d2",)
                with self.assertWarns(UserWarning):
                    sv_dict = _map._construct_state_values_dict(config_name, [pattern])
                    self.assertFalse(bool(sv_dict))

                # the 'dset_paths' dataset 'Command index' field does
                # NOT have correct shape or dtype
                configs_dict[config_name]["dset paths"] = ("/MSI/d3",)
                with self.assertWarns(UserWarning):
                    sv_dict = _map._construct_state_values_dict(config_name, [pattern])
                    self.assertFalse(bool(sv_dict))

        # -- check 'reset_state_values_config'                      ----
        cl = ("VOLT 20.0", "VOLT 25.0", "VOLT 30.0")
        pattern = r"(?P<VOLT>(\bVOLT\s)(?P<VAL>(\d+\.\d*|\.\d+|\d+\b)))"
        config_name = "config1"
        configs_dict = {
            config_name: {
                "command list": cl,
                "dset paths": ("/MSI/d1",),
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
                "dtype": np.dtype((np.unicode_, 10)),
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

        # -- check 'set_state_values_config'                        ----
        cl = ("VOLT 20.0", "VOLT 25.0", "VOLT 30.0")
        pattern = r"(?P<VOLT>(\bVOLT\s)(?P<VAL>(\d+\.\d*|\.\d+|\d+\b)))"
        config_name = "config1"
        configs_dict = {
            config_name: {
                "command list": cl,
                "dset paths": ("/MSI/d1",),
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
            with self.assertWarns(UserWarning):
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


if __name__ == "__main__":
    ut.main()
