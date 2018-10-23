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

from bapsflib._hdf import HDFMap
from unittest import mock

from . import TestBase
from ..hdfoverview import HDFOverview


class TestHDFOverview(TestBase):
    """
    Test case for
    :class:`~bapsflib._hdf.utils.hdfoverview.HDFOverview.`
    """

    def setUp(self):
        super().setUp()

        # setup HDF5 file
        self.f.add_module('SIS 3301')  # digitizer
        self.f.add_module('Waveform')  # control
        self.f.add_module('Discharge')  # MSI diagnostic
        self.f.create_group('Raw data + config/Unknown')

    def tearDown(self):
        super().tearDown()
        del self.f['Raw data + config/Unknown']

    @property
    def overview(self):
        return self.create_overview(self.bf)

    @staticmethod
    def create_overview(file):
        return HDFOverview(file)

    def test_not_file_obj(self):
        """Raise error if input is not bapsflib._hdf.utils.file.File"""
        with self.assertRaises(ValueError):
            self.create_overview(None)

    def test_overview_basics(self):
        _bf = self.bf
        _overview = self.overview

        # -- attribute existence                                    ----
        self.assertTrue(hasattr(_overview, 'control_discovery'))
        self.assertTrue(hasattr(_overview, 'digitizer_discovery'))
        self.assertTrue(hasattr(_overview, 'msi_discovery'))
        self.assertTrue(hasattr(_overview, 'print'))
        self.assertTrue(hasattr(_overview, 'report_control_configs'))
        self.assertTrue(hasattr(_overview, 'report_controls'))
        self.assertTrue(hasattr(_overview, 'report_details'))
        self.assertTrue(hasattr(_overview, 'report_digitizer_configs'))
        self.assertTrue(hasattr(_overview, 'report_digitizers'))
        self.assertTrue(hasattr(_overview, 'report_discovery'))
        self.assertTrue(hasattr(_overview, 'report_general'))
        self.assertTrue(hasattr(_overview, 'report_msi'))
        self.assertTrue(hasattr(_overview, 'report_msi_configs'))
        self.assertTrue(hasattr(_overview, 'save'))
        self.assertTrue(hasattr(_overview, 'unknowns_discovery'))

    @mock.patch('sys.stdout', new_callable=io.StringIO)
    def test_discoveries(self, mock_stdout):
        self.f.add_module('SIS crate')

        _bf = self.bf
        _overview = self.overview

        # HDFOverview.control_discovery()
        with mock.patch.object(
                HDFMap, 'controls', new_callable=mock.PropertyMock,
                return_value=_bf.file_map.controls) as mock_dmap:
            _overview.control_discovery()
            self.assertNotEqual(mock_stdout.getvalue(), '')
            self.assertTrue(mock_dmap.called)

        # "flush" StringIO
        mock_stdout.truncate(0)
        mock_stdout.seek(0)
        self.assertEqual(mock_stdout.getvalue(), '')

        # HDFOverview.digitizer_discovery()
        with mock.patch.object(
                HDFMap, 'digitizers', new_callable=mock.PropertyMock,
                return_value=_bf.file_map.digitizers) as mock_dmap:
            _overview.digitizer_discovery()
            self.assertNotEqual(mock_stdout.getvalue(), '')
            self.assertTrue(mock_dmap.called)

        # "flush" StringIO
        mock_stdout.truncate(0)
        mock_stdout.seek(0)
        self.assertEqual(mock_stdout.getvalue(), '')

        # HDFOverview.msi_discovery()
        with mock.patch.object(
                HDFMap, 'msi', new_callable=mock.PropertyMock,
                return_value=_bf.file_map.msi) as mock_dmap:
            _overview.msi_discovery()
            self.assertNotEqual(mock_stdout.getvalue(), '')
            self.assertTrue(mock_dmap.called)

        # "flush" StringIO
        mock_stdout.truncate(0)
        mock_stdout.seek(0)
        self.assertEqual(mock_stdout.getvalue(), '')

        # HDFOverview.unknowns_discovery()
        with mock.patch.object(
                HDFMap, 'unknowns', new_callable=mock.PropertyMock,
                return_value=_bf.file_map.unknowns) as mock_unknowns:
            _overview.unknowns_discovery()
            self.assertNotEqual(mock_stdout.getvalue(), '')
            self.assertTrue(mock_unknowns.called)

        # "flush" StringIO
        mock_stdout.truncate(0)
        mock_stdout.seek(0)
        self.assertEqual(mock_stdout.getvalue(), '')

        # HDFOverview.report_discovery()
        with mock.patch.multiple(
                HDFOverview,
                control_discovery=mock.DEFAULT,
                digitizer_discovery=mock.DEFAULT,
                msi_discovery=mock.DEFAULT,
                unknowns_discovery=mock.DEFAULT) as mock_values:
            mock_values['control_discovery'].side_effect = \
                _overview.control_discovery()
            mock_values['digitizer_discovery'].side_effect = \
                _overview.digitizer_discovery()
            mock_values['msi_discovery'].side_effect = \
                _overview.msi_discovery()
            mock_values['unknowns_discovery'].side_effect = \
                _overview.unknowns_discovery()

            _overview.report_discovery()
            self.assertNotEqual(mock_stdout.getvalue(), '')
            self.assertTrue(mock_values['control_discovery'].called)
            self.assertTrue(mock_values['digitizer_discovery'].called)
            self.assertTrue(mock_values['msi_discovery'].called)
            self.assertTrue(mock_values['unknowns_discovery'].called)

        # "flush" StringIO
        mock_stdout.truncate(0)
        mock_stdout.seek(0)
        self.assertEqual(mock_stdout.getvalue(), '')


if __name__ == '__main__':
    ut.main()
