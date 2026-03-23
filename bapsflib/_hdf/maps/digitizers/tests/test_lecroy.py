import numpy as np
import unittest as ut

from unittest import mock

from bapsflib._hdf.maps.digitizers.lecroy import HDFMapDigiLeCroy180E
from bapsflib._hdf.maps.digitizers.tests.common import DigitizerTestCase
from bapsflib._hdf.maps.digitizers.tests.fauxlecroy180e import FauxLeCroy180E
from bapsflib.utils.exceptions import HDFMappingError
from bapsflib.utils.warnings import HDFMappingWarning


class TestLeCroy180E(DigitizerTestCase):
    """Test class for HDFMapDigiLeCroy180E."""

    DEVICE_NAME = "LeCroy_scope"
    DEVICE_PATH = f"Raw data + config/{DEVICE_NAME}"
    MAP_CLASS = HDFMapDigiLeCroy180E

    def test_device_adcs(self):
        self.assertEqual(self.MAP_CLASS._device_adcs, ("lecroy",))

    def test_construct_dataset_name(self):
        _map = self.map

        cases = [
            # (kwargs, expected)
            (
                {"board": 0, "channel": 1},
                "Channel1",
            ),
            (
                {"board": 0, "channel": 2, "config_name": "lecroy", "adc": "lecroy"},
                "Channel2",
            ),
        ]
        for kwargs, expected in cases:
            with self.subTest(kwargs=kwargs, expected=expected):
                self.assertEqual(_map.construct_dataset_name(**kwargs), expected)

    def test_construct_dataset_name_raises(self):
        _map = self.map

        cases = [
            # (_raises, kwargs)
            # config_name not None or 'lecroy
            (
                ValueError,
                {"board": 0, "channel": 1, "config_name": 1, "adc": "lecroy"},
            ),
            (
                ValueError,
                {
                    "board": 0,
                    "channel": 1,
                    "config_name": "not lecroy",
                    "adc": "lecroy",
                },
            ),
            # adc not None or 'lecroy
            (
                ValueError,
                {"board": 0, "channel": 1, "config_name": None, "adc": "not lecroy"},
            ),
            (
                ValueError,
                {"board": 0, "channel": 1, "config_name": None, "adc": 5},
            ),
            # board is not 0
            (
                ValueError,
                {"board": 1, "channel": 1, "config_name": None, "adc": None},
            ),
            (
                ValueError,
                {"board": "not an int", "channel": 1, "config_name": None, "adc": None},
            ),
            # channel is not in (1, 2, 3, 4)
            (
                ValueError,
                {"board": 0, "channel": -1, "config_name": None, "adc": None},
            ),
            (
                ValueError,
                {"board": 0, "channel": 5, "config_name": None, "adc": None},
            ),
            (
                ValueError,
                {"board": 0, "channel": "not an int", "config_name": None, "adc": None},
            ),
            # specified channel is NOT active
            (
                ValueError,
                {"board": 0, "channel": 3, "config_name": None, "adc": None},
            ),
        ]
        for _raises, kwargs in cases:
            with self.subTest(_raises=_raises.__name__, kwargs=kwargs):
                self.assertRaises(_raises, _map.construct_dataset_name, **kwargs)

    def test_construct_header_dataset_name(self):
        _map = self.map

        with mock.patch.object(
            self.MAP_CLASS, "construct_dataset_name", wraps=_map.construct_dataset_name
        ) as mock_cdn:
            self.assertEqual(
                _map.construct_header_dataset_name(board=0, channel=1),
                "Headers/Channel1",
            )
            self.assertTrue(mock_cdn.called)

    def test_map_failure_no_headers_group(self):
        # Remove Headers group
        del self.mod["Headers"]

        with self.assertRaises(HDFMappingError):
            _map = self.map

    def test_map_failure_no_active_channels(self):
        # Remove Headers group
        self.mod.knobs.active_channels = None

        with self.assertRaises(HDFMappingError):
            _map = self.map

    def test_map_warning_channel_dset_has_fields(self):
        _mod = self.mod
        dset_name = "Channel1"
        del _mod[dset_name]

        data = np.ones(3, dtype=[("f1", np.int16), ("f2", np.int16)])
        _mod.create_dataset(dset_name, data=data)

        with self.assertWarns(HDFMappingWarning):
            _map = self.map

            # channel 1 is not included in the mapping
            self.assertEqual(_map.configs["lecroy"]["lecroy"][0][1], (2, ))

    def test_map_warning_channel_dset_not_2d(self):
        _mod = self.mod
        dset_name = "Channel1"
        del _mod[dset_name]

        data = np.ones((3, 100, 3), dtype=np.int16)
        _mod.create_dataset(dset_name, data=data)

        with self.assertWarns(HDFMappingWarning):
            _map = self.map

            # channel 1 is not included in the mapping
            self.assertEqual(_map.configs["lecroy"]["lecroy"][0][1], (2,))

    def test_map_failure_channel_dset_inconsistent_time_size(self):
        _mod = self.mod
        dset_name = "Channel1"
        del _mod[dset_name]

        sn_size = _mod.knobs.sn_size
        nt = _mod.knobs.nt
        data = np.ones((sn_size, nt + 10), dtype=np.int16)
        _mod.create_dataset(dset_name, data=data)

        with self.assertRaises(HDFMappingError):
            _map = self.map

    def test_map_failure_channel_dset_inconsistent_sn_size(self):
        _mod = self.mod
        dset_name = "Channel1"
        del _mod[dset_name]

        sn_size = _mod.knobs.sn_size
        nt = _mod.knobs.nt
        data = np.ones((sn_size + 10, nt), dtype=np.int16)
        _mod.create_dataset(dset_name, data=data)

        with self.assertRaises(HDFMappingError), self.assertWarns(HDFMappingWarning):
            _map = self.map

    def test_map_failure_all_channel_dset_and_header_size_inconsistent(self):
        _mod = self.mod
        del _mod["Headers/Channel1"]
        del _mod["Headers/Channel2"]

        sn_size = _mod.knobs.sn_size
        nt = _mod.knobs.nt
        data = np.ones((sn_size + 10, nt), dtype=np.int16)
        _mod["Headers"].create_dataset("Channel1", data=data)
        _mod["Headers"].create_dataset("Channel2", data=data)

        with self.assertRaises(HDFMappingError), self.assertWarns(HDFMappingWarning):
            _map = self.map

    def test_channel_does_not_have_header_dset(self):
        _mod = self.mod
        del _mod["Headers/Channel1"]

        _map = self.map

        # channel 1 is not included in the mapping
        self.assertEqual(_map.configs["lecroy"]["lecroy"][0][1], (2,))

    def test_channel_dset_is_actually_a_group(self):
        _mod = self.mod
        del _mod["Channel1"]
        _mod.create_group("Channel1")

        _map = self.map

        # channel 1 is not included in the mapping
        self.assertEqual(_map.configs["lecroy"]["lecroy"][0][1], (2,))

    def test_channel_dset_recorded_false(self):
        _mod = self.mod
        _mod["Channel1"].attrs["recorded"] = np.False_

        _map = self.map

        # channel 1 is not included in the mapping
        self.assertEqual(_map.configs["lecroy"]["lecroy"][0][1], (2,))

    def test_time_dset_not_1d_or_2d(self):
        _mod = self.mod
        del _mod["time"]

        nt = _mod.knobs.nt
        data = np.ones((2, 2, nt), dtype=np.int16)
        _mod.create_dataset("time", data=data)

        with self.assertWarns(HDFMappingWarning):
            _map = self.map
            connections = _map.configs["lecroy"]["lecroy"][0]
            self.assertTrue("time_dset_path" not in connections[2])

    def test_time_dset_inconsistent_1d_size(self):
        _mod = self.mod
        del _mod["time"]

        nt = _mod.knobs.nt
        data = np.ones((nt + 2), dtype=np.int16)
        _mod.create_dataset("time", data=data)

        with self.assertWarns(HDFMappingWarning):
            _map = self.map
            connections = _map.configs["lecroy"]["lecroy"][0]
            self.assertTrue("time_dset_path" not in connections[2])

    def test_time_dset_inconsistent_2d_size(self):
        _mod = self.mod
        del _mod["time"]

        sn_size = _mod.knobs.sn_size
        nt = _mod.knobs.nt
        data = np.ones((sn_size + 2, nt + 2), dtype=np.int16)
        _mod.create_dataset("time", data=data)

        with self.assertWarns(HDFMappingWarning):
            _map = self.map
            connections = _map.configs["lecroy"]["lecroy"][0]
            self.assertTrue("time_dset_path" not in connections[2])

    def test_time_dset_missing(self):
        _mod = self.mod
        del _mod["time"]

        with self.assertWarns(HDFMappingWarning):
            _map = self.map
            connections = _map.configs["lecroy"]["lecroy"][0]
            self.assertTrue("time_dset_path" not in connections[2])

    def test_config(self):
        _map = self.map
        _mod = self.mod  # type: FauxLeCroy180E

        self.assertEqual(set(_map.configs), {"lecroy"})
        self.assertTrue(_map.configs["lecroy"]["active"])
        self.assertEqual(_map.configs["lecroy"]["adc"], ("lecroy", ))
        self.assertEqual(_map.configs["lecroy"]["config group path"], _mod.name)
        self.assertIs(_map.configs["lecroy"]["shotnum"], None)
        self.assertTrue(len(_map.configs["lecroy"]["lecroy"]), 1)

        board = _map.configs["lecroy"]["lecroy"][0][0]
        channels = _map.configs["lecroy"]["lecroy"][0][1]
        setup = _map.configs["lecroy"]["lecroy"][0][2]
        self.assertEqual(board, 0)
        self.assertEqual(channels, (1, 2))

        self.assertIs(setup["bit"], None)
        self.assertIs(setup["clock rate"], None)
        self.assertEqual(setup["nshotnum"], _mod.knobs.sn_size)
        self.assertEqual(setup["nt"], _mod.knobs.nt)
        self.assertIs(setup["sample average (hardware)"], None)
        self.assertIs(setup["shot average (software)"], None)
        self.assertEqual(
            setup["channel_labels"],
            tuple(_mod._channel_labels[ii - 1] for ii in channels),
        )
        self.assertEqual(setup["time_dset_path"], "time")
