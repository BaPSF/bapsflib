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
import os
import unittest as ut

from unittest import mock

from bapsflib._hdf.maps import HDFMap
from bapsflib._hdf.utils.file import File
from bapsflib._hdf.utils.hdfoverview import HDFOverview
from bapsflib._hdf.utils.tests import TestBase
from bapsflib.utils.decorators import with_bf


class TestHDFOverview(TestBase):
    """
    Test case for
    :class:`~bapsflib._hdf.utils.hdfoverview.HDFOverview`.
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
        return HDFOverview(file)

    def test_not_file_obj(self):
        """Raise error if input is not bapsflib._hdf.utils.file.File"""
        with self.assertRaises(ValueError):
            self.create_overview(None)

    @with_bf
    def test_overview_basics(self, _bf: File):
        _overview = self.create_overview(_bf)

        # -- attribute existence                                    ----
        self.assertTrue(hasattr(_overview, "control_discovery"))
        self.assertTrue(hasattr(_overview, "digitizer_discovery"))
        self.assertTrue(hasattr(_overview, "msi_discovery"))
        self.assertTrue(hasattr(_overview, "print"))
        self.assertTrue(hasattr(_overview, "report_control_configs"))
        self.assertTrue(hasattr(_overview, "report_controls"))
        self.assertTrue(hasattr(_overview, "report_details"))
        self.assertTrue(hasattr(_overview, "report_digitizer_configs"))
        self.assertTrue(hasattr(_overview, "report_digitizers"))
        self.assertTrue(hasattr(_overview, "report_discovery"))
        self.assertTrue(hasattr(_overview, "report_general"))
        self.assertTrue(hasattr(_overview, "report_msi"))
        self.assertTrue(hasattr(_overview, "report_msi_configs"))
        self.assertTrue(hasattr(_overview, "save"))
        self.assertTrue(hasattr(_overview, "unknowns_discovery"))

    @with_bf
    @mock.patch("sys.stdout", new_callable=io.StringIO)
    def test_discoveries(self, _bf: File, mock_stdout):
        self.f.add_module("SIS crate")
        _bf._map_file()  # re-map file
        _overview = self.create_overview(_bf)

        # HDFOverview.control_discovery()
        with mock.patch.object(
            HDFMap,
            "controls",
            new_callable=mock.PropertyMock,
            return_value=_bf.file_map.controls,
        ) as mock_dmap:
            _overview.control_discovery()
            self.assertNotEqual(mock_stdout.getvalue(), "")
            self.assertTrue(mock_dmap.called)

        # "flush" StringIO
        mock_stdout.truncate(0)
        mock_stdout.seek(0)
        self.assertEqual(mock_stdout.getvalue(), "")

        # HDFOverview.digitizer_discovery()
        with mock.patch.object(
            HDFMap,
            "digitizers",
            new_callable=mock.PropertyMock,
            return_value=_bf.file_map.digitizers,
        ) as mock_dmap:
            _overview.digitizer_discovery()
            self.assertNotEqual(mock_stdout.getvalue(), "")
            self.assertTrue(mock_dmap.called)

        # "flush" StringIO
        mock_stdout.truncate(0)
        mock_stdout.seek(0)
        self.assertEqual(mock_stdout.getvalue(), "")

        # HDFOverview.msi_discovery()
        with mock.patch.object(
            HDFMap, "msi", new_callable=mock.PropertyMock, return_value=_bf.file_map.msi
        ) as mock_dmap:
            _overview.msi_discovery()
            self.assertNotEqual(mock_stdout.getvalue(), "")
            self.assertTrue(mock_dmap.called)

        # "flush" StringIO
        mock_stdout.truncate(0)
        mock_stdout.seek(0)
        self.assertEqual(mock_stdout.getvalue(), "")

        # HDFOverview.unknowns_discovery()
        with mock.patch.object(
            HDFMap,
            "unknowns",
            new_callable=mock.PropertyMock,
            return_value=_bf.file_map.unknowns,
        ) as mock_unknowns:
            _overview.unknowns_discovery()
            self.assertNotEqual(mock_stdout.getvalue(), "")
            self.assertTrue(mock_unknowns.called)

        # "flush" StringIO
        mock_stdout.truncate(0)
        mock_stdout.seek(0)
        self.assertEqual(mock_stdout.getvalue(), "")

        # HDFOverview.report_discovery()
        with mock.patch.multiple(
            HDFOverview,
            control_discovery=mock.DEFAULT,
            digitizer_discovery=mock.DEFAULT,
            msi_discovery=mock.DEFAULT,
            unknowns_discovery=mock.DEFAULT,
        ) as mock_values:
            mock_values["control_discovery"].side_effect = _overview.control_discovery()
            mock_values["digitizer_discovery"].side_effect = (
                _overview.digitizer_discovery()
            )
            mock_values["msi_discovery"].side_effect = _overview.msi_discovery()
            mock_values["unknowns_discovery"].side_effect = _overview.unknowns_discovery()

            _overview.report_discovery()
            self.assertNotEqual(mock_stdout.getvalue(), "")
            self.assertTrue(mock_values["control_discovery"].called)
            self.assertTrue(mock_values["digitizer_discovery"].called)
            self.assertTrue(mock_values["msi_discovery"].called)
            self.assertTrue(mock_values["unknowns_discovery"].called)

        # "flush" StringIO
        mock_stdout.truncate(0)
        mock_stdout.seek(0)
        self.assertEqual(mock_stdout.getvalue(), "")

    @with_bf
    @mock.patch("sys.stdout", new_callable=io.StringIO)
    def test_report_controls(self, _bf: File, mock_stdout):
        _overview = self.create_overview(_bf)

        # HDFOverview.report_control_configs                        ----
        control = _bf.controls["Waveform"]

        # control has no configurations
        with mock.patch.object(
            control.__class__, "configs", new_callable=mock.PropertyMock, return_value={}
        ) as mock_configs:
            _overview.report_control_configs(control)
            self.assertNotEqual(mock_stdout.getvalue(), "")
            self.assertTrue(mock_configs.called)

        # "flush" StringIO
        mock_stdout.truncate(0)
        mock_stdout.seek(0)
        self.assertEqual(mock_stdout.getvalue(), "")

        # control HAS configurations
        configs = control.configs.copy()
        mock_values = {}
        with mock.patch.object(
            control.__class__,
            "configs",
            new_callable=mock.PropertyMock,
            return_value=configs,
        ) as mock_values["configs"]:
            _overview.report_control_configs(control)
            self.assertNotEqual(mock_stdout.getvalue(), "")
            self.assertTrue(mock_values["configs"].called)

        # "flush" StringIO
        mock_stdout.truncate(0)
        mock_stdout.seek(0)
        self.assertEqual(mock_stdout.getvalue(), "")

        # HDFOverview.report_controls                               ----
        with mock.patch.object(
            HDFMap,
            "controls",
            new_callable=mock.PropertyMock,
            return_value=_bf.file_map.controls,
        ) as mock_dmap, mock.patch.object(
            HDFOverview,
            "report_control_configs",
            side_effect=_overview.report_control_configs,
        ) as mock_rcc:
            # specify an existing control
            _overview.report_controls("Waveform")
            self.assertNotEqual(mock_stdout.getvalue(), "")
            self.assertTrue(mock_dmap.called)
            self.assertTrue(mock_rcc.called)
            mock_dmap.reset_mock()
            mock_rcc.reset_mock()

            # "flush" StringIO
            mock_stdout.truncate(0)
            mock_stdout.seek(0)
            self.assertEqual(mock_stdout.getvalue(), "")

            # report all (aka specified control not in map dict)
            _overview.report_controls()
            self.assertNotEqual(mock_stdout.getvalue(), "")
            self.assertTrue(mock_dmap.called)
            self.assertTrue(mock_rcc.called)
            mock_dmap.reset_mock()
            mock_rcc.reset_mock()

            # "flush" StringIO
            mock_stdout.truncate(0)
            mock_stdout.seek(0)
            self.assertEqual(mock_stdout.getvalue(), "")

    @with_bf
    @mock.patch("sys.stdout", new_callable=io.StringIO)
    def test_report_details(self, _bf: File, mock_stdout):
        _overview = self.create_overview(_bf)

        with mock.patch.multiple(
            _overview.__class__,
            report_controls=mock.DEFAULT,
            report_digitizers=mock.DEFAULT,
            report_msi=mock.DEFAULT,
        ) as mock_values:
            _overview.report_details()
            self.assertNotEqual(mock_stdout.getvalue(), "")
            self.assertTrue(mock_values["report_digitizers"].called)
            self.assertTrue(mock_values["report_controls"].called)
            self.assertTrue(mock_values["report_msi"].called)

    @with_bf
    @mock.patch("sys.stdout", new_callable=io.StringIO)
    def test_report_digitizers(self, _bf: File, mock_stdout):
        self.f.add_module("SIS crate")
        _bf._map_file()  # re-map file
        _overview = self.create_overview(_bf)

        # HDFOverview.report_digitizer_configs                      ----
        digi = _bf.digitizers["SIS 3301"]

        # digitizer has no configurations
        with mock.patch.object(
            digi.__class__, "configs", new_callable=mock.PropertyMock, return_value={}
        ) as mock_configs:

            _overview.report_digitizer_configs(digi)
            self.assertNotEqual(mock_stdout.getvalue(), "")
            self.assertTrue(mock_configs.called)

        # "flush" StringIO
        mock_stdout.truncate(0)
        mock_stdout.seek(0)
        self.assertEqual(mock_stdout.getvalue(), "")

        # digitizer HAS configurations
        configs = digi.configs.copy()
        active = digi.active_configs.copy()
        mock_values = {}
        with mock.patch.object(
            digi.__class__,
            "configs",
            new_callable=mock.PropertyMock,
            return_value=configs,
        ) as mock_values["configs"], mock.patch.object(
            digi.__class__,
            "active_configs",
            new_callable=mock.PropertyMock,
            return_value=active,
        ) as mock_values[
            "active_configs"
        ]:

            _overview.report_digitizer_configs(digi)
            self.assertNotEqual(mock_stdout.getvalue(), "")
            self.assertTrue(mock_values["configs"].called)
            self.assertTrue(mock_values["active_configs"].called)

        # "flush" StringIO
        mock_stdout.truncate(0)
        mock_stdout.seek(0)
        self.assertEqual(mock_stdout.getvalue(), "")

        # HDFOverview.report_digitizers                             ----
        with mock.patch.object(
            HDFMap,
            "digitizers",
            new_callable=mock.PropertyMock,
            return_value=_bf.file_map.digitizers,
        ) as mock_dmap, mock.patch.object(
            HDFOverview,
            "report_digitizer_configs",
            side_effect=_overview.report_digitizer_configs,
        ) as mock_rdc:

            # specify an existing digitizer
            _overview.report_digitizers("SIS 3301")
            self.assertNotEqual(mock_stdout.getvalue(), "")
            self.assertTrue(mock_dmap.called)
            self.assertTrue(mock_rdc.called)
            mock_dmap.reset_mock()
            mock_rdc.reset_mock()

            # "flush" StringIO
            mock_stdout.truncate(0)
            mock_stdout.seek(0)
            self.assertEqual(mock_stdout.getvalue(), "")

            # report all (aka specified digitizer not in map dict)
            _overview.report_digitizers()
            self.assertNotEqual(mock_stdout.getvalue(), "")
            self.assertTrue(mock_dmap.called)
            self.assertTrue(mock_rdc.called)
            mock_dmap.reset_mock()
            mock_rdc.reset_mock()

            # "flush" StringIO
            mock_stdout.truncate(0)
            mock_stdout.seek(0)
            self.assertEqual(mock_stdout.getvalue(), "")

    @with_bf
    @mock.patch("sys.stdout", new_callable=io.StringIO)
    def test_report_general(self, _bf: File, mock_stdout):
        _overview = self.create_overview(_bf)

        with mock.patch.object(
            _bf.__class__, "info", new_callable=mock.PropertyMock, return_value=_bf.info
        ) as mock_info:
            _overview.report_general()
            self.assertNotEqual(mock_stdout.getvalue(), "")
            self.assertTrue(mock_info.called)

    @with_bf
    @mock.patch("sys.stdout", new_callable=io.StringIO)
    def test_report_msi(self, _bf: File, mock_stdout):
        _overview = self.create_overview(_bf)

        # HDFOverview.report_msi_configs                            ----
        msi = _bf.msi["Discharge"]

        # MSI has no configurations
        with mock.patch.object(
            msi.__class__, "configs", new_callable=mock.PropertyMock, return_value={}
        ) as mock_msi:
            _overview.report_msi_configs(msi)
            self.assertNotEqual(mock_stdout.getvalue(), "")
            self.assertTrue(mock_msi.called)

        # "flush" StringIO
        mock_stdout.truncate(0)
        mock_stdout.seek(0)
        self.assertEqual(mock_stdout.getvalue(), "")

        # MSI HAS configurations
        configs = msi.configs.copy()
        mock_values = {}
        with mock.patch.object(
            msi.__class__, "configs", new_callable=mock.PropertyMock, return_value=configs
        ) as mock_values["configs"]:
            _overview.report_msi_configs(msi)
            self.assertNotEqual(mock_stdout.getvalue(), "")
            self.assertTrue(mock_values["configs"].called)

        # "flush" StringIO
        mock_stdout.truncate(0)
        mock_stdout.seek(0)
        self.assertEqual(mock_stdout.getvalue(), "")

        # HDFOverview.report_msi                                    ----
        with mock.patch.object(
            HDFMap, "msi", new_callable=mock.PropertyMock, return_value=_bf.file_map.msi
        ) as mock_dmap, mock.patch.object(
            HDFOverview,
            "report_msi_configs",
            side_effect=_overview.report_control_configs,
        ) as mock_rmc:
            # specify an existing control
            _overview.report_msi("Discharge")
            self.assertNotEqual(mock_stdout.getvalue(), "")
            self.assertTrue(mock_dmap.called)
            self.assertTrue(mock_rmc.called)
            mock_dmap.reset_mock()
            mock_rmc.reset_mock()

            # "flush" StringIO
            mock_stdout.truncate(0)
            mock_stdout.seek(0)
            self.assertEqual(mock_stdout.getvalue(), "")

            # report all (aka specified control not in map dict)
            _overview.report_msi()
            self.assertNotEqual(mock_stdout.getvalue(), "")
            self.assertTrue(mock_dmap.called)
            self.assertTrue(mock_rmc.called)
            mock_dmap.reset_mock()
            mock_rmc.reset_mock()

            # "flush" StringIO
            mock_stdout.truncate(0)
            mock_stdout.seek(0)
            self.assertEqual(mock_stdout.getvalue(), "")

    @with_bf
    @mock.patch("sys.stdout", new_callable=io.StringIO)
    def test_print(self, _bf: File, mock_stdout):
        _overview = self.create_overview(_bf)

        with mock.patch.object(
            _bf.__class__, "info", new_callable=mock.PropertyMock, return_value=_bf.info
        ) as mock_info, mock.patch.multiple(
            _overview.__class__,
            report_general=mock.DEFAULT,
            report_discovery=mock.DEFAULT,
            report_details=mock.DEFAULT,
        ) as mock_values:
            _overview.print()
            self.assertNotEqual(mock_stdout.getvalue(), "")
            self.assertTrue(mock_info.called)
            self.assertTrue(mock_values["report_general"].called)
            self.assertTrue(mock_values["report_discovery"].called)
            self.assertTrue(mock_values["report_details"].called)

    @with_bf
    @mock.patch("__main__.__builtins__.open", new_callable=mock.mock_open)
    def test_save(self, _bf: File, mock_o):
        _overview = self.create_overview(_bf)

        with mock.patch.object(
            _overview.__class__, "print", side_effect=_overview.print
        ) as mock_print:

            # save overview file alongside HDF5 file
            filename = os.path.splitext(_bf.filename)[0] + ".txt"
            _overview.save()
            self.assertTrue(mock_print.called)
            self.assertEqual(mock_o.call_count, 1)
            mock_o.assert_called_with(filename, "w")

            # reset mocks
            mock_o.reset_mock()
            mock_print.reset_mock()

            # specify `filename`
            filename = "test.txt"
            _overview.save(filename=filename)
            self.assertTrue(mock_print.called)
            self.assertEqual(mock_o.call_count, 1)
            mock_o.assert_called_with(filename, "w")


if __name__ == "__main__":
    ut.main()
