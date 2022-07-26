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
import astropy.units as u
import h5py
import numpy as np
import os
import unittest as ut
import warnings

from unittest import mock

from bapsflib._hdf.maps import FauxHDFBuilder
from bapsflib._hdf.maps.digitizers.templates import HDFMapDigiTemplate


class TestDigiTemplates(ut.TestCase):
    """Test class for HDFMapDigTemplate."""

    f = NotImplemented  # type: FauxHDFBuilder
    DEVICE_NAME = "Digitizer"
    DEVICE_PATH = f"Raw data + config/{DEVICE_NAME}"
    MAP_CLASS = HDFMapDigiTemplate

    @classmethod
    def setUpClass(cls):
        # create HDF5 file
        super().setUpClass()
        cls.f = FauxHDFBuilder()
        cls.f.create_group(cls.DEVICE_PATH)

    @classmethod
    def tearDownClass(cls):
        """Cleanup temporary HDF5 file"""
        # cleanup and close HDF5 file
        super().tearDownClass()
        cls.f.cleanup()

    @property
    def group(self) -> h5py.Group:
        """HDF5 group for testing"""
        return self.f[self.DEVICE_PATH]

    @property
    def map(self):
        return self.map_device(self.group)

    def map_device(self, group: h5py.Group) -> HDFMapDigiTemplate:
        """A template mapping of a HDF5 group"""
        # Note: Since the template classes contain abstract methods that
        #       are intended to be overwritten, those methods must be
        #       overwritten before instantiating an object.
        #
        # override abstract methods
        # - all abstract methods will now return NotImplemented instead
        #   of raising NotImplementedError
        #
        new_dict = self.MAP_CLASS.__dict__.copy()
        absm_list = getattr(self.MAP_CLASS, "__abstractmethods__")
        for abstractmethod in absm_list:
            new_dict[abstractmethod] = lambda *args: NotImplemented

        # define new template class
        dummy_map = type("%sDummy" % self.MAP_CLASS.__name__, (self.MAP_CLASS,), new_dict)

        # return
        return dummy_map(group)

    def test_deduce_config_active_status(self):
        """
        Test functionality of method `deduce_config_active_status`.
        """
        # setup
        config_name = "config01"
        self.group.create_group(config_name)
        self.group.create_group("g2")

        # there are no datasets
        self.assertFalse(self.map.deduce_config_active_status(config_name))

        # datasets exist
        data = np.empty((3, 100), dtype=np.int32)
        self.group.create_dataset(f"{config_name}: 01", data=data)
        self.group.create_dataset("config02: 01", data=data)
        self.assertTrue(self.map.deduce_config_active_status(config_name))
        self.assertFalse(self.map.deduce_config_active_status("hello"))

        # clean up
        self.group.clear()

    @mock.patch.object(HDFMapDigiTemplate, "configs", new_callable=mock.PropertyMock)
    def test_get_adc_info(self, mock_configs):
        """Test functionality of method `get_adc_info`."""
        # pre-define config items
        configs_i1 = {
            "config01": {
                "active": True,
                "adc": ("SIS 3302",),
                "SIS 3302": (
                    (
                        1,
                        (1, 2, 5),
                        {
                            "bit": 10,
                            "clock rate": u.Quantity(100.0, unit="MHz"),
                            "nshotnum": 10,
                            "nt": 1000,
                            "sample average (hardware)": None,
                            "shot average (software)": None,
                        },
                    ),
                ),
            },
        }
        configs_i2 = {
            "config02": {
                "active": False,
                "adc": ("SIS 3305",),
                "SIS 3305": (
                    (
                        1,
                        (1, 2, 5),
                        {
                            "bit": 10,
                            "clock rate": u.Quantity(100.0, unit="MHz"),
                            "nshotnum": 10,
                            "nt": 1000,
                            "sample average (hardware)": None,
                            "shot average (software)": None,
                        },
                    ),
                ),
            },
        }
        configs_i3 = {
            "config03": {
                "active": True,
                "adc": ("SIS 3302", "SIS 3305"),
                "SIS 3302": (
                    (
                        1,
                        (1, 2, 5),
                        {
                            "bit": 10,
                            "clock rate": u.Quantity(100.0, unit="MHz"),
                            "nshotnum": 10,
                            "nt": 1000,
                            "sample average (hardware)": None,
                            "shot average (software)": None,
                        },
                    ),
                ),
                "SIS 3305": (
                    (
                        1,
                        (1, 2, 5),
                        {
                            "bit": 10,
                            "clock rate": u.Quantity(100.0, unit="MHz"),
                            "nshotnum": 10,
                            "nt": 1000,
                            "sample average (hardware)": None,
                            "shot average (software)": None,
                        },
                    ),
                ),
            }
        }

        # map instance
        _map = self.map

        # -- check `config_name` handling                           ----
        # `config_name` is None, there is MULTIPLE active configs
        configs = configs_i1.copy()
        configs.update(configs_i3)
        mock_configs.return_value = configs
        with self.assertRaises(ValueError):
            _map.get_adc_info(1, 1)

        # `config_name` is None, there is ONE active config
        mock_configs.return_value = configs_i1
        config_name = "config01"
        adc = _map.configs[config_name]["adc"][0]
        brd = _map.configs[config_name][adc][0][0]
        ch = _map.configs[config_name][adc][0][1][0]
        compare_to = _map.configs[config_name][adc][0][2].copy()
        compare_to.update(
            {
                "adc": adc,
                "board": brd,
                "channel": ch,
                "configuration name": config_name,
                "digitizer": _map.device_name,
            }
        )
        with self.assertWarns(UserWarning):
            adc_info = _map.get_adc_info(brd, ch, adc=adc)
            self.assertADCInfo(adc_info, compare_to=compare_to)

        # `config_name` is specifies an inactive config
        mock_configs.return_value = configs_i2
        config_name = "config02"
        adc = _map.configs[config_name]["adc"][0]
        brd = _map.configs[config_name][adc][0][0]
        ch = _map.configs[config_name][adc][0][1][0]
        compare_to = _map.configs[config_name][adc][0][2].copy()
        compare_to.update(
            {
                "adc": adc,
                "board": brd,
                "channel": ch,
                "configuration name": config_name,
                "digitizer": _map.device_name,
            }
        )
        with self.assertWarns(UserWarning):
            adc_info = _map.get_adc_info(brd, ch, config_name=config_name, adc=adc)
            self.assertADCInfo(adc_info, compare_to=compare_to)

        # -- check `adc` handling                                   ----
        # `adc` is None, the only ONE active adc
        mock_configs.return_value = configs_i1
        config_name = "config01"
        adc = _map.configs[config_name]["adc"][0]
        brd = _map.configs[config_name][adc][0][0]
        ch = _map.configs[config_name][adc][0][1][0]
        compare_to = _map.configs[config_name][adc][0][2].copy()
        compare_to.update(
            {
                "adc": adc,
                "board": brd,
                "channel": ch,
                "configuration name": config_name,
                "digitizer": _map.device_name,
            }
        )
        with self.assertWarns(UserWarning):
            adc_info = _map.get_adc_info(brd, ch, config_name=config_name)
            self.assertADCInfo(adc_info, compare_to=compare_to)

        # `adc` is None, the there are MULTIPLE active adc's
        mock_configs.return_value = configs_i3
        config_name = "config03"
        brd = _map.configs[config_name][adc][0][0]
        ch = _map.configs[config_name][adc][0][1][0]
        with self.assertRaises(ValueError):
            _map.get_adc_info(brd, ch, config_name=config_name)

        # -- check `board` argument handling                        ----
        # `board` not found
        mock_configs.return_value = configs_i1
        config_name = "config01"
        adc = _map.configs[config_name]["adc"][0]
        brd = -1
        ch = _map.configs[config_name][adc][0][1][0]
        with self.assertRaises(ValueError):
            _map.get_adc_info(brd, ch, config_name=config_name, adc=adc)

        # -- check `channel` argument handling                      ----
        # `channel` not found
        mock_configs.return_value = configs_i1
        config_name = "config01"
        adc = _map.configs[config_name]["adc"][0]
        brd = _map.configs[config_name][adc][0][0]
        ch = -1
        with self.assertRaises(ValueError):
            _map.get_adc_info(brd, ch, config_name=config_name, adc=adc)

        # -- everything works                                       ----
        mock_configs.return_value = configs_i1
        config_name = "config01"
        adc = _map.configs[config_name]["adc"][0]
        brd = _map.configs[config_name][adc][0][0]
        ch = _map.configs[config_name][adc][0][1][0]
        compare_to = _map.configs[config_name][adc][0][2].copy()
        compare_to.update(
            {
                "adc": adc,
                "board": brd,
                "channel": ch,
                "configuration name": config_name,
                "digitizer": _map.device_name,
            }
        )
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            adc_info = _map.get_adc_info(brd, ch, config_name=config_name, adc=adc)
            self.assertEqual(len(w), 0)
            self.assertADCInfo(adc_info, compare_to=compare_to)

    def test_not_h5py_group(self):
        """Test error if object to map is not h5py.Group"""
        with self.assertRaises(TypeError):
            self.map_device(None)

    def test_structure(self):
        """Test basic structure of the template class."""
        self.assertDigiTemplate(self.map, self.group)

    def assertADCInfo(self, adc_info: dict, compare_to=None):
        # check instance
        self.assertIsInstance(adc_info, dict)

        # examine keys
        self.assertIn("adc", adc_info)
        self.assertIn("board", adc_info)
        self.assertIn("channel", adc_info)
        self.assertIn("configuration name", adc_info)
        self.assertIn("digitizer", adc_info)

        # detailed comparison
        if bool(compare_to):
            for key, val in compare_to.items():
                self.assertIn(key, adc_info)
                self.assertEqual(val, adc_info[key])

    def assertDigiTemplate(self, _map: HDFMapDigiTemplate, _group: h5py):
        # check instance
        self.assertIsInstance(_map, HDFMapDigiTemplate)

        # check attribute existence
        # X '_build_configs'
        # X 'active_configs'
        # X 'configs'
        # X 'construct_dataset_name'
        # X 'construct_header_dataset_name'
        #   'deduce_config_active_status'
        # X 'device_adcs'
        # X 'device_name'
        #   'get_adc_info'
        # X 'group'
        # X 'info'
        #
        # * detailed tests of `deduce_config_active_status` and
        #   `get_adc_info` are left to their own test methods
        #
        attrs = (
            "_build_configs",
            "active_configs",
            "configs",
            "construct_dataset_name",
            "construct_header_dataset_name",
            "deduce_config_active_status",
            "device_adcs",
            "device_name",
            "get_adc_info",
            "group",
            "info",
        )
        for attr in attrs:
            self.assertTrue(hasattr(_map, attr))

        # -- check 'active_configs'                                 ----
        test_dict = {
            "config01": {"active": True},
            "config02": {"active": False},
            "config03": {"active": True},
        }
        with mock.patch.dict(_map.configs, test_dict):
            self.assertEqual(sorted(_map.active_configs), ["config01", "config03"])

        # -- check 'configs'                                        ----
        self.assertIsInstance(_map.configs, dict)
        self.assertEqual(len(_map.configs), 0)

        # -- check 'device_adcs'                                    ----
        self.assertIsInstance(type(_map).device_adcs, property)
        with self.assertRaises(AttributeError):
            _map.device_adcs = "con not do this"
        device_adcs = ("SIS 3302", "SIS 3301")
        _map._device_adcs = device_adcs
        self.assertEqual(_map.device_adcs, device_adcs)
        _map._device_adcs = ()

        # -- check 'device_name'                                    ----
        self.assertEqual(_map.device_name, _map.info["group name"])

        # -- check 'group'                                          ----
        self.assertEqual(_map.group, _group)

        # -- check 'info'                                           ----
        # assert is a dict
        self.assertIsInstance(_map.info, dict)

        # assert required keys
        self.assertIn("group name", _map.info)
        self.assertIn("group path", _map.info)

        # assert values
        self.assertEqual(_map.info["group name"], os.path.basename(_group.name))
        self.assertEqual(_map.info["group path"], _group.name)

        # -- check abstract methods                                 ----
        # Note: `self.map_device` overrides all abstract methods to
        #       return NotImplemented values
        #
        abs_methods = (
            "_build_configs",
            "construct_dataset_name",
            "construct_header_dataset_name",
        )
        for method in abs_methods:
            self.assertEqual(_map.__class__.__dict__[method](), NotImplemented)


if __name__ == "__main__":
    ut.main()
