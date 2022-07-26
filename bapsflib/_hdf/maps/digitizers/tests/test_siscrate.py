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
import numpy as np
import unittest as ut

from typing import List, Tuple
from unittest import mock

from bapsflib._hdf.maps.digitizers.siscrate import HDFMapDigiSISCrate
from bapsflib._hdf.maps.digitizers.tests.common import DigitizerTestCase
from bapsflib.utils.exceptions import HDFMappingError


class TestSISCrate(DigitizerTestCase):
    """Test class for HDFMapDigiSISCrate"""

    # TODO: write a test for an active board with no active channels
    #       will likely need modification to
    #       `bapsflib._hdf.maps.digitizers.tests.fauxsiscrate.FauxSISCrate`.

    DEVICE_NAME = "SIS crate"
    DEVICE_PATH = f"/Raw data + config/{DEVICE_NAME}"
    MAP_CLASS = HDFMapDigiSISCrate

    def setUp(self):
        super().setUp()

    def tearDown(self):
        super().tearDown()

    def test_construct_dataset_name(self):
        """Test functionality of method `construct_dataset_name`"""
        # setup
        config_name = "config01"
        adc = "SIS 3302"
        # config_path = 'Configuration: {}'.format(config_name)
        my_sabc = [
            (5, adc, 1, (1, 3, 5)),
            (9, adc, 3, (1, 2, 3, 4)),
            (11, adc, 4, (5, 6, 7)),
        ]  # type: List[Tuple[int, str, int, Tuple[int, ...]]]
        dtype = self.mod.knobs.active_brdch.dtype
        bc_arr = np.zeros((), dtype=dtype)
        for slot, adc, brd, chns in my_sabc:
            for ch in chns:
                bc_arr[adc][brd - 1][ch - 1] = True
        self.mod.knobs.n_configs = 2
        self.mod.knobs.active_brdch = bc_arr

        # -- Handling of kwarg `config_name`                        ----
        # not specified, and only ONE active config
        slot = my_sabc[0][0]
        adc = my_sabc[0][1]
        brd = my_sabc[0][2]
        ch = my_sabc[0][3][0]
        dset_name = f"{config_name} [Slot {slot}: SIS 3302 ch {ch}]"
        with self.assertWarns(UserWarning):
            self.assertEqual(self.map.construct_dataset_name(brd, ch), dset_name)

        # not specified, and MULTIPLE active configs
        slot = my_sabc[0][0]
        adc = my_sabc[0][1]
        brd = my_sabc[0][2]
        ch = my_sabc[0][3][0]
        self.mod.knobs.active_config = (config_name, "config02")
        self.assertRaises(ValueError, self.map.construct_dataset_name, brd, ch)
        self.mod.knobs.active_config = config_name

        # not specified, and NO active configs
        slot = my_sabc[0][0]
        adc = my_sabc[0][1]
        brd = my_sabc[0][2]
        ch = my_sabc[0][3][0]
        _map = self.map
        with mock.patch.object(
            HDFMapDigiSISCrate, "active_configs", new_callable=mock.PropertyMock
        ) as mock_aconfig:
            mock_aconfig.return_value = []
            self.assertRaises(ValueError, _map.construct_dataset_name, brd, ch)

        # `config_name` not in configs
        slot = my_sabc[0][0]
        adc = my_sabc[0][1]
        brd = my_sabc[0][2]
        ch = my_sabc[0][3][0]
        self.assertRaises(
            ValueError,
            self.map.construct_dataset_name,
            brd,
            ch,
            config_name="not a config",
        )

        # `config_name` in configs but not active
        slot = my_sabc[0][0]
        adc = my_sabc[0][1]
        brd = my_sabc[0][2]
        ch = my_sabc[0][3][0]
        self.assertRaises(
            ValueError, self.map.construct_dataset_name, brd, ch, config_name="config02"
        )

        # -- Handling of kwarg `adc`                                ----
        # `adc` not 'SIS 3302' or 'SIS 3305'
        slot = my_sabc[0][0]
        adc = my_sabc[0][1]
        brd = my_sabc[0][2]
        ch = my_sabc[0][3][0]
        self.assertRaises(
            ValueError, self.map.construct_dataset_name, brd, ch, adc="not a real SIS"
        )

        # `adc` is None and there's only ONE active adc
        slot = my_sabc[0][0]
        adc = my_sabc[0][1]
        brd = my_sabc[0][2]
        ch = my_sabc[0][3][0]
        dset_name = f"{config_name} [Slot {slot}: SIS 3302 ch {ch}]"
        with self.assertWarns(UserWarning):
            self.assertEqual(_map.construct_dataset_name(brd, ch), dset_name)

        # `adc` is None and there's TWO active adc
        my_sabc = [
            (5, adc, 1, (1, 3, 5)),
            (9, adc, 3, (1, 2, 3, 4)),
            (13, "SIS 3305", 1, (2, 6, 7)),
        ]  # type: List[Tuple[int, str, int, Tuple[int, ...]]]
        dtype = self.mod.knobs.active_brdch.dtype
        bc_arr = np.zeros((), dtype=dtype)
        for slot, adc, brd, chns in my_sabc:
            for ch in chns:
                bc_arr[adc][brd - 1][ch - 1] = True
        self.mod.knobs.n_configs = 2
        self.mod.knobs.active_brdch = bc_arr
        slot = my_sabc[0][0]
        adc = my_sabc[0][1]
        brd = my_sabc[0][2]
        ch = my_sabc[0][3][0]
        dset_name = f"{config_name} [Slot {slot}: SIS 3302 ch {ch}]"
        with self.assertWarns(UserWarning):
            self.assertEqual(self.map.construct_dataset_name(brd, ch), dset_name)

        # -- `board` and `channel` combo not in configs             ----
        brd = 5  # SIS 3302 only goes up to board 4
        ch = 1
        self.assertRaises(ValueError, self.map.construct_dataset_name, brd, ch)

        # -- calls to SIS 3305                                      ----
        # a channel that is on FPGA 1
        slot = my_sabc[2][0]
        adc = my_sabc[2][1]
        brd = my_sabc[2][2]
        ch = my_sabc[2][3][0]
        dset_name = f"{config_name} [Slot {slot}: SIS 3305 FPGA 1 ch {ch}]"
        self.assertEqual(
            self.map.construct_dataset_name(brd, ch, config_name=config_name, adc=adc),
            dset_name,
        )

        # a channel that is on FPGA 2
        slot = my_sabc[2][0]
        adc = my_sabc[2][1]
        brd = my_sabc[2][2]
        ch = my_sabc[2][3][-1]
        dset_name = f"{config_name} [Slot {slot}: SIS 3305 FPGA 2 ch {ch-4}]"
        self.assertEqual(
            self.map.construct_dataset_name(brd, ch, config_name=config_name, adc=adc),
            dset_name,
        )

        # -- return when `return_info=True`                         ----
        slot = my_sabc[0][0]
        adc = my_sabc[0][1]
        brd = my_sabc[0][2]
        ch = my_sabc[0][3][0]
        dset_name = f"{config_name} [Slot {slot}: SIS 3302 ch {ch}]"
        _map = self.map
        d_info = {}
        for conn in _map.configs[config_name][adc]:
            if brd == conn[0] and ch in conn[1]:
                d_info = conn[2]
                break

        # get dset_name
        val = _map.construct_dataset_name(brd, ch, return_info=True)

        self.assertIsInstance(val, tuple)
        self.assertEqual(len(val), 2)

        # first element is dataset name
        self.assertEqual(val[0], dset_name)

        # second element is dataset info
        self.assertIsInstance(val[1], dict)
        keys = (
            "adc",
            "bit",
            "clock rate",
            "configuration name",
            "digitizer",
            "nshotnum",
            "nt",
            "sample average (hardware)",
            "shot average (software)",
        )
        for key in keys:
            self.assertIn(key, val[1])

            if key == "adc":
                self.assertEqual(val[1][key], adc)
            elif key == "configuration name":
                self.assertEqual(val[1][key], config_name)
            elif key == "digitizer":
                self.assertEqual(val[1][key], _map.info["group name"])
            else:
                self.assertEqual(val[1][key], d_info[key])

    def test_construct_header_dataset_name(self):
        """
        Test functionality of method `construct_header_dataset_name`
        """
        # setup:
        config_name = "config01"
        adc = "SIS 3302"
        # config_path = 'Configuration: {}'.format(config_name)
        my_sabc = [
            (5, adc, 1, (1, 3, 5)),
            (9, adc, 3, (1, 2, 3, 4)),
            (11, adc, 4, (5, 6, 7)),
        ]  # type: List[Tuple[int, str, int, Tuple[int, ...]]]
        dtype = self.mod.knobs.active_brdch.dtype
        bc_arr = np.zeros((), dtype=dtype)
        for slot, adc, brd, chns in my_sabc:
            for ch in chns:
                bc_arr[adc][brd - 1][ch - 1] = True
        self.mod.knobs.n_configs = 2
        self.mod.knobs.active_brdch = bc_arr

        # `return_info` does NOT return extra info
        slot = my_sabc[0][0]
        adc = my_sabc[0][1]
        brd = my_sabc[0][2]
        ch = my_sabc[0][3][0]
        dset_name = f"{config_name} [Slot {slot}: SIS 3302 ch {ch}]"
        hdset_name = f"{dset_name} headers"
        _map = self.map
        with mock.patch.object(
            HDFMapDigiSISCrate,
            "construct_dataset_name",
            wraps=_map.construct_dataset_name,
        ) as mock_cdn:

            name = _map.construct_header_dataset_name(brd, ch, return_info=True)

            # check `construct_dataset_name` was called
            self.assertTrue(mock_cdn.called)

            # check equality
            self.assertEqual(name, hdset_name)

    def test_map_failures(self):
        """Test scenarios that should raise HDFMappingError"""
        # 1. defined configuration slot numbers and indices are not 1D
        #    arrays
        # 2. define slot numbers and configuration indices are not the
        #    same size
        # 3. defined slot numbers are not unique
        # 4. for active config, configuration index is assigned to
        #    multiple slots for the same adc
        # 5. group has no identifiable configuration group
        # 6. none of the configurations are active
        # 7. for active config, no adc's identified
        # 8. adc connections for active config are NULL
        #
        # setup faux group
        config_name = "config01"
        config_path = config_name
        adc = "SIS 3302"
        my_sabc = [
            (5, adc, 1, (1, 3, 5)),
            (9, adc, 3, (1, 2, 3, 4)),
            (11, adc, 4, (5, 6, 7)),
        ]  # type: List[Tuple[int, str, int, Tuple[int, ...]]]
        dtype = self.mod.knobs.active_brdch.dtype
        bc_arr = np.zeros((), dtype=dtype)
        for slot, adc, brd, chns in my_sabc:
            for ch in chns:
                bc_arr[adc][brd - 1][ch - 1] = True
        self.mod.knobs.active_brdch = bc_arr

        # -- failures that occur in `_find_adc_connections`         ----
        # defined configuration slot and indices are not 1D arrays   (1)
        cgroup = self.dgroup[config_path]
        slots = cgroup.attrs["SIS crate slot numbers"]
        indices = cgroup.attrs["SIS crate config indices"]
        cgroup.attrs["SIS crate slot numbers"] = np.zeros((2, 3), dtype=np.uint32)
        with self.assertRaises(HDFMappingError):
            _map = self.map
        cgroup.attrs["SIS crate slot numbers"] = slots
        cgroup.attrs["SIS crate config indices"] = np.zeros((2, 3), dtype=np.uint32)
        with self.assertRaises(HDFMappingError):
            _map = self.map
        cgroup.attrs["SIS crate config indices"] = indices

        # defined slot numbers and configuration indices are not     (2)
        # the same size
        cgroup.attrs["SIS crate slot numbers"] = np.append(slots, [13])
        with self.assertRaises(HDFMappingError):
            _map = self.map
        cgroup.attrs["SIS crate slot numbers"] = slots

        # defined slot numbers are not unique                        (3)
        slots2 = slots.copy()
        slots2[-1] = slots2[0]
        cgroup.attrs["SIS crate slot numbers"] = slots2
        with self.assertRaises(HDFMappingError):
            _map = self.map
        cgroup.attrs["SIS crate slot numbers"] = slots

        # for active config, configuration index is assigned to      (4)
        # multiple slots for the same adc
        cgroup = self.dgroup[config_path]
        indices = cgroup.attrs["SIS crate config indices"]
        wrong_ii = indices.copy()
        wrong_ii[2] = indices[1]
        cgroup.attrs["SIS crate config indices"] = wrong_ii
        with self.assertRaises(HDFMappingError):
            _map = self.map
        cgroup.attrs["SIS crate config indices"] = indices

        # -- failures that occur in `_build_configs`                ----
        # group had no identifiable configuration group              (5)
        slots = cgroup.attrs["SIS crate slot numbers"]
        del cgroup.attrs["SIS crate slot numbers"]
        with self.assertRaises(HDFMappingError):
            _map = self.map
        cgroup.attrs["SIS crate slot numbers"] = slots

        # none of the configurations are active                      (6)
        self.dgroup.move(config_path, "Not used")
        with self.assertRaises(HDFMappingError):
            _map = self.map
        self.dgroup.move("Not used", config_path)

        # for active config, no adc's identified                     (7)
        brd_types = cgroup.attrs["SIS crate board types"]  # type: np.ndarray
        cgroup.attrs["SIS crate board types"] = np.array(
            [5] * brd_types.size, dtype=brd_types.dtype
        )
        with self.assertRaises(HDFMappingError):
            _map = self.map
        cgroup.attrs["SIS crate board types"] = brd_types

        # adc connections for active config are NULL                 (8)
        names = list(cgroup)
        for name in names:
            del cgroup[name]
        with self.assertRaises(HDFMappingError):
            _map = self.map

    def test_map_warnings(self):
        """Test scenarios that should cause a UserWarning."""
        # 1.  configuration group defines unexpected/unknown slot
        #     number
        # 2.  for inactive config, configuration index is assigned to
        #     multiple slots for the same adc
        # 3.  top-level configuration group defines a configuration
        #     index that does not have an associated sub-group adc
        #     configuration
        # 4.  adc configuration group has a configuration index that
        #     is NOT defined in the top-level configuration group
        # 5.  adc configuration sub-group defines a NULL list of
        #     channels
        # 6.  adc 'SIS 3305' configuration group is missing the
        #     'Channel mode' attribute
        # 7.  adc 'SIS 3303' configuration group defines a none integer
        #     'Channel mode' attribute
        # 8.  an expected dataset is missing
        # 9.  all expected datasets for a board are missing
        # 10. dataset has fields
        # 11. dataset is not a 2D array
        # 12. number of dataset time samples not consistent for all
        #     channels connected to a board
        # 13. number of dataset shot numbers not consistent for all
        #     channels connect to a board, but are still consistent
        #     with their associated header dataset
        # 14. header dataset missing expected shot number field
        # 15. shot number field in header dataset does not have
        #     expected shape and/or dtype
        # 16. dataset and associated header dataset do not have same
        #     number of shot numbers
        # 17. after all the above checks, ensure the connected channels
        #     are not NULL for the board
        #
        # setup group
        config_name = "config01"
        config_path = config_name
        self.mod.knobs.n_configs = 2
        self.mod.knobs.active_config = config_name
        adc = "SIS 3302"
        my_sabc = [
            (5, adc, 1, (1, 3, 5)),
            (9, adc, 3, (1, 2, 3, 4)),
            (11, adc, 4, (5, 6, 7)),
        ]  # type: List[Tuple[int, str, int, Tuple[int, ...]]]
        dtype = self.mod.knobs.active_brdch.dtype
        bc_arr = np.zeros((), dtype=dtype)
        for slot, adc, brd, chns in my_sabc:
            for ch in chns:
                bc_arr[adc][brd - 1][ch - 1] = True
        self.mod.knobs.active_brdch = bc_arr

        # -- warnings that occur in `_find_adc_connections`         ----
        # configuration group defines an unexpected/unknown          (1)
        # slot number
        # - this will also trigger #3
        cgroup = self.dgroup[config_path]
        slots = cgroup.attrs["SIS crate slot numbers"]
        wrong_ss = slots.copy()
        wrong_ss[2] = 5000
        cgroup.attrs["SIS crate slot numbers"] = wrong_ss
        with self.assertWarns(UserWarning):
            _map = self.map
        cgroup.attrs["SIS crate slot numbers"] = slots

        # for inactive config, configuration index is assigned       (2)
        # to multiple slots for the same adc
        cgroup = self.dgroup["config02"]
        indices = cgroup.attrs["SIS crate config indices"]
        wrong_ii = indices.copy()
        wrong_ii[2] = indices[1]
        cgroup.attrs["SIS crate config indices"] = wrong_ii
        with self.assertWarns(UserWarning):
            _map = self.map
            self.assertEqual(_map.configs["config02"][adc], ())
        cgroup.attrs["SIS crate config indices"] = indices

        # top-level configuration group defines a configuration      (3)
        # index that does not have an associated sub-group
        # adc configuration
        # - same code-block is triggered by #4
        cgroup = self.dgroup[config_path]
        slot = cgroup.attrs["SIS crate slot numbers"][-1]
        indices = cgroup.attrs["SIS crate config indices"]
        wrong_ii = indices.copy()
        wrong_ii[-1] = 5
        cgroup.attrs["SIS crate config indices"] = wrong_ii
        with self.assertWarns(UserWarning):
            _map = self.map  # type: HDFMapDigiSISCrate
            brd = _map.slot_info[slot][0]
            self.assertTrue(
                all(brd != conn[0] for conn in _map.configs[config_name][adc])
            )
        cgroup.attrs["SIS crate config indices"] = indices

        # adc configuration group has a configuration index that     (4)
        # is NOT defined in the top-level configuration group
        # - same code-block is triggered by #3
        cgroup = self.dgroup[config_path]
        cgroup.create_group("SIS crate 3302 configurations[5]")
        with self.assertWarns(UserWarning):
            _map = self.map
        del cgroup["SIS crate 3302 configurations[5]"]

        # adc configuration sub-group defines a NULL list            (5)
        # of channels
        brd = my_sabc[0][2]
        adc_config_name = "SIS crate 3302 configurations[0]"
        cgroup = self.dgroup[config_path]
        adc_group = cgroup[adc_config_name]
        save = []
        for ii in range(1, 9):
            attr_name = f"Enabled {ii}"
            save.append(adc_group.attrs[attr_name])
            adc_group.attrs[attr_name] = np.bytes_("FALSE")
        with self.assertWarns(UserWarning):
            _map = self.map

            self.assertTrue(
                all(brd != conn[0] for conn in _map.configs[config_name][adc])
            )
        for ii in range(1, 9):
            attr_name = f"Enabled {ii}"
            adc_group.attrs[attr_name] = save[ii - 1]

        # setup a 'SIS 3305' connection
        config_name = "config01"
        config_path = config_name
        self.mod.knobs.n_configs = 2
        self.mod.knobs.active_config = config_name
        adc = "SIS 3305"
        my_sabc = [
            (13, adc, 1, (1, 3, 5)),
            (15, adc, 2, (1, 2, 3, 4)),
        ]  # type: List[Tuple[int, str, int, Tuple[int, ...]]]
        dtype = self.mod.knobs.active_brdch.dtype
        bc_arr = np.zeros((), dtype=dtype)
        for slot, adc, brd, chns in my_sabc:
            for ch in chns:
                bc_arr[adc][brd - 1][ch - 1] = True
        self.mod.knobs.active_brdch = bc_arr

        # adc 'SIS 3305' configuration group is missing the          (6)
        # 'Channel mode' attribute
        brd = my_sabc[0][2]
        adc_config_name = "SIS crate 3305 configurations[0]"
        cgroup = self.dgroup[config_path]
        adc_group = cgroup[adc_config_name]
        cr_mode = adc_group.attrs["Channel mode"]
        del adc_group.attrs["Channel mode"]
        with self.assertWarns(UserWarning):
            _map = self.map

            conns = _map.configs[config_name][adc]
            self.assertIn(brd, [conn[0] for conn in conns])

            for conn in conns:
                if brd == conn[0]:
                    self.assertIsNone(conn[2]["clock rate"])

        # adc 'SIS 3305' configuration group defines a none          (7)
        # integer 'Channel mode' attribute
        adc_group.attrs["Channel mode"] = np.bytes_("five")
        with self.assertWarns(UserWarning):
            _map = self.map

            conns = _map.configs[config_name][adc]
            self.assertIn(brd, [conn[0] for conn in conns])

            for conn in conns:
                if brd == conn[0]:
                    self.assertIsNone(conn[2]["clock rate"])
        adc_group.attrs["Channel mode"] = cr_mode

        # -- warnings that occur in `_adc_info_first_pass`          ----
        # * none are defined, all warnings are issued when
        #   `_find_adc_connections` is called

        # -- warnings that occur in `_adc_info_second_pass`         ----
        # setup (back to SIS 3302)
        config_name = "config01"
        config_path = config_name
        self.mod.knobs.n_configs = 2
        self.mod.knobs.active_config = config_name
        adc = "SIS 3302"
        my_sabc = [
            (5, adc, 1, (1, 3, 5)),
            (9, adc, 3, (1, 2, 3, 4)),
            (11, adc, 4, (5, 6, 7)),
        ]  # type: List[Tuple[int, str, int, Tuple[int, ...]]]
        dtype = self.mod.knobs.active_brdch.dtype
        bc_arr = np.zeros((), dtype=dtype)
        for slot, adc, brd, chns in my_sabc:
            for ch in chns:
                bc_arr[adc][brd - 1][ch - 1] = True
        self.mod.knobs.active_brdch = bc_arr

        # an expected dataset is missing                             (8)
        slot = my_sabc[0][0]
        brd = my_sabc[0][2]
        ch = my_sabc[0][3][0]
        dset_name = f"{config_name} [Slot {slot}: SIS 3302 ch {ch}]"
        new_name = dset_name + "Q"
        self.dgroup.move(dset_name, new_name)
        with self.assertWarns(UserWarning):
            _map = self.map

            chs = None
            for conn in _map.configs[config_name][adc]:
                if conn[0] == brd:
                    chs = conn[1]

            if chs is None:
                self.fail("board missing from connections")
            else:
                self.assertNotIn(ch, chs)
        self.dgroup.move(new_name, dset_name)

        # all expected datasets for a board are missing              (9)
        slot = my_sabc[0][0]
        brd = my_sabc[0][2]
        chs = my_sabc[0][3]
        for ch in chs:
            dset_name = f"{config_name} [Slot {slot}: SIS 3302 ch {ch}]"
            new_name = dset_name + "Q"
            self.dgroup.move(dset_name, new_name)
        with self.assertWarns(UserWarning):
            _map = self.map

            self.assertNotIn(brd, [conn[0] for conn in _map.configs[config_name][adc]])
        for ch in chs:
            dset_name = f"{config_name} [Slot {slot}: SIS 3302 ch {ch}]"
            new_name = dset_name + "Q"
            self.dgroup.move(new_name, dset_name)

        # dataset has fields                                        (10)
        slot = my_sabc[0][0]
        brd = my_sabc[0][2]
        ch = my_sabc[0][3][0]
        dset_name = f"{config_name} [Slot {slot}: SIS 3302 ch {ch}]"
        new_name = dset_name + "Q"
        self.dgroup.move(dset_name, new_name)
        data = np.empty(3, dtype=[("f1", np.int16), ("f2", np.int16)])
        self.dgroup.create_dataset(dset_name, data=data)
        with self.assertWarns(UserWarning):
            _map = self.map

            chs = None
            for conn in _map.configs[config_name][adc]:
                if conn[0] == brd:
                    chs = conn[1]

            if chs is None:
                self.fail("board missing from connections")
            else:
                self.assertNotIn(ch, chs)
        del self.dgroup[dset_name]
        self.dgroup.move(new_name, dset_name)

        # dataset has fields                                        (11)
        slot = my_sabc[0][0]
        brd = my_sabc[0][2]
        ch = my_sabc[0][3][0]
        dset_name = f"{config_name} [Slot {slot}: SIS 3302 ch {ch}]"
        new_name = dset_name + "Q"
        self.dgroup.move(dset_name, new_name)
        data = np.empty((3, 100, 3), dtype=np.int16)
        self.dgroup.create_dataset(dset_name, data=data)
        with self.assertWarns(UserWarning):
            _map = self.map

            chs = None
            for conn in _map.configs[config_name][adc]:
                if conn[0] == brd:
                    chs = conn[1]

            if chs is None:
                self.fail("board missing from connections")
            else:
                self.assertNotIn(ch, chs)
        del self.dgroup[dset_name]
        self.dgroup.move(new_name, dset_name)

        # number of dataset time samples not consistent for all     (12)
        # channels connected to a board
        slot = my_sabc[0][0]
        brd = my_sabc[0][2]
        ch = my_sabc[0][3][0]
        dset_name = f"{config_name} [Slot {slot}: SIS 3302 ch {ch}]"
        new_name = dset_name + "Q"
        self.dgroup.move(dset_name, new_name)
        dset = self.dgroup[new_name]
        data = np.empty((dset.shape[0], dset.shape[1] + 1), dtype=dset.dtype)
        self.dgroup.create_dataset(dset_name, data=data)
        with self.assertWarns(UserWarning):
            _map = self.map

            chs = None
            for conn in _map.configs[config_name][adc]:
                if conn[0] == brd:
                    chs = conn[1]

                    # nt is set to -1
                    self.assertEqual(conn[2]["nt"], -1)

            # channel still in mapping
            if chs is None:
                self.fail("board missing from connections")
            else:
                self.assertIn(ch, chs)
        del self.dgroup[dset_name]
        self.dgroup.move(new_name, dset_name)

        # number of dataset shot numbers not consistent for all     (13)
        # channels connected to a board, but are still consistent,
        # with their associated header dataset
        slot = my_sabc[0][0]
        brd = my_sabc[0][2]
        ch = my_sabc[0][3][0]
        dset_name = f"{config_name} [Slot {slot}: SIS 3302 ch {ch}]"
        hdset_name = f"{dset_name} headers"
        data = self.dgroup[dset_name][...]
        hdata = self.dgroup[hdset_name][...]
        data2 = np.append(data, data[-2::, ...], axis=0)
        hdata2 = np.append(hdata, hdata[-2::, ...], axis=0)
        self.dgroup.move(dset_name, dset_name + "Q")
        self.dgroup.move(hdset_name, hdset_name + "Q")
        self.dgroup.create_dataset(dset_name, data=data2)
        self.dgroup.create_dataset(hdset_name, data=hdata2)
        with self.assertWarns(UserWarning):
            _map = self.map

            chs = None
            for conn in _map.configs[config_name][adc]:
                if conn[0] == brd:
                    chs = conn[1]

                    # nshotnum is set to -1
                    self.assertEqual(conn[2]["nshotnum"], -1)

            # channel still in mapping
            if chs is None:
                self.fail("board missing from connections")
            else:
                self.assertIn(ch, chs)
        del self.dgroup[dset_name]
        del self.dgroup[hdset_name]
        self.dgroup.move(dset_name + "Q", dset_name)
        self.dgroup.move(hdset_name + "Q", hdset_name)

        # header dataset missing expected shot number field         (14)
        slot = my_sabc[0][0]
        brd = my_sabc[0][2]
        ch = my_sabc[0][3][0]
        dset_name = f"{config_name} [Slot {slot}: SIS 3302 ch {ch}]"
        hdset_name = f"{dset_name} headers"
        hdata = self.dgroup[hdset_name][...]
        names = list(hdata.dtype.names)
        names.remove("Shot number")
        hdata2 = hdata[names]
        self.dgroup.move(hdset_name, hdset_name + "Q")
        self.dgroup.create_dataset(hdset_name, data=hdata2)
        with self.assertWarns(UserWarning):
            _map = self.map

            chs = None
            for conn in _map.configs[config_name][adc]:
                if conn[0] == brd:
                    chs = conn[1]

            # channel not in mapping
            if chs is None:
                self.fail("board missing from connections")
            else:
                self.assertNotIn(ch, chs)
        del self.dgroup[hdset_name]
        self.dgroup.move(hdset_name + "Q", hdset_name)

        # shot number field in header dataset does not have         (15)
        # expected shape and/or dtype
        slot = my_sabc[0][0]
        brd = my_sabc[0][2]
        ch = my_sabc[0][3][0]
        dset_name = f"{config_name} [Slot {slot}: SIS 3302 ch {ch}]"
        hdset_name = f"{dset_name} headers"
        hdata = self.dgroup[hdset_name][...]
        self.dgroup.move(hdset_name, hdset_name + "Q")

        # wrong dtype
        hdata2 = np.empty(hdata.shape, dtype=[("Shot number", np.float32)])
        self.dgroup.create_dataset(hdset_name, data=hdata2)
        with self.assertWarns(UserWarning):
            _map = self.map

            chs = None
            for conn in _map.configs[config_name][adc]:
                if conn[0] == brd:
                    chs = conn[1]

            # channel not in mapping
            if chs is None:
                self.fail("board missing from connections")
            else:
                self.assertNotIn(ch, chs)
        del self.dgroup[hdset_name]

        # wrong shape
        hdata2 = np.empty(hdata.shape, dtype=[("Shot number", np.uint32, 2)])
        self.dgroup.create_dataset(hdset_name, data=hdata2)
        with self.assertWarns(UserWarning):
            _map = self.map

            chs = None
            for conn in _map.configs[config_name][adc]:
                if conn[0] == brd:
                    chs = conn[1]

            # channel not in mapping
            if chs is None:
                self.fail("board missing from connections")
            else:
                self.assertNotIn(ch, chs)
        del self.dgroup[hdset_name]
        self.dgroup.move(hdset_name + "Q", hdset_name)

        # dataset and associated header dataset do not have         (16)
        # same number of shot numbers
        slot = my_sabc[0][0]
        brd = my_sabc[0][2]
        ch = my_sabc[0][3][0]
        dset_name = f"{config_name} [Slot {slot}: SIS 3302 ch {ch}]"
        hdset_name = f"{dset_name} headers"
        hdata = self.dgroup[hdset_name][...]
        hdata2 = np.append(hdata, hdata[-2::, ...], axis=0)
        self.dgroup.move(hdset_name, hdset_name + "Q")
        self.dgroup.create_dataset(hdset_name, data=hdata2)
        with self.assertWarns(UserWarning):
            _map = self.map

            chs = None
            for conn in _map.configs[config_name][adc]:
                if conn[0] == brd:
                    chs = conn[1]

            # channel not in mapping
            if chs is None:
                self.fail("board missing from connections")
            else:
                self.assertNotIn(ch, chs)
        del self.dgroup[hdset_name]
        self.dgroup.move(hdset_name + "Q", hdset_name)

        # after all the above checks, ensure the connected          (17)
        # channels are not NULL for the board
        # i.e. this could happen if all the header datasets for a
        #      given board are missing the shot number field
        slot = my_sabc[0][0]
        brd = my_sabc[0][2]
        chs = my_sabc[0][3]
        for ch in chs:
            dset_name = f"{config_name} [Slot {slot}: SIS 3302 ch {ch}]"
            hdset_name = f"{dset_name} headers"

            hdata = self.dgroup[hdset_name][...]
            names = list(hdata.dtype.names)
            names.remove("Shot number")
            hdata2 = hdata[names]

            self.dgroup.move(hdset_name, hdset_name + "Q")
            self.dgroup.create_dataset(hdset_name, data=hdata2)
        with self.assertWarns(UserWarning):
            _map = self.map

            self.assertNotIn(brd, [conn[0] for conn in _map.configs[config_name][adc]])
        for ch in chs:
            dset_name = f"{config_name} [Slot {slot}: SIS 3302 ch {ch}]"
            hdset_name = f"{dset_name} headers"
            del self.dgroup[hdset_name]
            self.dgroup.move(hdset_name + "Q", hdset_name)

    def test_mappings(self):
        """Test various digitizer group setups."""
        # -- One Config & One Active Config                         ----
        # -- & One Active ADC (SIS 3302)                            ----
        # setup faux group
        config_name = "config01"
        adc = "SIS 3302"
        my_sabc = [
            (5, adc, 1, (1, 3, 5)),
            (9, adc, 3, (1, 2, 3, 4)),
            (11, adc, 4, (5, 6, 7)),
        ]  # type: List[Tuple[int, str, int, Tuple[int, ...]]]
        dtype = self.mod.knobs.active_brdch.dtype
        bc_arr = np.zeros((), dtype=dtype)
        for slot, adc, brd, chns in my_sabc:
            for ch in chns:
                bc_arr[adc][brd - 1][ch - 1] = True
        self.mod.knobs.active_brdch = bc_arr

        # test
        _map = self.map
        self.assertDigitizerMapBasics(_map, self.dgroup)
        self.assertEqual(_map.active_configs, [config_name])
        self.assertEqual(list(_map.configs), [config_name])
        self.assertEqual(_map.configs[config_name]["adc"], (adc,))
        self.assertConnectionsEqual(
            _map, tuple([(stuff[2], stuff[3]) for stuff in my_sabc]), adc, config_name
        )

        # -- One Config & One Active Config                         ----
        # -- & One Active ADC (SIS 3305)                            ----
        # setup faux group
        config_name = "config01"
        adc = "SIS 3305"
        my_sabc = [
            (13, adc, 1, (1,)),
            (15, adc, 2, (1, 4, 7)),
        ]  # type: List[Tuple[int, str, int, Tuple[int, ...]]]
        dtype = self.mod.knobs.active_brdch.dtype
        bc_arr = np.zeros((), dtype=dtype)
        for slot, adc, brd, chns in my_sabc:
            for ch in chns:
                bc_arr[adc][brd - 1][ch - 1] = True
        self.mod.knobs.active_brdch = bc_arr

        # test
        _map = self.map
        self.assertDigitizerMapBasics(_map, self.dgroup)
        self.assertEqual(_map.active_configs, [config_name])
        self.assertEqual(list(_map.configs), [config_name])
        self.assertEqual(_map.configs[config_name]["adc"], (adc,))
        self.assertConnectionsEqual(
            _map, tuple([(stuff[2], stuff[3]) for stuff in my_sabc]), adc, config_name
        )

        # -- Multiple Configs & One Active Config                   ----
        # -- & MULTIPULE Active ADCs                                ---
        # setup faux group
        config_name = "config02"
        # adc = 'SIS 3302'
        self.mod.knobs.n_configs = 3
        self.mod.knobs.active_config = config_name
        my_sabc = [
            (5, "SIS 3302", 1, (1, 3, 5)),
            (9, "SIS 3302", 3, (1, 2, 3, 4)),
            (15, "SIS 3305", 2, (1, 4, 7)),
        ]  # type: List[Tuple[int, str, int, Tuple[int, ...]]]
        dtype = self.mod.knobs.active_brdch.dtype
        bc_arr = np.zeros((), dtype=dtype)
        for slot, adc, brd, chns in my_sabc:
            for ch in chns:
                bc_arr[adc][brd - 1][ch - 1] = True
        self.mod.knobs.active_brdch = bc_arr

        # test
        _map = self.map
        self.assertDigitizerMapBasics(_map, self.dgroup)
        self.assertEqual(_map.active_configs, [config_name])
        self.assertEqual(sorted(list(_map.configs)), sorted(self.mod.config_names))
        for adc in ("SIS 3302", "SIS 3305"):
            self.assertIn(adc, _map.configs[config_name]["adc"])

            conns = []
            for stuff in my_sabc:
                if stuff[1] == adc:
                    conns.append((stuff[2], stuff[3]))

            self.assertConnectionsEqual(_map, tuple(conns), adc, config_name)

        # -- Multiple Configs & Two Active Config                   ----
        # setup faux group
        config_names = ("config02", "config03")
        adc = "SIS 3302"
        self.mod.knobs.n_configs = 3
        self.mod.knobs.active_config = config_names
        my_sabc = [
            (5, adc, 1, (1, 3, 5)),
            (9, adc, 3, (1, 2, 3, 4)),
            (11, adc, 4, (5, 6, 7)),
        ]  # type: List[Tuple[int, str, int, Tuple[int, ...]]]
        dtype = self.mod.knobs.active_brdch.dtype
        bc_arr = np.zeros((), dtype=dtype)
        for slot, adc, brd, chns in my_sabc:
            for ch in chns:
                bc_arr[adc][brd - 1][ch - 1] = True
        self.mod.knobs.active_brdch = bc_arr

        # test
        _map = self.map
        self.assertDigitizerMapBasics(_map, self.dgroup)
        self.assertEqual(sorted(_map.active_configs), sorted(list(config_names)))
        self.assertEqual(sorted(list(_map.configs)), sorted(self.mod.config_names))
        for config_name in config_names:
            self.assertEqual(_map.configs[config_name]["adc"], (adc,))
            self.assertConnectionsEqual(
                _map, tuple([(stuff[2], stuff[3]) for stuff in my_sabc]), adc, config_name
            )

    def test_misc(self):
        """
        Test misc behavior the does not fit into other test methods.
        """
        # setup
        config_name = "config01"
        config_path = config_name
        self.mod.knobs.n_configs = 2
        self.mod.knobs.active_config = config_name
        adc = "SIS 3302"
        my_sabc = [
            (5, adc, 1, (1, 3, 5)),
            (9, adc, 3, (1, 2, 3, 4)),
            (11, adc, 4, (5, 6, 7)),
        ]  # type: List[Tuple[int, str, int, Tuple[int, ...]]]
        dtype = self.mod.knobs.active_brdch.dtype
        bc_arr = np.zeros((), dtype=dtype)
        for slot, adc, brd, chns in my_sabc:
            for ch in chns:
                bc_arr[adc][brd - 1][ch - 1] = True
        self.mod.knobs.active_brdch = bc_arr

        # -- examine property `slot_info`                          ----
        _map = self.map  # type: HDFMapDigiSISCrate
        self.assertTrue(hasattr(_map, "slot_info"))
        self.assertIsInstance(type(_map).slot_info, property)
        self.assertIsInstance(_map.slot_info, dict)

        for key, val in _map.slot_info.items():
            self.assertIsInstance(key, int)
            self.assertIsInstance(val, tuple)
            self.assertEqual(len(val), 2)
            self.assertIsInstance(val[0], int)
            self.assertIn(val[1], ("SIS 3302", "SIS 3305"))

        # -- examine method `get_slot`                              ----
        self.assertTrue(hasattr(_map, "get_slot"))
        slot = my_sabc[0][0]
        adc = my_sabc[0][1]
        brd = my_sabc[0][2]
        si = _map.slot_info.copy()
        with mock.patch.object(
            HDFMapDigiSISCrate, "slot_info", new_callable=mock.PropertyMock
        ) as mock_si:
            mock_si.return_value = si

            # good inputs
            self.assertEqual(_map.get_slot(brd, adc), slot)
            self.assertTrue(mock_si.called)
            mock_si.reset_mock()

            # inputs do not correlate to a slot
            self.assertIsNone(_map.get_slot(-1, ""))
            self.assertTrue(mock_si.called)

        # -- adc config group has an 'Enabled *' keyword but does   ----
        # -- not match an expected pattern                          ----
        # everything is done as normal
        adc_config_name = "SIS crate 3302 configurations[0]"
        adc_group = self.dgroup[f"{config_path}/{adc_config_name}"]
        adc_group.attrs["Enabled B"] = np.bytes_("TRUE")
        self.assertDigitizerMapBasics(self.map, self.dgroup)
        del adc_group.attrs["Enabled B"]

        # -- config group attribute `Shot averaging (software)`     ----
        shot_key = "Shot averaging (software)"
        adc_config_name = "SIS crate 3302 configurations[0]"
        adc_config_path = f"{config_path}/{adc_config_name}"
        sh2a = self.dgroup[adc_config_path].attrs[shot_key]

        # `Shot averaging (software)' missing
        del self.dgroup[adc_config_path].attrs[shot_key]
        _map = self.map
        for conn in _map.configs[config_name][adc]:
            self.assertIsNone(conn[2]["shot average (software)"])

        # `Shots averaging (software)' is 0 or 1
        self.dgroup[adc_config_path].attrs[shot_key] = 1
        _map = self.map
        for conn in _map.configs[config_name][adc]:
            self.assertIsNone(conn[2]["shot average (software)"])

        # `Shot averaging (software)' is >1
        self.dgroup[adc_config_path].attrs[shot_key] = 5
        _map = self.map
        brd = my_sabc[0][2]
        for conn in _map.configs[config_name][adc]:
            if conn[0] == brd:
                self.assertEqual(conn[2]["shot average (software)"], 5)

        self.dgroup[adc_config_path].attrs[shot_key] = sh2a

        # -- config group attribute `Sample averaging (hardware)`   ----
        brd = my_sabc[0][2]
        sp2a_key = "Sample averaging (hardware)"
        adc_config_name = "SIS crate 3302 configurations[0]"
        adc_config_path = f"{config_path}/{adc_config_name}"
        sp2a = self.dgroup[adc_config_path].attrs[sp2a_key]

        # 'Sample averaging (hardware)' is missing
        del self.dgroup[adc_config_path].attrs[sp2a_key]
        _map = self.map
        for conn in _map.configs[config_name][adc]:
            if conn[0] == brd:
                self.assertIsNone(conn[2]["sample average (hardware)"])

        # 'Sample averaging (hardware)' is 0
        self.dgroup[adc_config_path].attrs[sp2a_key] = 0
        _map = self.map
        for conn in _map.configs[config_name][adc]:
            if conn[0] == brd:
                self.assertIsNone(conn[2]["sample average (hardware)"])

        # 'Sample averaging (hardware)' is 5
        self.dgroup[adc_config_path].attrs[sp2a_key] = 5
        _map = self.map
        for conn in _map.configs[config_name][adc]:
            if conn[0] == brd:
                self.assertEqual(conn[2]["sample average (hardware)"], 2**5)

        self.dgroup[adc_config_path].attrs[sp2a_key] = sp2a

        # -- config group attribute `clock rate`                    ----
        # * 'clock rate' is not a defined attribute for 'SIS 3302' and
        #   will always be 100 MHz
        #
        # setup
        config_name = "config01"
        config_path = config_name
        self.mod.knobs.n_configs = 2
        self.mod.knobs.active_config = config_name
        my_sabc = [
            (13, "SIS 3305", 1, (1, 3, 5)),
        ]  # type: List[Tuple[int, str, int, Tuple[int, ...]]]
        dtype = self.mod.knobs.active_brdch.dtype
        bc_arr = np.zeros((), dtype=dtype)
        for slot, adc, brd, chns in my_sabc:
            for ch in chns:
                bc_arr[adc][brd - 1][ch - 1] = True
        self.mod.knobs.active_brdch = bc_arr

        brd = my_sabc[0][2]
        adc = my_sabc[0][1]
        adc_config_name = "SIS crate 3305 configurations[0]"
        adc_config_path = f"{config_path}/{adc_config_name}"
        cr_mode = self.dgroup[adc_config_path].attrs["Channel mode"]

        # mode set to 0
        self.dgroup[adc_config_path].attrs["Channel mode"] = 0
        _map = self.map
        conns = _map.configs[config_name][adc]
        for conn in conns:
            if conn[0] == brd:
                self.assertEqual(conn[2]["clock rate"], u.Quantity(1.25, unit="GHz"))

        # mode set to 1
        self.dgroup[adc_config_path].attrs["Channel mode"] = 1
        _map = self.map
        conns = _map.configs[config_name][adc]
        for conn in conns:
            if conn[0] == brd:
                self.assertEqual(conn[2]["clock rate"], u.Quantity(2.5, unit="GHz"))

        # mode set to 2
        self.dgroup[adc_config_path].attrs["Channel mode"] = 2
        _map = self.map
        conns = _map.configs[config_name][adc]
        for conn in conns:
            if conn[0] == brd:
                self.assertEqual(conn[2]["clock rate"], u.Quantity(5.0, unit="GHz"))

        # mode is anything else
        self.dgroup[adc_config_path].attrs["Channel mode"] = 7
        _map = self.map
        conns = _map.configs[config_name][adc]
        for conn in conns:
            if conn[0] == brd:
                self.assertIsNone(conn[2]["clock rate"])

    def test_parse_config_name(self):
        """Test HDFMapDigiSIS3301 method `_parse_config_name`."""
        _map = self.map  # type: HDFMapDigiSISCrate
        self.assertTrue(hasattr(_map, "_parse_config_name"))

        # `name` is a config
        self.assertEqual(_map._parse_config_name("config01"), "config01")

        # `name` is not in the 'SIS crate' group
        self.assertIsNone(_map._parse_config_name("not a config"))

        # `name` specifies a dataset
        dset_name = _map.construct_dataset_name(
            1, 1, config_name="config01", adc="SIS 3302"
        )
        self.assertIsNone(_map._parse_config_name(dset_name))

        # config group is missing key attributes
        attrs = (
            "SIS crate board types",
            "SIS crate config indices",
            "SIS crate slot numbers",
        )
        for attr in attrs:
            val = self.dgroup["config01"].attrs[attr]
            del self.dgroup["config01"].attrs[attr]

            self.assertIsNone(_map._parse_config_name("config01"))

            self.dgroup["config01"].attrs[attr] = val


if __name__ == "__main__":
    ut.main()
