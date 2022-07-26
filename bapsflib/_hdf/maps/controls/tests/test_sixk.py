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
import os
import unittest as ut

from unittest import mock

from bapsflib._hdf.maps.controls import ConType
from bapsflib._hdf.maps.controls.sixk import HDFMapControl6K
from bapsflib._hdf.maps.controls.tests.common import ControlTestCase
from bapsflib.utils.exceptions import HDFMappingError


class TestSixK(ControlTestCase):
    """Test class for HDFMapControl6K"""

    # define setup variables
    DEVICE_NAME = "6K Compumotor"
    DEVICE_PATH = "Raw data + config/6K Compumotor"
    MAP_CLASS = HDFMapControl6K

    def setUp(self):
        super().setUp()

    def tearDown(self):
        super().tearDown()

    def test_contype(self):
        self.assertEqual(self.map.info["contype"], ConType.motion)

    def test_map_failures(self):
        """Test conditions that result in unsuccessful mappings."""
        # any failed build must throw a HDFMappingError
        #
        # make a default/clean '6K Compumotor' module
        self.mod.knobs.reset()

        # -- no PL items (config groups) found                      ----
        # remove PL group instance
        rnum = self.mod.config_names[0]
        name = f"Probe: XY[{rnum}]: probe01"
        del self.dgroup[name]
        with self.assertRaises(HDFMappingError):
            _map = self.map

        # reset module
        self.mod.knobs.reset()

        # -- dataset name missing in HDF5 file                      ----
        # rename dataset
        rnum = self.mod.config_names[0]
        name = f"XY[{rnum}]: probe01"
        self.dgroup.move(name, "Wrong name")
        with self.assertRaises(HDFMappingError):
            _map = self.map

        # reset module
        self.mod.knobs.reset()

        # -- dataset name construction fails                        ----
        # - mock HDFMapControl6K.construct_dataset_name to throw a
        #   ValueError
        #
        with mock.patch.object(HDFMapControl6K, "construct_dataset_name") as cdn_mock:
            cdn_mock.side_effect = ValueError
            with self.assertRaises(HDFMappingError):
                _map = self.map

    def test_misc(self):
        """Test Miscellaneous features."""
        # make a default/clean module
        self.mod.knobs.reset()

        # an extra group that does not match PL or ML group formats
        self.dgroup.create_group("Random group")
        self.assertSixKDetails()
        del self.dgroup["Random group"]

    def test_construct_dataset_name(self):
        """Test operation of `construct_dataset_name` method."""
        # make a default/clean module
        self.mod.knobs.reset()

        # ---- NO argument passed                                   ----
        # 6K has one config
        self.mod.knobs.n_configs = 1
        dset_name = self.map.construct_dataset_name()
        self.assertEqual(dset_name, f"XY[{self.mod.config_names[0]}]: probe01")

        # 6K has >1 config
        self.mod.knobs.n_configs = 3
        with self.assertRaises(ValueError):
            self.map.construct_dataset_name()

        # --- ONE argument passed                                   ----
        # - construct_dataset_name() only uses the 1st argument
        #
        # args[0] is a configuration
        self.mod.knobs.n_configs = 3
        dset_name = self.map.construct_dataset_name(2)
        self.assertEqual(dset_name, "XY[2]: probe02")

        # args[0] is NOT a configuration
        with self.assertRaises(ValueError):
            self.map.construct_dataset_name(None)
            self.map.construct_dataset_name(["Hello"])

    def test_analyze_motionlist(self):
        """Test operation of `_analyze_motionlist` method."""
        # make a default/clean module
        self.mod.knobs.reset()

        # check method existence
        self.assertTrue(hasattr(self.map, "_analyze_motionlist"))

        # get ML group instance
        mlg = self.dgroup["Motion list: ml-0001"]

        # -- RE does NOT match against `gname`                      ----
        # - empty dict is returned
        self.assertEqual(self.map._analyze_motionlist("Not a ML"), {})

        # -- operation on default ML group                          ----
        ml_stuff = self.map._analyze_motionlist(os.path.basename(mlg.name))
        self.assertIsInstance(ml_stuff, dict)
        self.assertEqual(ml_stuff["name"], "ml-0001")
        self.assertIsInstance(ml_stuff["config"], dict)
        self.assertMLConfigDict(ml_stuff["config"])

        # -- group attribute 'Motion list'                          ----
        default = mlg.attrs["Motion list"]

        # 'Motion list' value does NOT match discovered ML name
        mlg.attrs["Motion list"] = "wrong name"
        with self.assertWarns(UserWarning):
            ml_stuff = self.map._analyze_motionlist(os.path.basename(mlg.name))
            self.assertEqual(ml_stuff["name"], "ml-0001")

        # 'Motion list' attribute does NOT exist
        del mlg.attrs["Motion list"]
        with self.assertWarns(UserWarning):
            ml_stuff = self.map._analyze_motionlist(os.path.basename(mlg.name))
            self.assertEqual(ml_stuff["name"], "ml-0001")

        # return to default
        mlg.attrs["Motion list"] = default

        # -- check simple attributes                                ----
        default = mlg.attrs["Motion count"]

        # attribute is missing
        del mlg.attrs["Motion count"]
        with self.assertWarns(UserWarning):
            ml_stuff = self.map._analyze_motionlist(os.path.basename(mlg.name))
            self.assertIsNone(ml_stuff["config"]["motion count"])

        # return to default
        mlg.attrs["Motion count"] = default

        # -- check 'Delta' attributes                               ----
        # - dependent on 'Delta x' and 'Delta y' keys
        default = mlg.attrs["Delta x"]

        # attribute is missing
        del mlg.attrs["Delta x"]
        with self.assertWarns(UserWarning):
            ml_stuff = self.map._analyze_motionlist(os.path.basename(mlg.name))
            self.assertTrue(
                np.array_equal(ml_stuff["config"]["delta"], np.array([None, None, None]))
            )

        # return to default
        mlg.attrs["Delta x"] = default

        # -- check 'Grid center' attributes                         ----
        # - dependent on 'Grid center x' and 'Grid center y' keys
        default = mlg.attrs["Grid center x"]

        # attribute is missing
        del mlg.attrs["Grid center x"]
        with self.assertWarns(UserWarning):
            ml_stuff = self.map._analyze_motionlist(os.path.basename(mlg.name))
            self.assertTrue(
                np.array_equal(ml_stuff["config"]["center"], np.array([None, None, None]))
            )

        # return to default
        mlg.attrs["Grid center x"] = default

        # -- check 'N' attributes                                   ----
        # - dependent on 'Grid center x' and 'Grid center y' keys
        default = mlg.attrs["Nx"]

        # attribute is missing
        del mlg.attrs["Nx"]
        with self.assertWarns(UserWarning):
            ml_stuff = self.map._analyze_motionlist(os.path.basename(mlg.name))
            self.assertTrue(
                np.array_equal(
                    ml_stuff["config"]["npoints"], np.array([None, None, None])
                )
            )

        # return to default
        mlg.attrs["Nx"] = default

    def test_analyze_probelist(self):
        """Test operation of `_analyze_probelist` method."""
        # make a default/clean module
        self.mod.knobs.reset()

        # check method existence
        self.assertTrue(hasattr(self.map, "_analyze_probelist"))

        # get PL group instance
        rnum = self.mod.config_names[0]
        name = f"Probe: XY[{rnum}]: probe01"
        plg = self.dgroup[name]

        # -- RE does NOT match against `gname`                      ----
        # - empty dict is returned
        self.assertEqual(self.map._analyze_probelist("Not a PL"), {})

        # -- operation on default PL group                          ----
        pl_stuff = self.map._analyze_probelist(os.path.basename(plg.name))
        self.assertIsInstance(pl_stuff, dict)
        self.assertEqual(pl_stuff["probe-id"], f"probe01 - {rnum}")
        self.assertIsInstance(pl_stuff["config"], dict)
        self.assertProbeConfigDict(pl_stuff["config"])

        # -- group attribute 'Probe'                                ----
        default = plg.attrs["Probe"]

        # 'Probe' value does NOT match discovered PL name
        plg.attrs["Probe"] = "wrong name"
        with self.assertWarns(UserWarning):
            pl_stuff = self.map._analyze_probelist(os.path.basename(plg.name))
            self.assertEqual(pl_stuff["probe-id"], f"probe01 - {rnum}")

        # 'Probe' attribute does NOT exist
        del plg.attrs["Probe"]
        with self.assertWarns(UserWarning):
            pl_stuff = self.map._analyze_probelist(os.path.basename(plg.name))
            self.assertEqual(pl_stuff["probe-id"], f"probe01 - {rnum}")

        # return to default
        plg.attrs["Probe"] = default

        # -- group attribute 'Receptacle'                           ----
        default = plg.attrs["Receptacle"]

        # 'Receptacle' value does NOT match discovered recepetacle
        # number
        plg.attrs["Receptacle"] = 10
        with self.assertWarns(UserWarning):
            pl_stuff = self.map._analyze_probelist(os.path.basename(plg.name))
            self.assertEqual(pl_stuff["config"]["receptacle"], rnum)

        # 'Probe' attribute does NOT exist
        del plg.attrs["Receptacle"]
        with self.assertWarns(UserWarning):
            pl_stuff = self.map._analyze_probelist(os.path.basename(plg.name))
            self.assertEqual(pl_stuff["config"]["receptacle"], rnum)

        # return to default
        plg.attrs["Receptacle"] = default

        # -- check simple attributes                                ----
        default = plg.attrs["Port"]

        # attribute is missing
        del plg.attrs["Port"]
        with self.assertWarns(UserWarning):
            ml_stuff = self.map._analyze_probelist(os.path.basename(plg.name))
            self.assertIsNone(ml_stuff["config"]["port"])

        # return to default
        plg.attrs["Port"] = default

    def test_one_config_one_ml(self):
        # reset to one config and one motion list
        if self.mod.knobs.n_configs != 1:
            self.mod.knobs.n_configs = 1
        if self.mod.knobs.n_motionlists != 1:
            self.mod.knobs.n_motionlists = 1

        # assert details
        self.assertSixKDetails()

    def test_one_config_three_ml(self):
        # reset to one config and one motion list
        if self.mod.knobs.n_configs != 1:
            self.mod.knobs.n_configs = 1
        if self.mod.knobs.n_motionlists != 3:
            self.mod.knobs.n_motionlists = 3

        # assert details
        self.assertSixKDetails()

    def test_three_config(self):
        # reset to one config and one motion list
        if self.mod.knobs.n_configs != 3:
            self.mod.knobs.n_configs = 3

        # assert details
        self.assertSixKDetails()

    def assertSixKDetails(self):
        """
        Test details of a '6K Compumotor' mapping, i.e. the basic tests
        for a control device plus the unique features for the
        '6K Compumotor' group.
        """
        # define map instance
        _map = self.map

        # re-assert Mapping Basics
        self.assertControlMapBasics(_map, self.dgroup)

        # test dataset names
        # TODO: test dataset names

        # test construct_dataset_names
        # TODO: how to test 'construct_dataset_names'

        # test for command list
        self.assertFalse(_map.has_command_list)

        # test attribute 'one_config_per_dataset'
        self.assertTrue(_map.one_config_per_dset)

        # test that 'configs' attribute is setup correctly
        self.assertConfigsGeneralItems(_map)

    def assertConfigsGeneralItems(self, _map):
        """
        Test structure of the general, polymorphic elements of the
        `configs` mapping dictionary.
        """
        self.assertEqual(len(_map.configs), self.mod.knobs.n_configs)

        for cname, config in _map.configs.items():
            # look for '6K Compumotor' specific keys
            #
            self.assertIn(cname, self.mod.config_names)
            self.assertIn("receptacle", config)
            self.assertIn("probe", config)
            self.assertIn("motion lists", config)

            # inspect 'receptacle' item
            self.assertTrue(np.issubdtype(type(config["receptacle"]), np.integer))
            self.assertTrue(config["receptacle"] > 0)
            self.assertEqual(cname, config["receptacle"])

            # inspect 'probe' item
            self.assertIsInstance(config["probe"], dict)
            self.assertProbeConfigDict(config["probe"])

            # inspect 'motion lists' item
            self.assertIsInstance(config["motion lists"], dict)
            for val in config["motion lists"].values():
                self.assertMLConfigDict(val)

    def assertProbeConfigDict(self, config: dict):
        """Test existence of keys for a 'probe' item config"""
        pkeys = [
            "probe name",
            "group name",
            "group path",
            "receptacle",
            "calib",
            "level sy (cm)",
            "port",
            "probe channels",
            "probe type",
            "unnamed",
            "sx at end (cm)",
            "z",
        ]
        for key in pkeys:
            self.assertIn(key, config)

    def assertMLConfigDict(self, config: dict):
        """Test existence of keys for a 'motion list' item config"""
        self.assertIsInstance(config, dict)
        mkeys = [
            "group name",
            "group path",
            "created date",
            "data motion count",
            "motion count",
            "delta",
            "center",
            "npoints",
        ]
        for key in mkeys:
            self.assertIn(key, config)


if __name__ == "__main__":
    ut.main()
