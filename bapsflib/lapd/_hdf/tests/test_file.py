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
import io
import unittest as ut

from unittest import mock

import bapsflib

from bapsflib._hdf.maps.core import HDFMap
from bapsflib.lapd._hdf.file import File
from bapsflib.lapd._hdf.lapdmap import LaPDMap
from bapsflib.lapd._hdf.lapdoverview import LaPDOverview
from bapsflib.lapd._hdf.tests import BaseFile, TestBase
from bapsflib.utils.decorators import with_bf, with_lapdf


class TestLaPDFile(TestBase):
    """
    Test case for :class:`~bapsflib.lapd._hdf.file.File`
    """

    def setUp(self):
        super().setUp()

    def tearDown(self):
        super().tearDown()

    @with_bf
    @with_lapdf
    def test_file(self, _bf: BaseFile, _lapdf: File):
        # must subclass `bapsflib._hdf.utils.file.File`
        self.assertIsInstance(_lapdf, bapsflib._hdf.utils.file.File)

        # path attributes
        self.assertEqual(_lapdf.CONTROL_PATH, "Raw data + config")
        self.assertEqual(_lapdf.DIGITIZER_PATH, "Raw data + config")
        self.assertEqual(_lapdf.MSI_PATH, "MSI")

        # examine file mapping attributes                           ----
        # should override `_map_file` of subclass
        self.assertMethodOverride(bapsflib._hdf.utils.file.File, _lapdf, "_map_file")

        # `_map_file` should call LaPDMap
        with mock.patch(
            f"{File.__module__}.{LaPDMap.__qualname__}", return_value="mapped"
        ) as mock_map:

            _lapdf._map_file()
            self.assertTrue(mock_map.called)
            self.assertEqual(_lapdf._file_map, "mapped")

        # restore map
        _lapdf._map_file()

        # `file_map`
        self.assertIsInstance(_lapdf.file_map, HDFMap)
        self.assertIsInstance(_lapdf.file_map, LaPDMap)
        self.assertIsInstance(type(_lapdf).file_map, property)

        # examine `_build_info`                                     ----
        # should override `_build_info` of subclass
        self.assertMethodOverride(bapsflib._hdf.utils.file.File, _lapdf, "_build_info")

        # subclass `_build_info` in appended
        with mock.patch.object(
            bapsflib._hdf.utils.file.File, "_build_info", side_effect=_bf._build_info
        ) as mock_bi_super:
            _lapdf._build_info()
            self.assertTrue(mock_bi_super.called)

            # 'lapd version' should now be in the `info` dict
            self.assertEqual(_lapdf.info["lapd version"], _lapdf.file_map.lapd_version)

            # run info should now be in the `info` dict
            for key, val in _lapdf.file_map.run_info.items():
                self.assertEqual(_lapdf.info[key], val)

            # exp info should now be in the `info` dict
            for key, val in _lapdf.file_map.exp_info.items():
                self.assertEqual(_lapdf.info[key], val)

        # examine `overview` method                                 ----
        self.assertMethodOverride(bapsflib._hdf.utils.file.File, _lapdf, "overview")
        self.assertIsInstance(type(_lapdf).overview, property)
        self.assertIsInstance(_lapdf.overview, LaPDOverview)

        # examine `run_description` method                          ----
        self.assertTrue(hasattr(_lapdf, "run_description"))

        _lapdf.info["run description"] = "This experiment\nhad a run"
        with mock.patch(
            "sys.stdout", new_callable=io.StringIO
        ) as mock_stdout, mock.patch.object(
            File, "info", new_callable=mock.PropertyMock, return_value=_lapdf.info
        ) as mock_info:
            _lapdf.run_description()
            self.assertNotEqual(mock_stdout.getvalue(), "")
            self.assertTrue(mock_info.called)


if __name__ == "__main__":
    ut.main()
