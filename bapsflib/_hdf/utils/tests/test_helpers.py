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

from h5py import Group
from numpy.lib import recfunctions as rfn

from bapsflib._hdf.maps.controls.waveform import HDFMapControlWaveform
from bapsflib._hdf.utils.file import File
from bapsflib._hdf.utils.helpers import (
    build_shotnum_dset_relation,
    condition_controls,
    condition_shotnum,
    do_shotnum_intersection,
)
from bapsflib._hdf.utils.tests import TestBase
from bapsflib.utils import _bytes_to_str
from bapsflib.utils.decorators import with_bf


class TestBuildShotnumDsetRelation(TestBase):
    """Test Case for build_shotnum_dset_relation"""

    def setUp(self):
        # setup HDF5 file
        super().setUp()
        self.f.add_module("Waveform", mod_args={"n_configs": 1, "sn_size": 100})
        self.mod = self.f.modules["Waveform"]

    def tearDown(self):
        super().tearDown()

    @property
    def cgroup(self) -> Group:
        return self.f["Raw data + config/Waveform"]

    @property
    def map(self):
        return HDFMapControlWaveform(self.cgroup)

    def test_simple_dataset(self):
        """
        Tests for a dataset containing recorded data for a single
        configuration.
        """
        # -- dset with 1 shotnum                                    ----
        self.mod.knobs.sn_size = 1
        self.assertInRangeSN()
        self.assertOutRangeSN()

        # -- typical dset with sequential shot numbers              ----
        self.mod.knobs.sn_size = 100
        self.assertInRangeSN()
        self.assertOutRangeSN()

        # -- dset with non-sequential shot numbers                  ----
        self.mod.knobs.sn_size = 100
        data = self.cgroup["Run time list"][...]
        data["Shot number"] = np.append(
            np.arange(5, 25, dtype=np.uint32),
            np.append(
                np.arange(51, 111, dtype=np.uint32), np.arange(150, 170, dtype=np.uint32)
            ),
        )
        del self.cgroup["Run time list"]
        self.cgroup.create_dataset("Run time list", data=data)
        self.assertInRangeSN()
        self.assertOutRangeSN()

    def test_complex_dataset(self):
        """
        Tests for a dataset containing recorded data for a multiple
        configurations.
        """
        # define multiple configurations for one dataset
        self.mod.knobs.n_configs = 3

        # -- dset with 1 shotnum                                    ----
        self.mod.knobs.sn_size = 1
        self.assertInRangeSN()
        self.assertOutRangeSN()

        # -- typical dset with sequential shot numbers              ----
        self.mod.knobs.sn_size = 100
        self.assertInRangeSN()
        self.assertOutRangeSN()

        # -- dset with non-sequential shot numbers                  ----
        self.mod.knobs.sn_size = 100
        data = self.cgroup["Run time list"][...]
        sn_arr = np.append(
            np.arange(5, 25, dtype=np.uint32),
            np.append(
                np.arange(51, 111, dtype=np.uint32), np.arange(150, 170, dtype=np.uint32)
            ),
        )
        data["Shot number"][0::3] = sn_arr
        data["Shot number"][1::3] = sn_arr
        data["Shot number"][2::3] = sn_arr
        del self.cgroup["Run time list"]
        self.cgroup.create_dataset("Run time list", data=data)
        self.assertInRangeSN()
        self.assertOutRangeSN()

        # -- dset without a configuration fields                    ----
        self.mod.knobs.sn_size = 50
        data = self.cgroup["Run time list"][...]
        data = rfn.rename_fields(data, {"Configuration name": "oops"})
        del self.cgroup["Run time list"]
        self.cgroup.create_dataset("Run time list", data=data)
        cdset = self.cgroup["Run time list"]
        with self.assertRaises(ValueError):
            build_shotnum_dset_relation(
                shotnum=np.empty(5, dtype=np.uint32),
                dset=cdset,
                shotnumkey="Shot number",
                n_configs=len(self.map.configs),
                config_column_value="config01",
            )

    def assertInRangeSN(self):
        """
        Assert shot numbers cases with in-range of dataset shot numbers.
        """
        cdset = self.cgroup["Run time list"]
        shotnumkey = "Shot number"
        configkey = "Configuration name"
        last_sn = cdset[-1, "Shot number"]
        shotnum_list = [
            [10],
            [50, 51],
            [50, 60],
            [1, self.mod.knobs.sn_size],
            [50, 51, 52, 53, 54, 55, 56, 57, 58, 59],
            [1, 11, 21, 31, 41, 51, 61, 71, 81, 91],
        ]
        if last_sn > 2:
            shotnum_list.append([last_sn - 1])
        for og_shotnum in shotnum_list:
            if og_shotnum == [1, 1]:
                continue

            sn_arr = np.array(og_shotnum, dtype=np.uint32)
            for cconfn in self.map.configs:
                index, sni = build_shotnum_dset_relation(
                    shotnum=sn_arr,
                    dset=cdset,
                    shotnumkey=shotnumkey,
                    n_configs=len(self.map.configs),
                    config_column_value=cconfn,
                )

                self.assertSNSuite(
                    sn_arr, index, sni, cdset, shotnumkey, configkey, cconfn
                )

    def assertOutRangeSN(self):
        """
        Assert shot number cases where some shot numbers are out of
        range of the dataset shotnumbers.
        """
        # Note: condition_shotnum() will ensure shotnum >= 0 so
        #       build_shotnum_dset_relation() does not handle this
        #
        # - one above largest shot number
        # - out of range above (sn_size+1, sn_size+10, sn_size+100)
        #   and valid
        #
        shotnum_list = [
            [self.mod.knobs.sn_size + 1],
            [self.mod.knobs.sn_size + 1, self.mod.knobs.sn_size + 10],
            [10, 15, self.mod.knobs.sn_size + 1],
            [
                10,
                15,
                self.mod.knobs.sn_size + 1,
                self.mod.knobs.sn_size + 10,
                self.mod.knobs.sn_size + 100,
            ],
        ]
        cdset = self.cgroup["Run time list"]
        shotnumkey = "Shot number"
        configkey = "Configuration name"
        for ii, og_shotnum in enumerate(shotnum_list):
            sn_arr = np.array(og_shotnum, dtype=np.uint32)
            for jj, config_name in enumerate(self.map.configs):
                config_column = configkey if (ii * jj) % 2 else None

                index, sni = build_shotnum_dset_relation(
                    shotnum=sn_arr,
                    dset=cdset,
                    shotnumkey=shotnumkey,
                    n_configs=len(self.map.configs),
                    config_column_value=config_name,
                    config_column=config_column,
                )

                self.assertSNSuite(
                    sn_arr, index, sni, cdset, shotnumkey, configkey, config_name
                )

    def assertSNSuite(self, shotnum, index, sni, cdset, shotnumkey, configkey, cconfn):
        """Suite of assertions for shot number conditioning"""
        # shotnum    - original requested shot number
        # index      - index of dataset
        # sni        - boolean mask for shotnum
        #               shotnum[sni] = cdset[index, shotnumkey]
        # cdset      - control devices dataset
        # shotnumkey - field in cdset that corresponds to shot numbers
        # configkey  - field in cdset that corresponds to configuration
        #              names
        # cconfn     - configuration name for control device
        #
        # all return variables should be np.ndarray
        self.assertTrue(isinstance(index, np.ndarray))
        self.assertTrue(isinstance(sni, np.ndarray))

        # all should be 1D arrays
        self.assertEqual(index.ndim, 1)
        self.assertEqual(sni.ndim, 1)

        # equate array sizes
        self.assertEqual(shotnum.size, sni.size)
        self.assertEqual(np.count_nonzero(sni), index.size)

        # shotnum[sni] = cdset[index, shotnumkey]
        if index.size != 0:
            self.assertTrue(
                np.array_equal(shotnum[sni], cdset[index.tolist(), shotnumkey])
            )
        else:
            self.assertEqual(shotnum[sni].size, 0)

        # ensure correct config is grabbed
        if index.size != 0:
            cname_arr = cdset[index.tolist(), configkey]
            for name in cname_arr:
                self.assertEqual(_bytes_to_str(name), cconfn)

    def test_raises(self):
        base_kwargs = {
            "shotnum": np.arange(1, 30, 2),
            "dset": self.cgroup["Run time list"],
            "shotnumkey": "Shot number",
            "n_configs": 1,
            "config_column_value": list(self.map.configs.keys())[0],
            "config_column": "Configuration name",
        }
        _conditions = [
            # (assert, kwargs, expected)
            (
                self.assertRaises,
                {**base_kwargs, "shotnumkey": "wrong name"},
                ValueError,
            ),
            (
                self.assertRaises,
                {**base_kwargs, "config_column": "wrong name"},
                ValueError,
            ),
            (
                self.assertRaises,
                {**base_kwargs, "config_column_value": "wrong value"},
                ValueError,
            ),
        ]
        for _assert, kwargs, expected in _conditions:
            self.assert_runner(
                _assert=_assert,
                attr=build_shotnum_dset_relation,
                args=(),
                kwargs=kwargs,
                expected=expected,
            )

    def test_raises_multiple_configuration_columns(self):
        # testing no config_column given (i.e. config_column == None) and
        # the dataset has multiple columns with "configuration" in their
        # name
        #
        # modify dataset to have two configuration columns
        data = self.cgroup["Run time list"][...]
        data = rfn.append_fields(data, "configuration 2", data["Configuration name"])
        del self.cgroup["Run time list"]
        self.cgroup.create_dataset("Run time list", data=data)

        with self.assertRaises(ValueError):
            build_shotnum_dset_relation(
                shotnum=np.arange(1, 30, 2),
                dset=self.cgroup["Run time list"],
                shotnumkey="Shot number",
                n_configs=1,
                config_column_value=list(self.map.configs.keys())[0],
                config_column=None,
            )

    def test_raises_no_configuration_column_w_multiple_configs(self):
        # testing no config_column given (i.e. config_column == None) and
        # the dataset has NO columns with "configuration" in their
        # name and the dset holds multiple configurations
        #
        # modify dataset to have NO configuration columns
        data = self.cgroup["Run time list"][...]
        data = rfn.append_fields(data, "bad named column", data["Configuration name"])
        column_names = list(data.dtype.names)
        column_names.remove("Configuration name")
        data = data[column_names]
        del self.cgroup["Run time list"]
        self.cgroup.create_dataset("Run time list", data=data)

        with self.assertRaises(ValueError):
            build_shotnum_dset_relation(
                shotnum=np.arange(1, 30, 2),
                dset=self.cgroup["Run time list"],
                shotnumkey="Shot number",
                n_configs=2,
                config_column_value=list(self.map.configs.keys())[0],
                config_column=None,
            )

    def test_raises_dset_single_config_w_duplicate_shotnums(self):
        # testing that dataset indicated with one configuration (n_configs == 1)
        # but has duplicate shot numbers (indicating multiple configs)
        #
        # modify dataset
        data = self.cgroup["Run time list"][...]
        new_shotnum = np.tile(data["Shot number"], 2)
        column_names = list(data.dtype.names)
        column_names.remove("Shot number")
        data = data[column_names]
        data = rfn.append_fields(data, "Shot number", new_shotnum)
        del self.cgroup["Run time list"]
        self.cgroup.create_dataset("Run time list", data=data)

        with self.assertRaises(ValueError):
            build_shotnum_dset_relation(
                shotnum=np.arange(1, 30, 2),
                dset=self.cgroup["Run time list"],
                shotnumkey="Shot number",
                n_configs=1,
                config_column_value=list(self.map.configs.keys())[0],
                config_column=None,
            )

    def test_dset_per_config(self):
        # Test a dataset that has no configuration column and represents
        # only one configuration
        #
        # modify dataset to have two configuration columns
        data = self.cgroup["Run time list"][...]
        column_names = list(data.dtype.names)
        column_names.remove("Configuration name")
        data = data[column_names]
        del self.cgroup["Run time list"]
        self.cgroup.create_dataset("Run time list", data=data)

        dset = self.cgroup["Run time list"]
        shotnums = [
            np.arange(1, 30, 2),
            np.arange(90, 110, 1),
        ]
        for shotnum in shotnums:
            with self.subTest(shotnum=shotnum):
                index, sni = build_shotnum_dset_relation(
                    shotnum=shotnum,
                    dset=dset,
                    shotnumkey="Shot number",
                    n_configs=1,
                    config_column_value=list(self.map.configs.keys())[0],
                    config_column=None,
                )
                self.assertTrue(np.allclose(shotnum[sni], dset["Shot number"][index]))

    def test_sequential_configurations(self):
        # Test relation construction when a dataset saves configuration data
        # sequentially... i.e. all data for config 1 then all data for config 2
        #
        # modify dataset to have two configuration columns
        self.mod.knobs.n_configs = 2
        self.mod.knobs.sn_size = 50
        config_names = list(self.map.configs.keys())
        data = self.cgroup["Run time list"][...]
        data["Shot number"] = np.arange(1, 101, 1, dtype=data["Shot number"].dtype)
        data["Configuration name"][0:50] = config_names[0]
        data["Configuration name"][50:100] = config_names[1]
        del self.cgroup["Run time list"]
        self.cgroup.create_dataset("Run time list", data=data)

        base_kwargs = {
            "shotnum": np.arange(40, 61, 1),
            "dset": self.cgroup["Run time list"],
            "shotnumkey": "Shot number",
            "n_configs": 2,
            "config_column_value": None,
            "config_column": "Configuration name",
        }
        _conditions = [
            # (kwargs, expected)
            (
                {**base_kwargs, "config_column_value": config_names[0]},
                np.arange(40, 51, 1),
            ),
            (
                {**base_kwargs, "config_column_value": config_names[1]},
                np.arange(51, 61, 1),
            ),
        ]
        for kwargs, expected in _conditions:
            with self.subTest(kwargs=kwargs, expected=expected):
                index, sni = build_shotnum_dset_relation(**kwargs)

                self.assertTrue(
                    np.allclose(
                        kwargs["shotnum"][sni],
                        kwargs["dset"]["Shot number"][index],
                    )
                )
                self.assertTrue(np.allclose(kwargs["shotnum"][sni], expected))


