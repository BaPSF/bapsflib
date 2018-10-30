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

from bapsflib._hdf.utils.hdfoverview import HDFOverview
from unittest import mock

from . import TestBase
from ..lapdoverview import LaPDOverview


class TestLaPDOverview(TestBase):
    """
    Test case for :class:`~bapsflib.lapd._hdf.lapdoverview.HDFOverview`
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
        return self.create_overview(self.lapdf)

    @staticmethod
    def create_overview(file):
        return LaPDOverview(file)

    def test_overview(self):
        _lapdf = self.lapdf
        _overview = self.overview

        # LaPDOverview subclasses HDFOverview
        self.assertIsInstance(_overview, LaPDOverview)

        # override method `report_general`
        self.assertMethodOverride(HDFOverview, _overview,
                                  'report_general')

        # `report_general` prints to screen
        _lapdf.info['exp description'] = "This experiment\n" \
                                         "did something"
        _overview = self.create_overview(_lapdf)
        with mock.patch('sys.stdout',
                        new_callable=io.StringIO) as mock_stdout, \
                mock.patch.object(HDFOverview, 'report_general',
                                  side_effect=print('hello')) \
                as mock_rg_super:
            _overview.report_general()
            self.assertNotEqual(mock_stdout.getvalue(), '')
            self.assertTrue(mock_rg_super.called)


if __name__ == '__main__':
    ut.main()
