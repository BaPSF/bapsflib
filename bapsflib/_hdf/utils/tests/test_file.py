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
import os
import unittest as ut

from unittest import mock

from bapsflib._hdf import HDFMap
from bapsflib._hdf.utils.file import File
from bapsflib._hdf.utils.hdfoverview import HDFOverview
from bapsflib._hdf.utils.hdfreadcontrols import HDFReadControls
from bapsflib._hdf.utils.hdfreaddata import HDFReadData
from bapsflib._hdf.utils.hdfreadmsi import HDFReadMSI
from bapsflib._hdf.utils.tests import TestBase
from bapsflib.utils.decorators import with_bf


class TestFile(TestBase):
    """Test case for :class:`~bapsflib._hdf.utils.file.File`."""

    def setUp(self):
        super().setUp()

    def tearDown(self):
        super().tearDown()

    @with_bf
    def test_file(self, _bf: File):
        # must by h5py.File instance
        self.assertIsInstance(_bf, h5py.File)

        # path attributes
        self.assertTrue(hasattr(_bf, "CONTROL_PATH"))
        self.assertTrue(hasattr(_bf, "DIGITIZER_PATH"))
        self.assertTrue(hasattr(_bf, "MSI_PATH"))
        self.assertEqual(_bf.CONTROL_PATH, "Raw data + config")
        self.assertEqual(_bf.DIGITIZER_PATH, "Raw data + config")
        self.assertEqual(_bf.MSI_PATH, "MSI")

        # `info` attributes`                                        ----
        self.assertTrue(hasattr(_bf, "_build_info"))
        self.assertTrue(hasattr(_bf, "info"))
        self.assertIsInstance(_bf.info, dict)
        self.assertIsInstance(type(_bf).info, property)
        self.assertEqual(_bf.info["file"], os.path.basename(_bf.filename))
        self.assertEqual(_bf.info["absolute file path"], os.path.abspath(_bf.filename))

        # mapping attributes                                        ----
        self.assertTrue(hasattr(_bf, "_map_file"))
        self.assertTrue(hasattr(_bf, "file_map"))
        self.assertTrue(hasattr(_bf, "controls"))
        self.assertTrue(hasattr(_bf, "digitizers"))
        self.assertTrue(hasattr(_bf, "msi"))

        # `_map_file` should call HDFMap
        with mock.patch(
            f"{File.__module__}.{HDFMap.__qualname__}", return_value="mapped"
        ) as mock_map:

            _bf._map_file()
            self.assertTrue(mock_map.called)
            self.assertEqual(_bf._file_map, "mapped")

        # restore map
        _bf._map_file()

        # `file_map`
        self.assertIsInstance(_bf.file_map, HDFMap)
        self.assertIsInstance(type(_bf).file_map, property)

        # individual mappings
        self.assertIsInstance(type(_bf).controls, property)
        self.assertIs(_bf.controls, _bf.file_map.controls)
        self.assertIsInstance(type(_bf).digitizers, property)
        self.assertIs(_bf.digitizers, _bf.file_map.digitizers)
        self.assertIsInstance(type(_bf).msi, property)
        self.assertIs(_bf.msi, _bf.file_map.msi)

        # `overview` attribute                                      ----
        self.assertTrue(hasattr(_bf, "overview"))
        self.assertIsInstance(type(_bf).overview, property)
        self.assertIsInstance(_bf.overview, HDFOverview)

        # read attributes                                           ----
        self.assertTrue(hasattr(_bf, "read_controls"))
        self.assertTrue(hasattr(_bf, "read_data"))
        self.assertTrue(hasattr(_bf, "read_msi"))

        # calling `read_controls`
        with mock.patch(
            f"{HDFReadControls.__module__}.{HDFReadControls.__qualname__}",
            return_value="read control",
        ) as mock_rc:
            extras = {
                "shotnum": 2,
                "intersection_set": True,
            }
            cdata = _bf.read_controls(["control"], **extras, silent=False)
            self.assertTrue(mock_rc.called)
            self.assertEqual(cdata, "read control")
            mock_rc.assert_called_once_with(_bf, ["control"], **extras)

        # calling `read_data`
        with mock.patch(
            f"{HDFReadData.__module__}.{HDFReadData.__qualname__}",
            return_value="read data",
        ) as mock_rd:
            extras = {
                "index": 1,
                "shotnum": 2,
                "digitizer": "digi",
                "adc": "SIS",
                "config_name": "config01",
                "keep_bits": True,
                "add_controls": ["control"],
                "intersection_set": True,
            }
            data = _bf.read_data(1, 2, **extras, silent=False)
            self.assertTrue(mock_rd.called)
            self.assertEqual(data, "read data")
            mock_rd.assert_called_once_with(_bf, 1, 2, **extras)

        # calling `read_msi`
        with mock.patch(
            f"{HDFReadMSI.__module__}.{HDFReadMSI.__qualname__}", return_value="read msi"
        ) as mock_rm:
            mdata = _bf.read_msi("Discharge", silent=False)
            self.assertTrue(mock_rm.called)
            self.assertEqual(mdata, "read msi")
            mock_rm.assert_called_once_with(_bf, "Discharge")

        # __init__ calling                                          ----
        # methods `_build_info` and `_map_file` should be called in
        # __init__
        with mock.patch.object(
            File, "_build_info", side_effect=_bf._build_info
        ) as mock_bi, mock.patch.object(
            File, "_map_file", side_effect=_bf._map_file
        ) as mock_mf:
            _bf2 = File(
                self.f.filename,
                control_path="Raw data + config",
                digitizer_path="Raw data + config",
                msi_path="MSI",
            )
            self.assertTrue(mock_mf.called)
            self.assertTrue(mock_bi.called)
            _bf2.close()

        # `mode` calling
        with mock.patch("h5py.File.__init__", wraps=h5py.File.__init__) as mock_file:
            for mode in ("r", "r+"):
                _bf2 = File(
                    self.f.filename,
                    mode=mode,
                    control_path="Raw data + config",
                    digitizer_path="Raw data + config",
                    msi_path="MSI",
                    silent=True,
                )
                self.assertTrue(mock_file.called)
                mock_file.assert_called_once_with(_bf2, self.f.filename, mode=mode)
                mock_file.reset_mock()
                _bf2.close()

        # raise ValueError if mode not in ('r', 'r+')
        with self.assertRaises(ValueError):
            _bf2 = File(self.f.filename, mode="w")
            _bf2.close()


if __name__ == "__main__":
    ut.main()
