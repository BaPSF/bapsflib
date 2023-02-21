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

from typing import Any, Dict, List, Tuple
from unittest import mock

from bapsflib._hdf.maps import ConType, HDFMap
from bapsflib._hdf.maps.controls.templates import HDFMapControlTemplate
from bapsflib._hdf.utils.file import File
from bapsflib._hdf.utils.hdfreadcontrols import HDFReadControls
from bapsflib._hdf.utils.tests import TestBase
from bapsflib.utils.decorators import with_bf


class TestHDFReadControl(TestBase):
    """Test Case for HDFReadControls class."""

    # Note:
    # - Key code segments of HDFReadControls are tested by:
    #   1. TestConditionControls
    #   2. TestConditionShotnum
    #   3. TestBuildShotnumDsetRelation
    #   4. TestDoShotnumIntersection
    # - TestBuildShotnumDsetRelation tests HDFReadControls's ability to
    #   properly identify the dataset indices corresponding to the
    #   desired shot numbers (it checks against an original dataset)
    # - TestDoIntersection tests HDFReadControls's ability to intersect
    #   all shot numbers between the datasets and shotnum
    # - Thus, testing here should focus on the construction and
    #   basic population of cdata and not so much ensuring the exact
    #   dset values are populated
    #
    # What to test:
    # 1. handling of hdf_file input
    # 2. output object format
    # 3. reading from one control dataset
    #    - for all cases ensure fields are properly transferred over
    #    - datasets w/ sequential and non-sequential shot numbers
    #    - intersection_set = True/False
    #      > shotnum is omitted, int, list, or slice
    #      > proper fill of "NaN" values
    # 4. reading from two control datasets
    #    - for all cases ensure fields are properly transferred over
    #    - datasets w/ sequential and non-sequential shot numbers
    #    - intersection_set = True/False
    #      > shotnum is omitted, int, list, or slice
    #      > proper fill of "NaN" values
    # 5. command list functionality
    #    - for command list datasets, commands are properly assigned
    #

    def setUp(self):
        super().setUp()

    def tearDown(self):
        super().tearDown()

    @with_bf
    def test_raise_errors(self, _bf: File):
        """Test handling of input argument `hdf_file`."""
        # Note:
        # - raised errors from conditioning `controls` is handled by
        #   condition_controls() and TestConditionControls
        # - raised errors from conditioning `shotnum` is handled by
        #   condition_shotnum() and TestConditionShotnum
        #
        # `hdf_fil` is NOT a bapsflib._hdf.utils.file.File
        self.assertRaises(TypeError, HDFReadControls, self.f, [])

        # HDF5 file object has no mapped control devices
        self.assertRaises(ValueError, HDFReadControls, _bf, [])

    @with_bf
    def test_misc_behavior(self, _bf: File):
        """Test miscellaneous behavior"""
        # setup HDF5 file
        self.f.add_module("Waveform")
        _bf._map_file()  # re-map file

        # 'assume_controls_conditioned' kwarg
        controls = [("Waveform", "config01")]
        sn = np.array([1, 2], dtype=np.uint32)
        control_plus = [
            (
                controls[0][0],
                controls[0][1],
                {"sn_requested": sn, "sn_correct": sn, "sn_valid": sn},
            )
        ]
        data = HDFReadControls(
            _bf, controls, shotnum=sn, assume_controls_conditioned=False
        )
        self.assertCDataObj(data, _bf, control_plus)

    @with_bf
    @mock.patch.object(HDFMap, "controls", new_callable=mock.PropertyMock)
    def test_missing_dataset_fields(self, _bf: File, mock_controls):
        """
        Test readout behavior when an expected/unexpected dataset
        field is absent."""
        # -- Define "Sample Control" in HDF5 file                   ----
        data = np.empty(
            10,
            dtype=[
                ("Shot number", np.uint32),
                ("x", np.float64),
                ("z", np.float64),
                ("i1", np.int32),
                ("i2", np.int32),
                ("u1", np.uint32),
                ("u2", np.uint32),
                ("c1", "S10"),
                ("c2", "S10"),
                ("field", np.float64),
            ],
        )
        data["Shot number"] = np.arange(1, 11, 1, dtype=np.uint32)
        data["x"] = np.arange(0.0, 10.0, 1.0, dtype=np.float64)
        data["z"] = np.arange(-2.25, 2.26, 0.5, dtype=np.float64)
        self.f.create_group("Raw data + config/Sample")
        self.f.create_dataset("Raw data + config/Sample/Dataset", data=data)
        _bf._map_file()  # re-map file

        # -- Define "Sample Control Mapping Class"                  ----
        class HDFMapSampleControl(HDFMapControlTemplate):
            def __init__(self, group):
                HDFMapControlTemplate.__init__(self, group)

                # define control type
                self._info["contype"] = ConType.motion

                # populate self.configs
                self._build_configs()

            def _build_configs(self):
                config_name = "config01"
                dset_name = self.construct_dataset_name()
                dset = self.group[dset_name]
                dset_paths = (dset.name,)
                self._configs[config_name] = {
                    "dset paths": dset_paths,
                    "shotnum": {
                        "dset paths": dset_paths,
                        "dset field": ("Shot number",),
                        "shape": (),
                        "dtype": np.uint32,
                    },
                    "state values": {
                        "xyz": {
                            "dset paths": dset_paths,
                            "dset field": ("x", "", "z"),
                            "shape": (3,),
                            "dtype": np.float64,
                        },
                        "index": {
                            "dset paths": dset_paths,
                            "dset field": ("i1", "i2", ""),
                            "shape": (3,),
                            "dtype": np.int32,
                        },
                        "uindex": {
                            "dset paths": dset_paths,
                            "dset field": ("u1", "u2", ""),
                            "shape": (3,),
                            "dtype": np.uint32,
                        },
                        "cindex": {
                            "dset paths": dset_paths,
                            "dset field": ("c1", "c2", ""),
                            "shape": (3,),
                            "dtype": np.dtype((np.bytes_, 10)),
                        },
                        "field": {
                            "dset paths": dset_paths,
                            "dset field": ("field",),
                            "shape": (),
                            "dtype": np.float64,
                        },
                    },
                }

            def construct_dataset_name(self, *args):
                return "Dataset"

        # -- Set Mocking                                            ----
        mock_controls.return_value = {
            "Sample": HDFMapSampleControl(self.f["Raw data + config/Sample"]),
        }

        # -- Run Tests                                              ----
        # -- expected non-existent dataset field --
        # - e.g. the dataset only has the 'x' and 'z' fields for the
        #   'xyz' numpy array field
        # - an expected non-existent field is added to the mapping
        #   `configs` like
        #
        #       configs[cname]['state values']['xyz']['dset field'] = \
        #           ('x', '', 'z')
        #
        sn = np.array([8, 9, 10, 11, 12, 13], dtype=np.uint32)
        sn_v = np.array([8, 9, 10], dtype=np.uint32)
        controls = [("Sample", "config01")]
        cdata = HDFReadControls(
            _bf, controls, shotnum=sn, assume_controls_conditioned=True
        )
        self.assertTrue(np.array_equal(cdata["shotnum"], sn_v))
        self.assertTrue(
            np.array_equal(cdata["xyz"][..., 1], np.zeros(3, dtype=np.float64))
        )
        self.assertTrue(
            np.array_equal(cdata["index"][..., 2], np.zeros(3, dtype=np.int32))
        )
        self.assertTrue(
            np.array_equal(cdata["uindex"][..., 2], np.zeros(3, dtype=np.uint32))
        )
        self.assertTrue(np.array_equal(cdata["cindex"][..., 2], np.zeros(3, dtype="S10")))

        # -- expected dataset field missing for a grouping of fields  --
        # -- that map to one numpy field                              --
        # - e.g. field 'x' is missing from the dataset but is needed
        #   for the 'xyz' numpy field
        #
        # remove fields from data
        fields = list(data.dtype.names)
        for field in ("x", "i1", "u1", "c1"):
            fields.remove(field)
        del self.f["Raw data + config/Sample/Dataset"]
        self.f.create_dataset("Raw data + config/Sample/Dataset", data=data[fields])

        # build control data array
        sn = np.array([8, 9, 10, 11, 12, 13], dtype=np.uint32)
        sn_v = np.array([8, 9, 10], dtype=np.uint32)
        controls = [("Sample", "config01")]
        with self.assertWarns(UserWarning):
            cdata = HDFReadControls(
                _bf, controls, shotnum=sn, assume_controls_conditioned=True
            )

            self.assertTrue(np.array_equal(cdata["shotnum"], sn_v))
            self.assertTrue(np.all(np.isnan(cdata["xyz"][..., 0])))
            self.assertTrue(
                np.array_equal(cdata["xyz"][..., 1], np.zeros(3, dtype=np.float64))
            )
            self.assertTrue(
                np.array_equal(
                    cdata["index"][..., 0], np.array([-99999] * 3, dtype=np.int32)
                )
            )
            self.assertTrue(
                np.array_equal(cdata["index"][..., 2], np.zeros(3, dtype=np.int32))
            )
            self.assertTrue(
                np.array_equal(cdata["uindex"][..., 0], np.zeros(3, dtype=np.uint32))
            )
            self.assertTrue(
                np.array_equal(cdata["uindex"][..., 2], np.zeros(3, dtype=np.uint32))
            )
            self.assertTrue(
                np.array_equal(cdata["cindex"][..., 0], np.zeros(3, dtype="S10"))
            )
            self.assertTrue(
                np.array_equal(cdata["cindex"][..., 2], np.zeros(3, dtype="S10"))
            )

        # -- expected dataset field is missing and is the only field  --
        # -- mapped to the numpy field                                --
        # remove fields from data
        fields = list(data.dtype.names)
        fields.remove("field")
        del self.f["Raw data + config/Sample/Dataset"]
        self.f.create_dataset("Raw data + config/Sample/Dataset", data=data[fields])

        # test
        sn = np.array([8, 9, 10, 11, 12, 13], dtype=np.uint32)
        controls = [("Sample", "config01")]
        with self.assertRaises(ValueError):
            cdata = HDFReadControls(
                _bf, controls, shotnum=sn, assume_controls_conditioned=True
            )

    @with_bf
    @mock.patch.object(HDFMap, "controls", new_callable=mock.PropertyMock)
    def test_nan_fill(self, _bf: File, mock_controls):
        """Test different NaN fills."""
        # -- Define "Sample Control" in HDF5 file                   ----
        data = np.empty(
            10,
            dtype=[
                ("Shot number", np.uint32),
                ("index", np.int32),
                ("bits", np.uint32),
                ("signal", np.float32),
                ("command", np.bytes_, 10),
                ("valid", bool),
            ],
        )
        data["Shot number"] = np.arange(1, 11, 1, dtype=np.uint32)
        data["index"] = np.arange(-11, -21, -1, dtype=np.int32)
        data["bits"] = np.arange(21, 31, 1, dtype=np.uint32)
        data["signal"] = np.arange(-5.0, 9.0, 1.5, dtype=np.float32)
        for ii in range(data.size):
            data["command"][ii] = f"VOLT {data['signal'][ii]:5.1f}"
        data["valid"][[1, 8]] = True
        self.f.create_group("Raw data + config/Sample")
        self.f.create_dataset("Raw data + config/Sample/Dataset", data=data)
        _bf._map_file()  # re-map file

        # -- Define "Sample Control Mapping Class"                  ----
        class HDFMapSampleControl(HDFMapControlTemplate):
            def __init__(self, group):
                HDFMapControlTemplate.__init__(self, group)

                # define control type
                self._info["contype"] = ConType.motion

                # populate self.configs
                self._build_configs()

            def _build_configs(self):
                config_name = "config01"
                dset_name = self.construct_dataset_name()
                dset = self.group[dset_name]
                dset_paths = (dset.name,)
                self._configs[config_name] = {
                    "dset paths": dset_paths,
                    "shotnum": {
                        "dset paths": dset_paths,
                        "dset field": ("Shot number",),
                        "shape": (),
                        "dtype": np.uint32,
                    },
                    "state values": {
                        "index": {
                            "dset paths": dset_paths,
                            "dset field": ("index",),
                            "shape": (),
                            "dtype": np.int32,
                        },
                        "bits": {
                            "dset paths": dset_paths,
                            "dset field": ("bits",),
                            "shape": (),
                            "dtype": np.uint32,
                        },
                        "signal": {
                            "dset paths": dset_paths,
                            "dset field": ("signal",),
                            "shape": (),
                            "dtype": np.float32,
                        },
                        "command": {
                            "dset paths": dset_paths,
                            "dset field": ("command",),
                            "shape": (),
                            "dtype": np.dtype((np.unicode_, 10)),
                        },
                        "valid": {
                            "dset paths": dset_paths,
                            "dset field": ("valid",),
                            "shape": (),
                            "dtype": bool,
                        },
                    },
                }

            def construct_dataset_name(self, *args):
                return "Dataset"

        # -- Set Mocking                                            ----
        mock_controls.return_value = {
            "Sample": HDFMapSampleControl(self.f["Raw data + config/Sample"]),
        }

        # -- Run Tests                                              ----
        with self.assertWarns(UserWarning):
            sn = np.array([8, 9, 10, 11, 12, 13], dtype=np.uint32)
            sn_v = np.array([8, 9, 10], dtype=np.uint32)
            controls = [("Sample", "config01")]
            control_plus = [
                (
                    controls[0][0],
                    controls[0][1],
                    {"sn_requested": sn, "sn_correct": sn, "sn_valid": sn_v},
                )
            ]
            data = HDFReadControls(
                _bf,
                controls,
                shotnum=sn,
                intersection_set=False,
                assume_controls_conditioned=True,
            )
            self.assertCDataObj(data, _bf, control_plus, intersection_set=False)

    @with_bf
    def test_single_control(self, _bf: File):
        """
        Testing HDF5 with one control device that saves data from
        ONE configuration into ONE dataset. (Simple Control)
        """
        # Test Outline:
        # 1. Dataset with sequential shot numbers
        #    a. intersection_set = True
        #       - shotnum = int, list, slice
        #    b. intersection_set = False
        #       - shotnum = int, list, slice
        #    c. shotnum omitted
        #       - intersection_set = True/False
        #         (should be no difference)
        # 2. Dataset with a jump in shot numbers
        #    a. intersection_set = True
        #       - shotnum = int, list, slice
        #    b. intersection_set = False
        #       - shotnum = int, list, slice
        #    c. shotnum omitted
        #       - intersection_set = True/False
        #
        # clean HDF5 file
        self.f.remove_all_modules()
        self.f.add_module(
            "6K Compumotor", {"n_configs": 1, "sn_size": 50, "n_motionlists": 1}
        )
        _bf._map_file()  # re-map file
        sixk_cspec = self.f.modules["6K Compumotor"].config_names[0]
        control = [("6K Compumotor", sixk_cspec)]
        control_plus = [
            (
                "6K Compumotor",
                sixk_cspec,
                {"sn_requested": None, "sn_correct": None, "sn_valid": None},
            ),
        ]  # type: List[Tuple[str, Any, Dict[str, Any]]]

        # ====== Dataset w/ Sequential Shot Numbers               ======
        # ------ intersection_set = True                          ------
        sn_list_requested = [1, [2], [10, 20, 30], [45, 110], slice(40, 61, 3)]
        sn_list_correct = [[1], [2], [10, 20, 30], [45], [40, 43, 46, 49]]
        sn_list_valid = sn_list_correct
        for sn_r, sn_c, sn_v in zip(sn_list_requested, sn_list_correct, sn_list_valid):
            # update control plus
            control_plus[0][2]["sn_requested"] = sn_r
            control_plus[0][2]["sn_correct"] = sn_c
            control_plus[0][2]["sn_valid"] = sn_v

            # grab requested control data
            cdata = HDFReadControls(_bf, control, shotnum=sn_r)

            # assert cdata format
            self.assertCDataObj(cdata, _bf, control_plus)

        # ====== Dataset w/ Sequential Shot Numbers               ======
        # ------ intersection_set = False                         ------
        sn_list_requested = [1, [2], [10, 20, 30], [45, 110], slice(40, 61, 3)]
        sn_list_correct = [
            [1],
            [2],
            [10, 20, 30],
            [45, 110],
            [40, 43, 46, 49, 52, 55, 58],
        ]
        sn_list_valid = [[1], [2], [10, 20, 30], [45], [40, 43, 46, 49]]
        for sn_r, sn_c, sn_v in zip(sn_list_requested, sn_list_correct, sn_list_valid):
            # update control plus
            control_plus[0][2]["sn_requested"] = sn_r
            control_plus[0][2]["sn_correct"] = sn_c
            control_plus[0][2]["sn_valid"] = sn_v

            # grab requested control data
            cdata = HDFReadControls(_bf, control, shotnum=sn_r, intersection_set=False)
            # assert cdata format
            self.assertCDataObj(cdata, _bf, control_plus, intersection_set=False)

        # ====== Dataset w/ Sequential Shot Numbers               ======
        # ------ shotnum omitted                                  ------
        # ------ intersection_set = True/False                    ------
        sn_c = np.arange(1, 51, 1)
        control_plus[0][2]["sn_requested"] = slice(None)
        control_plus[0][2]["sn_correct"] = sn_c
        control_plus[0][2]["sn_valid"] = sn_c

        # grab & test data for intersection_set=True
        cdata = HDFReadControls(_bf, control)
        self.assertCDataObj(cdata, _bf, control_plus)

        # grab & test data for intersection_set=False
        cdata = HDFReadControls(_bf, control, intersection_set=False)
        self.assertCDataObj(cdata, _bf, control_plus, intersection_set=False)

        # ====== Dataset w/ a Jump in Shot Numbers ======
        # create a jump in the dataset
        dset_name = self.f.modules["6K Compumotor"]._configs[sixk_cspec]["dset name"]
        dset = self.f.modules["6K Compumotor"][dset_name]
        sn_arr = dset["Shot number"]  # type: np.ndarray
        sn_arr[30::] = np.arange(41, 61, 1, dtype=sn_arr.dtype)
        dset["Shot number"] = sn_arr
        _bf._map_file()  # re-map file

        # ====== Dataset w/ a Jump in Shot Numbers                ======
        # ------ intersection_set = True                          ------
        sn_list_requested = [1, [2], [10, 20, 30], [22, 36, 110], slice(38, 75, 3)]
        sn_list_correct = [[1], [2], [10, 20, 30], [22], [41, 44, 47, 50, 53, 56, 59]]
        sn_list_valid = sn_list_correct
        for sn_r, sn_c, sn_v in zip(sn_list_requested, sn_list_correct, sn_list_valid):
            # update control plus
            control_plus[0][2]["sn_requested"] = sn_r
            control_plus[0][2]["sn_correct"] = sn_c
            control_plus[0][2]["sn_valid"] = sn_v

            # grab requested control data
            cdata = HDFReadControls(_bf, control, shotnum=sn_r)

            # assert cdata format
            self.assertCDataObj(cdata, _bf, control_plus)

        # ====== Dataset w/ a Jump in Shot Numbers                ======
        # ------ intersection_set = False                         ------
        sn_list_requested = [1, [2], [10, 20, 30], [22, 36, 110], slice(38, 75, 3)]
        sn_list_correct = [
            [1],
            [2],
            [10, 20, 30],
            [22, 36, 110],
            [38, 41, 44, 47, 50, 53, 56, 59, 62, 65, 68, 71, 74],
        ]
        sn_list_valid = [[1], [2], [10, 20, 30], [22], [41, 44, 47, 50, 53, 56, 59]]
        for sn_r, sn_c, sn_v in zip(sn_list_requested, sn_list_correct, sn_list_valid):
            # update control plus
            control_plus[0][2]["sn_requested"] = sn_r
            control_plus[0][2]["sn_correct"] = sn_c
            control_plus[0][2]["sn_valid"] = sn_v

            # grab requested control data
            cdata = HDFReadControls(_bf, control, shotnum=sn_r, intersection_set=False)

            # assert cdata format
            self.assertCDataObj(cdata, _bf, control_plus, intersection_set=False)

        # ====== Dataset w/ a Jump in Shot Numbers                ======
        # ------ shotnum omitted                                  ------
        # ------ intersection_set = True/False                    ------
        sn_c = sn_arr
        control_plus[0][2]["sn_requested"] = slice(None)
        control_plus[0][2]["sn_correct"] = sn_c
        control_plus[0][2]["sn_valid"] = sn_c

        # grab & test data for intersection_set=True
        cdata = HDFReadControls(_bf, control)
        self.assertCDataObj(cdata, _bf, control_plus)

        # grab & test data for intersection_set=False
        sn_c = np.arange(1, 61, 1)
        control_plus[0][2]["sn_correct"] = sn_c
        cdata = HDFReadControls(_bf, control, intersection_set=False)
        self.assertCDataObj(cdata, _bf, control_plus, intersection_set=False)

    @with_bf
    def test_two_controls(self, _bf: File):
        """
        Testing HDF5 with two control devices.  Each control is setup
        with one configuration each.
        """
        # Test Outline:
        # 1. Both Datasets have matching sequential shot numbers
        #    a. intersection_set = True
        #       - shotnum = int, list, slice
        #    b. intersection_set = False
        #       - shotnum = int, list, slice
        #    c. shotnum omitted
        #       - intersection_set = True/False
        #         (should be no difference)
        # 2. Both Datasets have jumps in shot numbers
        #    a. intersection_set = True
        #       - shotnum = int, list, slice
        #    b. intersection_set = False
        #       - shotnum = int, list, slice
        #    c. shotnum omitted
        #       - intersection_set = True/False
        #
        # clean HDF5 file
        self.f.remove_all_modules()
        self.f.add_module(
            "6K Compumotor", {"n_configs": 1, "sn_size": 50, "n_motionlists": 1}
        )
        self.f.add_module("Waveform", {"n_configs": 1, "sn_size": 50})
        _bf._map_file()  # re-map file
        sixk_cspec = self.f.modules["6K Compumotor"].config_names[0]
        control = [("Waveform", "config01"), ("6K Compumotor", sixk_cspec)]
        control_plus = [
            (
                "Waveform",
                "config01",
                {"sn_requested": None, "sn_correct": None, "sn_valid": None},
            ),
            (
                "6K Compumotor",
                sixk_cspec,
                {"sn_requested": None, "sn_correct": None, "sn_valid": None},
            ),
        ]  # type: List[Tuple[str, Any, Dict[str, Any]]]

        # ==== Both Datasets Have Matching Sequential Shot Numbers ====
        # ---- intersection_set = True                             ----
        sn_list_requested = [1, [2], [10, 20, 30], [45, 110], slice(40, 61, 3)]
        sn_list_correct = [[1], [2], [10, 20, 30], [45], [40, 43, 46, 49]]
        sn_list_waveform = sn_list_correct
        sn_list_sixk = sn_list_correct
        for sn_r, sn_c, sn_w, sn_sk in zip(
            sn_list_requested, sn_list_correct, sn_list_waveform, sn_list_sixk
        ):
            # update control plus
            # 0 = Waveform
            # 1 = 6K Compumotor
            #
            control_plus[0][2]["sn_requested"] = sn_r
            control_plus[0][2]["sn_correct"] = sn_c
            control_plus[0][2]["sn_valid"] = sn_w
            control_plus[1][2]["sn_requested"] = sn_r
            control_plus[1][2]["sn_correct"] = sn_c
            control_plus[1][2]["sn_valid"] = sn_sk

            # grab requested control data
            cdata = HDFReadControls(_bf, control, shotnum=sn_r)

            # assert cdata format
            self.assertCDataObj(cdata, _bf, control_plus)

        # ==== Both Datasets Have Matching Sequential Shot Numbers ====
        # ---- intersection_set = False                            ----
        sn_list_requested = [1, [2], [10, 20, 30], [45, 110], slice(40, 61, 3)]
        sn_list_correct = [
            [1],
            [2],
            [10, 20, 30],
            [45, 110],
            [40, 43, 46, 49, 52, 55, 58],
        ]
        sn_list_waveform = [[1], [2], [10, 20, 30], [45], [40, 43, 46, 49]]
        sn_list_sixk = sn_list_waveform
        for sn_r, sn_c, sn_w, sn_sk in zip(
            sn_list_requested, sn_list_correct, sn_list_waveform, sn_list_sixk
        ):
            # update control plus
            # 0 = Waveform
            # 1 = 6K Compumotor
            #
            control_plus[0][2]["sn_requested"] = sn_r
            control_plus[0][2]["sn_correct"] = sn_c
            control_plus[0][2]["sn_valid"] = sn_w
            control_plus[1][2]["sn_requested"] = sn_r
            control_plus[1][2]["sn_correct"] = sn_c
            control_plus[1][2]["sn_valid"] = sn_sk

            # grab requested control data
            cdata = HDFReadControls(_bf, control, shotnum=sn_r, intersection_set=False)

            # assert cdata format
            self.assertCDataObj(cdata, _bf, control_plus, intersection_set=False)

        # ==== Both Datasets Have Matching Sequential Shot Numbers ====
        # ---- shotnum omitted                                     ----
        # ---- intersection_set = True/False                       ----
        # update control plus
        # 0 = Waveform
        # 1 = 6K Compumotor
        #
        sn_c = np.arange(1, 51, 1)
        control_plus[0][2]["sn_requested"] = slice(None)
        control_plus[0][2]["sn_correct"] = sn_c
        control_plus[0][2]["sn_valid"] = sn_c
        control_plus[1][2]["sn_requested"] = slice(None)
        control_plus[1][2]["sn_correct"] = sn_c
        control_plus[1][2]["sn_valid"] = sn_c

        # grab & test data for intersection_set=True
        cdata = HDFReadControls(_bf, control)
        self.assertCDataObj(cdata, _bf, control_plus)

        # grab & test data for intersection_set=False
        cdata = HDFReadControls(_bf, control, intersection_set=False)
        self.assertCDataObj(cdata, _bf, control_plus, intersection_set=False)

        # ====      Both Datasets Have Jumps in Shot Numbers      ====
        # ---- Waveform has a jump of 10 at sn = 20               ----
        # ---- 6K Compumotor has a jump of 8 at sn = 30           ----
        #
        # Place sn jump in 'Waveform'
        dset_name = self.f.modules["Waveform"]._configs["config01"]["dset name"]
        dset = self.f.modules["Waveform"][dset_name]
        sn_arr = dset["Shot number"]  # type: np.ndarray
        sn_arr[20::] = np.arange(31, 61, 1, dtype=sn_arr.dtype)
        dset["Shot number"] = sn_arr
        sn_wave = sn_arr

        # Place sn jump in '6K Compumotor'
        dset_name = self.f.modules["6K Compumotor"]._configs[sixk_cspec]["dset name"]
        dset = self.f.modules["6K Compumotor"][dset_name]
        sn_arr = dset["Shot number"]  # type: np.ndarray
        sn_arr[30::] = np.arange(38, 58, 1, dtype=sn_arr.dtype)
        dset["Shot number"] = sn_arr
        sn_sixk = sn_arr
        _bf._map_file()  # re-map file

        # ====      Both Datasets Have Jumps in Shot Numbers      ====
        # ---- intersection_set = True                            ----
        sn_list_requested = [1, [2], [10, 20, 30], [22, 45, 110], slice(35, 50, 3)]
        sn_list_correct = [[1], [2], [10, 20], [45], [38, 41, 44, 47]]
        sn_list_waveform = sn_list_correct
        sn_list_sixk = sn_list_correct
        for sn_r, sn_c, sn_w, sn_sk in zip(
            sn_list_requested, sn_list_correct, sn_list_waveform, sn_list_sixk
        ):
            # update control plus
            # 0 = Waveform
            # 1 = 6K Compumotor
            #
            control_plus[0][2]["sn_requested"] = sn_r
            control_plus[0][2]["sn_correct"] = sn_c
            control_plus[0][2]["sn_valid"] = sn_w
            control_plus[1][2]["sn_requested"] = sn_r
            control_plus[1][2]["sn_correct"] = sn_c
            control_plus[1][2]["sn_valid"] = sn_sk

            # grab requested control data
            cdata = HDFReadControls(_bf, control, shotnum=sn_r)

            # assert cdata format
            self.assertCDataObj(cdata, _bf, control_plus)

        # ====      Both Datasets Have Jumps in Shot Numbers      ====
        # ---- intersection_set = False                           ----
        sn_list_requested = [1, [2], [10, 20, 30], [22, 45, 110], slice(35, 50, 3)]
        sn_list_correct = [[1], [2], [10, 20, 30], [22, 45, 110], [35, 38, 41, 44, 47]]
        sn_list_waveform = [[1], [2], [10, 20], [45], [35, 38, 41, 44, 47]]
        sn_list_sixk = [[1], [2], [10, 20, 30], [22, 45], [38, 41, 44, 47]]
        for sn_r, sn_c, sn_w, sn_sk in zip(
            sn_list_requested, sn_list_correct, sn_list_waveform, sn_list_sixk
        ):
            # update control plus
            # 0 = Waveform
            # 1 = 6K Compumotor
            #
            control_plus[0][2]["sn_requested"] = sn_r
            control_plus[0][2]["sn_correct"] = sn_c
            control_plus[0][2]["sn_valid"] = sn_w
            control_plus[1][2]["sn_requested"] = sn_r
            control_plus[1][2]["sn_correct"] = sn_c
            control_plus[1][2]["sn_valid"] = sn_sk

            # grab requested control data
            cdata = HDFReadControls(_bf, control, shotnum=sn_r, intersection_set=False)

            # assert cdata format
            self.assertCDataObj(cdata, _bf, control_plus, intersection_set=False)

        # ====      Both Datasets Have Jumps in Shot Numbers      ====
        # ---- shotnum omitted                                     ----
        # ---- intersection_set = True/False                       ----
        # update control plus
        # 0 = Waveform
        # 1 = 6K Compumotor
        #
        sn_c = np.intersect1d(sn_wave, sn_sixk)  # type: np.ndarray
        control_plus[0][2]["sn_requested"] = slice(None)
        control_plus[0][2]["sn_correct"] = sn_c
        control_plus[0][2]["sn_valid"] = sn_c
        control_plus[1][2]["sn_requested"] = slice(None)
        control_plus[1][2]["sn_correct"] = sn_c
        control_plus[1][2]["sn_valid"] = sn_c

        # grab & test data for intersection_set=True
        cdata = HDFReadControls(_bf, control)
        self.assertCDataObj(cdata, _bf, control_plus)

        # grab & test data for intersection_set=False
        sn_c = np.arange(1, 61, 1)
        control_plus[0][2]["sn_correct"] = sn_c
        control_plus[0][2]["sn_valid"] = np.intersect1d(sn_c, sn_wave)  # type: np.ndarray
        control_plus[1][2]["sn_correct"] = sn_c
        control_plus[1][2]["sn_valid"] = np.intersect1d(sn_c, sn_sixk)  # type: np.ndarray

        cdata = HDFReadControls(_bf, control, intersection_set=False)
        self.assertCDataObj(cdata, _bf, control_plus, intersection_set=False)

    def assertCDataObj(
        self,
        cdata: HDFReadControls,
        _bf: File,
        control_plus: List[Tuple[str, Any, Dict[str, Any]]],
        intersection_set=True,
    ):
        """Assertion for detailed format of returned data object."""
        # cdata            - returned data object of HDFReadControls()
        # control_plus     - control name, control configuration, and
        #                    expected shot numbers ('sn_valid')
        # intersection_set - whether cdata is generated w/
        #                    intersection_set=True (or False)
        #
        # data is a structured numpy array
        self.assertIsInstance(cdata, np.ndarray)

        # -- check 'info' attribute                                 ----
        # check existence and type
        self.assertTrue(hasattr(cdata, "info"))
        self.assertIsInstance(cdata.info, dict)

        # examine HDFReadControls defined keys
        self.assertIn("source file", cdata.info)
        self.assertIn("controls", cdata.info)
        self.assertIn("probe name", cdata.info)
        self.assertIn("port", cdata.info)

        # examine values of HDFReadControls defined keys
        self.assertEqual(cdata.info["source file"], os.path.abspath(_bf.filename))
        self.assertIsInstance(cdata.info["controls"], dict)
        self.assertIsInstance(cdata.info["port"], tuple)
        self.assertEqual(len(cdata.info["port"]), 2)

        # examine control specific meta-info items
        for control in control_plus:
            # get control device vars
            device = control[0]
            config_name = control[1]
            _map = _bf.file_map.controls[device]
            config = _map.configs[config_name]

            # check device inclusion
            self.assertIn(device, cdata.info["controls"])
            _sub_info = cdata.info["controls"][device]

            # gather all control meta-info keys
            infokeys = list(config.keys())
            infokeys.remove("dset paths")
            infokeys.remove("shotnum")
            infokeys.remove("state values")
            infokeys = [
                "device group path",
                "device dataset path",
                "contype",
                "configuration name",
            ] + infokeys

            # check all meta-info keys
            for key in infokeys:
                # existence
                self.assertIn(key, _sub_info)

                # value
                if key == "device group path":
                    self.assertEqual(_sub_info[key], _map.info["group path"])
                elif key == "device dataset path":
                    self.assertEqual(_sub_info[key], config["dset paths"][0])
                elif key == "contype":
                    self.assertEqual(_sub_info[key], _map.contype)
                elif key == "configuration name":
                    self.assertEqual(_sub_info[key], config_name)
                else:
                    self.assertRecursiveEqual(_sub_info[key], config[key])

        # -- check obj array                                        ----
        # check shot numbers are correct
        sn_correct = control_plus[0][2]["sn_correct"]
        self.assertTrue(np.array_equal(cdata["shotnum"], sn_correct))

        # perform assertions based on control
        for control in control_plus:
            # extract necessary content
            device = control[0]
            config = control[1]
            # sn_r = control[2]['sn_requested']
            # sn_c = control[2]['sn_correct']
            sn_v = control[2]["sn_valid"]

            # retrieve control mapping
            cmap = _bf.file_map.controls[device]

            # gather fields that should be in cdata for this control
            # device
            fields = list(cmap.configs[config]["state values"])

            # check that all fields are in cdata
            for field in fields:
                self.assertIn(field, cdata.dtype.fields)

            # Check proper fill of "NaN" values
            #
            sni = np.isin(cdata["shotnum"], sn_v)
            sni_not = np.logical_not(sni)
            for field in fields:
                if field == "shotnum":
                    continue

                # dtype for field
                dtype = cdata.dtype[field].base

                # assert "NaN" fills
                if np.issubdtype(dtype, np.signedinteger):
                    cd_nan = np.where(cdata[field] == -99999, True, False)
                elif np.issubdtype(dtype, np.unsignedinteger):
                    cd_nan = np.where(cdata[field] == 0, True, False)
                elif np.issubdtype(dtype, np.floating):
                    cd_nan = np.isnan(cdata[field])
                elif np.issubdtype(dtype, np.flexible):
                    cd_nan = np.where(cdata[field] == "", True, False)
                else:
                    cd_nan = None

                if cd_nan is None:
                    # no NaN Fill was performed
                    pass
                elif intersection_set:
                    # there should be NO NaN fills
                    # 1. cd_nan should be False for all entries
                    # 2. sni should be True for all entries
                    self.assertTrue(np.all(np.logical_not(cd_nan)))
                    self.assertTrue(np.all(sni))
                else:
                    # there is a possibility for NaN fill
                    # 1. cd_nan should be False for all sni entries
                    # 2. cd_nan should be True for all sni_not entries
                    self.assertTrue(np.all(np.logical_not(cd_nan[sni])))
                    self.assertTrue(np.all(cd_nan[sni_not]))

    def assertRecursiveEqual(self, item1, item2):
        """
        Recursively check equality of a dictionary with array items.
        """
        try:
            self.assertEqual(item1, item2)
        except ValueError:
            if isinstance(item1, np.ndarray) and isinstance(item2, np.ndarray):
                self.assertTrue(np.array_equal(item1, item2))
            elif isinstance(item1, dict) and isinstance(item2, dict):
                for key, val in item1.items():
                    self.assertIn(key, item2)
                    self.assertRecursiveEqual(val, item2[key])
            else:
                self.fail()


if __name__ == "__main__":
    ut.main()
