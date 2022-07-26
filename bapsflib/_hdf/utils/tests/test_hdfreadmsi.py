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

from bapsflib._hdf.utils.file import File
from bapsflib._hdf.utils.hdfreadmsi import HDFReadMSI
from bapsflib._hdf.utils.tests import TestBase
from bapsflib.utils.decorators import with_bf


class TestHDFReadMSI(TestBase):
    """Test Case for the HDFReadMSI class."""

    # What to test:
    #   1. Diagnostic aliases
    #   2. Input arguments
    #   3. Designed Failures

    def setUp(self):
        super().setUp()

    def tearDown(self):
        super().tearDown()

    @staticmethod
    def read(hdf_obj: File, name: str) -> HDFReadMSI:
        """Read MSI diagnostic data"""
        return HDFReadMSI(hdf_obj, name)

    @with_bf
    def test_raise_errors(self, _bf: File):
        """Test designed raise exceptions"""
        # 1.`hdf_file` not a lapd.File object
        # 2. `dname` not valid
        #    * not a string
        #    * not a mapped MSI diagnostic
        # 3. not all datasets have matching shot numbers for `dname`
        #    device
        #
        # -- `hdf_file` not a lapd.File object                      ----
        with self.assertRaises(TypeError):
            self.read(None, "")

        # -- `dname` not valid                                      ----
        # `dname` is not a string
        with self.assertRaises(TypeError):
            self.read(_bf, None)

        # `dname` not a mapped MSI diagnostic
        with self.assertRaises(ValueError):
            self.read(_bf, "Not Diagnostic")

        # -- Not all datasets for `dname` have matching             ----
        # -- shot numbers                                           ----
        # Using 'Interferometer array' as a test case
        self.f.add_module(
            "Interferometer array",
            mod_args={
                "n interferometers": 4,
            },
        )
        dset_path = (
            "/MSI/Interferometer array/Interferometer [1]/Interferometer summary list"
        )
        dset = self.f[dset_path]
        data = dset[:]
        data["Shot number"][1] += 1
        del self.f[dset_path]
        self.f.create_dataset(dset_path, data=data)
        _bf._map_file()  # re-map file
        with self.assertRaises(ValueError):
            self.read(_bf, "Interferometer array")

    @with_bf
    def test_read_simple(self, _bf: File):
        """
        Test reading data from a simple device. (i.e. a device with
        one sequence of data per shot number)
        """
        # Using 'Discharge' as a test case
        self.f.add_module("Discharge")
        _bf._map_file()  # re-map file
        _map = _bf.file_map.msi["Discharge"]
        self.assertDataObj(self.read(_bf, "Discharge"), _bf, _map)

    @with_bf
    def test_read_complex(self, _bf: File):
        """
        Test reading data from a complex device. (i.e. a device with
        more than one sequence of data per shot number)
        """
        # Using 'Interferometer array' as a test case
        self.f.add_module(
            "Interferometer array",
            mod_args={
                "n interferometers": 4,
            },
        )
        _bf._map_file()  # re-map file
        _map = _bf.file_map.msi["Interferometer array"]
        self.assertDataObj(self.read(_bf, "Interferometer array"), _bf, _map)

    def assertDataObj(self, _data: HDFReadMSI, _bf, _map):
        # data is a structured numpy array
        self.assertIsInstance(_data, np.ndarray)

        # look for expected fields
        # 'shotnum' and 'meta'
        self.assertTrue(all(x in _data.dtype.fields for x in ["shotnum", "meta"]))

        # check 'shape'
        self.assertEqual(_data.shape, _map.configs["shape"])

        # -- check 'shotnum'                                        ----
        self.assertEqual(_data["shotnum"].dtype.shape, ())
        self.assertTrue(np.issubdtype(_data["shotnum"].dtype, np.integer))

        # check equality of read arrays
        sn_config = _map.configs["shotnum"]
        for ii, path in enumerate(sn_config["dset paths"]):
            # determine field
            field = (
                sn_config["dset field"][0]
                if len(sn_config["dset field"]) == 1
                else sn_config["dset field"][ii]
            )

            # grab dataset
            dset = _bf.get(path)
            sn_arr = dset[field]

            # examine
            self.assertTrue(np.array_equal(sn_arr, _data["shotnum"]))

        # -- check 'meta'                                           ----
        # examine each expected 'meta' field
        for field, config in _map.configs["meta"].items():
            # skip 'shape'
            if field == "shape":
                continue

            # all expected fields are in the numpy array
            self.assertIn(field, _data["meta"].dtype.fields)

            # compare values
            for ii, path in enumerate(config["dset paths"]):
                # determine dset_field
                dset_field = (
                    config["dset field"][0]
                    if len(config["dset field"]) == 1
                    else config["dset field"][ii]
                )

                # grab dataset
                dset = _bf.get(path)

                # examine
                if len(config["dset paths"]) == 1:
                    self.assertTrue(
                        np.array_equal(dset[dset_field], _data["meta"][field])
                    )
                else:
                    self.assertTrue(
                        np.array_equal(dset[dset_field], _data["meta"][field][:, ii, ...])
                    )

        # -- check signal fields                                    ----
        # examine each expected 'signals' field
        for field, config in _map.configs["signals"].items():
            # all expected fields are in the numpy array
            self.assertIn(field, _data.dtype.fields)

            # compare values
            for ii, path in enumerate(config["dset paths"]):
                # grab dataset
                dset = _bf.get(path)

                # examine
                if len(config["dset paths"]) == 1:
                    self.assertTrue(np.array_equal(dset, _data[field]))
                else:
                    self.assertTrue(np.array_equal(dset, _data[field][:, ii, ...]))

        # check 'info' attribute                                    ----
        # check existence and type
        self.assertTrue(hasattr(_data, "info"))
        self.assertIsInstance(_data.info, dict)

        # examine each key
        infokeys = list(_map.configs.keys())
        infokeys.remove("shape")
        infokeys.remove("shotnum")
        infokeys.remove("signals")
        infokeys.remove("meta")
        infokeys = ["source file", "device name", "device group path"] + infokeys
        for key in infokeys:
            # existence
            self.assertIn(key, _data.info)

            # value
            if key == "source file":
                self.assertEqual(_data.info[key], os.path.abspath(_bf.filename))
            elif key == "device name":
                self.assertEqual(_data.info[key], _map.info["group name"])
            elif key == "device group path":
                self.assertEqual(_data.info[key], _map.info["group path"])
            else:
                self.assertEqual(_data.info[key], _map.configs[key])


if __name__ == "__main__":
    ut.main()
