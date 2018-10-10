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

from bapsflib.utils.errors import HDFMappingError
from typing import (List, Tuple)
from unittest import mock

from .common import DigitizerTestCase
from ..siscrate import HDFMapDigiSISCrate


class TestSIS3305(DigitizerTestCase):
    """Test class for HDFMapDigiSISCrate"""

    DEVICE_NAME = 'SIS crate'
    DEVICE_PATH = '/Raw data + config/' + DEVICE_NAME
    MAP_CLASS = HDFMapDigiSISCrate

    def setUp(self):
        super().setUp()

    def tearDown(self):
        super().tearDown()

    def test_construct_dataset_name(self):
        """Test functionality of method `construct_dataset_name`"""
        # setup
        config_name = 'config01'
        adc = 'SIS 3302'
        # config_path = 'Configuration: {}'.format(config_name)
        my_sabc = [
            (5, adc, 1, (1, 3, 5)),
            (9, adc, 3, (1, 2, 3, 4)),
            (11, adc, 4, (5, 6, 7)),
        ]  # type: List[Tuple[int, str, int, Tuple[int, ...]]]
        bc_arr = self.mod.knobs.active_brdch
        bc_arr[...] = False
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
        dset_name = "{0} [Slot {1}: SIS 3302 ch {2}]".format(
            config_name, slot, ch)
        with self.assertWarns(UserWarning):
            self.assertEqual(self.map.construct_dataset_name(brd, ch),
                             dset_name)

        # not specified, and MULTIPLE active configs
        slot = my_sabc[0][0]
        adc = my_sabc[0][1]
        brd = my_sabc[0][2]
        ch = my_sabc[0][3][0]
        self.mod.knobs.active_config = (config_name, 'config02')
        self.assertRaises(ValueError,
                          self.map.construct_dataset_name, brd, ch)
        self.mod.knobs.active_config = config_name

        # not specified, and NO active configs
        slot = my_sabc[0][0]
        adc = my_sabc[0][1]
        brd = my_sabc[0][2]
        ch = my_sabc[0][3][0]
        _map = self.map
        with mock.patch.object(HDFMapDigiSISCrate, 'active_configs',
                               new_callable=mock.PropertyMock) \
                as mock_aconfig:
            mock_aconfig.return_value = []
            self.assertRaises(ValueError,
                              _map.construct_dataset_name, brd, ch)

        # `config_name` not in configs
        slot = my_sabc[0][0]
        adc = my_sabc[0][1]
        brd = my_sabc[0][2]
        ch = my_sabc[0][3][0]
        self.assertRaises(ValueError,
                          self.map.construct_dataset_name,
                          brd, ch, config_name='not a config')

        # `config_name` in configs but not active
        slot = my_sabc[0][0]
        adc = my_sabc[0][1]
        brd = my_sabc[0][2]
        ch = my_sabc[0][3][0]
        self.assertRaises(ValueError,
                          self.map.construct_dataset_name,
                          brd, ch, config_name='config02')

        # -- Handling of kwarg `adc`                                ----
        # `adc` not 'SIS 3302' or 'SIS 3305'
        slot = my_sabc[0][0]
        adc = my_sabc[0][1]
        brd = my_sabc[0][2]
        ch = my_sabc[0][3][0]
        self.assertRaises(ValueError,
                          self.map.construct_dataset_name,
                          brd, ch, adc='not a real SIS')

        # `adc` is None and there's only ONE active adc
        slot = my_sabc[0][0]
        adc = my_sabc[0][1]
        brd = my_sabc[0][2]
        ch = my_sabc[0][3][0]
        dset_name = "{0} [Slot {1}: SIS 3302 ch {2}]".format(
            config_name, slot, ch)
        with self.assertWarns(UserWarning):
            self.assertEqual(_map.construct_dataset_name(brd, ch),
                             dset_name)

        # `adc` is None and there's TWO active adc
        my_sabc = [
            (5, adc, 1, (1, 3, 5)),
            (9, adc, 3, (1, 2, 3, 4)),
            (13, 'SIS 3305', 1, (2, 6, 7)),
        ]  # type: List[Tuple[int, str, int, Tuple[int, ...]]]
        bc_arr = self.mod.knobs.active_brdch
        bc_arr[...] = False
        for slot, adc, brd, chns in my_sabc:
            for ch in chns:
                bc_arr[adc][brd - 1][ch - 1] = True
        self.mod.knobs.n_configs = 2
        self.mod.knobs.active_brdch = bc_arr
        slot = my_sabc[0][0]
        adc = my_sabc[0][1]
        brd = my_sabc[0][2]
        ch = my_sabc[0][3][0]
        dset_name = "{0} [Slot {1}: SIS 3302 ch {2}]".format(
            config_name, slot, ch)
        with self.assertWarns(UserWarning):
            self.assertEqual(self.map.construct_dataset_name(brd, ch),
                             dset_name)

        # -- `board` and `channel` combo not in configs             ----
        brd = 5  # SIS 3302 only goes up to board 4
        ch = 1
        self.assertRaises(ValueError,
                          self.map.construct_dataset_name, brd, ch)

        # -- calls to SIS 3305                                      ----
        # a channel that is on FPGA 1
        slot = my_sabc[2][0]
        adc = my_sabc[2][1]
        brd = my_sabc[2][2]
        ch = my_sabc[2][3][0]
        dset_name = "{0} [Slot {1}: SIS 3305 FPGA 1 ch {2}]".format(
            config_name, slot, ch)
        self.assertEqual(
            self.map.construct_dataset_name(
                brd, ch, config_name=config_name, adc=adc),
            dset_name)

        # a channel that is on FPGA 2
        slot = my_sabc[2][0]
        adc = my_sabc[2][1]
        brd = my_sabc[2][2]
        ch = my_sabc[2][3][-1]
        dset_name = "{0} [Slot {1}: SIS 3305 FPGA 2 ch {2}]".format(
            config_name, slot, ch - 4)
        self.assertEqual(
            self.map.construct_dataset_name(
                brd, ch, config_name=config_name, adc=adc),
            dset_name)

        # -- return when `return_info=True`                         ----
        slot = my_sabc[0][0]
        adc = my_sabc[0][1]
        brd = my_sabc[0][2]
        ch = my_sabc[0][3][0]
        dset_name = "{0} [Slot {1}: SIS 3302 ch {2}]".format(
            config_name, slot, ch)
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
        keys = ('adc', 'bit', 'clock rate', 'configuration name',
                'digitizer', 'nshotnum', 'nt',
                'sample average (hardware)',
                'shot average (software)')
        for key in keys:
            self.assertIn(key, val[1])

            if key == 'adc':
                self.assertEqual(val[1][key], adc)
            elif key == 'configuration name':
                self.assertEqual(val[1][key], config_name)
            elif key == 'digitizer':
                self.assertEqual(val[1][key], _map.info['group name'])
            else:
                self.assertEqual(val[1][key], d_info[key])

    def test_construct_header_dataset_name(self):
        """
        Test functionality of method `construct_header_dataset_name`
        """
        # setup:
        config_name = 'config01'
        adc = 'SIS 3302'
        # config_path = 'Configuration: {}'.format(config_name)
        my_sabc = [
            (5, adc, 1, (1, 3, 5)),
            (9, adc, 3, (1, 2, 3, 4)),
            (11, adc, 4, (5, 6, 7)),
        ]  # type: List[Tuple[int, str, int, Tuple[int, ...]]]
        bc_arr = self.mod.knobs.active_brdch
        bc_arr[...] = False
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
        dset_name = "{0} [Slot {1}: SIS 3302 ch {2}]".format(
            config_name, slot, ch)
        hdset_name = dset_name + ' headers'
        _map = self.map
        with mock.patch.object(
                HDFMapDigiSISCrate, 'construct_dataset_name',
                wraps=_map.construct_dataset_name) as mock_cdn:

            name = _map.construct_header_dataset_name(
                brd, ch, return_info=True)

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
        config_name = 'config01'
        config_path = config_name
        adc = 'SIS 3302'
        my_sabc = [
            (5, adc, 1, (1, 3, 5)),
            (9, adc, 3, (1, 2, 3, 4)),
            (11, adc, 4, (5, 6, 7)),
        ]  # type: List[Tuple[int, str, int, Tuple[int, ...]]]
        bc_arr = self.mod.knobs.active_brdch
        bc_arr[...] = False
        for slot, adc, brd, chns in my_sabc:
            for ch in chns:
                bc_arr[adc][brd - 1][ch - 1] = True
        self.mod.knobs.active_brdch = bc_arr

        # -- failures that occur in `_find_adc_connections`         ----
        # defined configuration slot and indices are not 1D arrays   (1)
        cgroup = self.dgroup[config_path]
        slots = cgroup.attrs['SIS crate slot numbers']
        indices = cgroup.attrs['SIS crate config indices']
        cgroup.attrs['SIS crate slot numbers'] = \
            np.zeros((2, 3), dtype=np.uint32)
        with self.assertRaises(HDFMappingError):
            _map = self.map
        cgroup.attrs['SIS crate slot numbers'] = slots
        cgroup.attrs['SIS crate config indices'] = \
            np.zeros((2, 3), dtype=np.uint32)
        with self.assertRaises(HDFMappingError):
            _map = self.map
        cgroup.attrs['SIS crate config indices'] = indices

        # defined slot numbers and configuration indices are not     (2)
        # the same size
        cgroup.attrs['SIS crate slot numbers'] = np.append(slots, [13])
        with self.assertRaises(HDFMappingError):
            _map = self.map
        cgroup.attrs['SIS crate slot numbers'] = slots

        # defined slot numbers are not unique                        (3)
        slots2 = slots.copy()
        slots2[-1] = slots2[0]
        cgroup.attrs['SIS crate slot numbers'] = slots2
        with self.assertRaises(HDFMappingError):
            _map = self.map
        cgroup.attrs['SIS crate slot numbers'] = slots

        # for active config, configuration index is assigned to      (4)
        # multiple slots for the same adc
        cgroup = self.dgroup[config_path]
        indices = cgroup.attrs['SIS crate config indices']
        wrong_ii = indices.copy()
        wrong_ii[2] = indices[1]
        cgroup.attrs['SIS crate config indices'] = wrong_ii
        with self.assertRaises(HDFMappingError):
            _map = self.map
        cgroup.attrs['SIS crate config indices'] = indices

        # -- failures that occur in `_build_configs`                ----
        # group had no identifiable configuration group              (5)
        slots = cgroup.attrs['SIS crate slot numbers']
        del cgroup.attrs['SIS crate slot numbers']
        with self.assertRaises(HDFMappingError):
            _map = self.map
        cgroup.attrs['SIS crate slot numbers'] = slots

        # none of the configurations are active                      (6)
        self.dgroup.move(config_path, 'Not used')
        with self.assertRaises(HDFMappingError):
            _map = self.map
        self.dgroup.move('Not used', config_path)

        # for active config, no adc's identified                     (7)
        brd_types = cgroup.attrs[
            'SIS crate board types']  # type: np.ndarray
        cgroup.attrs['SIS crate board types'] = \
            np.array([5] * brd_types.size, dtype=brd_types.dtype)
        with self.assertRaises(HDFMappingError):
            _map = self.map
        cgroup.attrs['SIS crate board types'] = brd_types

        # adc connections for active config are NULL                 (8)
        names = list(cgroup)
        for name in names:
            del cgroup[name]
        with self.assertRaises(HDFMappingError):
            _map = self.map

    def test_mappings(self):
        # -- One Config & One Active Config                         ----
        # -- & One Active ADC (SIS 3302)                            ----
        # setup faux group
        config_name = 'config01'
        adc = 'SIS 3302'
        my_sabc = [
            (5, adc, 1, (1, 3, 5)),
            (9, adc, 3, (1, 2, 3, 4)),
            (11, adc, 4, (5, 6, 7)),
        ]  # type: List[Tuple[int, str, int, Tuple[int, ...]]]
        bc_arr = self.mod.knobs.active_brdch
        bc_arr[...] = False
        for slot, adc, brd, chns in my_sabc:
            for ch in chns:
                bc_arr[adc][brd - 1][ch - 1] = True
        self.mod.knobs.active_brdch = bc_arr

        # test
        _map = self.map
        self.assertDigitizerMapBasics(_map, self.dgroup)
        self.assertEqual(_map.active_configs, [config_name])
        self.assertEqual(list(_map.configs), [config_name])
        self.assertEqual(_map.configs[config_name]['adc'], (adc,))
        self.assertConnectionsEqual(
            _map,
            tuple([(stuff[2], stuff[3])for stuff in my_sabc]),
            adc, config_name)

        # -- One Config & One Active Config                         ----
        # -- & One Active ADC (SIS 3305)                            ----
        # setup faux group
        config_name = 'config01'
        adc = 'SIS 3305'
        my_sabc = [
            (13, adc, 1, (1,)),
            (15, adc, 2, (1, 4, 7)),
        ]  # type: List[Tuple[int, str, int, Tuple[int, ...]]]
        bc_arr = self.mod.knobs.active_brdch
        bc_arr[...] = False
        for slot, adc, brd, chns in my_sabc:
            for ch in chns:
                bc_arr[adc][brd - 1][ch - 1] = True
        self.mod.knobs.active_brdch = bc_arr

        # test
        _map = self.map
        self.assertDigitizerMapBasics(_map, self.dgroup)
        self.assertEqual(_map.active_configs, [config_name])
        self.assertEqual(list(_map.configs), [config_name])
        self.assertEqual(_map.configs[config_name]['adc'], (adc,))
        self.assertConnectionsEqual(
            _map,
            tuple([(stuff[2], stuff[3]) for stuff in my_sabc]),
            adc, config_name)

        # -- Multiple Configs & One Active Config                   ----
        # -- & MULTIPULE Active ADCs                                ---
        # setup faux group
        config_name = 'config02'
        # adc = 'SIS 3302'
        self.mod.knobs.n_configs = 3
        self.mod.knobs.active_config = config_name
        my_sabc = [
            (5, 'SIS 3302', 1, (1, 3, 5)),
            (9, 'SIS 3302', 3, (1, 2, 3, 4)),
            (15, 'SIS 3305', 2, (1, 4, 7)),
        ]  # type: List[Tuple[int, str, int, Tuple[int, ...]]]
        bc_arr = self.mod.knobs.active_brdch
        bc_arr[...] = False
        for slot, adc, brd, chns in my_sabc:
            for ch in chns:
                bc_arr[adc][brd - 1][ch - 1] = True
        self.mod.knobs.active_brdch = bc_arr

        # test
        _map = self.map
        self.assertDigitizerMapBasics(_map, self.dgroup)
        self.assertEqual(_map.active_configs, [config_name])
        self.assertEqual(set(list(_map.configs)),
                         set(self.mod.config_names))
        for adc in ('SIS 3302', 'SIS 3305'):
            self.assertIn(adc, _map.configs[config_name]['adc'])

            conns = []
            for stuff in my_sabc:
                if stuff[1] == adc:
                    conns.append((stuff[2], stuff[3]))

            self.assertConnectionsEqual(
                _map, tuple(conns), adc, config_name)

        # -- Multiple Configs & Two Active Config                   ----
        # setup faux group
        config_names = ('config02', 'config03')
        adc = 'SIS 3302'
        self.mod.knobs.n_configs = 3
        self.mod.knobs.active_config = config_names
        my_sabc = [
            (5, adc, 1, (1, 3, 5)),
            (9, adc, 3, (1, 2, 3, 4)),
            (11, adc, 4, (5, 6, 7)),
        ]  # type: List[Tuple[int, str, int, Tuple[int, ...]]]
        bc_arr = self.mod.knobs.active_brdch
        bc_arr[...] = False
        for slot, adc, brd, chns in my_sabc:
            for ch in chns:
                bc_arr[adc][brd - 1][ch - 1] = True
        self.mod.knobs.active_brdch = bc_arr

        # test
        _map = self.map
        self.assertDigitizerMapBasics(_map, self.dgroup)
        self.assertEqual(_map.active_configs, list(config_names))
        self.assertEqual(list(_map.configs), self.mod.config_names)
        for config_name in config_names:
            self.assertEqual(_map.configs[config_name]['adc'], (adc,))
            self.assertConnectionsEqual(
                _map,
                tuple([(stuff[2], stuff[3]) for stuff in my_sabc]),
                adc, config_name)

    def test_misc(self):
        """
        Test misc behavior the does not fit into other test methods.
        """
        # TODO: test `get_slot`
        # TODO: test `slot_info`
        '''
        # setup
        config_name = 'config01'
        adc = 'SIS 3301'
        config_path = 'Configuration: {}'.format(config_name)
        my_bcs = [(0, (0, 3, 5)),
                  (3, (0, 1, 2, 3)),
                  (5, (5, 6, 7))]
        bc_arr = self.mod.knobs.active_brdch
        bc_arr[...] = False
        for brd, chns in my_bcs:
            bc_arr[brd, chns] = True
        self.mod.knobs.active_brdch = bc_arr

        # -- config group attribute `Shots to average`              ----
        sh2a = self.dgroup[config_path].attrs['Shots to average']

        # `Shots to average' missing
        del self.dgroup[config_path].attrs['Shots to average']
        _map = self.map
        for conn in _map.configs[config_name][adc]:
            self.assertIsNone(conn[2]['shot average (software)'])

        # `Shots to average' is 0 or 1
        self.dgroup[config_path].attrs['Shots to average'] = 1
        _map = self.map
        for conn in _map.configs[config_name][adc]:
            self.assertIsNone(conn[2]['shot average (software)'])

        # `Shots to average' is >1
        self.dgroup[config_path].attrs['Shots to average'] = 5
        _map = self.map
        for conn in _map.configs[config_name][adc]:
            self.assertEqual(conn[2]['shot average (software)'], 5)

        self.dgroup[config_path].attrs['Shots to average'] = sh2a

        # -- config group attribute `Samples to average`            ----
        sp2a = self.dgroup[config_path].attrs['Samples to average']

        # 'Samples to average' is missing
        del self.dgroup[config_path].attrs['Samples to average']
        _map = self.map
        for conn in _map.configs[config_name][adc]:
            self.assertIsNone(conn[2]['sample average (hardware)'])

        # 'Samples to average' is 'No averaging'
        self.dgroup[config_path].attrs['Samples to average'] = \
            np.bytes_('No averaging')
        _map = self.map
        for conn in _map.configs[config_name][adc]:
            self.assertIsNone(conn[2]['sample average (hardware)'])

        # 'Samples to average' does not match string
        # 'Average {} Samples'
        self.dgroup[config_path].attrs['Samples to average'] = \
            np.bytes_('hello')
        _map = self.map
        for conn in _map.configs[config_name][adc]:
            self.assertIsNone(conn[2]['sample average (hardware)'])

        # 'Samples to average' does match string 'Average {} Samples',
        # but can not be converted to int
        self.dgroup[config_path].attrs['Samples to average'] = \
            np.bytes_('Average 5.0 Samples')
        _map = None
        with self.assertWarns(UserWarning):
            _map = self.map
        for conn in _map.configs[config_name][adc]:
            self.assertIsNone(conn[2]['sample average (hardware)'])

        # 'Samples to average' does match string 'Average {} Samples',
        # and is converted to an int of 0 or 1
        for val in (0, 1):
            self.dgroup[config_path].attrs['Samples to average'] = \
                np.bytes_('Average {} Samples'.format(val))
            _map = self.map
            for conn in _map.configs[config_name][adc]:
                self.assertIsNone(conn[2]['sample average (hardware)'])

        # 'Samples to average' does match string 'Average {} Samples',
        # and is converted to an int >1
        self.dgroup[config_path].attrs['Samples to average'] = \
            np.bytes_('Average 5 Samples'.format(val))
        _map = self.map
        for conn in _map.configs[config_name][adc]:
            self.assertEqual(conn[2]['sample average (hardware)'], 5)
        '''
        self.fail()

    def test_parse_config_name(self):
        """Test HDFMapDigiSIS3301 method `_parse_config_name`."""
        _map = self.map  # type: HDFMapDigiSISCrate
        self.assertTrue(hasattr(_map, '_parse_config_name'))

        # `name` is a config
        self.assertEqual(_map._parse_config_name('config01'),
                         'config01')

        # `name` is not in the 'SIS crate' group
        self.assertIsNone(_map._parse_config_name('not a config'))

        # `name` specifies a dataset
        dset_name = _map.construct_dataset_name(
            1, 1, config_name='config01', adc='SIS 3302')
        self.assertIsNone(_map._parse_config_name(dset_name))

        # config group is missing key attributs
        attrs = ('SIS crate board types', 'SIS crate config indices',
                 'SIS crate slot numbers')
        for attr in attrs:
            val = self.dgroup['config01'].attrs[attr]
            del self.dgroup['config01'].attrs[attr]

            self.assertIsNone(_map._parse_config_name('config01'))

            self.dgroup['config01'].attrs[attr] = val


if __name__ == '__main__':
    ut.main()
