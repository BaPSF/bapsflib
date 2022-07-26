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
import unittest as ut

from numpy.lib import recfunctions as rfn
from unittest import mock

from bapsflib._hdf.maps.digitizers.sis3301 import HDFMapDigiSIS3301
from bapsflib._hdf.maps.digitizers.tests.common import DigitizerTestCase
from bapsflib.utils.exceptions import HDFMappingError


class TestSIS3301(DigitizerTestCase):
    """Test class for HDFMapDigiSIS3301"""

    DEVICE_NAME = "SIS 3301"
    DEVICE_PATH = f"/Raw data + config/{DEVICE_NAME}"
    MAP_CLASS = HDFMapDigiSIS3301

    def setUp(self):
        super().setUp()

    def tearDown(self):
        super().tearDown()

    def test_construct_dataset_name(self):
        """Test functionality of method `construct_dataset_name`"""
        # setup
        config_name = "config01"
        adc = "SIS 3301"
        # config_path = 'Configuration: {}'.format(config_name)
        my_bcs = [(0, (0, 3, 5)), (3, (0, 1, 2, 3)), (5, (5, 6, 7))]
        bc_arr = self.mod.knobs.active_brdch
        bc_arr[...] = False
        for brd, chns in my_bcs:
            bc_arr[brd, chns] = True
        self.mod.knobs.n_configs = 2
        self.mod.knobs.active_brdch = bc_arr

        # -- Handling of kwarg `config_name`                        ----
        # not specified, and only ONE active config
        brd = my_bcs[0][0]
        ch = my_bcs[0][1][0]
        dset_name = f"{config_name} [{brd}:{ch}]"
        with self.assertWarns(UserWarning):
            self.assertEqual(self.map.construct_dataset_name(brd, ch), dset_name)

        # not specified, and MULTIPLE active configs
        brd = my_bcs[0][0]
        ch = my_bcs[0][1][0]
        self.mod.knobs.active_config = (config_name, "config02")
        self.assertRaises(ValueError, self.map.construct_dataset_name, brd, ch)
        self.mod.knobs.active_config = config_name

        # not specified, and NO active configs
        brd = my_bcs[0][0]
        ch = my_bcs[0][1][0]
        _map = self.map
        with mock.patch.object(
            HDFMapDigiSIS3301, "active_configs", new_callable=mock.PropertyMock
        ) as mock_aconfig:
            mock_aconfig.return_value = []
            self.assertRaises(ValueError, _map.construct_dataset_name, brd, ch)

        # `config_name` not in configs
        brd = my_bcs[0][0]
        ch = my_bcs[0][1][0]
        self.assertRaises(
            ValueError,
            self.map.construct_dataset_name,
            brd,
            ch,
            config_name="not a config",
        )

        # `config_name` in configs but not active
        brd = my_bcs[0][0]
        ch = my_bcs[0][1][0]
        self.assertRaises(
            ValueError, self.map.construct_dataset_name, brd, ch, config_name="config02"
        )

        # -- Handling of kwarg `adc`                                ----
        # `adc` not 'SIS 3301'
        brd = my_bcs[0][0]
        ch = my_bcs[0][1][0]
        self.assertRaises(
            ValueError, self.map.construct_dataset_name, brd, ch, adc="not SIS 3301"
        )

        # -- `board` and `channel` combo not in configs             ----
        brd = 1
        ch = 1
        for conn in my_bcs:
            if brd == conn[0] and ch in conn[1]:
                self.fail(
                    "test setup is incorrect, brd and ch should not be in connections"
                )
        self.assertRaises(ValueError, self.map.construct_dataset_name, brd, ch)

        # -- return when `return_info=True`                         ----
        brd = my_bcs[0][0]
        ch = my_bcs[0][1][0]
        dset_name = f"{config_name} [{brd}:{ch}]"
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
        # adc = 'SIS 3301'
        # config_path = 'Configuration: {}'.format(config_name)
        my_bcs = [(0, (0, 3, 5)), (3, (0, 1, 2, 3)), (5, (5, 6, 7))]
        bc_arr = self.mod.knobs.active_brdch
        bc_arr[...] = False
        for brd, chns in my_bcs:
            bc_arr[brd, chns] = True
        self.mod.knobs.n_configs = 2
        self.mod.knobs.active_brdch = bc_arr

        # `return_info` does NOT return extra info
        brd = my_bcs[0][0]
        ch = my_bcs[0][1][0]
        dset_name = f"{config_name} [{brd}:{ch}]"
        hdset_name = f"{dset_name} headers"
        _map = self.map
        with mock.patch.object(
            HDFMapDigiSIS3301, "construct_dataset_name", wraps=_map.construct_dataset_name
        ) as mock_cdn:

            name = _map.construct_header_dataset_name(brd, ch, return_info=True)

            # check `construct_dataset_name` was called
            self.assertTrue(mock_cdn.called)

            # check equality
            self.assertEqual(name, hdset_name)

    def test_map_failures(self):
        """Test scenarios that should raise HDFMappingError"""
        # 1. board config group missing attribute 'Board'
        # 2. more than one board config group (for the same config_name)
        #    defines the same board number
        # 3. channel config group missing attribute 'Channel'
        # 4. there are no identifiable configuration groups
        # 5. none of the configurations are active
        # 6. adc connections for active config are NULL
        #
        # setup group
        config_name = "config01"
        # adc = 'SIS 3301'
        config_path = f"Configuration: {config_name}"
        my_bcs = [(0, (0, 3, 5)), (3, (0, 1, 2, 3)), (5, (5, 6, 7))]
        bc_arr = self.mod.knobs.active_brdch
        bc_arr[...] = False
        for brd, chns in my_bcs:
            bc_arr[brd, chns] = True
        self.mod.knobs.active_brdch = bc_arr

        # -- failures that occur in `_find_adc_connections`         ----
        # attribute 'Board' missing in board config group
        path = f"{config_path}/Boards[0]"
        brd_group = self.dgroup[path]
        brd = brd_group.attrs["Board"]
        del brd_group.attrs["Board"]
        with self.assertRaises(HDFMappingError):
            _map = self.map
        brd_group.attrs["Board"] = brd

        # the same board number is defined multiple times for an active
        # configuration
        path = f"{config_path}/Boards[0]"
        path2 = f"{config_path}/Boards[{len(my_bcs)}]"
        brd = self.dgroup[path].attrs["Board"]
        self.dgroup.create_group(path2)
        self.dgroup[path2].attrs["Board"] = brd
        with self.assertRaises(HDFMappingError):
            _map = self.map
        del self.dgroup[path2]

        # attribute 'Channel' missing in channel config group
        brd_path = f"{config_path}/Boards[0]"
        ch_path = f"{brd_path}/Channels[0]"
        ch_group = self.dgroup[ch_path]
        ch = ch_group.attrs["Channel"]
        del ch_group.attrs["Channel"]
        with self.assertRaises(HDFMappingError):
            _map = self.map
        ch_group.attrs["Channel"] = ch

        # -- failures that occur in `_build_configs`                ----
        # group had no identifiable configuration group
        self.dgroup.move(config_path, "wrong config name")
        with self.assertRaises(HDFMappingError):
            _map = self.map
        self.dgroup.move("wrong config name", config_path)

        # none of the configurations are active
        self.dgroup.move(config_path, "Configuration: Not used")
        with self.assertRaises(HDFMappingError):
            _map = self.map
        self.dgroup.move("Configuration: Not used", config_path)

        # adc connections for active config are NULL
        brd_config_names = list(self.dgroup[config_path])
        for name in brd_config_names:
            path = f"{config_path}/{name}"
            del self.dgroup[path]
        with self.assertRaises(HDFMappingError):
            _map = self.map

    def test_map_warnings(self):
        """Test scenarios that should cause a UserWarning."""
        # 1.  a configuration group sub-group does not match naming
        #     scheme for a board config group
        # 2.  'Board' attribute for a board config group is not an int
        #     or np.integer
        # 3.  'Board' attribute for a board config group is a negative
        #     integer
        # 4.  for a none active config, two board groups define the same
        #     board number
        # 5.  a board config sub-group does not match the naming scheme
        #     for a channel group
        # 6.  'Channel' attribute for a channel config group is not an
        #     int or np.integer
        # 7.  'Channel' attribute for a channel config group is a
        #     negative integer
        # 8.  two channel config groups define the same channel number
        # 9.  the list of discovered channel numbers is NULL
        # 10. config group attribute 'Samples to average' is not
        #     convertible to int
        # 11. an expected dataset is missing
        # 12. all expected datasets for a board are missing
        # 13. dataset has fields
        # 14. dataset is not a 2D array
        # 15. number of dataset time samples not consistent for all
        #     channels connected to a board
        # 16. number of dataset shot numbers not consistent for all
        #     channels connect to a board, but are still consistent
        #     with their associated header dataset
        # 17. header dataset missing expected shot number field
        # 18. shot number field in header dataset does not have
        #     expected shape and/or dtype
        # 19. dataset and associated header dataset do not have same
        #     number of shot numbers
        # 20. after all the above checks, ensure the connected channels
        #     are not NULL for the board
        #
        # setup group
        config_name = "config01"
        adc = "SIS 3301"
        config_path = f"Configuration: {config_name}"
        my_bcs = [(0, (0, 3, 5)), (3, (0, 1, 2, 3)), (5, (5, 6, 7))]
        bc_arr = self.mod.knobs.active_brdch
        bc_arr[...] = False
        for brd, chns in my_bcs:
            bc_arr[brd, chns] = True
        self.mod.knobs.n_configs = 2
        self.mod.knobs.active_brdch = bc_arr

        # -- warnings that occur in `_find_adc_connections`         ----
        # configuration group sub-group does not match board group   (1)
        # name
        brd_path = f"{config_path}/Boards[0]"
        new_path = f"{config_path}/Not a board"
        self.dgroup.move(brd_path, new_path)
        with self.assertWarns(UserWarning):
            _map = self.map
        self.dgroup.move(new_path, brd_path)

        # 'Board' attribute for a board config group is not an int   (2)
        # or np.integer
        brd_path = f"{config_path}/Boards[0]"
        brd_group = self.dgroup[brd_path]
        brd = brd_group.attrs["Board"]
        brd_group.attrs["Board"] = "five"
        with self.assertWarns(UserWarning):
            _map = self.map

            self.assertNotIn("five", [conn[0] for conn in _map.configs[config_name][adc]])

        # 'Board' attribute for a board config group is a negative   (3)
        # int
        brd_group.attrs["Board"] = -1
        with self.assertWarns(UserWarning):
            _map = self.map

            self.assertNotIn(-1, [conn[0] for conn in _map.configs[config_name][adc]])
        brd_group.attrs["Board"] = brd

        # for none active config, two board config groups define     (4)
        # the same board number
        path = "Configuration: config02/Boards[0]"
        path2 = "Configuration: config02/Boards[1]"
        brd = self.dgroup[path2].attrs["Board"]
        self.dgroup[path2].attrs["Board"] = self.dgroup[path].attrs["Board"]
        with self.assertWarns(UserWarning):
            _map = self.map

            self.assertNotIn(brd, [conn[0] for conn in _map.configs["config02"][adc]])
        self.dgroup[path2].attrs["Board"] = brd

        # a board config group sub-group does not match naming       (5)
        # scheme for a channel group
        brd_path = f"{config_path}/Boards[0]"
        ch_path = f"{brd_path}/Channels[0]"
        new_path = f"{brd_path}/Not a channel"
        self.dgroup.move(ch_path, new_path)
        with self.assertWarns(UserWarning):
            _map = self.map
        self.dgroup.move(new_path, ch_path)

        # 'Channel' attribute for a channel config group is not an   (6)
        # int or np.integer
        brd_path = f"{config_path}/Boards[0]"
        ch_path = f"{brd_path}/Channels[0]"
        ch_group = self.dgroup[ch_path]
        brd = self.dgroup[brd_path].attrs["Board"]
        ch = ch_group.attrs["Channel"]
        ch_group.attrs["Channel"] = "five"
        with self.assertWarns(UserWarning):
            _map = self.map

            chs = None
            for conn in _map.configs[config_name][adc]:
                if conn[0] == brd:
                    chs = conn[1]

            if chs is None:
                self.fail("board missing from connections")
            else:
                self.assertNotIn("five", chs)

        # 'Channel' attribute for a channel config group is a        (7)
        # negative int
        ch_group.attrs["Channel"] = -1
        with self.assertWarns(UserWarning):
            _map = self.map

            chs = None
            for conn in _map.configs[config_name][adc]:
                if conn[0] == brd:
                    chs = conn[1]

            if chs is None:
                self.fail("board missing from connections")
            else:
                self.assertNotIn(-1, chs)
        ch_group.attrs["Channel"] = ch

        # two channel config groups define the same channel number   (8)
        path = f"{brd_path}/Channels[0]"
        path2 = f"{brd_path}/Channels[1]"
        brd = self.dgroup[brd_path].attrs["Board"]
        ch = self.dgroup[path2].attrs["Channel"]
        self.dgroup[path2].attrs["Channel"] = self.dgroup[path].attrs["Channel"]
        with self.assertWarns(UserWarning):
            _map = self.map

            self.assertNotIn(brd, [conn[0] for conn in _map.configs[config_name][adc]])
        self.dgroup[path2].attrs["Channel"] = ch

        # the list of discovered channel numbers is NULL             (9)
        # - this could happen if there are no channel config groups
        brd_path = f"{config_path}/Boards[0]"
        brd = self.dgroup[brd_path].attrs["Board"]
        ch_group_names = list(self.dgroup[brd_path])
        for name in ch_group_names:
            old_path = f"{brd_path}/{name}"
            new_path = old_path + "Q"
            self.dgroup.move(old_path, new_path)
        with self.assertWarns(UserWarning):
            _map = self.map

            self.assertNotIn(brd, [conn[0] for conn in _map.configs[config_name][adc]])
        for name in ch_group_names:
            old_path = f"{brd_path}/{name}"
            new_path = old_path + "Q"
            self.dgroup.move(new_path, old_path)

        # -- warnings that occur in `_adc_info_first_pass`          ----
        # config group attribute 'Samples to average' is not        (10)
        # convertible to int
        config_group = self.dgroup[config_path]
        s2a = config_group.attrs["Samples to average"]
        config_group.attrs["Samples to average"] = b"Average 9.0 Samples"
        with self.assertWarns(UserWarning):
            _map = self.map

            for conn in _map.configs[config_name][adc]:
                self.assertIsNone(conn[2]["sample average (hardware)"])
        config_group.attrs["Samples to average"] = s2a

        # -- warnings that occur in `_adc_info_second_pass`         ----
        # an expected dataset is missing                            (11)
        # i.e. the config groups define a board-channel combo that
        #      does not have an existing dataset
        brd = my_bcs[0][0]
        ch = my_bcs[0][1][0]
        dset_name = f"{config_name} [{brd}:{ch}]"
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

        # all expected datasets for a given board are missing       (12)
        brd = my_bcs[0][0]
        chs = my_bcs[0][1]
        for ch in chs:
            dset_name = f"{config_name} [{brd}:{ch}]"
            new_name = dset_name + "Q"
            self.dgroup.move(dset_name, new_name)
        with self.assertWarns(UserWarning):
            _map = self.map

            self.assertNotIn(brd, [conn[0] for conn in _map.configs[config_name][adc]])
        for ch in chs:
            dset_name = f"{config_name} [{brd}:{ch}]"
            new_name = dset_name + "Q"
            self.dgroup.move(new_name, dset_name)

        # datasets has fields                                       (13)
        brd = my_bcs[0][0]
        ch = my_bcs[0][1][0]
        dset_name = f"{config_name} [{brd}:{ch}]"
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

        # dataset is not a 2D array                                 (14)
        brd = my_bcs[0][0]
        ch = my_bcs[0][1][0]
        dset_name = f"{config_name} [{brd}:{ch}]"
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

        # number of dataset time samples not consistent for         (15)
        # all channels connected to board
        brd = my_bcs[0][0]
        ch = my_bcs[0][1][0]
        dset_name = f"{config_name} [{brd}:{ch}]"
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

        # number dataset shot numbers not consistent for all        (16)
        # channels connected to board, but are still consistent
        # with their associated header dataset
        brd = my_bcs[0][0]
        ch = my_bcs[0][1][0]
        dset_name = f"{config_name} [{brd}:{ch}]"
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

        # header dataset missing expected shot number field         (17)
        brd = my_bcs[0][0]
        ch = my_bcs[0][1][0]
        dset_name = f"{config_name} [{brd}:{ch}]"
        hdset_name = f"{dset_name} headers"
        hdata = self.dgroup[hdset_name][...]
        names = list(hdata.dtype.names)
        names.remove("Shot")
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

        # shot number field in header dataset does not have         (18)
        # expected shape and/or dtype
        brd = my_bcs[0][0]
        ch = my_bcs[0][1][0]
        dset_name = f"{config_name} [{brd}:{ch}]"
        hdset_name = f"{dset_name} headers"
        hdata = self.dgroup[hdset_name][...]
        self.dgroup.move(hdset_name, hdset_name + "Q")

        # wrong dtype
        hdata2 = np.empty(hdata.shape, dtype=[("Shot", np.float32)])
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
        hdata2 = np.empty(hdata.shape, dtype=[("Shot", np.uint32, 2)])
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

        # dataset and associated header dataset do not have same    (19)
        # number of shot numbers
        brd = my_bcs[0][0]
        ch = my_bcs[0][1][0]
        dset_name = f"{config_name} [{brd}:{ch}]"
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

        # after all the above checks, ensure the connected          (20)
        # channels are not NULL for the board
        # i.e. this could happen if all the header datasets for a
        #      given board are missing the shot number field
        brd = my_bcs[0][0]
        chs = my_bcs[0][1]
        for ch in chs:
            dset_name = f"{config_name} [{brd}:{ch}]"
            hdset_name = f"{dset_name} headers"

            hdata = self.dgroup[hdset_name][...]
            names = list(hdata.dtype.names)
            names.remove("Shot")
            hdata2 = hdata[names]

            self.dgroup.move(hdset_name, hdset_name + "Q")
            self.dgroup.create_dataset(hdset_name, data=hdata2)
        with self.assertWarns(UserWarning):
            _map = self.map

            self.assertNotIn(brd, [conn[0] for conn in _map.configs[config_name][adc]])
        for ch in chs:
            dset_name = f"{config_name} [{brd}:{ch}]"
            hdset_name = f"{dset_name} headers"
            del self.dgroup[hdset_name]
            self.dgroup.move(hdset_name + "Q", hdset_name)

    def test_mappings(self):
        """Test various digitizer group setups."""
        # -- One Config & One Active Config                         ----
        # setup faux group
        config_name = "config01"
        adc = "SIS 3301"
        my_bcs = [(0, (0, 3, 5)), (3, (0, 1, 2, 3)), (5, (5, 6, 7))]
        bc_arr = self.mod.knobs.active_brdch
        bc_arr[...] = False
        for brd, chns in my_bcs:
            bc_arr[brd, chns] = True
        self.mod.knobs.active_brdch = bc_arr

        # test
        _map = self.map
        self.assertDigitizerMapBasics(_map, self.dgroup)
        self.assertEqual(_map.active_configs, [config_name])
        self.assertEqual(list(_map.configs), [config_name])
        self.assertConnectionsEqual(_map, tuple(my_bcs), adc, config_name)

        # -- Multiple Configs & One Active Config                   ----
        # setup faux group
        config_name = "config02"
        adc = "SIS 3301"
        self.mod.knobs.n_configs = 3
        self.mod.knobs.active_config = config_name
        my_bcs = [(0, (1, 2, 3)), (3, (0, 1, 2, 3))]
        bc_arr = self.mod.knobs.active_brdch
        bc_arr[...] = False
        for brd, chns in my_bcs:
            bc_arr[brd, chns] = True
        self.mod.knobs.active_brdch = bc_arr

        # test
        _map = self.map
        self.assertDigitizerMapBasics(_map, self.dgroup)
        self.assertEqual(_map.active_configs, [config_name])
        self.assertEqual(sorted(list(_map.configs)), sorted(self.mod.config_names))
        self.assertConnectionsEqual(_map, tuple(my_bcs), adc, config_name)

        # -- Multiple Configs & Two Active Config                   ----
        # setup faux group
        config_names = ("config02", "config03")
        adc = "SIS 3301"
        self.mod.knobs.n_configs = 3
        self.mod.knobs.active_config = config_names
        my_bcs = [(0, (0, 3, 5)), (3, (0, 1, 2, 3)), (5, (5, 6, 7)), (8, (1,))]
        bc_arr = self.mod.knobs.active_brdch
        bc_arr[...] = False
        for brd, chns in my_bcs:
            bc_arr[brd, chns] = True
        self.mod.knobs.active_brdch = bc_arr

        # test
        _map = self.map
        self.assertDigitizerMapBasics(_map, self.dgroup)
        self.assertEqual(sorted(_map.active_configs), sorted(list(config_names)))
        self.assertEqual(sorted(list(_map.configs)), sorted(self.mod.config_names))
        for config_name in config_names:
            self.assertConnectionsEqual(_map, tuple(my_bcs), adc, config_name)

    def test_misc(self):
        """
        Test misc behavior the does not fit into other test methods.
        """
        # What's tested...
        #   1. Behavior of digitizer configuration group attribute
        #      `Shots to average`
        #   2. Behavior of digitizer configuration group attribute
        #      `Samples to average`
        #      - including when attribute is named 'Unnamed' instead
        #   4. Identifying header datasets with shot number field name
        #      of 'Shot number'
        #
        # setup
        config_name = "config01"
        adc = "SIS 3301"
        config_path = f"Configuration: {config_name}"
        my_bcs = [(0, (0, 3, 5)), (3, (0, 1, 2, 3)), (5, (5, 6, 7))]
        bc_arr = self.mod.knobs.active_brdch
        bc_arr[...] = False
        for brd, chns in my_bcs:
            bc_arr[brd, chns] = True
        self.mod.knobs.active_brdch = bc_arr

        # -- config group attribute `Shots to average`              ----
        sh2a = self.dgroup[config_path].attrs["Shots to average"]

        # `Shots to average' missing
        del self.dgroup[config_path].attrs["Shots to average"]
        _map = self.map
        for conn in _map.configs[config_name][adc]:
            self.assertIsNone(conn[2]["shot average (software)"])

        # `Shots to average' is 0 or 1
        self.dgroup[config_path].attrs["Shots to average"] = 1
        _map = self.map
        for conn in _map.configs[config_name][adc]:
            self.assertIsNone(conn[2]["shot average (software)"])

        # `Shots to average' is >1
        self.dgroup[config_path].attrs["Shots to average"] = 5
        _map = self.map
        for conn in _map.configs[config_name][adc]:
            self.assertEqual(conn[2]["shot average (software)"], 5)

        self.dgroup[config_path].attrs["Shots to average"] = sh2a

        # -- config group attribute `Samples to average`            ----
        sp2a = self.dgroup[config_path].attrs["Samples to average"]

        # 'Samples to average' is missing
        del self.dgroup[config_path].attrs["Samples to average"]
        _map = self.map
        for conn in _map.configs[config_name][adc]:
            self.assertIsNone(conn[2]["sample average (hardware)"])

        # 'Samples to average' is 'No averaging'
        self.dgroup[config_path].attrs["Samples to average"] = np.bytes_("No averaging")
        _map = self.map
        for conn in _map.configs[config_name][adc]:
            self.assertIsNone(conn[2]["sample average (hardware)"])

        # 'Samples to average' does not match string
        # 'Average {} Samples'
        self.dgroup[config_path].attrs["Samples to average"] = np.bytes_("hello")
        _map = self.map
        for conn in _map.configs[config_name][adc]:
            self.assertIsNone(conn[2]["sample average (hardware)"])

        # 'Samples to average' does match string 'Average {} Samples',
        # but can not be converted to int
        self.dgroup[config_path].attrs["Samples to average"] = np.bytes_(
            "Average 5.0 Samples"
        )
        _map = None
        with self.assertWarns(UserWarning):
            _map = self.map
        for conn in _map.configs[config_name][adc]:
            self.assertIsNone(conn[2]["sample average (hardware)"])

        # 'Samples to average' does match string 'Average {} Samples',
        # and is converted to an int of 0 or 1
        for val in (0, 1):
            self.dgroup[config_path].attrs["Samples to average"] = np.bytes_(
                f"Average {val} Samples"
            )
            _map = self.map
            for conn in _map.configs[config_name][adc]:
                self.assertIsNone(conn[2]["sample average (hardware)"])

        # 'Samples to average' does match string 'Average {} Samples',
        # and is converted to an int >1
        self.dgroup[config_path].attrs["Samples to average"] = np.bytes_(
            "Average 5 Samples"
        )
        _map = self.map
        for conn in _map.configs[config_name][adc]:
            self.assertEqual(conn[2]["sample average (hardware)"], 5)

        # 'Samples to average' is named 'Unnamed' instead, and valid
        # (as seen on some SmPD HDF5 files)
        del self.dgroup[config_path].attrs["Samples to average"]
        self.dgroup[config_path].attrs["Unnamed"] = np.bytes_("Average 2 Samples")
        _map = self.map
        for conn in _map.configs[config_name][adc]:
            self.assertEqual(conn[2]["sample average (hardware)"], 2)

        # 'Samples to average' is named 'Unnamed' instead, and is NOT a
        # byte string (as seen on some SmPD HDF5 files)
        self.dgroup[config_path].attrs["Unnamed"] = 5
        _map = self.map
        for conn in _map.configs[config_name][adc]:
            self.assertIsNone(conn[2]["sample average (hardware)"])
        del self.dgroup[config_path].attrs["Unnamed"]

        # restore original value
        self.dgroup[config_path].attrs["Samples to average"] = sp2a

        # -- header dataset with 'Shot number' field                ----
        # rename field for all board-channel connections
        for conn in my_bcs:
            brd = conn[0]
            for ch in conn[1]:
                dset_name = f"{config_name} [{brd}:{ch}]"
                hdset_name = f"{dset_name} headers"
                hdset = self.dgroup[hdset_name][...]
                hdset = rfn.rename_fields(hdset, {"Shot": "Shot number"})
                del self.dgroup[hdset_name]
                self.dgroup.create_dataset(hdset_name, data=hdset)

        _map = self.map
        self.assertEqual(
            _map.configs[config_name]["shotnum"]["dset field"], ("Shot number",)
        )

        # Note: module has NOT been reset to defaults at this point

    def test_parse_config_name(self):
        """Test HDFMapDigiSIS3301 method `_parse_config_name`."""
        _map = self.map  # type: HDFMapDigiSIS3301
        self.assertTrue(hasattr(_map, "_parse_config_name"))
        self.assertEqual(
            _map._parse_config_name("Configuration: all-probes"), "all-probes"
        )
        self.assertIsNone(_map._parse_config_name("Not a config"))


if __name__ == "__main__":
    ut.main()