class TestConditionControls(TestBase):
    """Test Case for condition_controls"""

    # What to test:
    # 1. passing of non lapd.File object
    #    - raises AttributeError
    # 2. passing of controls as None (or not a list)
    #    - raises TypeError
    # 3. HDF5 file with no controls
    #    - raises AttributeError
    # 4. HDF5 file with one control
    #    - pass controls with
    #      a. just control name, no config
    #      b. control name and valid config
    #      c. control name and invalid config
    #      d. two control names
    # 5. HDF5 file with multiple controls
    #

    def setUp(self):
        # setup HDF5 file
        super().setUp()

    def tearDown(self):
        super().tearDown()

    @with_bf
    def test_input_failures(self, _bf: File):
        """Test input failures of `controls`"""
        # `controls` is Null
        self.assertRaises(ValueError, condition_controls, _bf, [])

        # `controls` is not a string or Iterable
        self.assertRaises(TypeError, condition_controls, _bf, True)

        # 'controls` element is not a str or tuple
        self.assertRaises(TypeError, condition_controls, _bf, ["Waveform", 8])

        # `controls` tuple element has length > 2
        self.assertRaises(ValueError, condition_controls, _bf, [("Waveform", "c1", "c2")])

    @with_bf
    def test_file_w_one_control(self, _bf: File):
        """
        Test `controls` conditioning for file with one control device.
        """
        # set one control device
        self.f.add_module("Waveform", mod_args={"n_configs": 1, "sn_size": 100})
        _bf._map_file()  # re-map file

        # ---- Waveform w/ one Configuration                        ----
        # conditions that work
        con_list = [
            "Waveform",
            ("Waveform",),
            ["Waveform"],
            [("Waveform", "config01")],
        ]
        for og_con in con_list:
            self.assertEqual(condition_controls(_bf, og_con), [("Waveform", "config01")])

        # conditions that raise ValueError
        con_list = [
            ["Waveform", "config01"],
            ["Waveform", ("Waveform", "config01")],
            ["Waveform", "6K Compumotor"],
        ]
        for og_con in con_list:
            self.assertRaises(ValueError, condition_controls, _bf, og_con)

        # ---- Waveform w/ three Configurations                     ----
        self.f.modules["Waveform"].knobs.n_configs = 3
        _bf._map_file()  # re-map file

        # conditions that work
        con_list = [[("Waveform", "config01")], [("Waveform", "config02")]]
        for og_con in con_list:
            self.assertEqual(condition_controls(_bf, og_con), og_con)

        # conditions that raise ValueError
        con_list = [
            ["Waveform"],
            ["6K Compumotor", ("Waveform", "config01")],
        ]
        for og_con in con_list:
            self.assertRaises(ValueError, condition_controls, _bf, og_con)

    @with_bf
    def test_file_w_multiple_controls(self, _bf: File):
        """
        Test `controls` conditioning for file with multiple (2) control
        devices.
        """
        # set modules
        self.f.add_module("Waveform", {"n_configs": 1, "sn_size": 100})
        self.f.add_module("6K Compumotor", {"n_configs": 1, "sn_size": 100})
        _bf._map_file()  # re-map file

        # ---- 1 Waveform Config & 1 6K Config                      ----
        sixk_cspec = self.f.modules["6K Compumotor"].config_names[0]

        # conditions that work
        con_list = [
            ("Waveform", [("Waveform", "config01")]),
            (["Waveform"], [("Waveform", "config01")]),
            ([("Waveform", "config01")], [("Waveform", "config01")]),
            (["6K Compumotor"], [("6K Compumotor", sixk_cspec)]),
            ([("6K Compumotor", sixk_cspec)], [("6K Compumotor", sixk_cspec)]),
            (
                ["Waveform", "6K Compumotor"],
                [("Waveform", "config01"), ("6K Compumotor", sixk_cspec)],
            ),
            (
                ["Waveform", ("6K Compumotor", sixk_cspec)],
                [("Waveform", "config01"), ("6K Compumotor", sixk_cspec)],
            ),
            (
                [("Waveform", "config01"), "6K Compumotor"],
                [("Waveform", "config01"), ("6K Compumotor", sixk_cspec)],
            ),
            (
                [("Waveform", "config01"), ("6K Compumotor", sixk_cspec)],
                [("Waveform", "config01"), ("6K Compumotor", sixk_cspec)],
            ),
        ]
        for og_con, correct_con in con_list:
            self.assertEqual(condition_controls(_bf, og_con), correct_con)

        # conditions that raise TypeError
        con_list = [
            ["6K Compumotor", sixk_cspec],
        ]
        for og_con in con_list:
            self.assertRaises(TypeError, condition_controls, _bf, og_con)

        # conditions that raise ValueError
        con_list = [
            ["Waveform", "config01"],
            ["Waveform", ("Waveform", "config01")],
            ["6K Compumotor", ("6K Compumotor", sixk_cspec)],
            [("Waveform", "config02")],
        ]
        for og_con in con_list:
            self.assertRaises(ValueError, condition_controls, _bf, og_con)

        # ---- 3 Waveform Config & 1 6K Config                      ----
        self.f.modules["Waveform"].knobs.n_configs = 3
        _bf._map_file()  # re-map file
        sixk_cspec = self.f.modules["6K Compumotor"].config_names[0]

        # conditions that work
        con_list = [
            ([("Waveform", "config01")], [("Waveform", "config01")]),
            ([("Waveform", "config03")], [("Waveform", "config03")]),
            ("6K Compumotor", [("6K Compumotor", sixk_cspec)]),
            (["6K Compumotor"], [("6K Compumotor", sixk_cspec)]),
            ([("6K Compumotor", sixk_cspec)], [("6K Compumotor", sixk_cspec)]),
            (
                [("Waveform", "config01"), "6K Compumotor"],
                [("Waveform", "config01"), ("6K Compumotor", sixk_cspec)],
            ),
            (
                [("Waveform", "config02"), ("6K Compumotor", sixk_cspec)],
                [("Waveform", "config02"), ("6K Compumotor", sixk_cspec)],
            ),
        ]
        for og_con, correct_con in con_list:
            self.assertEqual(condition_controls(_bf, og_con), correct_con)

        # conditions that raise TypeError
        con_list = [
            ["6K Compumotor", sixk_cspec],
        ]
        for og_con in con_list:
            self.assertRaises(TypeError, condition_controls, _bf, og_con)

        # conditions that raise ValueError
        con_list = [
            ["Waveform"],
            ["Waveform", "config01"],
            ["Waveform", "6K Compumotor"],
            ["Waveform", ("6K Compumotor", sixk_cspec)],
            ["Waveform", ("Waveform", "config01")],
            ["6K Compumotor", ("6K Compumotor", sixk_cspec)],
            [("Waveform", "config05")],
        ]
        for og_con in con_list:
            self.assertRaises(ValueError, condition_controls, _bf, og_con)

        # ---- 1 Waveform Config & 3 6K Config                      ----
        self.f.modules["Waveform"].knobs.n_configs = 1
        self.f.modules["6K Compumotor"].knobs.n_configs = 3
        _bf._map_file()  # re-map file
        sixk_cspec = self.f.modules["6K Compumotor"].config_names

        # conditions that work
        con_list = [
            (["Waveform"], [("Waveform", "config01")]),
            ([("Waveform", "config01")], [("Waveform", "config01")]),
            ([("6K Compumotor", sixk_cspec[0])], [("6K Compumotor", sixk_cspec[0])]),
            ([("6K Compumotor", sixk_cspec[2])], [("6K Compumotor", sixk_cspec[2])]),
            (
                ["Waveform", ("6K Compumotor", sixk_cspec[1])],
                [("Waveform", "config01"), ("6K Compumotor", sixk_cspec[1])],
            ),
        ]
        for og_con, correct_con in con_list:
            self.assertEqual(condition_controls(_bf, og_con), correct_con)

        # conditions that raise TypeError
        con_list = [
            ["6K Compumotor", sixk_cspec[0]],
        ]
        for og_con in con_list:
            self.assertRaises(TypeError, condition_controls, _bf, og_con)

        # conditions that raise ValueError
        con_list = [
            ["Waveform", "config01"],
            ["6K Compumotor"],
            ["Waveform", "6K Compumotor"],
            [("Waveform", "config01"), "6K Compumotor"],
            ["Waveform", ("Waveform", "config01")],
            ["6K Compumotor", ("6K Compumotor", sixk_cspec[1])],
            [("Waveform", "config02")],
        ]
        for og_con in con_list:
            self.assertRaises(ValueError, condition_controls, _bf, og_con)

        # ---- 3 Waveform Config & 3 6K Config                      ----
        self.f.modules["Waveform"].knobs.n_configs = 3
        _bf._map_file()  # re-map file
        sixk_cspec = self.f.modules["6K Compumotor"].config_names

        # conditions that work
        con_list = [
            ([("Waveform", "config01")], [("Waveform", "config01")]),
            ([("Waveform", "config02")], [("Waveform", "config02")]),
            ([("6K Compumotor", sixk_cspec[0])], [("6K Compumotor", sixk_cspec[0])]),
            ([("6K Compumotor", sixk_cspec[2])], [("6K Compumotor", sixk_cspec[2])]),
            (
                [("Waveform", "config03"), ("6K Compumotor", sixk_cspec[1])],
                [("Waveform", "config03"), ("6K Compumotor", sixk_cspec[1])],
            ),
        ]
        for og_con, correct_con in con_list:
            self.assertEqual(condition_controls(_bf, og_con), correct_con)

        # conditions that raise TypeError
        con_list = [
            ["6K Compumotor", sixk_cspec[0]],
        ]
        for og_con in con_list:
            self.assertRaises(TypeError, condition_controls, _bf, og_con)

        # conditions that raise ValueError
        con_list = [
            ["Waveform"],
            ["Waveform", "config01"],
            ["6K Compumotor"],
            ["Waveform", "6K Compumotor"],
            [("Waveform", "config01"), "6K Compumotor"],
            ["Waveform", ("Waveform", "config01")],
            ["6K Compumotor", ("6K Compumotor", sixk_cspec[1])],
        ]
        for og_con in con_list:
            self.assertRaises(ValueError, condition_controls, _bf, og_con)

    @with_bf
    def test_controls_w_same_contype(self, _bf: File):
        """
        Test `controls` conditioning for multiple devices with the
        same contype.
        """
        # set modules (1 Waveform Config & 1 6K Config)
        self.f.add_module("Waveform", {"n_configs": 1, "sn_size": 100})
        self.f.add_module("6K Compumotor", {"n_configs": 1, "sn_size": 100})
        _bf._map_file()  # re-map file

        # fake 6K as contype.waveform
        _bf.file_map.controls["6K Compumotor"]._contype = _bf.file_map.controls[
            "Waveform"
        ].contype

        # test
        self.assertRaises(
            TypeError, condition_controls, _bf, ["Waveform", "6K Compumotor"]
        )


