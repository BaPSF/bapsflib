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
import astropy.units as u
import h5py
import numpy as np
import os
import unittest as ut

from unittest import mock

from bapsflib._hdf.maps import HDFMap
from bapsflib._hdf.maps.digitizers.sis3301 import HDFMapDigiSIS3301
from bapsflib._hdf.utils.file import File
from bapsflib._hdf.utils.hdfreadcontrols import HDFReadControls
from bapsflib._hdf.utils.hdfreaddata import (
    build_sndr_for_simple_dset,
    condition_shotnum,
    do_shotnum_intersection,
    HDFReadData,
)
from bapsflib._hdf.utils.tests import TestBase
from bapsflib.utils.decorators import with_bf


class TestHDFReadData(TestBase):
    """
    Test Case for
    :class:`~bapsflib._hdf.utils.hdfreaddata.HDFReadData`
    """

    #
    # Notes:
    # - tests are currently performed on digitizer 'SIS 3301'

    def setUp(self):
        super().setUp()

    def tearDown(self):
        super().tearDown()

    @with_bf
    @mock.patch("bapsflib._hdf.utils.hdfreaddata.HDFReadControls")
    @mock.patch("bapsflib._hdf.utils.hdfreaddata.condition_controls")
    @mock.patch.object(
        HDFMap, "controls", new_callable=mock.PropertyMock, return_value={"control": None}
    )
    def test_adding_controls(self, _bf: File, mock_cmap, mock_cc, mock_cdata):
        """Test adding control device data to digitizer data."""
        # setup HDF5
        sn_size = 50
        self.f.add_module("SIS 3301", {"n_configs": 1, "sn_size": sn_size, "nt": 1000})
        _mod = self.f.modules["SIS 3301"]
        digi = "SIS 3301"
        adc = "SIS 3301"
        config_name = _mod.knobs.active_config[0]
        bc_arr = _mod.knobs.active_brdch
        bc_indices = np.where(bc_arr)
        brd = bc_indices[0][0]
        ch = bc_indices[1][0]
        _bf._map_file()  # re-map file
        digi_path = "Raw data + config/SIS 3301"
        dset_name = f"{config_name} [{brd}:{ch}]"
        dset_path = f"{digi_path}/{dset_name}"
        dset = _bf.get(dset_path)
        dheader = _bf.get(f"{dset_path} headers")
        shotnumkey = "Shot"

        # setup mock control data
        cdata = np.empty(
            20,
            dtype=[
                ("shotnum", np.uint32, 1),
                ("xyz", np.float32, 3),
                ("freq", np.float32, 1),
            ],
        )
        cdata["shotnum"] = np.arange(41, 61, 1, dtype=np.uint32)
        cdata["xyz"][..., 0] = np.arange(0.0, 20.0, 1.0, dtype=np.float32)
        cdata["xyz"][..., 1] = np.arange(0.0, 30.0, 1.5, dtype=np.float32)
        cdata["xyz"][..., 2] = np.arange(0.0, -40.0, -2.0, dtype=np.float32)
        cdata["freq"] = np.arange(20.0, 120.0, 5.0, dtype=np.float32)

        # setup mock condition_controls
        mock_cc.return_value = [("control", "config01")]

        # -- `intersection_set=True`                                ----
        # shotnum exists in both digitizer and control dataset
        shotnum = 45
        indices = [44]
        m_info = {
            "controls": {
                "control": {
                    "device group path": "Raw data + config/control",
                    "contype": "motion+",
                    "configuration name": "config01",
                }
            }
        }
        m_cdata = np.reshape(cdata[4], 1).view(HDFReadControls)
        m_cdata._info = m_info
        mock_cdata.return_value = m_cdata.view(HDFReadControls)
        data = HDFReadData(
            _bf,
            brd,
            ch,
            config_name=config_name,
            adc=adc,
            digitizer=digi,
            shotnum=shotnum,
            add_controls=[("control", "config01")],
            intersection_set=True,
        )
        self.assertDataObj(data, _bf, motion_added=True)
        self.assertTrue(
            np.array_equiv(data["shotnum"], np.array([shotnum], dtype=np.uint32))
        )
        self.assertDataArrayValues(data, dset, indices)
        self.assertControlInData(
            m_cdata, data, np.array([shotnum], dtype=np.uint32).reshape(1)
        )
        self.assertTrue(mock_cdata.called)
        self.assertTrue(mock_cc.called)
        mock_cdata.reset_mock()
        mock_cc.reset_mock()

        # some shot numbers are missing from the control dataset
        shotnum = [20, 45]
        indices = [44]
        m_info = {
            "controls": {
                "control": {
                    "device group path": "Raw data + config/control",
                    "contype": "motion+",
                    "configuration name": "config01",
                }
            }
        }
        fields = list(cdata.dtype.names)
        fields.remove("xyz")
        m_cdata = np.reshape(cdata[fields][4], (1,))
        m_cdata = m_cdata.view(HDFReadControls)
        m_cdata._info = m_info
        mock_cdata.return_value = m_cdata.view(HDFReadControls)
        data = HDFReadData(
            _bf,
            brd,
            ch,
            config_name=config_name,
            adc=adc,
            digitizer=digi,
            shotnum=shotnum,
            add_controls=[("control", "config01")],
            intersection_set=True,
        )
        self.assertDataObj(data, _bf, motion_added=True)
        self.assertTrue(np.array_equiv(data["shotnum"], np.array([45], dtype=np.uint32)))
        self.assertDataArrayValues(data, dset, indices)
        self.assertControlInData(
            m_cdata, data, np.array([45], dtype=np.uint32).reshape(1)
        )
        self.assertTrue(mock_cdata.called)
        self.assertTrue(mock_cc.called)
        mock_cdata.reset_mock()
        mock_cc.reset_mock()

        # control does not have 'xyz'
        shotnum = 45
        indices = [44]
        m_info = {
            "controls": {
                "control": {
                    "device group path": "Raw data + config/control",
                    "contype": "motion+",
                    "configuration name": "config01",
                }
            }
        }
        m_cdata = np.reshape(cdata[4], 1).view(HDFReadControls)
        m_cdata._info = m_info
        mock_cdata.return_value = m_cdata.view(HDFReadControls)
        data = HDFReadData(
            _bf,
            brd,
            ch,
            config_name=config_name,
            adc=adc,
            digitizer=digi,
            shotnum=shotnum,
            add_controls=[("control", "config01")],
            intersection_set=True,
        )
        self.assertDataObj(data, _bf, motion_added=True)
        self.assertTrue(
            np.array_equiv(data["shotnum"], np.array([shotnum], dtype=np.uint32))
        )
        self.assertDataArrayValues(data, dset, indices)
        self.assertControlInData(
            m_cdata, data, np.array([shotnum], dtype=np.uint32).reshape(1)
        )
        self.assertTrue(mock_cdata.called)
        self.assertTrue(mock_cc.called)
        mock_cdata.reset_mock()
        mock_cc.reset_mock()

        # -- `intersection_set=False`                               ----
        # some shot numbers are missing from the control dataset
        shotnum = [20, 45]
        indices = [19, 44]
        m_info = {
            "controls": {
                "control": {
                    "device group path": "Raw data + config/control",
                    "contype": "motion+",
                    "configuration name": "config01",
                }
            }
        }
        m_cdata = np.empty(1, dtype=cdata.dtype).view(HDFReadControls)
        m_cdata[0]["shotnum"] = 20
        m_cdata[0]["xyz"] = np.nan
        m_cdata[0]["freq"] = np.nan
        m_cdata = np.append(m_cdata, np.reshape(cdata[4], 1))
        m_cdata = m_cdata.view(HDFReadControls)
        m_cdata._info = m_info
        mock_cdata.return_value = m_cdata.view(HDFReadControls)
        data = HDFReadData(
            _bf,
            brd,
            ch,
            config_name=config_name,
            adc=adc,
            digitizer=digi,
            shotnum=shotnum,
            add_controls=[("control", "config01")],
            intersection_set=False,
        )
        self.assertDataObj(data, _bf, motion_added=True)
        self.assertTrue(
            np.array_equiv(data["shotnum"], np.array([shotnum], dtype=np.uint32))
        )
        self.assertDataArrayValues(data, dset, indices)
        self.assertControlInData(m_cdata, data, np.array(shotnum, dtype=np.uint32))
        self.assertTrue(mock_cdata.called)
        self.assertTrue(mock_cc.called)
        mock_cdata.reset_mock()
        mock_cc.reset_mock()

    @with_bf
    def test_kwarg_adc(self, _bf: File):
        """Test handling of keyword `adc`."""
        # Handling should be done by mapping function
        # `construct_dset_name` which is covered by the associated
        # mapping test
        #
        # add a digitizer
        self.f.add_module("SIS 3301", {"n_configs": 1, "sn_size": 50})
        _mod = self.f.modules["SIS 3301"]
        digi = "SIS 3301"
        adc = "SIS 3301"
        config_name = _mod.knobs.active_config[0]
        bc_arr = _mod.knobs.active_brdch
        bc_indices = np.where(bc_arr)
        brd = bc_indices[0][0]
        ch = bc_indices[1][0]

        _bf._map_file()  # re-map file
        _map = _bf.file_map.digitizers[digi]
        with mock.patch.object(
            HDFMapDigiSIS3301, "construct_dataset_name", wraps=_map.construct_dataset_name
        ) as mock_cdn:

            # everything is good
            data = HDFReadData(
                _bf, brd, ch, adc=adc, digitizer=digi, config_name=config_name
            )
            self.assertTrue(mock_cdn.called)
            self.assertDataObj(data, _bf)
            self.assertEqual(data.info["adc"], adc)
            mock_cdn.reset_mock()

            # not a configuration name
            with self.assertRaises(ValueError):
                data = HDFReadData(
                    _bf,
                    brd,
                    ch,
                    adc="not an adc",
                    digitizer=digi,
                    config_name=config_name,
                )
                self.assertTrue(mock_cdn.called)
            mock_cdn.reset_mock()

            # `adc` None
            data = HDFReadData(_bf, brd, ch, digitizer=digi, config_name=config_name)
            self.assertTrue(mock_cdn.called)
            self.assertDataObj(data, _bf)
            self.assertEqual(data.info["adc"], adc)
            mock_cdn.reset_mock()

    @with_bf
    def test_kwarg_board(self, _bf: File):
        """Test handling of argument `board`."""
        # Handling should be done by mapping function
        # `construct_dset_name` which is covered by the associated
        # mapping test
        #
        # add a digitizer
        self.f.add_module("SIS 3301", {"n_configs": 1, "sn_size": 50})
        _mod = self.f.modules["SIS 3301"]
        digi = "SIS 3301"
        adc = "SIS 3301"
        config_name = _mod.knobs.active_config[0]
        bc_arr = _mod.knobs.active_brdch
        bc_indices = np.where(bc_arr)
        brd = bc_indices[0][0]
        ch = bc_indices[1][0]

        # re-map file
        _bf._map_file()

        # run assertions
        _map = _bf.file_map.digitizers[digi]
        with mock.patch.object(
            HDFMapDigiSIS3301, "construct_dataset_name", wraps=_map.construct_dataset_name
        ) as mock_cdn:

            # everything is good
            data = HDFReadData(
                _bf, brd, ch, adc=adc, digitizer=digi, config_name=config_name
            )
            self.assertTrue(mock_cdn.called)
            self.assertDataObj(data, _bf)
            self.assertEqual(data.info["board"], brd)
            mock_cdn.reset_mock()

            # not a configuration name
            with self.assertRaises(ValueError):
                data = HDFReadData(
                    _bf, -1, ch, adc=adc, digitizer=digi, config_name=config_name
                )
                self.assertTrue(mock_cdn.called)
                mock_cdn.reset_mock()

    @with_bf
    def test_kwarg_channel(self, _bf: File):
        """Test handling of argument `channel`."""
        # Handling should be done by mapping function
        # `construct_dset_name` which is covered by the associated
        # mapping test
        #
        # add a digitizer
        self.f.add_module("SIS 3301", {"n_configs": 1, "sn_size": 50})
        _mod = self.f.modules["SIS 3301"]
        digi = "SIS 3301"
        adc = "SIS 3301"
        config_name = _mod.knobs.active_config[0]
        bc_arr = _mod.knobs.active_brdch
        bc_indices = np.where(bc_arr)
        brd = bc_indices[0][0]
        ch = bc_indices[1][0]

        _bf._map_file()  # re-map file
        _map = _bf.file_map.digitizers[digi]
        with mock.patch.object(
            HDFMapDigiSIS3301, "construct_dataset_name", wraps=_map.construct_dataset_name
        ) as mock_cdn:

            # everything is good
            data = HDFReadData(
                _bf, brd, ch, adc=adc, digitizer=digi, config_name=config_name
            )
            self.assertTrue(mock_cdn.called)
            self.assertDataObj(data, _bf)
            self.assertEqual(data.info["channel"], ch)
            mock_cdn.reset_mock()

            # not a configuration name
            with self.assertRaises(ValueError):
                data = HDFReadData(
                    _bf, brd, -1, adc=adc, digitizer=digi, config_name=config_name
                )
                self.assertTrue(mock_cdn.called)
                mock_cdn.reset_mock()

    @with_bf
    def test_kwarg_config_name(self, _bf: File):
        """Test handling of keyword `digitizer`."""
        # Handling should be done by mapping function
        # `construct_dset_name` which is covered by the associated
        # mapping test
        #
        # add a digitizer
        self.f.add_module("SIS 3301", {"n_configs": 1, "sn_size": 50})
        _mod = self.f.modules["SIS 3301"]
        digi = "SIS 3301"
        adc = "SIS 3301"
        config_name = _mod.knobs.active_config[0]
        bc_arr = _mod.knobs.active_brdch
        bc_indices = np.where(bc_arr)
        brd = bc_indices[0][0]
        ch = bc_indices[1][0]

        _bf._map_file()  # re-map file
        _map = _bf.file_map.digitizers[digi]
        with mock.patch.object(
            HDFMapDigiSIS3301, "construct_dataset_name", wraps=_map.construct_dataset_name
        ) as mock_cdn:

            # everything is good
            data = HDFReadData(
                _bf, brd, ch, adc=adc, digitizer=digi, config_name=config_name
            )
            self.assertTrue(mock_cdn.called)
            self.assertDataObj(data, _bf)
            self.assertEqual(data.info["configuration name"], config_name)
            mock_cdn.reset_mock()

            # not a configuration name
            with self.assertRaises(ValueError):
                data = HDFReadData(
                    _bf, brd, ch, adc=adc, digitizer=digi, config_name="not a config"
                )
                self.assertTrue(mock_cdn.called)
                mock_cdn.reset_mock()

            # `config_name` None
            with self.assertWarns(UserWarning):
                data = HDFReadData(_bf, brd, ch, adc=adc, digitizer=digi)
                self.assertTrue(mock_cdn.called)
                self.assertDataObj(data, _bf)
                self.assertEqual(data.info["configuration name"], config_name)
                mock_cdn.reset_mock()

    @with_bf
    def test_kwarg_digitizer(self, _bf: File):
        """Test handling of keyword `digitizer`."""
        # Note: cases were an exception is raise is covered by
        #       `test_raise_errors`
        #
        # add a digitizer
        self.f.add_module("SIS 3301", {"n_configs": 1, "sn_size": 50})
        _mod = self.f.modules["SIS 3301"]
        digi = "SIS 3301"
        adc = "SIS 3301"
        config_name = _mod.knobs.active_config[0]
        bc_arr = _mod.knobs.active_brdch
        bc_indices = np.where(bc_arr)
        brd = bc_indices[0][0]
        ch = bc_indices[1][0]
        _bf._map_file()  # re-map file

        # `digitizer` is None and "main" digitizer was identified
        with self.assertWarns(UserWarning):
            data = HDFReadData(_bf, brd, ch, adc=adc, config_name=config_name)
            self.assertDataObj(data, _bf)
            self.assertEqual(data.info["digitizer"], digi)

        # specified `digitizer` is VALID
        data = HDFReadData(_bf, brd, ch, digitizer=digi, adc=adc, config_name=config_name)
        self.assertDataObj(data, _bf)
        self.assertEqual(data.info["digitizer"], digi)

    @with_bf
    def test_kwarg_keep_bits(self, _bf: File):
        """Test behavior of keyword `keep_bits`."""
        # setup
        sn_size = 50
        self.f.add_module("SIS 3301", {"n_configs": 1, "sn_size": sn_size, "nt": 1000})
        _mod = self.f.modules["SIS 3301"]
        digi = "SIS 3301"
        adc = "SIS 3301"
        config_name = _mod.knobs.active_config[0]
        bc_arr = _mod.knobs.active_brdch
        bc_indices = np.where(bc_arr)
        brd = bc_indices[0][0]
        ch = bc_indices[1][0]
        _bf._map_file()  # re-map file
        digi_path = "Raw data + config/SIS 3301"
        dset_name = f"{config_name} [{brd}:{ch}]"
        dset_path = f"{digi_path}/{dset_name}"
        dset = _bf.get(dset_path)
        dheader = _bf.get(f"{dset_path} headers")
        shotnumkey = "Shot"

        # -- `keep_bits=False` (DEFAULT)                            ----
        shotnum = 5
        indices = [4]
        data = HDFReadData(
            _bf,
            brd,
            ch,
            config_name=config_name,
            adc=adc,
            digitizer=digi,
            shotnum=shotnum,
            keep_bits=False,
        )
        self.assertDataObj(data, _bf)
        self.assertTrue(np.array_equiv(data["shotnum"], np.array([5], dtype=np.uint32)))
        self.assertDataArrayValues(data, dset, indices)
        self.assertEqual(data.info["signal units"], u.volt)

        # voltage step size can not be calculated
        shotnum = 5
        indices = [4]
        with mock.patch.object(
            HDFReadData, "dv", new_callable=mock.PropertyMock(return_value=None)
        ):
            with self.assertWarns(UserWarning):
                data = HDFReadData(
                    _bf,
                    brd,
                    ch,
                    config_name=config_name,
                    adc=adc,
                    digitizer=digi,
                    shotnum=shotnum,
                    keep_bits=False,
                )
            self.assertTrue(np.issubdtype(data.dtype["signal"].base, np.floating))
            self.assertTrue(
                np.array_equal(data["signal"], dset[indices, ...].astype(np.float32))
            )
            self.assertEqual(data.info["signal units"], u.bit)

        # -- `keep_bits=True`                                       ----
        # default behavior
        shotnum = 5
        indices = [4]
        data = HDFReadData(
            _bf,
            brd,
            ch,
            config_name=config_name,
            adc=adc,
            digitizer=digi,
            shotnum=shotnum,
            keep_bits=True,
        )
        self.assertDataObj(data, _bf, keep_bits=True)
        self.assertTrue(np.array_equiv(data["shotnum"], np.array([5], dtype=np.uint32)))
        self.assertDataArrayValues(data, dset, indices, keep_bits=True)
        self.assertEqual(data.info["signal units"], u.bit)

    @with_bf
    @mock.patch(
        "bapsflib._hdf.utils.hdfreaddata.do_shotnum_intersection",
        side_effect=do_shotnum_intersection,
    )
    def test_kwarg_intersection_set(self, _bf: File, mock_inter):
        """Test behavior of keyword `intersection_set`."""
        # Note: `intersection_set` has no affect when calling with
        #       `index` and no `add_controls`
        #
        # setup
        sn_size = 50
        self.f.add_module("SIS 3301", {"n_configs": 1, "sn_size": sn_size, "nt": 1000})
        _mod = self.f.modules["SIS 3301"]
        digi = "SIS 3301"
        adc = "SIS 3301"
        config_name = _mod.knobs.active_config[0]
        bc_arr = _mod.knobs.active_brdch
        bc_indices = np.where(bc_arr)
        brd = bc_indices[0][0]
        ch = bc_indices[1][0]
        _bf._map_file()  # re-map file
        digi_path = "Raw data + config/SIS 3301"
        dset_name = f"{config_name} [{brd}:{ch}]"
        dset_path = f"{digi_path}/{dset_name}"
        dset = _bf.get(dset_path)
        dheader = _bf.get(f"{dset_path} headers")
        shotnumkey = "Shot"

        # -- examine `intersection_set=True` (DEFAULT)              ----
        # specified shot numbers are in range of dataset shot numbers
        shotnum = [10, 20]
        indices = [9, 19]
        data = HDFReadData(
            _bf,
            brd,
            ch,
            config_name=config_name,
            adc=adc,
            digitizer=digi,
            shotnum=shotnum,
        )
        self.assertDataObj(data, _bf)
        self.assertTrue(np.array_equal(data["shotnum"], dheader[indices, shotnumkey]))
        self.assertDataArrayValues(data, dset, indices)
        self.assertTrue(mock_inter.called)
        mock_inter.reset_mock()

        # some of the specified shot numbers are not contained in
        # the dataset
        shotnum = [1, sn_size + 1]
        indices = [0]
        data = HDFReadData(
            _bf,
            brd,
            ch,
            config_name=config_name,
            adc=adc,
            digitizer=digi,
            shotnum=shotnum,
        )
        self.assertDataObj(data, _bf)
        self.assertTrue(np.array_equal(data["shotnum"], dheader[indices, shotnumkey]))
        self.assertDataArrayValues(data, dset, indices)
        self.assertTrue(mock_inter.called)
        mock_inter.reset_mock()

        # -- examine `intersection_set=False`                       ----
        # negative shot numbers are still excluded
        # - shot number 20 is VALID so no nan fill
        shotnum = [-5, 20]
        indices = [19]
        data = HDFReadData(
            _bf,
            brd,
            ch,
            config_name=config_name,
            adc=adc,
            digitizer=digi,
            shotnum=shotnum,
            intersection_set=False,
        )
        self.assertDataObj(data, _bf)
        self.assertTrue(np.array_equal(data["shotnum"], dheader[indices, shotnumkey]))
        self.assertDataArrayValues(data, dset, indices)
        self.assertFalse(mock_inter.called)
        mock_inter.reset_mock()

        # some specified shot numbers are not contained in the
        # dataset
        shotnum = [20, sn_size + 2]
        indices = [19]
        data = HDFReadData(
            _bf,
            brd,
            ch,
            config_name=config_name,
            adc=adc,
            digitizer=digi,
            shotnum=shotnum,
            intersection_set=False,
        )
        self.assertDataObj(data, _bf)
        self.assertTrue(
            np.array_equal(data["shotnum"][0], dheader[indices, shotnumkey][0])
        )
        self.assertDataArrayValues(
            np.delete(data, np.s_[1]).view(HDFReadData), dset, indices
        )
        self.assertTrue(np.all(np.isnan(data["signal"][1])))
        self.assertFalse(mock_inter.called)
        mock_inter.reset_mock()

        # some specified shot numbers are not contained in the
        # dataset (keep_bits = True)
        shotnum = [20, sn_size + 2]
        indices = [19]
        data = HDFReadData(
            _bf,
            brd,
            ch,
            config_name=config_name,
            adc=adc,
            digitizer=digi,
            shotnum=shotnum,
            keep_bits=True,
            intersection_set=False,
        )
        self.assertDataObj(data, _bf, keep_bits=True)
        self.assertTrue(
            np.array_equal(data["shotnum"][0], dheader[indices, shotnumkey][0])
        )
        self.assertDataArrayValues(
            np.delete(data, np.s_[1]).view(HDFReadData), dset, indices, keep_bits=True
        )
        self.assertTrue(np.all(data["signal"][1] == 0))
        self.assertFalse(mock_inter.called)
        mock_inter.reset_mock()

    @with_bf
    def test_misc_behavior(self, _bf: File):
        """Test miscellaneous behavior"""
        # setup
        sn_size = 50
        self.f.add_module("SIS 3301", {"n_configs": 1, "sn_size": sn_size, "nt": 1000})
        _mod = self.f.modules["SIS 3301"]
        digi = "SIS 3301"
        adc = "SIS 3301"
        config_name = _mod.knobs.active_config[0]
        bc_arr = _mod.knobs.active_brdch
        bc_indices = np.where(bc_arr)
        brd = bc_indices[0][0]
        ch = bc_indices[1][0]
        _bf._map_file()  # re-map file
        digi_path = "Raw data + config/SIS 3301"
        dset_name = f"{config_name} [{brd}:{ch}]"
        dset_path = f"{digi_path}/{dset_name}"
        dset = _bf.get(dset_path)
        dheader = _bf.get(f"{dset_path} headers")
        shotnumkey = "Shot"

        # -- `index` and `shotnum` are both defined                   --
        # - HDFReadData should ignore `shotnum` and default to `index`
        #
        index = [2, 3]
        shotnum = [45, 50]
        data = HDFReadData(
            _bf,
            brd,
            ch,
            adc=adc,
            digitizer=digi,
            config_name=config_name,
            index=index,
            shotnum=shotnum,
        )
        self.assertDataObj(data, _bf)
        self.assertTrue(np.array_equal(data["shotnum"], dheader[index, shotnumkey]))

        # -- Digitizer header dataset is missing the 'Offset' field   --
        index = [2, 3]
        shotnum = [45, 50]
        hdata = dheader[...]
        _bf.move(f"{dset_path} headers", f"{dset_path} headers_")
        fields = list(hdata.dtype.names)
        fields.remove("Offset")
        _bf.create_dataset(f"{dset_path} headers", data=hdata[fields])
        with self.assertWarns(UserWarning):
            data = HDFReadData(
                _bf,
                brd,
                ch,
                adc=adc,
                digitizer=digi,
                config_name=config_name,
                index=index,
                shotnum=shotnum,
            )
            self.assertIsNone(data.info["voltage offset"])
            self.assertIsNone(data.dv)
            self.assertEqual(data.info["signal units"], u.bit)
            self.assertTrue(np.issubdtype(data.dtype["signal"].base, np.floating))
        del _bf[f"{dset_path} headers"]
        _bf.move(f"{dset_path} headers_", f"{dset_path} headers")

        # -- test property `dv`                                       --
        index = [2, 3]
        shotnum = [45, 50]
        data = HDFReadData(
            _bf,
            brd,
            ch,
            adc=adc,
            digitizer=digi,
            config_name=config_name,
            index=index,
            shotnum=shotnum,
        )

        # `info` keys 'voltage offset' and/or 'bit' are None
        keys = ("bit", "voltage offset")
        for key in keys:
            old_val = data.info[key]
            data.info[key] = None
            self.assertIsNone(data.dv)
            data.info[key] = old_val

        # test known value
        old_bit = data.info["bit"]
        old_offset = data.info["voltage offset"]
        data.info["bit"] = 10
        data.info["voltage offset"] = -1.0 * u.volt
        dv = 2.0 * abs(-1.0) / ((2.0**10) - 1.0)
        self.assertIsInstance(data.dv, u.Quantity)
        self.assertEqual(data.dv.value, dv)
        self.assertEqual(data.dv.unit, u.volt)
        data.info["bit"] = old_bit
        data.info["voltage offset"] = old_offset

        # -- test property `dt`                                       --
        index = [2, 3]
        shotnum = [45, 50]
        data = HDFReadData(
            _bf,
            brd,
            ch,
            adc=adc,
            digitizer=digi,
            config_name=config_name,
            index=index,
            shotnum=shotnum,
        )

        # `info` key 'clock rate' not an astropy.units.Quantity
        old_cr = data.info["clock rate"]
        data.info["clock rate"] = 100.0
        self.assertIsNone(data.dt)

        # known case (w/ sample averaging)
        old_ave = data.info["sample average"]
        data.info["sample average"] = 5
        data.info["clock rate"] = u.Quantity(2.0, unit="MHz")
        dt = (1.0 / 2.0e6) * float(5)
        self.assertIsInstance(data.dt, u.Quantity)
        self.assertEqual(data.dt.value, dt)
        self.assertEqual(data.dt.unit, u.s)

        # known case (no sample averaging)
        data.info["sample average"] = None
        dt = 1.0 / 2.0e6
        self.assertIsInstance(data.dt, u.Quantity)
        self.assertEqual(data.dt.value, dt)
        self.assertEqual(data.dt.unit, u.s)
        data.info["clock rate"] = old_cr
        data.info["sample average"] = old_ave

    @with_bf
    def test_raise_errors(self, _bf: File):
        """Test scenarios that cause exceptions to be raised."""
        # 1. input file object `hdf_obj` is not a bapsflib file object
        #    bapsflib._hdf.utils.file.File
        # 2. `add_controls` is requested but there are no control
        #    devices
        # 3. HDF5 file has no digitizers
        # 4. `digitizer` is None and no "main" digitizer was identified
        # 5. specified `digitizer` is not a mapped digitizer
        # 6. specified `index` in not a valid type
        #
        # not a bapsflib._hdf.utils.file.File object                 (1)
        self.assertRaises(TypeError, HDFReadData, None, 0, 0)

        # `add_controls` is requested but there are no               (2)
        # control devices
        self.assertRaises(ValueError, HDFReadData, _bf, 0, 0, add_controls="Waveform")

        # HDF5 file has no digitizers                                (3)
        self.assertRaises(ValueError, HDFReadData, _bf, 0, 0)

        # `digitizer` is None and no "main" digitizer was            (4)
        # identified
        #
        # setup
        self.f.add_module("SIS 3301", {"n_configs": 1, "sn_size": 50})
        _mod = self.f.modules["SIS 3301"]
        digi = "SIS 3301"
        adc = "SIS 3301"
        config_name = _mod.knobs.active_config[0]
        bc_arr = _mod.knobs.active_brdch
        bc_indices = np.where(bc_arr)
        brd = bc_indices[0][0]
        ch = bc_indices[1][0]
        _bf._map_file()  # re-map file

        # test
        with mock.patch.object(
            HDFMap, "main_digitizer", new_callable=mock.PropertyMock, return_value=None
        ):
            self.assertRaises(ValueError, HDFReadData, _bf, brd, ch)

        # specified `digitizer` is not a mapped digitizer            (5)
        self.assertRaises(ValueError, HDFReadData, _bf, brd, ch, digitizer="Not a digi")

        # specified `index` is NOT a valid type                      (6)
        self.assertRaises(
            TypeError,
            HDFReadData,
            _bf,
            brd,
            ch,
            index="blah",
            digitizer=digi,
            adc=adc,
            config_name=config_name,
        )

    @with_bf
    def test_read_w_index(self, _bf: File):
        """Test reading data using `index` keyword."""
        # setup
        sn_size = 50
        self.f.add_module("SIS 3301", {"n_configs": 1, "sn_size": sn_size, "nt": 1000})
        _mod = self.f.modules["SIS 3301"]
        digi = "SIS 3301"
        adc = "SIS 3301"
        config_name = _mod.knobs.active_config[0]
        bc_arr = _mod.knobs.active_brdch
        bc_indices = np.where(bc_arr)
        brd = bc_indices[0][0]
        ch = bc_indices[1][0]
        _bf._map_file()  # re-map file
        digi_path = "Raw data + config/SIS 3301"
        dset_name = f"{config_name} [{brd}:{ch}]"
        dset_path = f"{digi_path}/{dset_name}"
        dheader = _bf.get(f"{dset_path} headers")
        shotnumkey = "Shot"

        # -- examine the various `index` types                      ----
        # Note: the scenario where `index` is an invalid type is covered
        #       by `test_raise_errors`
        #
        # `index` is an int
        data = HDFReadData(
            _bf, brd, ch, config_name=config_name, adc=adc, digitizer=digi, index=1
        )
        self.assertDataObj(data, _bf)
        self.assertTrue(np.array_equiv(data["shotnum"], dheader[1, shotnumkey]))

        # `index` is a list
        data = HDFReadData(
            _bf, brd, ch, config_name=config_name, adc=adc, digitizer=digi, index=[1, 5]
        )
        self.assertDataObj(data, _bf)
        self.assertTrue(np.array_equal(data["shotnum"], dheader[[1, 5], shotnumkey]))

        # `index` is a slice object
        data = HDFReadData(
            _bf,
            brd,
            ch,
            config_name=config_name,
            adc=adc,
            digitizer=digi,
            index=slice(4, 10, 3),
        )
        self.assertDataObj(data, _bf)
        self.assertTrue(
            np.array_equal(data["shotnum"], dheader[slice(4, 10, 3), shotnumkey])
        )

        # `index` is a numpy array
        data = HDFReadData(
            _bf,
            brd,
            ch,
            config_name=config_name,
            adc=adc,
            digitizer=digi,
            index=np.array([10, 20, 30]),
        )
        self.assertDataObj(data, _bf)
        self.assertTrue(
            np.array_equal(
                data["shotnum"], dheader[np.array([10, 20, 30]).tolist(), shotnumkey]
            )
        )

        # `index` is an Ellipsis
        data = HDFReadData(
            _bf,
            brd,
            ch,
            config_name=config_name,
            adc=adc,
            digitizer=digi,
            index=np.s_[...],
        )
        self.assertDataObj(data, _bf)
        self.assertTrue(np.array_equal(data["shotnum"], dheader[np.s_[...], shotnumkey]))

        # `index` (and `shotnum`) not defined
        data = HDFReadData(_bf, brd, ch, config_name=config_name, adc=adc, digitizer=digi)
        self.assertDataObj(data, _bf)
        self.assertTrue(np.array_equal(data["shotnum"], dheader[:, shotnumkey]))

        # -- examine handling of negative indices                   ----
        # valid negative index
        data = HDFReadData(
            _bf, brd, ch, config_name=config_name, adc=adc, digitizer=digi, index=[10, -2]
        )
        self.assertDataObj(data, _bf)
        self.assertTrue(
            np.array_equal(
                data["shotnum"], [dheader[10, shotnumkey], dheader[-2, shotnumkey]]
            ),
        )

        # invalid negative index
        with self.assertRaises(IndexError):
            data = HDFReadData(
                _bf,
                brd,
                ch,
                config_name=config_name,
                adc=adc,
                digitizer=digi,
                index=[-sn_size - 10],
            )
            self.assertDataObj(data, _bf)

    @with_bf
    @mock.patch(
        "bapsflib._hdf.utils.hdfreaddata.condition_shotnum", side_effect=condition_shotnum
    )
    @mock.patch(
        "bapsflib._hdf.utils.hdfreaddata.build_sndr_for_simple_dset",
        side_effect=build_sndr_for_simple_dset,
    )
    @mock.patch(
        "bapsflib._hdf.utils.hdfreaddata.do_shotnum_intersection",
        side_effect=do_shotnum_intersection,
    )
    def test_read_w_shotnum(self, _bf: File, mock_inter, mock_build_sndr, mock_cs):
        """Test reading data using `index` keyword."""
        # setup
        sn_size = 50
        self.f.add_module("SIS 3301", {"n_configs": 1, "sn_size": sn_size, "nt": 1000})
        _mod = self.f.modules["SIS 3301"]
        digi = "SIS 3301"
        adc = "SIS 3301"
        config_name = _mod.knobs.active_config[0]
        bc_arr = _mod.knobs.active_brdch
        bc_indices = np.where(bc_arr)
        brd = bc_indices[0][0]
        ch = bc_indices[1][0]
        _bf._map_file()  # re-map file
        digi_path = "Raw data + config/SIS 3301"
        dset_name = f"{config_name} [{brd}:{ch}]"
        dset_path = f"{digi_path}/{dset_name}"
        dset = _bf.get(dset_path)
        dheader = _bf.get(f"{dset_path} headers")
        shotnumkey = "Shot"

        # -- examine the various `shotnum` types                    ----
        # Note: relying on test for `condition_shotnum`,
        #       `build_sndr_for_simple_dset`, and
        #       `do_shotnum_intersection` for detailed behavior and
        #       testing
        #
        # `shotnum` is an int
        shotnum = 5
        indices = [4]
        data = HDFReadData(
            _bf,
            brd,
            ch,
            config_name=config_name,
            adc=adc,
            digitizer=digi,
            shotnum=shotnum,
        )
        self.assertDataObj(data, _bf)
        self.assertTrue(np.array_equiv(data["shotnum"], np.array([5], dtype=np.uint32)))
        self.assertDataArrayValues(data, dset, indices)
        self.assertTrue(mock_build_sndr.called)
        self.assertTrue(mock_cs.called)
        self.assertTrue(mock_inter.called)
        mock_build_sndr.reset_mock()
        mock_cs.reset_mock()
        mock_inter.reset_mock()

        # `shotnum` is a list
        shotnum = [-10, 50]
        indices = [49]
        data = HDFReadData(
            _bf,
            brd,
            ch,
            config_name=config_name,
            adc=adc,
            digitizer=digi,
            shotnum=shotnum,
        )
        self.assertDataObj(data, _bf)
        self.assertTrue(np.array_equal(data["shotnum"], np.array([50], dtype=np.uint32)))
        self.assertDataArrayValues(data, dset, indices)
        self.assertTrue(mock_build_sndr.called)
        self.assertTrue(mock_cs.called)
        self.assertTrue(mock_inter.called)
        mock_build_sndr.reset_mock()
        mock_cs.reset_mock()
        mock_inter.reset_mock()

        # `shotnum` is a slice object
        shotnum = slice(5, 10, 2)
        indices = [4, 6, 8]
        data = HDFReadData(
            _bf,
            brd,
            ch,
            config_name=config_name,
            adc=adc,
            digitizer=digi,
            shotnum=shotnum,
        )
        self.assertDataObj(data, _bf)
        self.assertTrue(
            np.array_equal(data["shotnum"], np.array([5, 7, 9], dtype=np.uint32))
        )
        self.assertDataArrayValues(data, dset, indices)
        self.assertTrue(mock_build_sndr.called)
        self.assertTrue(mock_cs.called)
        self.assertTrue(mock_inter.called)
        mock_build_sndr.reset_mock()
        mock_cs.reset_mock()
        mock_inter.reset_mock()

        # `shotnum` is a numpy array
        shotnum = np.arange(1, 10, 3)
        indices = np.array(shotnum - 1).tolist()  # type: list
        data = HDFReadData(
            _bf,
            brd,
            ch,
            config_name=config_name,
            adc=adc,
            digitizer=digi,
            shotnum=shotnum,
        )
        self.assertDataObj(data, _bf)
        self.assertTrue(
            np.array_equal(data["shotnum"], np.arange(1, 10, 3, dtype=np.uint32))
        )
        self.assertDataArrayValues(data, dset, indices)
        self.assertTrue(mock_build_sndr.called)
        self.assertTrue(mock_cs.called)
        self.assertTrue(mock_inter.called)
        mock_build_sndr.reset_mock()
        mock_cs.reset_mock()
        mock_inter.reset_mock()

    def assertControlInData(
        self, cdata: HDFReadControls, data: HDFReadData, shotnum: np.ndarray
    ):

        # -- analyze numpy array                                    ----
        self.assertTrue(np.array_equal(data["shotnum"], shotnum))
        self.assertTrue(np.any(np.isin(shotnum, cdata["shotnum"])))

        mask = np.isin(cdata["shotnum"], data["shotnum"])
        self.assertTrue(np.all(mask))

        for field in cdata.dtype.names:
            self.assertIn(field, data.dtype.names)
            self.assertTrue(
                np.issubdtype(cdata.dtype[field].base, data.dtype[field].base)
            )
            self.assertEqual(cdata.dtype[field].shape, data.dtype[field].shape)

            if field == "shotnum":
                continue
            else:
                data_nan_mask = np.isnan(data[field])
                cdata_nan_mask = np.isnan(cdata[field])

                if np.any(data_nan_mask):
                    self.assertTrue(np.array_equal(data_nan_mask, cdata_nan_mask))
                    self.assertTrue(
                        np.array_equal(
                            cdata[field][np.logical_not(cdata_nan_mask)],
                            data[field][np.logical_not(data_nan_mask)],
                        )
                    )
                else:
                    self.assertTrue(np.array_equal(cdata[field], data[field]))

        # -- analyze `info` attribute                               ----
        self.assertEqual(data.info["controls"], cdata.info["controls"])

    def assertDataArrayValues(
        self, data: HDFReadData, dset: h5py.Dataset, indices: list, keep_bits=False
    ):
        """Assert the correct 'signal' values were added."""
        dv = data.dv.value
        offset = abs(data.info["voltage offset"].value)

        dset_arr = dset[indices, ...]
        if not keep_bits:
            dset_arr = dset_arr.astype(np.float32)
            dset_arr = (dv * dset_arr) - offset

        self.assertTrue(np.array_equal(data["signal"], dset_arr))

    def assertDataInfo(self, data, _bf):
        """
        Assertions for the `info` attribute bound to the returned data
        object.
        """
        # check types
        self.assertIsInstance(data.info, dict)
        self.assertIsInstance(type(data).info, property)

        # required keys
        keys = (
            "adc",
            "bit",
            "board",
            "channel",
            "clock rate",
            "configuration name",
            "controls",
            "device dataset path",
            "device group path",
            "digitizer",
            "port",
            "probe name",
            "sample average",
            "shot average",
            "signal units",
            "source file",
            "voltage offset",
        )
        for key in keys:
            self.assertIn(key, data.info)

            if key == "source file":
                self.assertEqual(data.info[key], os.path.abspath(_bf.filename))
            elif key in ("bit", "sample average", "shot average"):
                self.assertIsInstance(data.info[key], (type(None), int, np.integer))
            elif key in ("board", "channel"):
                self.assertIsInstance(data.info[key], (int, np.integer))
            elif key in (
                "adc",
                "configuration name",
                "device dataset path",
                "device group path",
                "digitizer",
            ):
                self.assertIsInstance(data.info[key], str)
            elif key == "controls":
                self.assertIsInstance(data.info[key], dict)
            elif key == "signal units":
                self.assertIsInstance(data.info[key], u.UnitBase)
            elif key == "voltage offset":
                self.assertIsInstance(data.info[key], (type(None), u.Quantity))

    def assertDataObj(
        self, data: HDFReadData, _bf: File, motion_added=False, keep_bits=False
    ):
        """Assertion for detailed format of returned data object."""
        # data is a structured numpy array
        self.assertIsInstance(data, np.ndarray)
        self.assertIsInstance(data, HDFReadData)

        # attribute existence
        self.assertTrue(hasattr(data, "dt"))
        self.assertTrue(hasattr(data, "dv"))
        self.assertTrue(hasattr(data, "info"))

        # -- check `info`                                           ----
        self.assertDataInfo(data, _bf)

        # -- check `dt`                                             ----
        self.assertIsInstance(type(data).dt, property)
        self.assertIsInstance(data.dt, (type(None), u.Quantity))

        # -- check `dv`                                             ----
        self.assertIsInstance(type(data).dv, property)
        self.assertIsInstance(data.dv, (type(None), u.Quantity))

        # -- examine data array                                     ----
        for field in ("shotnum", "signal", "xyz"):
            self.assertIn(field, data.dtype.names)

            if field == "shotnum":
                self.assertEqual(data.dtype["shotnum"].base, np.uint32)
                self.assertEqual(data.dtype["shotnum"].shape, ())
            elif field == "signal":
                self.assertEqual(data.dtype["signal"].ndim, 1)

                if keep_bits:
                    self.assertTrue(np.issubdtype(data.dtype["signal"].base, np.integer))
                else:
                    self.assertTrue(np.issubdtype(data.dtype["signal"].base, np.floating))

            elif field == "xyz":
                self.assertTrue(np.issubdtype(data.dtype["xyz"].base, np.floating))
                self.assertEqual(data.dtype["xyz"].shape, (3,))

                if motion_added is False:
                    self.assertTrue(np.all(np.isnan(data["xyz"])))


if __name__ == "__main__":
    ut.main()
