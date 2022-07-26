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

from bapsflib._hdf.utils.hdfoverview import HDFOverview
from bapsflib.lapd._hdf.file import File
from bapsflib.lapd._hdf.lapdoverview import LaPDOverview
from bapsflib.lapd._hdf.tests import TestBase
from bapsflib.utils.decorators import with_lapdf


class TestLaPDOverview(TestBase):
    """
    Test case for :class:`~bapsflib.lapd._hdf.lapdoverview.LaPDOverview`
    """

    def setUp(self):
        super().setUp()

        # setup HDF5 file
        self.f.add_module("SIS 3301")  # digitizer
        self.f.add_module("Waveform")  # control
        self.f.add_module("Discharge")  # MSI diagnostic
        self.f.create_group("Raw data + config/Unknown")

    def tearDown(self):
        super().tearDown()

    @staticmethod
    def create_overview(file):
        return LaPDOverview(file)

    @with_lapdf
    def test_overview(self, _lapdf: File):
        _overview = self.create_overview(_lapdf)

        # LaPDOverview subclasses HDFOverview
        self.assertIsInstance(_overview, LaPDOverview)

        # override method `report_general`
        self.assertMethodOverride(HDFOverview, _overview, "report_general")

        # `report_general` prints to screen
        _lapdf.info["exp description"] = "This experiment\ndid something"
        _overview = self.create_overview(_lapdf)
        with mock.patch(
            "sys.stdout", new_callable=io.StringIO
        ) as mock_stdout, mock.patch.object(
            HDFOverview, "report_general", side_effect=print("hello")
        ) as mock_rg_super:
            _overview.report_general()
            self.assertNotEqual(mock_stdout.getvalue(), "")
            self.assertTrue(mock_rg_super.called)


if __name__ == "__main__":
    ut.main()