class TestConditionShotnum(TestBase):
    """Test Case for condition_shotnum"""

    def test_shotnum_int(self):
        # shotnum <= 0 (invalid)
        sn = [-20, 0]
        for shotnum in sn:
            with self.assertRaises(ValueError):
                _sn = condition_shotnum(shotnum, [], [])

        # shotnum > 0 (valid)
        sn = [1, 100]
        for shotnum in sn:
            _sn = condition_shotnum(shotnum, [], [])

            self.assertIsInstance(_sn, np.ndarray)
            self.assertEqual(_sn.shape, (1,))
            self.assertTrue(np.issubdtype(_sn.dtype, np.uint32))
            self.assertEqual(_sn[0], shotnum)

    def test_shotnum_list(self):
        # not all list elements are integers
        sn = [
            [0, 1, None],
            [1.5, 2.6],
        ]
        for shotnum in sn:
            with self.assertRaises(ValueError):
                _sn = condition_shotnum(shotnum, [], [])

        # all shotnum values are <= 0
        sn = [
            [0],
            [-20, -5, -1],
        ]
        for shotnum in sn:
            with self.assertRaises(ValueError):
                _sn = condition_shotnum(shotnum, [], [])

        # valid shotnum lists
        sn = [
            ([0, 1, 5, 8], np.array([1, 5, 8], dtype=np.uint32)),
            ([-20, -5, 10], np.array([10], dtype=np.uint32)),
            ([1, 2, 4], np.array([1, 2, 4], dtype=np.uint32)),
        ]
        for shotnum, ex_sn in sn:
            _sn = condition_shotnum(shotnum, [], [])

            self.assertIsInstance(_sn, np.ndarray)
            self.assertTrue(np.array_equal(_sn, ex_sn))

    def test_shotnum_slice(self):
        # create 2 fake datasets (d1 and d1)
        data = np.array(
            np.arange(1, 6, dtype=np.uint32), dtype=[("Shot number", np.uint32)]
        )
        self.f.create_dataset("d1", data=data)
        data["Shot number"] = np.arange(3, 8, dtype=np.uint32)
        self.f.create_dataset("d2", data=data)

        # make fake dicts
        dset_list = [self.f["d1"], self.f["d2"]]
        shotnumkey_list = ["Shot number", "Shot number"]

        # invalid shotnum slices (creates NULL arrays)
        with self.assertRaises(ValueError):
            _sn = condition_shotnum(slice(-1, -4, 1), dset_list, shotnumkey_list)

        # valid shotnum slices
        sn = [
            (slice(None), np.array([1, 2, 3, 4, 5, 6, 7], dtype=np.uint32)),
            (slice(3), np.array([1, 2], dtype=np.uint32)),
            (slice(1, 8, 3), np.array([1, 4, 7], dtype=np.uint32)),
            (slice(5, 10, 1), np.array([5, 6, 7, 8, 9], dtype=np.uint32)),
            (slice(-2, -1), np.array([6], dtype=np.uint32)),
        ]
        for shotnum, ex_sn in sn:
            _sn = condition_shotnum(shotnum, dset_list, shotnumkey_list)

            self.assertIsInstance(_sn, np.ndarray)
            self.assertTrue(np.array_equal(_sn, ex_sn))

        # remove datasets
        del self.f["d1"]
        del self.f["d2"]

    def test_shotnum_ndarray(self):
        # shotnum invalid
        # 1. is not 1 dimensional
        # 2. has fields
        # 3. is not np.integer
        # 4. would result in NULL
        sn = [
            np.array([[1, 2], [3, 5]], dtype=np.uint32),
            np.zeros((5,), dtype=[("f1", np.uint8)]),
            np.array([True, False], dtype=bool),
            np.array([5.5, 7], dtype=np.float32),
            np.array([-20, -1], dtype=np.int32),
            np.array([0], dtype=np.int32),
        ]
        for shotnum in sn:
            with self.assertRaises(ValueError):
                _sn = condition_shotnum(shotnum, [], [])

        # shotnum valid
        sn = [
            (np.array([12], np.int32), np.array([12], np.uint32)),
            (np.array([-5, 0, 10], np.int32), np.array([10], np.uint32)),
            (np.array([20, 30], np.int32), np.array([20, 30], np.uint32)),
        ]
        for shotnum, ex_sn in sn:
            _sn = condition_shotnum(shotnum, [], [])

            self.assertIsInstance(_sn, np.ndarray)
            self.assertTrue(np.array_equal(_sn, ex_sn))

    def test_shotnum_invalid(self):
        # shotnum not int, List[int], slice, or ndarray
        sn = [1.5, None, True, {}]
        for shotnum in sn:
            with self.assertRaises(ValueError):
                _sn = condition_shotnum(shotnum, [], [])


