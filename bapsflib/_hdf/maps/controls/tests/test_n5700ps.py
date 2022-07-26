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

from bapsflib._hdf.maps.controls import ConType
from bapsflib._hdf.maps.controls.n5700ps import HDFMapControlN5700PS
from bapsflib._hdf.maps.controls.tests.common import ControlTestCase
from bapsflib.utils.exceptions import HDFMappingError


class TestN5700PS(ControlTestCase):
    """Test class for HDFMapControlN5700PS"""

    # define setup variables
    DEVICE_NAME = "N5700_PS"
    DEVICE_PATH = "Raw data + config/N5700_PS"
    MAP_CLASS = HDFMapControlN5700PS

    def setUp(self):
        super().setUp()

    def tearDown(self):
        super().tearDown()

    def test_contype(self):
        self.assertEqual(self.map.info["contype"], ConType.power)

    def test_map_failures(self):
        """Test conditions that result in unsuccessful mappings."""
        # any failed build must throw a HDFMappingError
        #
        # make a default/clean 'N5700_PS' module
        self.mod.knobs.reset()

        # expected dataset does not exist
        # - rename 'Run time list' dataset
        self.mod.move("Run time list", "N5700 data")
        with self.assertRaises(HDFMappingError):
            _map = self.map
        self.mod.move("N5700 data", "Run time list")

        # 'N5700 power supply command list' attribute does not exist
        #
        config_name = self.mod.config_names[0]
        cl = self.mod[config_name].attrs["N5700 power supply command list"]
        self.mod[config_name].attrs["Wrong command list"] = cl
        del self.mod[config_name].attrs["N5700 power supply command list"]
        with self.assertRaises(HDFMappingError):
            _map = self.map
        self.mod[config_name].attrs["N5700 power supply command list"] = cl
        del self.mod[config_name].attrs["Wrong command list"]

        # there are no configuration groups to map
        del self.f["Raw data + config/N5700_PS/config01"]
        with self.assertRaises(HDFMappingError):
            _map = self.map
        self.mod.knobs.reset()

    def test_misc(self):
        """Test Miscellaneous features."""
        # make a default/clean 'Waveform' module
        self.mod.knobs.reset()

        # no RE match so _default_state_values_dict() is used for
        # 'command list'
        #
        config_name = self.mod.config_names[0]
        cl = np.bytes_("AMP 10.0 \nAMP 15.0 \nAMP 20.0 \n")
        self.mod[config_name].attrs["N5700 power supply command list"] = cl
        self.assertControlMapBasics(self.map, self.dgroup)
        self.mod.knobs.reset()

        # check warning if a general item is missing from group
        # - a warning is thrown, but mapping continues
        # - remove attribute 'IP address'
        config_name = self.mod.config_names[0]
        del self.mod[config_name].attrs["IP address"]
        with self.assertWarns(UserWarning):
            _map = self.map
        self.mod.knobs.reset()

        # '_construct_state_values_dict' throws KeyError when executing
        # '_build_configs'
        # - default dict is used for state values
        #
        with mock.patch.object(
            self.MAP_CLASS, "_construct_state_values_dict", side_effect=KeyError
        ):
            _map = self.map
            for cname, config in _map.configs.items():
                self.assertEqual(
                    config["state values"], _map._default_state_values_dict(cname)
                )

    def test_one_config(self):
        """
        Test mapping of the 'N5700_PS' group with only one
        configuration.
        """
        # reset to one config
        if self.mod.knobs.n_configs != 1:
            self.mod.knobs.n_configs = 1

        # assert details
        self.assertN5700PSDetails()

    def test_three_configs(self):
        """
        Test mapping of the 'N5700_PS' group with THREE configurations.
        """
        # reset to 3 configs
        if self.mod.knobs.n_configs != 3:
            self.mod.knobs.n_configs = 3

        # assert details
        self.assertN5700PSDetails()

    def assertN5700PSDetails(self):
        """
        Test details of a 'N5700_PS' mapping, i.e. the basic tests for
        a control device plus the unique features for the 'N5700_PS'
        group.
        """
        # define map instance
        _map = self.map

        # re-assert Mapping Basics
        self.assertControlMapBasics(_map, self.dgroup)

        # test dataset names
        self.assertEqual(_map.dataset_names, ["Run time list"])

        # test construct_dataset_names
        self.assertEqual(_map.construct_dataset_name(), "Run time list")

        # test for command list
        self.assertTrue(_map.has_command_list)

        # test attribute 'one_config_per_dataset'
        if self.mod.knobs.n_configs == 1:
            self.assertTrue(_map.one_config_per_dset)
        else:
            self.assertFalse(_map.one_config_per_dset)

        # test that 'configs' attribute is setup correctly
        self.assertConfigsGeneralItems(_map)

    def assertConfigsGeneralItems(self, _map):
        """
        Test structure of the general, polymorphic elements of the
        `configs` mapping dictionary.
        """
        # only asserts 'N5700_PS' specific attributes
        self.assertEqual(len(_map.configs), self.mod.knobs.n_configs)

        for cname, config in _map.configs.items():
            # Note: 'command list' is not included since it is
            #         covered by assertControlMapBasics()
            #
            self.assertIn(cname, self.mod.config_names)
            self.assertIn("IP address", config)
            self.assertIn("power supply device", config)
            self.assertIn("initial state", config)


if __name__ == "__main__":
    ut.main()
