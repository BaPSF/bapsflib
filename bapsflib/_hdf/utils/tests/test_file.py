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

from unittest import mock

from bapsflib._hdf import HDFMapper
from bapsflib._hdf.maps.digitizers.templates import HDFMapDigiTemplate
from bapsflib._hdf.utils.file import File
from bapsflib._hdf.utils.hdfoverview import HDFOverview
from bapsflib._hdf.utils.hdfreadcontrols import HDFReadControls
from bapsflib._hdf.utils.hdfreaddata import HDFReadData
from bapsflib._hdf.utils.hdfreadmsi import HDFReadMSI
from bapsflib._hdf.utils.tests import TestBase
from bapsflib.utils.decorators import with_bf
from bapsflib.utils.warnings import HDFMappingWarning


class TestFile(TestBase):
    """Test case for :class:`~bapsflib._hdf.utils.file.File`."""

    @with_bf
    def test_file_subclass(self, _bf: File):
        # must be h5py.File instance
        self.assertIsInstance(_bf, h5py.File)

    @with_bf
    def test_attribute_existence(self, _bf: File):
        _conditions = [  # attribute name
            # path attributes
            "CONTROL_PATH",
            "DIGITIZER_PATH",
            "MSI_PATH",
            # 'info' attributes
            "_build_info",
            "info",
            # mapping attributes/methods
            "_map_file",
            "file_map",
            "controls",
            "digitizers",
            "msi",
            # read data attributes/methods
            "read_data",
            "read_controls",
            "read_msi",
            # other attributes/methods
            "overview",
        ]
        for attr_name in _conditions:
            with self.subTest(attr_name=attr_name):
                self.assertTrue(hasattr(_bf, attr_name))

    @with_bf
    def test_path_attribute_values(self, _bf: File):
        _conditions = [
            # (attr_name, expected)
            ("CONTROL_PATH", "Raw data + config"),
            ("DIGITIZER_PATH", "Raw data + config"),
            ("MSI_PATH", "MSI"),
        ]
        for attr_name, expected in _conditions:
            with self.subTest(attr_name=attr_name, expected=expected):
                self.assertEqual(getattr(_bf, attr_name), expected)

    @with_bf
    def test_map_file_call(self, _bf: File):
        # `_map_file` should call HDFMapper
        with mock.patch(
            f"{File.__module__}.{HDFMapper.__qualname__}", return_value="mapped"
        ) as mock_map:

            _bf._map_file()

            self.assertTrue(mock_map.called)
            self.assertEqual(_bf._file_map, "mapped")

    @with_bf
    def test_attributes_as_property(self, _bf: File):
        _conditions = [  # attribute name
            "info",
            "file_map",
            "controls",
            "digitizers",
            "msi",
            "overview",
        ]
        for attr_name in _conditions:
            with self.subTest(attr_name=attr_name):
                self.assertIsInstance(getattr(type(_bf), attr_name), property)

    @with_bf
    def test_info_property(self, _bf: File):
        _conditions = [
            # (_assert, key, expected)
            (self.assertIsInstance, None, dict),
            (self.assertEqual, "file", os.path.basename(_bf.filename)),
            (self.assertEqual, "absolute file path", os.path.abspath(_bf.filename)),
        ]
        for _assert, key, expected in _conditions:
            with self.subTest(_assert=_assert.__name__, key=key, expected=expected):
                if key is None:
                    _assert(_bf.info, expected)
                else:
                    _assert(_bf.info[key], expected)

    @with_bf
    def test_file_map(self, _bf: File):
        self.assertIsInstance(_bf.file_map, HDFMapper)

    @with_bf
    def test_mapping_properties(self, _bf: File):
        _conditions = [
            # property name
            "controls",
            "digitizers",
            "msi",
        ]
        for attr_name in _conditions:
            with self.subTest(attr_name=attr_name):
                self.assertIs(getattr(_bf, attr_name), getattr(_bf.file_map, attr_name))

    @with_bf
    def test_overview(self, _bf: File):
        self.assertIsInstance(_bf.overview, HDFOverview)

    @with_bf
    def test_read_controls(self, _bf: File):
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

    @with_bf
    def test_read_data(self, _bf: File):
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

    @with_bf
    def test_read_msi(self, _bf: File):
        with mock.patch(
            f"{HDFReadMSI.__module__}.{HDFReadMSI.__qualname__}", return_value="read msi"
        ) as mock_rm:
            mdata = _bf.read_msi("Discharge", silent=False)
            self.assertTrue(mock_rm.called)
            self.assertEqual(mdata, "read msi")
            mock_rm.assert_called_once_with(_bf, "Discharge")

    @with_bf
    def test_file_wrong_open_mode(self, _bf: File):
        # raise ValueError if mode not in ('r', 'r+')
        modes = ["w", "w-", "x", "a"]
        for mode in modes:
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                _bf2 = File(self.f.filename, mode=mode)
                _bf2.close()

    @with_bf
    def test_file_correct_open_mode(self, _bf: File):
        with mock.patch("h5py.File.__init__", wraps=h5py.File.__init__) as mock_file:
            for mode in ("r", "r+"):
                with self.subTest(mode=mode):
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

    @with_bf
    def test_file_init_sequence(self, _bf: File):
        # methods `_build_info` and `_map_file` should be called in
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

    def test_get_digitizer_specs_one_digi(self):
        self.f.reset()
        self.f.add_module("SIS crate")
        _bf = File(
            self.f.filename,
            control_path="Raw data + config",
            digitizer_path="Raw data + config",
            msi_path="MSI",
        )

        with mock.patch(
            f"{HDFMapDigiTemplate.__module__}.{HDFMapDigiTemplate.__qualname__}.get_adc_info",
            return_value="mapped",
        ) as mock_map:
            _bf.get_digitizer_specs(1, 1, digitizer=None, adc="SIS 3302", silent=True)
            mock_map.assert_called_once()

        _bf.close()
        self.f.reset()

    def test_get_digitizer_specs_two_digi(self):
        self.f.reset()
        self.f.add_module("SIS 3301")
        self.f.add_module("SIS crate")
        _bf = File(
            self.f.filename,
            control_path="Raw data + config",
            digitizer_path="Raw data + config",
            msi_path="MSI",
        )

        with mock.patch(
            f"{HDFMapDigiTemplate.__module__}.{HDFMapDigiTemplate.__qualname__}.get_adc_info",
            return_value="mapped",
        ) as mock_map:
            _bf.get_digitizer_specs(
                1, 1, digitizer="SIS crate", adc="SIS 3302", silent=True
            )
            mock_map.assert_called_once()

        _bf.close()
        self.f.reset()

    def test_get_digitizer_specs(self):
        self.f.reset()
        self.f.add_module("SIS crate")
        _bf = File(
            self.f.filename,
            control_path="Raw data + config",
            digitizer_path="Raw data + config",
            msi_path="MSI",
        )

        expected = _bf.digitizers["SIS crate"].get_adc_info(
            1, 1, adc="SIS 3302", config_name="config01"
        )
        specs = _bf.get_digitizer_specs(1, 1, adc="SIS 3302", silent=True)
        self.assertDictEqual(expected, specs)

    def test_get_digitizer_specs_raises(self):
        self.f.reset()
        self.f.add_module("SIS crate")
        self.f.add_module("SIS 3301")
        _bf = File(
            self.f.filename,
            control_path="Raw data + config",
            digitizer_path="Raw data + config",
            msi_path="MSI",
        )

        _conditions = [
            # (error, args, kwargs)
            (ValueError, (1, 1), {"silent": True}),
            (TypeError, (1, 1), {"digitizer": 5, "silent": True}),
            (ValueError, (1, 1), {"digitizer": "not a digitizer", "silent": True}),
        ]
        for _error, args, kwargs in _conditions:
            with (
                self.subTest(error=_error, args=args, kwargs=kwargs),
                self.assertRaises(_error),
            ):
                _bf.get_digitizer_specs(*args, **kwargs)

        _bf.close()
        self.f.reset()

    @with_bf
    def test_get_digitizer_specs_warnings(self, _bf: File):
        self.f.reset()
        self.f.add_module("SIS crate")
        _bf = File(
            self.f.filename,
            control_path="Raw data + config",
            digitizer_path="Raw data + config",
            msi_path="MSI",
        )

        with self.assertWarns(HDFMappingWarning):
            _bf.get_digitizer_specs(1, 1, adc="SIS 3302", silent=False)

        _bf.close()
        self.f.reset()