class TestDoShotnumIntersection(ut.TestCase):
    """Test Case for do_shotnum_intersection"""

    def test_one_control(self):
        """Test intersection behavior with one control device"""
        # test a case that results in a null result
        shotnum = np.arange(1, 21, 1, dtype=np.uint32)
        sni_dict = {"Waveform": {"command": np.zeros(shotnum.shape, dtype=bool)}}
        index_dict = {"Waveform": {"command": np.array([])}}
        self.assertRaises(
            ValueError, do_shotnum_intersection, shotnum, sni_dict, index_dict
        )

        # test a working case
        shotnum = np.arange(1, 21, 1)
        sni_dict = {"Waveform": {"command": np.zeros(shotnum.shape, dtype=bool)}}
        index_dict = {"Waveform": {"command": np.array([5, 6, 7])}}
        sni_dict["Waveform"]["command"][[5, 6, 7]] = True
        shotnum, sni_dict, index_dict = do_shotnum_intersection(
            shotnum, sni_dict, index_dict
        )
        self.assertTrue(np.array_equal(shotnum, [6, 7, 8]))
        self.assertTrue(np.array_equal(sni_dict["Waveform"]["command"], [True] * 3))
        self.assertTrue(np.array_equal(index_dict["Waveform"]["command"], [5, 6, 7]))

    def test_two_controls(self):
        """Test intersection behavior with two control devices"""
        # test a case that results in a null result
        shotnum = np.arange(1, 21, 1)
        sni_dict = {
            "Waveform": {"command": np.zeros(shotnum.shape, dtype=bool)},
            "6K Compumotor": {0: np.zeros(shotnum.shape, dtype=bool)},
        }
        index_dict = {
            "Waveform": {"command": np.array([])},
            "6K Compumotor": {0: np.array([5, 6, 7])},
        }
        sni_dict["6K Compumotor"][0][[6, 7, 8]] = True
        self.assertRaises(
            ValueError, do_shotnum_intersection, shotnum, sni_dict, index_dict
        )

        # test a working case
        shotnum = np.arange(1, 21, 1)
        shotnum_dict = {"Waveform": shotnum, "6K Compumotor": shotnum}
        sni_dict = {
            "Waveform": {"command": np.zeros(shotnum.shape, dtype=bool)},
            "6K Compumotor": {0: np.zeros(shotnum.shape, dtype=bool)},
        }
        index_dict = {
            "Waveform": {"command": np.array([5, 6])},
            "6K Compumotor": {0: np.array([5, 6, 7])},
        }
        sni_dict["Waveform"]["command"][[5, 6]] = True
        sni_dict["6K Compumotor"][0][[5, 6, 7]] = True
        shotnum, sni_dict, index_dict = do_shotnum_intersection(
            shotnum, sni_dict, index_dict
        )
        self.assertTrue(np.array_equal(shotnum, [6, 7]))
        for key in shotnum_dict:
            for state_key in sni_dict[key]:
                self.assertTrue(np.array_equal(sni_dict[key][state_key], [True] * 2))
                self.assertTrue(np.array_equal(index_dict[key][state_key], [5, 6]))


if __name__ == "__main__":
    ut.main()
