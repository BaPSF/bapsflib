import numpy as np
import unittest as ut

from unittest import mock

from bapsflib._hdf.maps.digitizers.lecroy import HDFMapDigiLeCroy180E
from bapsflib._hdf.maps.digitizers.tests.common import DigitizerTestCase
from bapsflib.utils.exceptions import HDFMappingError


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
